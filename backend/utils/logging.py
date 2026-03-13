import sys
from loguru import logger

# Remove default logger
logger.remove()

# Add standard console logger with nice formatting
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Optional: Add file logging for production
logger.add(
    "logs/bot_activity.log",
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
    serialize=True 
)

def sentry_handler(message):
    import sentry_sdk
    record = message.record
    if record["level"].no >= 40: # ERROR or higher
        sentry_sdk.capture_message(record["message"], level="error")

logger.add(sentry_handler, level="ERROR")

def get_logger(name: str):
    return logger.bind(module=name)
