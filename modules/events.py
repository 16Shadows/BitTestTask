from __future__ import annotations

from typing import Callable, Self
from weakref import WeakMethod


class WeakSubscriber[*TArgs](WeakMethod[Callable[[*TArgs], None]]):
    '''
    Слабый подписчик события (Event)
    '''

    #Реализуем call, который будет вызывать метод, если он ещё жив, а не возвращать метод для вызова
    def __call__(self, *args: *TArgs) -> None:
        m = super().__call__()
        if m is None:
            return
        m(*args)
    
    @property
    def alive(self: Self) -> bool:
        '''Жив ли ещё этот подписчик'''
        return self._alive # type: ignore


class Event[*TArgs]:
    '''
    Класс события с множеством подписчиков.
    Поддерживает слабые методы через WeakSubscriber.
    '''

    def __init__(self) -> None:
        self._subscribers : list[Callable[[*TArgs], None]] = []
        '''Подписчики этого события'''

    def __iadd__(self: Self, other: Callable[[*TArgs], None] | WeakSubscriber[*TArgs]) -> Self:
        '''
        Добавить подписчика этого события
        '''
        self._subscribers.append(other)
        return self

    def __isub__(self: Self, other: Callable[[*TArgs], None] | WeakSubscriber[*TArgs]) -> Self:
        '''
        Убрать подписчика этого события
        '''
        #remove subscriber if any
        try:
            self._subscribers.remove(other)
        except ValueError:
            pass
        return self
        
    def __call__(self: Self, *args: *TArgs) -> None:
        '''
        Вызвать всех подписчиков этого события с указанными аргументами
        '''
        purge = False
        for sub in self._subscribers:
            sub(*args)
            if isinstance(sub, WeakSubscriber):
                purge = purge or not sub.alive
        
        if purge:
            self._subscribers = [x for x in self._subscribers if not isinstance(x, WeakSubscriber) or x.alive]