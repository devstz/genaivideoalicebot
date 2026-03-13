import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.providers.ai_video_generators.hailuo import HailuoGenerator
from enums import GenerationStatus
from config.settings import settings

async def test_hailuo_mocked():
    print("Testing HailuoGenerator (Mocked)...")
    generator = HailuoGenerator(api_key="test_key")
    
    # Simple check for methods
    print(f"Generator initialized with model: {generator.model}")
    assert hasattr(generator, "generate")
    assert hasattr(generator, "check_status")
    assert hasattr(generator, "download_result")
    
    print("Basic method check passed.")

async def main():
    await test_hailuo_mocked()
    
    # Use real key from settings
    if settings.PIAPI_KEY and settings.PIAPI_KEY not in ["PIAPI_KEY", "your_piapi_key_here"]:
        print(f"\nRunning real integration test with key: {settings.PIAPI_KEY[:5]}***")
        generator = HailuoGenerator(api_key=settings.PIAPI_KEY)
        result = await generator.generate(
            image_path="", 
            prompt="A futuristic city with flying cars, cinematic lighting, 4k"
        )
        print(f"Generation started: {result}")
        
        if result.status != GenerationStatus.FAILED and result.task_id:
            print(f"Waiting for status for task {result.task_id}...")
            # Poll for a bit
            for _ in range(5):
                await asyncio.sleep(5)
                status = await generator.check_status(result.task_id)
                print(f"Status: {status.status}")
                if status.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
                    break
    else:
        print("\nSkipping real integration test (no PIAPI_KEY provided).")

if __name__ == "__main__":
    asyncio.run(main())
