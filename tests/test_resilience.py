import pytest
from unittest.mock import MagicMock
from resilience import retry, fallback, RetryExhaustedError


def test_retry_success_first_try():
    mock_func = MagicMock(return_value="success")
    mock_func.__name__ = "mock_func"
    decorated = retry()(mock_func)

    assert decorated() == "success"
    assert mock_func.call_count == 1


def test_retry_success_after_failures():
    mock_func = MagicMock(
        side_effect=[ValueError("fail"), ValueError("fail"), "success"]
    )
    mock_func.__name__ = "mock_func"
    decorated = retry(
        exceptions=(ValueError,), max_attempts=3, base_delay=0.01
    )(mock_func)

    assert decorated() == "success"
    assert mock_func.call_count == 3


def test_retry_exhausted():
    mock_func = MagicMock(side_effect=ValueError("fail"))
    mock_func.__name__ = "mock_func"
    decorated = retry(
        exceptions=(ValueError,), max_attempts=2, base_delay=0.01
    )(mock_func)

    with pytest.raises(RetryExhaustedError) as excinfo:
        decorated()

    assert "Max retries exhausted" in str(excinfo.value)
    assert mock_func.call_count == 2


def test_retry_unhandled_exception():
    mock_func = MagicMock(side_effect=TypeError("unhandled"))
    mock_func.__name__ = "mock_func"
    decorated = retry(exceptions=(ValueError,), max_attempts=3)(mock_func)

    with pytest.raises(TypeError):
        decorated()

    assert mock_func.call_count == 1


def test_fallback_success():
    mock_func = MagicMock(return_value="success")
    mock_func.__name__ = "mock_func"
    mock_fallback = MagicMock(return_value="fallback_success")
    mock_fallback.__name__ = "mock_fallback"

    decorated = fallback(fallback_func=mock_fallback)(mock_func)

    assert decorated() == "success"
    assert mock_func.call_count == 1
    assert mock_fallback.call_count == 0


def test_fallback_triggered():
    mock_func = MagicMock(side_effect=ValueError("fail"))
    mock_func.__name__ = "mock_func"
    mock_fallback = MagicMock(return_value="fallback_success")
    mock_fallback.__name__ = "mock_fallback"

    decorated = fallback(
        fallback_func=mock_fallback, exceptions=(ValueError,)
    )(mock_func)

    assert decorated() == "fallback_success"
    assert mock_func.call_count == 1
    assert mock_fallback.call_count == 1


def test_fallback_unhandled_exception():
    mock_func = MagicMock(side_effect=TypeError("unhandled"))
    mock_func.__name__ = "mock_func"
    mock_fallback = MagicMock(return_value="fallback_success")
    mock_fallback.__name__ = "mock_fallback"

    decorated = fallback(
        fallback_func=mock_fallback, exceptions=(ValueError,)
    )(mock_func)

    with pytest.raises(TypeError):
        decorated()

    assert mock_func.call_count == 1
    assert mock_fallback.call_count == 0


def test_combined_retry_and_fallback():
    mock_func = MagicMock(side_effect=ValueError("fail"))
    mock_func.__name__ = "mock_func"
    mock_fallback = MagicMock(return_value="fallback_success")
    mock_fallback.__name__ = "mock_fallback"

    @fallback(fallback_func=mock_fallback, exceptions=(RetryExhaustedError,))
    @retry(exceptions=(ValueError,), max_attempts=2, base_delay=0.01)
    def test_func():
        return mock_func()

    assert test_func() == "fallback_success"
    assert mock_func.call_count == 2
    assert mock_fallback.call_count == 1
