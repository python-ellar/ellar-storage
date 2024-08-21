import typing as t

from ellar.common import IModuleSetup, Module
from ellar.core import Config, ModuleSetup
from ellar.core.modules import DynamicModule, ModuleBase, ModuleRefBase
from ellar.di import ProviderConfig

from ellar_storage.controller import StorageController
from ellar_storage.schemas import StorageSetup
from ellar_storage.services import StorageService
from ellar_storage.storage import StorageDriver


class _ContainerOptions(t.TypedDict):
    key: str


class _StorageSetupKey(t.TypedDict):
    driver: t.Type[StorageDriver]
    options: t.Union[_ContainerOptions, t.Dict[str, t.Any]]


@Module(exports=[StorageService], name="EllarStorageModule")
class StorageModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(
        cls,
        default: t.Optional[str] = None,
        disable_storage_controller: bool = False,
        **kwargs: _StorageSetupKey,
    ) -> DynamicModule:
        schema = StorageSetup(
            storages=kwargs,  # type:ignore[arg-type]
            default=default,
            disable_storage_controller=disable_storage_controller,
        )
        return DynamicModule(
            cls,
            providers=[
                ProviderConfig(StorageService, use_value=StorageService(schema)),
            ],
            controllers=[]
            if schema.disable_storage_controller
            else [StorageController],
        )

    @classmethod
    def register_setup(cls) -> ModuleSetup:
        return ModuleSetup(cls, inject=[Config], factory=cls.__register_setup_factory)

    @staticmethod
    def __register_setup_factory(
        module_ref: ModuleRefBase, config: Config
    ) -> DynamicModule:
        if config.get("STORAGE_CONFIG") and isinstance(config.STORAGE_CONFIG, dict):
            schema = StorageSetup(**dict(config.STORAGE_CONFIG))
            return DynamicModule(
                module_ref.module,
                providers=[
                    ProviderConfig(StorageService, use_value=StorageService(schema)),
                ],
                controllers=[]
                if schema.disable_storage_controller
                else [StorageController],
            )
        raise RuntimeError("Could not find `STORAGE_CONFIG` in application config.")
