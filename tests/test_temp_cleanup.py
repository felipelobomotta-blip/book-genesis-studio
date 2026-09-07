from unittest.mock import Mock, patch
import pytest
from runner.adapters import AdapterError, _temporary_workdir


def test_locked_temp_directory_cannot_hide_the_provider_error():
    directory = Mock(name="temporary provider folder")
    directory.name = "test-temp"
    directory.cleanup.side_effect = PermissionError("still in use")
    with patch("runner.adapters.tempfile.TemporaryDirectory", return_value=directory), patch("runner.adapters.time.sleep"):
        with pytest.raises(AdapterError, match="model does not exist"):
            with _temporary_workdir("test-"):
                raise AdapterError("model does not exist")
    assert directory.cleanup.call_count == 3


def test_a_short_lived_lock_is_retried_without_losing_success():
    directory = Mock()
    directory.name = "test-temp"
    directory.cleanup.side_effect = [PermissionError("busy"), None]
    with patch("runner.adapters.tempfile.TemporaryDirectory", return_value=directory), patch("runner.adapters.time.sleep"):
        with _temporary_workdir("test-") as path:
            assert path == "test-temp"
    assert directory.cleanup.call_count == 2
