import pytest

from .utils import clear


@pytest.fixture
def clear_dir():
    yield
    clear("fixtures")
