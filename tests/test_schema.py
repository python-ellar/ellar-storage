import pytest

from ellar_storage import Provider, StorageSetup, get_driver


def test_storage_setup_works():
    schema = StorageSetup(
        storages={
            "local": {
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": "a/path/for/files"},
            },
            "cloud": {
                "driver": get_driver(Provider.GOOGLE_STORAGE),
                "options": {"key": "GOOG0123456789ABCXYZ", "secret": "key_secret"},
            },
        }
    )
    assert len(schema.storages) == 2
    cloud = schema.storages.get("cloud")

    assert cloud.driver.name == "Google Cloud Storage"
    assert cloud.options == {"key": "GOOG0123456789ABCXYZ", "secret": "key_secret"}

    assert schema.default == "local"


def test_storage_full_setup_works():
    schema = StorageSetup(
        storages={
            "local": {
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": "a/path/for/files"},
            },
            "cloud": {
                "driver": get_driver(Provider.GOOGLE_STORAGE),
                "options": {"key": "GOOG0123456789ABCXYZ", "secret": "key_secret"},
            },
        },
        default="cloud",
    )
    assert len(schema.storages) == 2
    local = schema.storages.get("local")

    assert local.driver.name == "Local Storage"
    assert local.options == {
        "key": "a/path/for/files",
    }

    assert schema.default == "cloud"


def test_storage_fails_for_empty_storages():
    with pytest.raises(
        ValueError, match="At least one storage setup is required storages"
    ):
        StorageSetup(storages={})


def test_storage_fails_for_invalid_default_storage():
    with pytest.raises(ValueError, match="storages must have a 'files' as key"):
        StorageSetup(
            storages={
                "cloud": {
                    "driver": get_driver(Provider.GOOGLE_STORAGE),
                    "options": {"key": "GOOG0123456789ABCXYZ", "secret": "key_secret"},
                }
            },
            default="files",
        )
