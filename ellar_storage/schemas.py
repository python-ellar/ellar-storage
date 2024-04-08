import typing as t

from ellar.pydantic import field_validator, model_validator
from pydantic import BaseModel

from ellar_storage.storage import StorageDriver


class _StorageSetupItem(BaseModel):
    driver: t.Type[StorageDriver]
    options: t.Dict[str, t.Any] = {}

    @field_validator("options", mode="before")
    def pre_options_validate(cls, value: t.Dict) -> t.Any:
        if "key" not in value:
            raise ValueError("Driver Options must have a `key` option ")

        return value


class StorageSetup(BaseModel):
    # default storage name that must exist in `storages`
    # as a key if set else it will default to the first entry in `storages`
    default: t.Optional[str] = None
    # storage configurations
    storages: t.Dict[str, _StorageSetupItem]

    @model_validator(mode="before")
    def post_default_validate(cls, values: t.Dict) -> t.Any:
        storages = values.get("storages")
        default = values.get("default")

        if not storages:
            raise ValueError("At least one storage setup is required storages")

        if not default and storages:
            values["default"] = list(storages.keys())[0]

        if default and default not in storages:
            raise ValueError(f"storages must have a '{default}' as key")
        return values
