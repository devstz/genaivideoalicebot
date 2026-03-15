import httpx
import logging
from typing import Any
from enums import GenerationStatus
from .base_generator import BaseGenerator, GenerationResult, GenerationStatusInfo

logger = logging.getLogger(__name__)

class PiAPIBaseGenerator(BaseGenerator):
    """Base class for piAPI.ai video generators."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.piapi.ai/api/v1/task"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def upload_to_catbox(self, file_content: bytes) -> str | None:
        """
        Uploads a file to Catbox.moe (reliable and free).
        """
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload"}
        files = {"fileToUpload": ("image.jpg", file_content, "image/jpeg")}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=data, files=files)
                response.raise_for_status()
                url_res = response.text.strip()
                if url_res.startswith("http"):
                    return url_res
        except Exception as e:
            logger.error(f"Error uploading to Catbox: {e}")
            return None

    async def upload_to_uguu(self, file_content: bytes) -> str | None:
        """
        Uploads a file to Uguu.se (reliable and free, handles .moe blocking better).
        """
        url = "https://uguu.se/upload.php"
        files = {"files[]": ("image.jpg", file_content, "image/jpeg")}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, files=files)
                response.raise_for_status()
                data = response.json()
                if data.get("success") and data.get("files"):
                    return data["files"][0].get("url")
        except Exception as e:
            logger.error(f"Error uploading to Uguu: {e}")
            return None

    async def upload_to_telegraph(self, file_content: bytes) -> str | None:
        """
        Uploads a file to Telegra.ph (anonymous and free).
        Useful when piAPI storage is unavailable (403 Forbidden).
        """
        url = "https://telegra.ph/upload"
        # Telegraph needs a proper User-Agent sometimes
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        files = {"file": ("image.jpg", file_content, "image/jpeg")}
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                response = await client.post(url, files=files)
                if response.status_code != 200:
                    logger.error(f"Telegraph upload failed with status {response.status_code}: {response.text}")
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    path = data[0].get("src")
                    return f"https://telegra.ph{path}"
        except Exception as e:
            logger.error(f"Error uploading to Telegraph: {e}")
            return None

    async def upload_file(self, file_content: bytes, file_name: str) -> str | None:
        """
        Uploads a file to piAPI's ephemeral storage or falls back to Catbox/Telegraph.
        """
        import base64
        url = "https://upload.theapi.app/api/ephemeral_resource"
        
        payload = {
            "file_name": file_name,
            "file_data": base64.b64encode(file_content).decode("utf-8")
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                # If 403 (no subscription), fallback to external hosts
                if response.status_code == 403:
                    logger.warning("piAPI storage return 403. Falling back to Uguu/Telegraph...")
                    return await self.upload_to_uguu(file_content) or await self.upload_to_telegraph(file_content) or await self.upload_to_catbox(file_content)
                
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("url")
        except Exception as e:
            logger.error(f"Error uploading file to piAPI: {e}. Falling back to external hosts...")
            return await self.upload_to_uguu(file_content) or await self.upload_to_telegraph(file_content) or await self.upload_to_catbox(file_content)

    async def generate(self, image_path: str, prompt: str, negative_prompt: str | None = None, **kwargs) -> GenerationResult:
        """
        Start the video generation process via piAPI.
        """
        model = kwargs.get("model")
        if not model:
            raise ValueError("Model must be specified for piAPI generation")

        payload = {
            "model": model,
            "task_type": kwargs.get("task_type", "video_generation"),
            "input": {
                "prompt": prompt
            },
            "config": {
                "service_mode": "public"
            }
        }
        
        # Add optional input params
        input_params = kwargs.get("input_params", {})
        payload["input"].update(input_params)
        
        # Handle image_path
        if image_path:
            image_url = image_path
            # If it's a local path, we MUST upload it
            import os
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    content = f.read()
                    name = os.path.basename(image_path)
                    uploaded_url = await self.upload_file(content, name)
                    if not uploaded_url:
                        return GenerationResult(
                            task_id="",
                            status=GenerationStatus.FAILED,
                            error="Failed to upload image to piAPI storage (check subscription/credits)"
                        )
                    image_url = uploaded_url
            
            payload["input"]["image_url"] = image_url

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        logger.info(f"Starting piAPI generation with payload: {payload}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.base_url, json=payload, headers=self.headers)
                if response.status_code != 200:
                    logger.error(f"piAPI error {response.status_code}: {response.text}")
                response.raise_for_status()
                data = response.json()
                
                task_id = data.get("data", {}).get("task_id") or data.get("task_id")
                if not task_id:
                    raise ValueError(f"No task_id in piAPI response: {data}")

                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.PENDING,
                    raw_response=data
                )
        except Exception as e:
            logger.error(f"Error starting piAPI generation: {e}")
            return GenerationResult(
                task_id="",
                status=GenerationStatus.FAILED,
                error=str(e)
            )

    async def check_status(self, task_id: str) -> GenerationStatusInfo:
        """
        Check the status of a generation task.
        """
        url = f"{self.base_url}/{task_id}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                # piAPI structure: {"timestamp": ..., "data": {"status": "completed", ...}}
                res_data = data.get("data") or {}
                status_str = res_data.get("status", "failed").lower()
                
                status_mapping = {
                    "pending": GenerationStatus.PENDING,
                    "processing": GenerationStatus.PROCESSING,
                    "completed": GenerationStatus.COMPLETED,
                    "failed": GenerationStatus.FAILED,
                    "cancelled": GenerationStatus.FAILED
                }
                
                status = status_mapping.get(status_str, GenerationStatus.FAILED)
                output = res_data.get("output") or {}
                download_url = output.get("video") or output.get("video_url") or output.get("download_url")
                percent_raw = output.get("percent")
                percent = int(percent_raw) if percent_raw is not None else None
                
                # Extract error message properly
                error_obj = res_data.get("error") or {}
                error_msg = None
                if isinstance(error_obj, dict):
                    error_msg = error_obj.get("message") or error_obj.get("raw_message")
                elif isinstance(error_obj, str):
                    error_msg = error_obj
                
                if not error_msg:
                    error_msg = res_data.get("error_msg")
                
                return GenerationStatusInfo(
                    task_id=task_id,
                    status=status,
                    download_url=download_url,
                    error=error_msg,
                    raw_response=data,
                    percent=percent,
                )
        except Exception as e:
            logger.error(f"Error checking piAPI status for task {task_id}: {e}")
            logger.error(f"Last response data: {data if 'data' in locals() else 'N/A'}")
            return GenerationStatusInfo(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error=str(e)
            )

    async def download_result(self, task_id: str) -> bytes | None:
        """
        Download the final generated video from the URL provided by check_status.
        Note: This usually needs the result from check_status if it's not stored.
        """
        status_info = await self.check_status(task_id)
        if status_info.status != GenerationStatus.COMPLETED or not status_info.download_url:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(status_info.download_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading piAPI result for task {task_id}: {e}")
            return None
