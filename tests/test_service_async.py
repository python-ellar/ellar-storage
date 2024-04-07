import os.path

import pytest
from ellar.common.datastructures import ContentFile
from ellar.testing import Test

from ellar_storage import (
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


@pytest.mark.asyncio
async def test_storage_get_operation_async(clear_dir):
    tm = Test.create_test_module(**module_config)
    storage_service: StorageService = tm.get(StorageService)

    await storage_service.save_async(ContentFile(b"File saving worked", name="get.txt"))
    await storage_service.save_async(
        ContentFile(b"File saving worked in images", name="get.txt"),
        upload_storage="images",
    )

    from_files = await storage_service.get_async("get.txt")
    from_images = await storage_service.get_async("images/get.txt")

    assert isinstance(from_files, StoredFile)
    assert isinstance(from_images, StoredFile)

    assert from_files.name == "get.txt"
    assert from_files.filename == "get.txt"
    assert from_files.read() == b"File saving worked"
    assert from_images.read() == b"File saving worked in images"


@pytest.mark.asyncio
async def test_storage_delete_operation_async(clear_dir):
    tm = Test.create_test_module(**module_config)
    storage_service: StorageService = tm.get(StorageService)

    await storage_service.save_async(ContentFile(b"File saving worked", name="get.txt"))
    await storage_service.save_async(
        ContentFile(b"File saving worked in images", name="get.txt"),
        upload_storage="images",
    )

    assert await storage_service.delete_async("get.txt")
    assert await storage_service.delete_async("images/get.txt")


@pytest.mark.asyncio
async def test_storage_save_content_operation_async(clear_dir):
    tm = Test.create_test_module(**module_config)

    storage_service: StorageService = tm.get(StorageService)
    file = ContentFile(b"File saving worked", name="get.txt")

    await storage_service.save_content_async(
        name=file.filename,
        content=file.file,
        upload_storage="images",
        metadata={"content_type": file.content_type, "filename": file.filename},
        headers=dict(file.headers),
    )
    await storage_service.save_content_async(
        name=file.filename,
        content=file.file,
        metadata={"content_type": file.content_type, "filename": file.filename},
        headers=dict(file.headers),
    )

    await storage_service.save_content_async(
        name="copied-test.txt",
        content_path=os.path.join(TEST_FIXTURES_DIRS, "test.txt"),
    )

    files = os.listdir(os.path.join(DUMB_DIRS, "fixtures", "files"))
    assert set(files) == {"copied-test.txt", "get.txt.metadata.json", "get.txt"}
