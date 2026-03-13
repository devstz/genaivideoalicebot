import asyncio
import uuid
from typing import Any

from enums import GenerationStatus
from .base_generator import BaseGenerator, GenerationResult, GenerationStatusInfo


class MockGenerator(BaseGenerator):
    """Mock generator for development and testing."""
    
    def __init__(self):
        self._tasks: dict[str, GenerationStatus] = {}

    async def generate(self, image_path: str, prompt: str, negative_prompt: str | None = None, **kwargs) -> GenerationResult:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = GenerationStatus.PROCESSING
        
        # Simulate API call delay
        await asyncio.sleep(1)
        
        # Schedule the mock completion in the background
        asyncio.create_task(self._process_mock_task(task_id))
        
        return GenerationResult(
            task_id=task_id,
            status=GenerationStatus.PROCESSING,
        )

    async def _process_mock_task(self, task_id: str):
        # Simulate generation time taking 5 seconds
        await asyncio.sleep(5)
        self._tasks[task_id] = GenerationStatus.COMPLETED

    async def check_status(self, task_id: str) -> GenerationStatusInfo:
        status = self._tasks.get(task_id, GenerationStatus.FAILED)
        
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        return GenerationStatusInfo(
            task_id=task_id,
            status=status,
            download_url="http://mock-url.com/video.mp4" if status == GenerationStatus.COMPLETED else None
        )

    async def download_result(self, task_id: str) -> bytes | None:
        if self._tasks.get(task_id) != GenerationStatus.COMPLETED:
            return None
        
        # Simulate network download delay
        await asyncio.sleep(1)
        
        # Return a dummy 1-byte file to mock a download representation
        return b"mock_video_content"
