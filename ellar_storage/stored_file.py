import contextlib
import io
import json
import typing as t

from ellar_storage.constants import LOCAL_STORAGE_DRIVER_NAME
from ellar_storage.exceptions import ObjectDoesNotExistError
from ellar_storage.storage import Object


class StoredFile(io.IOBase):
    """Represents a file that has been stored in a database. This class provides
    a file-like interface for reading the file content.
    """

    def __init__(self, obj: Object) -> None:
        if obj.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            """Retrieve metadata from associated metadata file"""
            try:
                metadata_obj = obj.container.get_object(f"{obj.name}.metadata.json")
                with open(metadata_obj.get_cdn_url()) as metadata_file:
                    obj.meta_data = json.load(metadata_file)
            except ObjectDoesNotExistError:  # pragma: no cover
                pass
        self.name = obj.name
        self.size = obj.size
        self.filename = obj.meta_data.get("filename", "unnamed")
        self.content_type = obj.extra.get(
            "content_type",
            obj.meta_data.get("content_type", "application/octet-stream"),
        )
        self.object = obj

    def get_cdn_url(self) -> t.Optional[str]:
        """Retrieves the CDN URL of the file if available."""
        try:
            return self.object.get_cdn_url()
        except NotImplementedError:  # pragma: no cover
            return None

    def read(self, n: int = -1, chunk_size: t.Optional[int] = None) -> bytes:
        """Reads the content of the file.

        Arguments:
            n: The number of bytes to read. If not specified or set to -1,
                it reads the entire content of the file. Defaults to -1.
            chunk_size: The size of the chunks to read at a time.
                If not specified, the default chunk size of the storage provider will be used.

        """
        return next(
            self.range_as_stream(
                0, end_bytes=n if n > 0 else None, chunk_size=chunk_size
            )
        )

    def close(self) -> None:  # pragma: no cover
        pass  # No need to close;

    def seekable(self) -> bool:
        return False  # Seeking is not supported ; pragma: no cover

    def writable(self) -> bool:
        return False  # Writing is not supported ; pragma: no cover

    def readable(self) -> bool:
        return True  # Reading is supported ; pragma: no cover

    def as_stream(self, chunk_size: t.Optional[int] = None) -> t.Iterator[bytes]:
        return self.object.as_stream(chunk_size=chunk_size)

    def range_as_stream(
        self,
        start_bytes: int,
        end_bytes: t.Optional[int] = None,
        chunk_size: t.Optional[int] = None,
    ) -> t.Iterator[bytes]:
        return self.object.range_as_stream(
            start_bytes=start_bytes,
            end_bytes=end_bytes,
            chunk_size=chunk_size,
        )

    def delete(self) -> bool:
        if self.object.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            """Try deleting associated metadata file"""
            with contextlib.suppress(ObjectDoesNotExistError):
                self.object.container.get_object(
                    f"{self.object.name}.metadata.json"
                ).delete()

        return self.object.delete()
