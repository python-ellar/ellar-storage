from ellar.common.datastructures import ContentFile
from ellar.testing import Test

from ellar_storage import StorageService

from .test_service import module_config


def test_storage_controller_download_file(clear_dir):
    tm = Test.create_test_module(**module_config)

    storage_service: StorageService = tm.get(StorageService)

    storage_service.save(ContentFile(b"File saving worked", name="get.txt"))
    storage_service.save(
        ContentFile(b"File saving worked in images", name="get.txt"),
        upload_storage="images",
    )

    url = tm.create_application().url_path_for(
        "storage:download", path="images/get.txt"
    )
    res = tm.get_test_client().get(url)

    assert res.status_code == 200
    assert res.stream
    assert res.text == "File saving worked in images"

    url = tm.create_application().url_path_for("storage:download", path="files/get.txt")
    res = tm.get_test_client().get(url)

    assert res.status_code == 200
    assert res.stream
    assert res.text == "File saving worked"

    res = tm.get_test_client().get(
        url=tm.create_application().url_path_for(
            "storage:download", path="files/get342.txt"
        )
    )
    assert res.status_code == 404
