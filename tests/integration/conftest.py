import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _mock_cache():
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    with patch('infrastructure.betexplorer_repository.cache', mock_cache):
        yield
