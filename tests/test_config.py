import json
import os
import tempfile
import pytest
from unittest import mock
from config import Config


def test_default_config():
    # Test that loading without a config file defaults to DEFAULT_CONFIG
    c = Config(config_path="nonexistent_config.json")
    assert c.SCRUB_MAX_ATTEMPTS == 3
    assert c.SCRUB_BASE_DELAY == 0.1
    assert c.SIMULATION_CONNECT_MAX_ATTEMPTS == 4


def test_load_from_json():
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump({"SCRUB_MAX_ATTEMPTS": 10, "NEW_KEY": "value"}, f)
        temp_path = f.name

    try:
        c = Config(config_path=temp_path)
        assert c.SCRUB_MAX_ATTEMPTS == 10
        assert c.SCRUB_BASE_DELAY == 0.1  # unchanged
        assert c.NEW_KEY == "value"
    finally:
        os.remove(temp_path)


def test_env_var_override():
    with mock.patch.dict(
        os.environ, {"SCRUB_MAX_ATTEMPTS": "5", "SCRUB_BASE_DELAY": "0.5"}
    ):
        c = Config(config_path="nonexistent_config.json")
        assert c.SCRUB_MAX_ATTEMPTS == 5  # Int override
        assert c.SCRUB_BASE_DELAY == 0.5  # Float override
        assert c.SIMULATION_CONNECT_MAX_ATTEMPTS == 4  # Default kept


def test_getattr_raises_attribute_error():
    c = Config(config_path="nonexistent_config.json")
    with pytest.raises(AttributeError):
        _ = c.NONEXISTENT_KEY
