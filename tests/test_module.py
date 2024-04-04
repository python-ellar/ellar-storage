import os.path

import pytest
from ellar.testing import Test

from ellar_storage import Provider, StorageModule, StorageService, get_driver

from .utils import DUMB_DIRS


def test_module_setup():
    tm = Test.create_test_module(
        modules=[
            StorageModule.setup(
                files={
                    "driver": get_driver(Provider.LOCAL),
                    "options": {"key": os.path.join(DUMB_DIRS, "fixtures")},
                }
            )
        ]
    )
    storage_service: StorageService = tm.get(StorageService)
    assert storage_service._storage_default == "files"
    assert storage_service.get_container("files").driver.name == "Local Storage"


def test_module_register_setup():
    tm = Test.create_test_module(
        modules=[StorageModule.register_setup()],
        config_module={
            "STORAGE_CONFIG": {
                "storages": {
                    "files": {
                        "driver": get_driver(Provider.LOCAL),
                        "options": {"key": os.path.join(DUMB_DIRS, "fixtures")},
                    },
                    "images": {
                        "driver": get_driver(Provider.LOCAL),
                        "options": {"key": os.path.join(DUMB_DIRS, "fixtures")},
                    },
                }
            }
        },
    )
    storage_service: StorageService = tm.get(StorageService)
    assert storage_service._storage_default == "files"
    assert storage_service.get_container("files").driver.name == "Local Storage"


def test_module_register_setup_with_default():
    tm = Test.create_test_module(
        modules=[StorageModule.register_setup()],
        config_module={
            "STORAGE_CONFIG": {
                "default": "images",
                "storages": {
                    "files": {
                        "driver": get_driver(Provider.LOCAL),
                        "options": {"key": os.path.join(DUMB_DIRS, "fixtures")},
                    },
                    "images": {
                        "driver": get_driver(Provider.LOCAL),
                        "options": {"key": os.path.join(DUMB_DIRS, "fixtures")},
                    },
                },
            }
        },
    )
    storage_service: StorageService = tm.get(StorageService)
    assert storage_service._storage_default == "images"
    assert storage_service.get_container("images").driver.name == "Local Storage"


def test_module_register_fails_config_key_absents():
    tm = Test.create_test_module(
        modules=[StorageModule.register_setup()],
        config_module={"STORAGE_CONFIG_InVALID_KEY": {}},
    )

    with pytest.raises(
        RuntimeError, match="Could not find `STORAGE_CONFIG` in application config."
    ):
        tm.create_application()
