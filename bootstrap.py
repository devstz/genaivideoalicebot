import asyncio
import logging

from bot.builder.bot_manager import BotManager
from bot.builder.dispatcher_manager import DispatcherManager
from config.logging_setup import setup_logging
from config.settings import get_settings


logger = logging.getLogger(__name__)


async def init_app() -> None:
    """
    Main entry point for starting the application.
    """
    # 1. Setup logging
    setup_logging("logs/bot.log")
    logger.info("Starting AI Video Bot application...")

    # 2. Load Configuration
    settings = get_settings()

    # 3. Initialize Bot & Dispatcher Manager (singleton pattern)
    bot_manager = BotManager(settings.TOKEN)
    dp_manager = DispatcherManager.initialize(bot_manager)

    # 4. Setup middlewares, routers, commands
    await dp_manager.setup()

    # 5. Start Polling
    logger.info("Starting bot polling...")
    try:
        await dp_manager.start_polling()
    except Exception as e:
        logger.exception("Error during polling: %s", e)
    finally:
        logger.info("Shutting down Application...")
        bot = bot_manager.get_bot()
        if bot:
            await bot.session.close()
