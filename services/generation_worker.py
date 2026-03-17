import asyncio
import logging
import os
import uuid
import httpx
from aiogram import Bot
from aiogram.types import FSInputFile

from bot.keyboards.inline.private_keyboards import main_menu_kb
from bot.locales import en as en_locale
from bot.locales import ru as ru_locale
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
        self._texts = {
            "ru": {
                "main_menu": ru_locale.WELCOME_MAIN,
                "video_ready": ru_locale.GENERATION_VIDEO_READY,
                "started": ru_locale.GENERATION_DRAFT_STARTED,
                "progress": ru_locale.GENERATION_PROGRESS,
                "progress_no_pct": ru_locale.GENERATION_PROGRESS_NO_PERCENT,
                "completed": ru_locale.GENERATION_DRAFT_COMPLETED,
                "start_error": ru_locale.GENERATION_START_ERROR,
                "failed_error": ru_locale.GENERATION_FAILED_ERROR,
                "timeout_error": ru_locale.GENERATION_TIMEOUT_ERROR,
                "direct_send_failed": ru_locale.GENERATION_DIRECT_SEND_FAILED,
            },
            "en": {
                "main_menu": en_locale.WELCOME_MAIN,
                "video_ready": en_locale.GENERATION_VIDEO_READY,
                "started": en_locale.GENERATION_DRAFT_STARTED,
                "progress": en_locale.GENERATION_PROGRESS,
                "progress_no_pct": en_locale.GENERATION_PROGRESS_NO_PERCENT,
                "completed": en_locale.GENERATION_DRAFT_COMPLETED,
                "start_error": en_locale.GENERATION_START_ERROR,
                "failed_error": en_locale.GENERATION_FAILED_ERROR,
                "timeout_error": en_locale.GENERATION_TIMEOUT_ERROR,
                "direct_send_failed": en_locale.GENERATION_DIRECT_SEND_FAILED,
            },
        }

    async def _update_draft(self, user_id: int, draft_id: int, text: str, lang: str = "ru") -> None:
        """Update Telegram draft message. Logs and continues on failure."""
        try:
            await self.bot.send_message_draft(
                chat_id=user_id,
                draft_id=draft_id,
                text=text,
                reply_parameters=None,
            )
        except Exception as e:
            logger.debug(f"Draft update failed for task {draft_id}: {e}")

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
            processing_tasks = [t for t in tasks if t.status == GenerationStatus.PROCESSING]
            pending_tasks = [t for t in tasks if t.status == GenerationStatus.PENDING]
            pending_tasks.sort(key=lambda t: t.created_at)

            for task in processing_tasks:
                try:
                    await self._handle_task(task, gs, uow)
                except Exception as e:
                    logger.error(f"Failed to handle task {task.id}: {e}")

            max_concurrent = self.settings.MAX_CONCURRENT_GENERATIONS
            if max_concurrent <= 0:
                tasks_to_start = pending_tasks
            else:
                available_slots = max(max_concurrent - len(processing_tasks), 0)
                tasks_to_start = pending_tasks[:available_slots]

            for task in tasks_to_start:
                try:
                    await self._handle_task(task, gs, uow)
                except Exception as e:
                    logger.error(f"Failed to start queued task {task.id}: {e}")

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
        cleanup_local_photo = True
        try:
            logger.info(f"Initiating generation for task {task.id}")
            os.makedirs(self.settings.MEDIA_ROOT, exist_ok=True)
            if task.media_folder:
                generation_dir = os.path.join(self.settings.MEDIA_ROOT, task.media_folder)
                os.makedirs(generation_dir, exist_ok=True)
                local_photo_path = os.path.join(generation_dir, "photo.jpg")
                cleanup_local_photo = False
            else:
                # Backward compatibility for old rows without media_folder.
                local_photo_path = os.path.join(self.settings.MEDIA_ROOT, f"input_{uuid.uuid4()}.jpg")
            
            # Note: We need to get the file from Telegram using the input_photo_path (file_id)
            file = await self.bot.get_file(task.input_photo_path)
            await self.bot.download_file(file.file_path, local_photo_path)

            # Build prompt and negative_prompt from template or use user prompt as full (custom mode)
            prompt: str
            negative_prompt: str | None = None
            if task.template_id is not None:
                template = await uow.template_repo.get(task.template_id)
                if template:
                    parts = [template.base_prompt]
                    if task.user_prompt and task.user_prompt.strip():
                        parts.append(task.user_prompt.strip())
                    prompt = "\n".join(parts)
                    negative_prompt = template.negative_prompt
                else:
                    prompt = task.user_prompt or "cinematic video"
            else:
                # Custom prompt mode: user typed full prompt
                prompt = task.user_prompt or "cinematic video"

            final_prompt = prompt
            await gs.update_final_prompt(task.id, final_prompt)

            # Start piAPI generation
            res = await self.generator.generate(
                local_photo_path,
                prompt=prompt,
                negative_prompt=negative_prompt,
            )
            
            if res.status == GenerationStatus.FAILED:
                raise Exception(res.error or "Failed to start generation in piAPI")

            # Update with external task ID and move to PROCESSING
            await gs.update_external_task_id(task.id, res.task_id)
            await gs.update_status(task.id, GenerationStatus.PROCESSING)
            await uow.commit()
            loc = self._texts.get("ru", self._texts["en"])
            await self._update_draft(task.user_id, task.id, loc["started"])
            logger.info(f"Task {task.id} initiated with internal task ID {res.task_id}")

        except Exception as e:
            logger.error(f"Initiation failed for task {task.id}: {e}")
            await gs.update_status(task.id, GenerationStatus.FAILED, error_message=str(e))
            await uow.commit()
            loc = self._texts.get("ru", self._texts["en"])
            await self.bot.send_message(task.user_id, loc["start_error"].format(error=str(e)))
        finally:
            if cleanup_local_photo and local_photo_path and os.path.exists(local_photo_path):
                os.remove(local_photo_path)

    async def _poll_generation(self, task, gs: GenerationService, uow: SQLAlchemyUnitOfWork):
        try:
            # We poll once per loop pass for each task
            status_info = await self.generator.check_status(task.external_task_id)
            
            if status_info.status == GenerationStatus.COMPLETED:
                logger.info(f"Task {task.id} COMPLETED.")
                loc = self._texts.get("ru", self._texts["en"])
                await self._update_draft(task.user_id, task.id, loc["completed"])
                os.makedirs(self.settings.MEDIA_ROOT, exist_ok=True)

                if task.media_folder:
                    generation_dir = os.path.join(self.settings.MEDIA_ROOT, task.media_folder)
                    os.makedirs(generation_dir, exist_ok=True)
                    local_video_path = os.path.join(generation_dir, "video.mp4")
                    result_video_path = f"{task.media_folder}/video.mp4"
                    cleanup_local_video = False
                else:
                    # Backward compatibility for old rows without media_folder.
                    local_video_path = os.path.join(self.settings.MEDIA_ROOT, f"output_{uuid.uuid4()}.mp4")
                    result_video_path = status_info.download_url
                    cleanup_local_video = True

                await gs.update_status(task.id, GenerationStatus.COMPLETED, result_video_path=result_video_path)
                await uow.commit()

                try:
                    logger.info(f"Downloading video for task {task.id} from {status_info.download_url}")
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        v_res = await client.get(status_info.download_url)
                        v_res.raise_for_status()
                        with open(local_video_path, "wb") as f:
                            f.write(v_res.content)
                    
                    video = FSInputFile(local_video_path)
                    msg = loc["video_ready"]
                    await self.bot.send_video(task.user_id, video, caption=msg)
                    await self.bot.send_message(
                        task.user_id,
                        loc["main_menu"],
                        reply_markup=main_menu_kb(),
                    )
                    logger.info(f"Video sent for task {task.id}")
                except Exception as send_err:
                    logger.error(f"Failed to download/send video for task {task.id}: {send_err}")
                    # We already marked it as COMPLETED in DB, but couldn't send.
                    # Maybe tell user?
                    await self.bot.send_message(
                        task.user_id,
                        loc["direct_send_failed"].format(url=status_info.download_url),
                    )
                    await self.bot.send_message(
                        task.user_id,
                        loc["main_menu"],
                        reply_markup=main_menu_kb(),
                    )
                finally:
                    if cleanup_local_video and os.path.exists(local_video_path):
                        os.remove(local_video_path)
                
            elif status_info.status in (GenerationStatus.PENDING, GenerationStatus.PROCESSING):
                loc = self._texts.get("ru", self._texts["en"])
                if status_info.percent is not None:
                    text = loc["progress"].format(percent=status_info.percent)
                else:
                    text = loc["progress_no_pct"]
                await self._update_draft(task.user_id, task.id, text)
            elif status_info.status == GenerationStatus.FAILED:
                logger.error(f"Task {task.id} FAILED in piAPI: {status_info.error}")
                await gs.update_status(task.id, GenerationStatus.FAILED, error_message=status_info.error)
                await uow.commit()
                loc = self._texts.get("ru", self._texts["en"])
                await self.bot.send_message(task.user_id, loc["failed_error"].format(error=status_info.error))
                await self.bot.send_message(
                    task.user_id,
                    loc["main_menu"],
                    reply_markup=main_menu_kb(),
                )

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
                 loc = self._texts.get("ru", self._texts["en"])
                 await self.bot.send_message(task.user_id, loc["timeout_error"])
                 await self.bot.send_message(
                     task.user_id,
                     loc["main_menu"],
                     reply_markup=main_menu_kb(),
                 )

        except Exception as e:
            logger.error(f"Polling failed for task {task.id}: {e}")
            # Don't fail the task immediately on network errors, just log and retry next loop
