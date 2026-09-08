import os
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Generic

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PersistentCache(ABC, Generic[T]):
    def __init__(self, model_class: Type[T], base_dir: str) -> None:
        self._model_class = model_class
        self.base_dir = base_dir
        self.folder_path = os.path.join(self.base_dir, self._model_class.__name__)
        super().__init__()

    @abstractmethod
    def set(self, key: str, data: T, expiry_time: float) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
