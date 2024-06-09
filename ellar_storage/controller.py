import typing as t

import ellar.common as ecm
from ellar.common import NotFound
from ellar.core import Request
from libcloud.storage.types import ObjectDoesNotExistError
from starlette.responses import RedirectResponse, StreamingResponse

from ellar_storage.services import StorageService


@ecm.Controller(name="storage")
class StorageController:
    def __init__(self, storage_service: StorageService):
        self._storage_service = storage_service

    @ecm.get("/download/{path:path}", name="download", include_in_schema=False)
    @ecm.file()
    def download_file(self, req: Request, path: str) -> t.Any:
        try:
            res = self._storage_service.get(path)

            if res.get_cdn_url() is None:  # pragma: no cover
                return StreamingResponse(
                    res.object.as_stream(),
                    media_type=res.content_type,
                    headers={
                        "Content-Disposition": f"attachment;filename={res.filename}"
                    },
                )

            if res.object.driver.name != "Local Storage":  # pragma: no cover
                return RedirectResponse(res.get_cdn_url())  # type:ignore[arg-type]

            return {
                "path": res.get_cdn_url(),  # since we are using a local storage, this will return a path to the file
                "filename": res.filename,
                "media_type": res.content_type,
            }

        except ObjectDoesNotExistError as obex:
            raise NotFound() from obex
