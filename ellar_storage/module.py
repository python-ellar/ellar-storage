import typing as t

from ellar.common import IModuleSetup, Module
from ellar.core import Config, ModuleSetup
from ellar.core.modules import DynamicModule, ModuleBase
from ellar.di import ProviderConfig

from ellar_storage.schemas import StorageSetup
from ellar_storage.services import StorageService
from ellar_storage.storage import StorageDriver


class _ContainerOptions(t.TypedDict):
    key: str


class _StorageSetupKey(t.TypedDict):
    driver: t.Type[StorageDriver]
    options: _ContainerOptions


@Module()
class StorageModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(
        cls, default: t.Optional[str] = None, **kwargs: _StorageSetupKey
    ) -> DynamicModule:
        schema = StorageSetup(storages=kwargs, default=default)  # type:ignore[arg-type]
        return DynamicModule(
            cls,
            providers=[
                ProviderConfig(StorageService, use_value=StorageService(schema)),
            ],
        )

    @classmethod
    def register_setup(cls) -> ModuleSetup:
        return ModuleSetup(cls, inject=[Config], factory=cls.__register_setup_factory)

    @staticmethod
    def __register_setup_factory(
        module: t.Type["StorageModule"], config: Config
    ) -> DynamicModule:
        if config.get("STORAGE_CONFIG") and isinstance(config.STORAGE_CONFIG, dict):
            schema = StorageSetup(**dict(config.STORAGE_CONFIG))
            return DynamicModule(
                module,
                providers=[
                    ProviderConfig(StorageService, use_value=StorageService(schema)),
                ],
            )
        raise RuntimeError("Could not find `STORAGE_CONFIG` in application config.")
