import pytest
from ellar.reflect import reflect

from .utils import clear


@pytest.fixture
def reflect_context():
    with reflect.context():
        yield


@pytest.fixture
def clear_dir():
    yield
    clear("fixtures")
