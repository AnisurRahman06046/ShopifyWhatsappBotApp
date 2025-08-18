# app/modules/BotApp/bot_cache.py

from .bot_models import BotConfig

_bot_config_cache: BotConfig | None = None


def set_bot_config(config: BotConfig):
    global _bot_config_cache
    _bot_config_cache = config


def get_bot_config() -> BotConfig | None:
    return _bot_config_cache
