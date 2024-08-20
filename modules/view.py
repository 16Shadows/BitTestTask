from collections.abc import Sequence
from typing import Self, overload
import abc

class View[T](Sequence[T], abc.ABC):
    """
        Абстрактный класс-реализация Sequence[T], упрощающая реализацию get_item.
    """
    def __len__(self: Self) -> int:
        return self._get_len()

    @overload
    def __getitem__(self: Self, index: int) -> T:
        pass
    @overload
    def __getitem__(self: Self, index: slice) -> Sequence[T]:
        pass

    def __getitem__(self: Self, index: int | slice) -> T | Sequence[T]:
        if isinstance(index, int):
            return self._get_slice(index, 1, 1)[0]
        else:
            scs = index.indices(self._get_len())
            return self._get_slice(scs[0], (scs[1] - scs[0]) // scs[2], scs[2])
        
    @abc.abstractmethod
    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[T]:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def _get_len(self: Self) -> int:
        raise NotImplementedError()
    
class CachingView[T](View[T], abc.ABC):
    """
        View[T], кеширующий значение своей длины и предоставляющий функцию сброса кеша.
    """
    _cached_len : int | None = None

    def __len__(self: Self) -> int:
        if self._cached_len is None:
            self._cached_len = self._get_len()
        return self._cached_len
    
    def reset_cache(self: Self) -> None:
        """
            Сбросить все кешированные значения.
        """
        self._cached_len = None