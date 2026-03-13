import asyncio
import logging
import os
import uuid
import httpx
from aiogram import Bot
from aiogram.types import FSInputFile

from config.settings import get_settings
from db.uow import SQLAlchemyUnitOfWork
from enums import GenerationStatus
from services.generation_service import GenerationService
from services.providers.ai_video_generators.hailuo import HailuoGenerator

logger = logging.getLogger(__name__)

class VideoGenerationWorker:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings = get_settings()
        self.generator = HailuoGenerator(api_key=self.settings.PIAPI_KEY)
        self._running = False
        # Mapping of localized messages for completion
        self._locales = {
            "ru": "✅ Ваше видео готово!",
            "en": "✅ Your video is ready!"
        }

    async def start(self):
        """Starts the worker loop."""
        if self._running:
            return
        self._running = True
        logger.info("VideoGenerationWorker started.")
        asyncio.create_task(self._loop())

    async def stop(self):
        """Stops the worker loop."""
        self._running = False
        logger.info("VideoGenerationWorker stopping...")

    async def _loop(self):
        while self._running:
            try:
                await self._process_tasks()
            except Exception as e:
                logger.error(f"Error in VideoGenerationWorker loop: {e}", exc_info=True)
            
            await asyncio.sleep(10) # Wait 10 seconds between passes

    async def _process_tasks(self):
        async with SQLAlchemyUnitOfWork() as uow:
            gs = GenerationService(uow)
            tasks = await gs.get_pending_and_processing()
            
            if not tasks:
                return

            logger.info(f"Worker found {len(tasks)} tasks to process.")
            for task in tasks:
                try:
                    await self._handle_task(task, gs, uow)
                except Exception as e:
                    logger.error(f"Failed to handle task {task.id}: {e}")

    async def _handle_task(self, task, gs: GenerationService, uow: SQLAlchemyUnitOfWork):
        # 1. Start generation if PENDING
        if task.status == GenerationStatus.PENDING:
            if not task.external_task_id:
                await self._initiate_generation(task, gs, uow)
            else:
                # Already has an external ID but still pending locally, move to processing
                await gs.update_status(task.id, GenerationStatus.PROCESSING)
                await uow.commit()

        # 2. Check status if PROCESSING
        elif task.status == GenerationStatus.PROCESSING:
            if not task.external_task_id:
                # This should not happen if initiated correctly, reset to pending?
                logger.warning(f"Task {task.id} is PROCESSING but has no external_task_id. Resetting to PENDING.")
                await gs.update_status(task.id, GenerationStatus.PENDING)
                await uow.commit()
                return

            await self._poll_generation(task, gs, uow)

    async def _initiate_generation(self, task, gs: GenerationService, uow: SQLAlchemyUnitOfWork):
        local_photo_path = None
        try:
            logger.info(f"Initiating generation for task {task.id}")
            # Download photo from Telegram
            os.makedirs(self.settings.MEDIA_ROOT, exist_ok=True)
            local_photo_path = os.path.join(self.settings.MEDIA_ROOT, f"input_{uuid.uuid4()}.jpg")
            
            # Note: We need to get the file from Telegram using the input_photo_path (file_id)
            file = await self.bot.get_file(task.input_photo_path)
            await self.bot.download_file(file.file_path, local_photo_path)

            # Start piAPI generation
            res = await self.generator.generate(local_photo_path, prompt=task.user_prompt or "cinematic video")
            
            if res.status == GenerationStatus.FAILED:
                raise Exception(res.error or "Failed to start generation in piAPI")

            # Update with external task ID and move to PROCESSING
            await gs.update_external_task_id(task.id, res.task_id)
            await gs.update_status(task.id, GenerationStatus.PROCESSING)
            await uow.commit()
            logger.info(f"Task {task.id} initiated with internal task ID {res.task_id}")

        except Exception as e:
            logger.error(f"Initiation failed for task {task.id}: {e}")
            await gs.update_status(task.id, GenerationStatus.FAILED, error_message=str(e))
            await uow.commit()
            await self.bot.send_message(task.user_id, f"❌ Ошибка при запуске генерации: {str(e)}")
        finally:
            if local_photo_path and os.path.exists(local_photo_path):
                os.remove(local_photo_path)

    async def _poll_generation(self, task, gs: GenerationService, uow: SQLAlchemyUnitOfWork):
        try:
            # We poll once per loop pass for each task
            status_info = await self.generator.check_status(task.external_task_id)
            
            if status_info.status == GenerationStatus.COMPLETED:
                logger.info(f"Task {task.id} COMPLETED.")
                await gs.update_status(task.id, GenerationStatus.COMPLETED, result_video_path=status_info.download_url)
                await uow.commit()
                
                # Download the video manually to avoid aiogram URLInputFile timeouts
                local_video_path = os.path.join(self.settings.MEDIA_ROOT, f"output_{uuid.uuid4()}.mp4")
                try:
                    logger.info(f"Downloading video for task {task.id} from {status_info.download_url}")
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        v_res = await client.get(status_info.download_url)
                        v_res.raise_for_status()
                        with open(local_video_path, "wb") as f:
                            f.write(v_res.content)
                    
                    video = FSInputFile(local_video_path)
                    msg = self._locales.get("ru")
                    await self.bot.send_video(task.user_id, video, caption=msg)
                    logger.info(f"Video sent for task {task.id}")
                except Exception as send_err:
                    logger.error(f"Failed to download/send video for task {task.id}: {send_err}")
                    # We already marked it as COMPLETED in DB, but couldn't send.
                    # Maybe tell user?
                    await self.bot.send_message(task.user_id, f"✅ Видео сгенерировано, но не удалось его отправить напрямую. Ссылка: {status_info.download_url}")
                finally:
                    if os.path.exists(local_video_path):
                        os.remove(local_video_path)
                
            elif status_info.status == GenerationStatus.FAILED:
                logger.error(f"Task {task.id} FAILED in piAPI: {status_info.error}")
                await gs.update_status(task.id, GenerationStatus.FAILED, error_message=status_info.error)
                await uow.commit()
                await self.bot.send_message(task.user_id, f"❌ Ошибка при генерации:\n{status_info.error}")

            # Check for timeout (optional, but good practice)
            # If created_at > 20 minutes ago and still processing, mark as failed
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            # Ensure task.created_at has timezone
            created_at = task.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=datetime.timezone.utc)
                
            if (now - created_at).total_seconds() > 1200: # 20 minutes
                 logger.warning(f"Task {task.id} timed out after 20 minutes.")
                 await gs.update_status(task.id, GenerationStatus.FAILED, error_message="Timed out after 20 minutes")
                 await uow.commit()
                 await self.bot.send_message(task.user_id, "❌ Время ожидания генерации истекло.")

        except Exception as e:
            logger.error(f"Polling failed for task {task.id}: {e}")
            # Don't fail the task immediately on network errors, just log and retry next loop
