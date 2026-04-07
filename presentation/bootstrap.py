"""
FastAPI Application Bootstrap.
Creates the FastAPI app and manages the Telegram Bot lifecycle.
"""

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import get_settings
from config.logging_setup import setup_logging
from bot.builder.bot_manager import BotManager
from bot.builder.dispatcher_manager import DispatcherManager
from presentation.api.v1.routers.connect_routers import connect_routers
from services.generation_worker import VideoGenerationWorker
from services.telegram_bot_username import ensure_resolved_bot_username

import asyncio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan.
    Starts the Telegram bot when the API starts, and stops it when the API stops.
    """
    setup_logging("logs/bot.log")
    settings = get_settings()
    
    # 1. Initialize Bot & Dispatcher Manager
    logger.info("Initializing Telegram Bot...")
    bot_manager = BotManager(settings.TOKEN)
    dp_manager = DispatcherManager.initialize(bot_manager)
    await dp_manager.setup()

    un = await ensure_resolved_bot_username(settings)
    if un:
        logger.info("Bot username for deep links: %s", un)
    else:
        logger.warning("Bot username not resolved; set TOKEN or BOT_USERNAME for admin/UTM links")

    # 2. Start Polling in background
    logger.info("Starting bot polling in background...")
    
    async def safe_polling():
        try:
            # It is critical to pass handle_signals=False so aiogram doesn't hijack SIGINT from Uvicorn
            await dp_manager.start_polling(handle_signals=False)
        except Exception as e:
            logger.error("Bot polling failed with error: %s", e)
            
    polling_task = asyncio.create_task(safe_polling())
    
    # 3. Start Video Generation Worker
    worker = VideoGenerationWorker(bot_manager.get_bot())
    await worker.start()
    
    yield
    
    # 4. Shutdown
    logger.info("Stopping VideoGenerationWorker...")
    await worker.stop()
    
    logger.info("Stopping Telegram Bot...")
    try:
        polling_task.cancel()
        await polling_task
    except asyncio.CancelledError:
        pass
        
    bot = bot_manager.get_bot()
    if bot:
        await bot.session.close()


def _configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Video Bot API",
        version="1.0.0",
        redirect_slashes=False,
        lifespan=lifespan,
        root_path=settings.API_ROOT_PATH,
    )

    _configure_cors(app)
    connect_routers(app)

    media_dir = Path(settings.MEDIA_ROOT).resolve()
    if media_dir.exists():
        from fastapi.responses import FileResponse

        @app.get("/media/{file_path:path}")
        async def serve_media(file_path: str):
            full = media_dir / file_path
            if not full.resolve().is_relative_to(media_dir) or not full.is_file():
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Not Found")
            return FileResponse(str(full))

    return app
