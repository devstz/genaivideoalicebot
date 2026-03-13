import httpx
import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from enums import GenerationStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hailuo_generation():
    """
    Standalone script to debug Hailuo generation.
    Tries stable v2.3 and logs EVERYTHING.
    """
    api_key = settings.PIAPI_KEY
    if not api_key:
        print("ERROR: PIAPI_KEY not found in .env")
        return

    # 1. Use a standard public image to rule out hosting issues
    # This is a public image of a cat
    # Try a different host (uguu.se)
    test_image_url = "https://h.uguu.se/jpmyTybw.jpg"
    
    base_url = "https://api.piapi.ai/api/v1/task"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # payload based on documentation
    payload = {
        "model": "hailuo",
        "task_type": "video_generation",
        "input": {
            "model": "v2.3-fast",
            "prompt": "cinematic video",
            "image_url": test_image_url,
            "expand_prompt": True,
            "duration": 6,
            "resolution": 768
        },
        "config": {
            "service_mode": "public"
        }
    }

    print(f"\n--- Starting Generation ---")
    print(f"Model: hailuo v2.3-fast")
    print(f"Image: {test_image_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # CREATE TASK
            response = await client.post(base_url, json=payload, headers=headers)
            print(f"Create Response [{response.status_code}]: {response.text}")
            response.raise_for_status()
            data = response.json()
            
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                print("Failed to get task_id")
                return

            print(f"Task ID created: {task_id}")
            print(f"Polling status...")

            # POLL STATUS
            for i in range(20):
                await asyncio.sleep(15)
                status_res = await client.get(f"{base_url}/{task_id}", headers=headers)
                print(f"[{i+1}] Status Response: {status_res.text}")
                
                status_data = status_res.json()
                res_data = status_data.get("data", {})
                status_str = res_data.get("status", "").lower()
                
                if status_str == "completed":
                    video_url = res_data.get("output", {}).get("video") or res_data.get("output", {}).get("video_url")
                    print(f"SUCCESS! Video URL: {video_url}")
                    
                    # Store result
                    os.makedirs("media/test_results", exist_ok=True)
                    save_path = f"media/test_results/{task_id}.mp4"
                    print(f"Downloading to {save_path}...")
                    
                    video_res = await client.get(video_url)
                    with open(save_path, "wb") as f:
                        f.write(video_res.content)
                    print(f"File saved successfully!")
                    return
                
                if status_str == "failed":
                    error = res_data.get("error")
                    print(f"TASK FAILED. Error details: {error}")
                    return
                
                print(f"Still {status_str}...")

            print("Timed out waiting for completion.")

    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_hailuo_generation())
