<p align="center">
  <a href="#" target="blank"><img src="https://python-ellar.github.io/ellar/img/EllarLogoB.png" width="200" alt="Ellar Logo" /></a>
</p>

![Test](https://github.com/python-ellar/ellar-storage/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar-storage)
[![PyPI version](https://badge.fury.io/py/ellar-storage.svg)](https://badge.fury.io/py/ellar-storage)
[![PyPI version](https://img.shields.io/pypi/v/ellar-storage.svg)](https://pypi.python.org/pypi/ellar-storage)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar-storage.svg)](https://pypi.python.org/pypi/ellar-storage)

## Introduction
The EllarStorage Module enriches your Ellar application with robust support for managing both cloud and 
local file storage.
Leveraging the capabilities of the [Apache `libcloud`](https://github.com/apache/libcloud) package
to simplify file storage operations within your Ellar-powered projects.

## Installation
```shell
$(venv) pip install ellar-storage
```

This library drew inspiration from [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file).

## Usage
To integrate EllarStorage into your project, follow the standard Ellar project structure and then configure the module as follows:

### StorageModule
Similar to other Ellar modules, the `StorageModule` can be configured directly where it's used or through the application configuration.

### StorageModule.setup
You can set up the `StorageModule` using the `setup` method. Here's a quick example:

```python
import os
from pathlib import Path
from ellar.common import Module
from ellar.core import ModuleBase
from ellar_storage import StorageModule, get_driver, Provider

BASE_DIRS = Path(__file__).parent

@Module(modules=[
    StorageModule.setup(
        files={
            "driver": get_driver(Provider.LOCAL),
            "options": {"key": os.path.join(BASE_DIRS, "media")},
        },
        images={
            "driver": get_driver(Provider.LOCAL),
            "options": {"key": os.path.join(BASE_DIRS, "media")},
        },
        documents={
            "driver": get_driver(Provider.LOCAL),
            "options": {"key": os.path.join(BASE_DIRS, "media")},
        },
        default="files"
    )
])
class ApplicationModule(ModuleBase):
    pass
```

In this example, after application initialization, folders for `files`, `images`, and `documents` will be created in the specified directory. Each folder is configured to be managed by a local storage driver. You can explore other supported [storage drivers](https://libcloud.readthedocs.io/en/stable/storage/supported_providers.html#provider-matrix).

### StorageModule.register_setup
Alternatively, you can move the storage configuration to the application config:

```python
## project_name/root_module.py

from ellar.common import Module
from ellar.core import ModuleBase
from ellar_storage import StorageModule

@Module(modules=[StorageModule.register_setup()])
class ApplicationModule(ModuleBase):
    pass
```

Then, in `config.py`, you can define the storage configurations:

```python
import os
from pathlib import Path
from ellar.core.conf import ConfigDefaultTypesMixin
from ellar_storage import get_driver, Provider

BASE_DIRS = Path(__file__).parent

class DevelopmentConfig(ConfigDefaultTypesMixin):
    DEBUG = True

    STORAGE_CONFIG = dict(
        storages=dict(
            files={
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": os.path.join(BASE_DIRS, "media")},
            },
            images={
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": os.path.join(BASE_DIRS, "media")},
            },
            documents={
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": os.path.join(BASE_DIRS, "media")},
            }
        ),
        default="files"
    )
```

### StorageController
`StorageModule` also registers `StorageController` which is useful when retrieving saved files.
This can be disabled by setting `disable_storage_controller` to `True`.

Also, `StorageController` is not protected and will be accessible to the public.
However, it can be protected by simply applying `@Guard` or `@Authorize` decorator.

#### Retrieving Saved Data
By using `request.url_for`, we can generate a download link for the file we wish to retrieve
For example:

```python
from ellar.common import Inject, post
from ellar.core import Request

@post('/get-books')
def get_book_by_id(self, req: Request, book_id, session: Inject[Session]):
    book = session.execute(
        select(Book).where(Book.title == "Pointless Meetings")
    ).scalar_one()
    
    return {
      "title": book.title,
      "cover": req.url_for("storage:download", path="{storage_name}/{file_name}"),
      "thumbnail": req.url_for("storage:download", path=book.thumbnail.path)
    }
```
With `req.url_for("storage:download", path="{storage_name}/{file_name}")`,
we are able to create a download link to retrieve saved files.

### StorageService
At the end of the `StorageModule` setup, `StorageService` is registered into the Ellar DI system. Here's a quick example of how to use it:

```python
## project_name/server.py

import os
from ellar.app import AppFactory
from ellar.common import datastructures, constants
from ellar.core import LazyModuleImport as lazyLoad
from ellar_storage import StorageService

application = AppFactory.create_from_app_module(
    lazyLoad("project_name.root_module:ApplicationModule"),
    config_module=os.environ.get(
        constants.ELLAR_CONFIG_MODULE, "carapp.config:DevelopmentConfig"
    ),
)

storage_service: StorageService = application.injector.get(StorageService)
# Example: save a file in the 'files' folder
storage_service.save(
    file=datastructures.ContentFile(b"We can now save files in the 'files' folder", name="file.txt"), upload_storage='files')
# Example: save a file in the 'images' folder
storage_service.save(
    file=datastructures.ContentFile(b"We can now save files in the 'images' folder", name="image.txt"), upload_storage='images')
# Example: save a file in the 'documents' folder
storage_service.save(
    file=datastructures.ContentFile(b"We can now save files in the 'documents' folder", name="docs.txt"), upload_storage='documents')
```

### StorageService in Route Functions
You can inject `StorageService` into your controllers or route functions. For instance:

In Controller:

```python
from ellar.common import ControllerBase, Controller
from ellar_storage import StorageService

@Controller()
class FileManagerController(ControllerBase):
    def __init__(self, storage_service: StorageService):
        self._storage_service = storage_service
```

In Route Function:

```python
from ellar.common import UploadFile, Inject, post
from ellar_storage import StorageService

@post('/upload')
def upload_file(self, file: UploadFile, storage_service: Inject[StorageService]):
    pass
```

See [Sample Project](https://github.com/python-ellar/ellar-storage/tree/master/samples)

## Some Quick Cloud Setup

### Google Cloud Storage

- For a service Account

    ```python
    from ellar.common import Module
    from ellar.core import ModuleBase
    from ellar_storage import StorageModule, get_driver, Provider
    
    @Module(modules=[
        StorageModule.setup(
            files={
                # For a service Account
                "driver": get_driver(Provider.GOOGLE_STORAGE),
                "options": {
                    "key": "client_email",
                    "secret": "private_key",
                    "...": "..."
                },
            },
        )
    ])
    class ApplicationModule(ModuleBase):
        pass
    ```
- Installed Application
    ```python
    from ellar.common import Module
    from ellar.core import ModuleBase
    from ellar_storage import StorageModule, get_driver, Provider
    
    @Module(modules=[
        StorageModule.setup(
            files={
                # For a service Account
                "driver": get_driver(Provider.GOOGLE_STORAGE),
                "options": {
                    "key": "client_id",
                    "secret": "client_secret",
                    "...": "..."
                },
            },
        )
    ])
    class ApplicationModule(ModuleBase):
        pass
    ```

- GCE instance
    ```python
    from ellar.common import Module
    from ellar.core import ModuleBase
    from ellar_storage import StorageModule, get_driver, Provider
    
    @Module(modules=[
        StorageModule.setup(
            files={
                # For a service Account
                "driver": get_driver(Provider.GOOGLE_STORAGE),
                "options": {
                    "key": "GOOG0123456789ABCXYZ",
                    "secret": "key_secret",
                    "...": "..."
                },
            },
        )
    ])
    class ApplicationModule(ModuleBase):
        pass
    ```
See [GCS](https://libcloud.readthedocs.io/en/stable/storage/drivers/google_storage.html?highlight=Google%20Cloud%20Storage#api-docs)

### AWS S3

```python
from ellar.common import Module
from ellar.core import ModuleBase
from ellar_storage import StorageModule, get_driver, Provider

@Module(modules=[
    StorageModule.setup(
        files={
            "driver": get_driver(Provider.S3),
            "options": {
                "key": "api key",
                "secret": "api secret key"
            },
        },
    )
])
class ApplicationModule(ModuleBase):
    pass
```

#### Specifying canned ACL when uploading an object
If you want to specify custom ACL when uploading an object, 
you can do so by passing `extra` argument with the acl attribute to the `save` or `save_content` methods.

Valid values for this attribute are:

- private (default)
- public-read 
- public-read-write 
- authenticated-read 
- bucket-owner-read 
- bucket-owner-full-control

For example
```python
from ellar.common import UploadFile, Inject, post
from ellar_storage import StorageService

@post('/upload')
def upload_file(self, file: UploadFile, storage_service: Inject[StorageService]):
    extra = {"content_type": "application/octet-stream", "acl": "public-read"}
    stored_file = storage_service.save(file=file, extra=extra)
    
    return {"message": f"{stored_file.filename} saved"}
```

## API Reference

### StorageService

- **_save(self, file: UploadFile, upload_storage: Optional[str] = None) -> StoredFile_**: Saves a file from an `UploadFile` object.
- **_save_async(self, file: UploadFile, upload_storage: Optional[str] = None) -> StoredFile_**: Asynchronously saves a file from an `UploadFile` object.
- **_save_content(self, **kwargs) -> StoredFile_**: Saves a file from content/bytes or through a file path.
- **_save_content_async(self, **kwargs) -> StoredFile_**: Asynchronously saves a file from content/bytes or through a file path.
- **_get(self, path: str) -> StoredFile_**: Retrieves a saved file if the specified `path` exists. The `path` can be in the format `container/filename.extension` or `filename.extension`.
- **_get_async(self, path: str) -> StoredFile_**: Asynchronously retrieves a saved file if the specified `path` exists.
- **_delete(self, path: str) -> bool_**: Deletes a saved file if the specified `path` exists.
- **_delete_async(self, path: str) -> bool_**: Asynchronously deletes a saved file if the specified `path` exists.
- **_get_container(self, name: Optional[str] = None) -> Container_**: Gets a `libcloud.storage.base.Container` instance for a configured storage setup.

### StoredFile

`StoredFile` is a file-like object returned from saving and retrieving files. 
It extends some `libcloud` Object methods and has a reference to the 
`libcloud` Object retrieved from the storage container.

Key attributes include:

- **_name_**: File name
- **_size_**: File size
- **_filename_**: File name 
- **_content_type_**: File content type
- **_object_**: `libcloud` Object reference
- **_read(self, n: int = -1, chunk_size: Optional[int] = None) -> bytes_**: Reads file content
- **_get_cdn_url(self) -> Optional[str]_**: Gets file CDN URL
- **_as_stream(self, chunk_size: Optional[int] = None) -> Iterator[bytes]_**: Creates a file stream
- **_delete(self) -> bool_**: Deletes the file from the container

## License
Ellar is [MIT licensed](LICENSE).
