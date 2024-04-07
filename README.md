<p align="center">
  <a href="#" target="blank"><img src="https://python-ellar.github.io/ellar/img/EllarLogoB.png" width="200" alt="Ellar Logo" /></a>
</p>

![Test](https://github.com/eadwinCode/ellar-storage/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar-storage)
[![PyPI version](https://badge.fury.io/py/ellar-storage.svg)](https://badge.fury.io/py/ellar-storage)
[![PyPI version](https://img.shields.io/pypi/v/ellar-storage.svg)](https://pypi.python.org/pypi/ellar-storage)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar-storage.svg)](https://pypi.python.org/pypi/ellar-storage)

## Introduction
EllarStorage Module adds support for cloud and local file storage
management using [apache `libcloud`](https://github.com/apache/libcloud) package to your Ellar application.

## Installation
```shell
$(venv) pip install ellar-storage
```

This library was inspired by [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file)


## **Usage**
Follow Ellar project scaffold here, then you configure your module.

### StorageModule
Just like every other ellar `Module`s, `StorageModule`
can be configured directly in where its used or through application config.

### **StorageModule.setup**
Quick example using `StorageModule.setup` method.

Pattern of configuring Storages are in key-word patterns
where the `key` is `Folder name/Container` and value is `StorageDriver` init properties.
Example is shown below:

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

In the above illustration, When application initialization is complete,
`files`, `images` and `documents` will be created in `os.path.join(BASE_DIRS, "media")`.
Each is configured to be managed by Local Storage Driver.
See other supported [storage drivers](https://libcloud.readthedocs.io/en/stable/storage/supported_providers.html#provider-matrix)

Each storage required `key` and some other parameters for object instantiation,
so those should be provided in the `options` as a key-value pair.

Also, `default` parameter defines container/folder of choice when saving/retrieving 
a file if storage container was specified. 
It is important to note that if `default` is not set,
it will default to the first storage container which in this can is `files`.


### **StorageModule.register_setup**
Alternatively, we can move the storage configuration to application Config and everything will still work fine.
For example:
```python
## project_name/root_module.py

from ellar.common import Module
from ellar.core import ModuleBase
from ellar_storage import StorageModule

@Module(modules=[StorageModule.register_setup()])
class ApplicationModule(ModuleBase):
    pass
```

Then in `config.py` add the following code:

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

### StorageService

At the end of `StorageModule` setup, `StorageService` is registered into an Ellar DI system.
A quick way to test this would be through application instance.
For example:

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
# save a file in files folder
storage_service.save(
    file=datastructures.ContentFile(b"We can now save files in files folder", name="file.txt"), upload_storage='files')
# save a file in images folder
storage_service.save(
    file=datastructures.ContentFile(b"We can now save files in images folder", name="image.txt"), upload_storage='images')
# save a file in document folder
storage_service.save(
    file=datastructures.ContentFile(b"We can now save files in documents folder", name="docs.txt"), upload_storage='documents')
```
### StorageService in Route functions
You can inject `StorageService` into your controller or route functions. For example:

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

Here is a quick example of a controller to manage files. This is just to illustrate how to use `StorageService`.

```python
from ellar.common import (
    Controller,
    ControllerBase,
    File,
    Form,
    Inject,
    Query,
    UploadFile,
    delete,
    file,
    get,
    post,
)

from ellar_storage import StorageService


@Controller('/upload')
class FileManagerController(ControllerBase):
    def __init__(self, storage_service: StorageService):
        self._storage_service = storage_service

    @post("/", response=str)
    def upload_file(
            self,
            upload: File[UploadFile],
            storage_service: Inject[StorageService],
            upload_storage: Form[str]
    ):
        assert self._storage_service == storage_service
        res = storage_service.save(file=upload, upload_storage=upload_storage)
        return res.filename

    @get("/")
    @file(media_type="application/octet-stream", streaming=True)
    def download_file(self, path: Query[str]):
        res = self._storage_service.get(path)
        return {"media_type": res.content_type, "content": res.as_stream()}

    @get("/download_as_attachment")
    @file(media_type="application/octet-stream")
    def download_as_attachment(self, path: Query[str]):
        res = self._storage_service.get(path)
        return {
            "path": res.get_cdn_url(),  # since we are using a local storage, this will return a path to the file
            "filename": res.filename,
            'media_type': res.content_type
        }

    @delete("/", response=dict)
    def delete_file(self, path: Query[str]):
        self._storage_service.delete(path)
        return ""
```

See [Sample Project]()


### StoredFile
`StoredFile` is file-like object returned from saving and retrieving saved files. 
Its also extends some `libcloud` Object methods
and has reference to the `libcloud` Object retrieved from the `libcloud` storage container.

Some important attributes:

- **name**: File name
- **size**: File Size
- **filename**: File name 
- **content_type**: File Content Type
- **object**: `libcloud` Object reference
- **read(self, n: int = -1, chunk_size: t.Optional[int] = None) -> bytes**: Reads file content
- **get_cdn_url(self) -> t.Optional[str]**: gets file cdn url
- **as_stream(self, chunk_size: t.Optional[int] = None) -> t.Iterator[bytes]**: create a file stream
- **delete(self) -> bool**: deletes file from container

## License
Ellar is [MIT licensed](LICENSE).
