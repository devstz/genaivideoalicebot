from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from enums import GenerationStatus


@dataclass
class GenerationResult:
    task_id: str
    status: GenerationStatus
    error: str | None = None
    raw_response: dict[str, Any] | None = None


@dataclass
class GenerationStatusInfo:
    task_id: str
    status: GenerationStatus
    download_url: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None
    percent: int | None = None


class BaseGenerator(ABC):
    @abstractmethod
    async def generate(self, image_path: str, prompt: str, negative_prompt: str | None = None, **kwargs) -> GenerationResult:
        """
        Start the video generation process.
        """
        pass

    @abstractmethod
    async def check_status(self, task_id: str) -> GenerationStatusInfo:
        """
        Check the status of a generation task.
        """
        pass

    @abstractmethod
    async def download_result(self, task_id: str) -> bytes | None:
        """
        Download the final generated video.
        """
        pass
