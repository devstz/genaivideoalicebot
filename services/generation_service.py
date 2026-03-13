from sqlalchemy import select
from db.models import Generation
from db.uow import SQLAlchemyUnitOfWork
from enums import GenerationStatus


class GenerationService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self.uow = uow

    async def create_generation_request(self, user_id: int, template_id: int, input_photo_path: str, user_prompt: str | None = None) -> Generation | None:
        """
        Attempts to create a generation request. Deducts 1 generation from balance if successful.
        Returns the created Generation object or None if insufficient balance.
        """
        balance = await self.uow.user_balance_repo.get_or_create(user_id)
        if balance.generations_remaining <= 0:
            return None

        # Subtract 1 generation
        await self.uow.user_balance_repo.subtract_generations(user_id, 1)

        # Create generation record
        generation = Generation(
            user_id=user_id,
            template_id=template_id,
            input_photo_path=input_photo_path,
            user_prompt=user_prompt,
            status=GenerationStatus.PENDING
        )
        
        return await self.uow.generation_repo.add(generation)

    async def update_status(self, generation_id: int, status: GenerationStatus, result_video_path: str | None = None, error_message: str | None = None) -> bool:
        generation = await self.uow.generation_repo.get(generation_id)
        if not generation:
            return False
            
        generation.status = status
        
        if result_video_path:
            generation.result_video_path = result_video_path
            
        if error_message:
            generation.error_message = error_message
            
        await self.uow.generation_repo.update(generation)
        return True

    async def get_pending_and_processing(self) -> list[Generation]:
        """Get all generations that are PENDING or PROCESSING."""
        stmt = select(Generation).where(
            Generation.status.in_([GenerationStatus.PENDING, GenerationStatus.PROCESSING])
        )
        result = await self.uow.session.execute(stmt)
        return list(result.scalars().all())

    async def update_external_task_id(self, generation_id: int, external_task_id: str) -> bool:
        generation = await self.uow.generation_repo.get(generation_id)
        if not generation:
            return False
        generation.external_task_id = external_task_id
        await self.uow.generation_repo.update(generation)
        return True
