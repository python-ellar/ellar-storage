import json
import typing as t
from tempfile import SpooledTemporaryFile

from ellar_storage.constants import IN_MEMORY_FILESIZE


def get_metadata_file_obj(
    metadata: t.Dict[str, t.Any],
) -> "SpooledTemporaryFile[bytes]":
    f = SpooledTemporaryFile(IN_MEMORY_FILESIZE)
    f.write(json.dumps(metadata).encode())
    f.seek(0)
    return f
