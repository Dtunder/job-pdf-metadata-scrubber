import json
import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "SCRUB_MAX_ATTEMPTS": 3,
    "SCRUB_BASE_DELAY": 0.1,
    "SIMULATION_CONNECT_MAX_ATTEMPTS": 4,
    "SIMULATION_CONNECT_BASE_DELAY": 0.1,
    "SIMULATION_PROCESS_MAX_ATTEMPTS": 2,
    "SIMULATION_PROCESS_BASE_DELAY": 0.1,
    "SIMULATION_FAIL_TIMES": 2,
    "SIMULATION_TIMEOUT_TIMES": 2,
    "RETRY_DEFAULT_MAX_ATTEMPTS": 3,
    "RETRY_DEFAULT_BASE_DELAY": 1.0,
    "RETRY_DEFAULT_BACKOFF_FACTOR": 2.0,
}


class Config:
    def __init__(self, config_path: str = "config.json"):
        self.settings: Dict[str, Any] = DEFAULT_CONFIG.copy()

        # Load from config.json if it exists
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    file_settings = json.load(f)
                    for k, v in file_settings.items():
                        if k in self.settings:
                            self.settings[k] = v
                        else:
                            self.settings[k] = v
            except Exception as e:
                logger.warning(f"Failed to load {config_path}: {e}")

        # Override with environment variables
        for key in self.settings.keys():
            if key in os.environ:
                env_val = os.environ[key]
                default_type = type(DEFAULT_CONFIG.get(key, env_val))
                try:
                    if default_type == bool and env_val.lower() in (
                        "true",
                        "false",
                        "1",
                        "0",
                    ):
                        self.settings[key] = env_val.lower() in ("true", "1")
                    elif default_type == float:
                        self.settings[key] = float(env_val)
                    elif default_type == int:
                        self.settings[key] = int(env_val)
                    else:
                        self.settings[key] = str(env_val)  # type: ignore
                except ValueError:
                    logger.warning(
                        f"Invalid type for env var {key}. Expected {default_type.__name__}."
                    )

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def __getattr__(self, name: str) -> Any:
        if name in self.settings:
            val = self.settings[name]
            return val
        raise AttributeError(f"'Config' object has no attribute '{name}'")


config = Config()
