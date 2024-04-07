import os.path
import typing

import pytest
from ellar.common.datastructures import ContentFile
from ellar.testing import Test

from ellar_storage import (
    Container,
    Object,
    Provider,
    StorageModule,
    StorageService,
    StoredFile,
    get_driver,
)

from .utils import DUMB_DIRS, TEST_FIXTURES_DIRS

module_config = {
    "modules": [StorageModule.register_setup()],
    "config_module": {
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
}


def test_storage_get_operation(clear_dir):
    tm = Test.create_test_module(**module_config)
    storage_service: StorageService = tm.get(StorageService)

    storage_service.save(ContentFile(b"File saving worked", name="get.txt"))
    storage_service.save(
        ContentFile(b"File saving worked in images", name="get.txt"),
        upload_storage="images",
    )

    from_files = storage_service.get("get.txt")
    from_images = storage_service.get("images/get.txt")

    assert isinstance(from_files, StoredFile)
    assert isinstance(from_images, StoredFile)

    assert from_files.name == "get.txt"
    assert from_files.filename == "get.txt"
    assert from_files.read() == b"File saving worked"
    assert from_images.read() == b"File saving worked in images"


def test_storage_delete_operation(clear_dir):
    tm = Test.create_test_module(**module_config)
    storage_service: StorageService = tm.get(StorageService)

    storage_service.save(ContentFile(b"File saving worked", name="get.txt"))
    storage_service.save(
        ContentFile(b"File saving worked in images", name="get.txt"),
        upload_storage="images",
    )

    assert storage_service.delete("get.txt")
    assert storage_service.delete("images/get.txt")


def test_storage_save_content_operation(clear_dir):
    tm = Test.create_test_module(**module_config)

    storage_service: StorageService = tm.get(StorageService)
    file = ContentFile(b"File saving worked", name="get.txt")

    storage_service.save_content(
        name=file.filename,
        content=file.file,
        upload_storage="images",
        metadata={"content_type": file.content_type, "filename": file.filename},
        headers=dict(file.headers),
    )
    storage_service.save_content(
        name=file.filename,
        content=file.file,
        metadata={"content_type": file.content_type, "filename": file.filename},
        headers=dict(file.headers),
    )

    storage_service.save_content(
        name="copied-test.txt",
        content_path=os.path.join(TEST_FIXTURES_DIRS, "test.txt"),
    )

    files = os.listdir(os.path.join(DUMB_DIRS, "fixtures", "files"))
    assert set(files) == {"copied-test.txt", "get.txt.metadata.json", "get.txt"}


def test_storage_get_container(clear_dir):
    tm = Test.create_test_module(**module_config)

    storage_service: StorageService = tm.get(StorageService)
    files_container = storage_service.get_container()
    files_container2 = storage_service.get_container("files")

    images_container2 = storage_service.get_container("images")

    assert files_container == files_container2
    assert isinstance(files_container2, Container)

    assert isinstance(images_container2, Container)

    with pytest.raises(
        RuntimeError,
        match="images-invalid storage has not been added to Storage Config",
    ):
        storage_service.get_container("images-invalid")


def test_storage_stored_file(clear_dir):
    tm = Test.create_test_module(**module_config)

    storage_service: StorageService = tm.get(StorageService)
    stored_file = storage_service.save(
        ContentFile(b"File saving worked", name="get.txt")
    )

    assert stored_file.name == "get.txt"
    assert stored_file.filename == "get.txt"
    assert stored_file.size == 18
    assert stored_file.content_type == "text/plain"

    assert stored_file.readable() is True
    assert stored_file.seekable() is False
    assert stored_file.writable() is False

    assert os.path.exists(stored_file.get_cdn_url())

    assert isinstance(stored_file.object, Object)

    assert isinstance(stored_file.as_stream(), typing.Generator)

    stored_file.delete()

    files = os.listdir(os.path.join(DUMB_DIRS, "fixtures", "files"))
    assert files == []
