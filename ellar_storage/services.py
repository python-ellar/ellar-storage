import contextlib
import os
import typing as t
import uuid

from ellar.common import UploadFile
from ellar.di import injectable
from starlette.concurrency import run_in_threadpool

from ellar_storage.constants import LOCAL_STORAGE_DRIVER_NAME
from ellar_storage.exceptions import (
    ContainerAlreadyExistsError,
    ObjectDoesNotExistError,
)
from ellar_storage.schemas import StorageSetup
from ellar_storage.storage import Container
from ellar_storage.stored_file import StoredFile
from ellar_storage.utils import get_metadata_file_obj


@injectable
class StorageService:
    """
    Manages lib-cloud registered storage drivers for saving, deleting and retrieving files
    """

    __slots__ = ("_storages", "_storage_default")

    def __init__(self, storage_setup: StorageSetup) -> None:
        result = {}

        for storage_name, value in storage_setup.storages.items():
            if value.driver.name == LOCAL_STORAGE_DRIVER_NAME:
                # if its local storage, we need to create the path
                os.makedirs(value.options["key"], 0o777, exist_ok=True)

            driver = value.driver(**value.options)

            with contextlib.suppress(ContainerAlreadyExistsError):
                driver.create_container(container_name=storage_name)

            storage_container = driver.get_container(container_name=storage_name)
            result[storage_name] = storage_container

        self._storages = result
        self._storage_default = t.cast(str, storage_setup.default)

    def get_container(self, name: t.Optional[str] = None) -> Container:
        """
        Gets the container instance associate to the name,
        return default if name isn't provided.
        """
        if name is None:
            container = self._storages.get(self._storage_default)
            assert container is not None
            return container
        if name in self._storages:
            return self._storages[name]
        raise RuntimeError(f"{name} storage has not been added to Storage Config")

    def save(
        self,
        file: UploadFile,
        upload_storage: t.Optional[str] = None,
    ) -> StoredFile:
        return self.save_content(
            name=file.filename or str(uuid.uuid4())[10],
            content=file.file,
            upload_storage=upload_storage,
            metadata={"content_type": file.content_type, "filename": file.filename},
            headers=dict(file.headers),
        )

    def save_content(
        self,
        name: str,
        content: t.Optional[t.Iterator[bytes]] = None,
        upload_storage: t.Optional[str] = None,
        metadata: t.Optional[t.Dict[str, t.Any]] = None,
        extra: t.Optional[t.Dict[str, t.Any]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        content_path: t.Optional[str] = None,
    ) -> StoredFile:
        """Save file into provided `upload_storage`"""
        if content is None and content_path is None:
            raise ValueError("Either content or content_path must be specified")

        if metadata is not None:
            extra = {
                "meta_data": metadata,
                "content_type": metadata.get(
                    "content_type", "application/octet-stream"
                ),
            }

        container = self.get_container(upload_storage)

        if (
            container.driver.name == LOCAL_STORAGE_DRIVER_NAME
            and extra is not None
            and extra.get("meta_data", None) is not None
        ):
            """
            Libcloud local storage driver doesn't support metadata, so the metadata
            is saved in the same container with the combination of the original name
            and `.metadata.json` as name
            """
            container.upload_object_via_stream(
                iterator=get_metadata_file_obj(extra["meta_data"]),
                object_name=f"{name}.metadata.json",
            )
        if content_path is not None:
            return StoredFile(
                container.upload_object(
                    file_path=content_path,
                    object_name=name,
                    extra=extra,
                    headers=headers,
                )
            )
        assert content is not None
        return StoredFile(
            container.upload_object_via_stream(
                iterator=content, object_name=name, extra=extra, headers=headers
            )
        )

    def __get_storage_from_path(self, path: str) -> t.Tuple[str, str]:
        path_split = path.split("/")
        if len(path_split) == 1:
            upload_storage, file_id = self._storage_default, path_split[0]
        else:
            upload_storage, file_id = path_split
        return upload_storage, file_id

    def get(self, path: str) -> StoredFile:
        """
        Retrieve the file with `provided` path, path is expected to be `storage_name/file_id`.
        """
        upload_storage, file_id = self.__get_storage_from_path(path)
        return StoredFile(self.get_container(upload_storage).get_object(file_id))

    def delete(self, path: str) -> bool:
        """
        Delete the file with `provided` path.

        The path is expected to be `storage_name/file_id`.
        """
        upload_storage, file_id = self.__get_storage_from_path(path)
        obj = self.get_container(upload_storage).get_object(file_id)

        if obj.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            """Try deleting associated metadata file"""
            with contextlib.suppress(ObjectDoesNotExistError):
                obj.container.get_object(f"{obj.name}.metadata.json").delete()

        return obj.delete()

    async def delete_async(self, path: str) -> bool:
        """Async Delete File Operation"""
        return await run_in_threadpool(self.delete, path)

    async def get_async(self, path: str) -> StoredFile:
        """Async Get File Operation"""
        return await run_in_threadpool(self.get, path)

    async def save_async(
        self,
        file: UploadFile,
        upload_storage: t.Optional[str] = None,
    ) -> StoredFile:
        """Async Save File Operation"""
        return await run_in_threadpool(self.save, file, upload_storage=upload_storage)

    async def save_content_async(
        self,
        name: str,
        content: t.Optional[t.Iterator[bytes]] = None,
        upload_storage: t.Optional[str] = None,
        metadata: t.Optional[t.Dict[str, t.Any]] = None,
        extra: t.Optional[t.Dict[str, t.Any]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        content_path: t.Optional[str] = None,
    ) -> StoredFile:
        """Async Save Content Operation"""
        return await run_in_threadpool(
            self.save_content,
            name,
            content=content,
            upload_storage=upload_storage,
            metadata=metadata,
            extra=extra,
            headers=headers,
            content_path=content_path,
        )
