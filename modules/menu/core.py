from __future__ import annotations

from typing import Self, Callable
from collections.abc import Sequence
import abc

class MenuEntryBase(abc.ABC):
    """Базовый абстрактный класс пункта меню."""

    @property
    @abc.abstractmethod
    def text(self: Self) -> str:
        """Возвращает текст этого пункта меню"""
        raise NotImplementedError()

    @abc.abstractmethod
    def on_selected(self: Self, host: MenuHostBase) -> None:
        """Обработчик события выбора этого пункта меню.
        
        Аргументы:
        host : MenuHostBase -- контекст, в котором отображается меню.
        """
        raise NotImplementedError()

class MenuBase(abc.ABC):
    """Базовый абстрактный класс меню."""

    @property
    @abc.abstractmethod
    def text(self: Self) -> str:
        """Возвращает текст этого меню."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        """Возвращает пункты этого меню"""
        raise NotImplementedError()

class MenuHostBase(abc.ABC):
    """Базовый класс контекста отображения меню. Реализует логику перехода между меню и их отображения."""
    def __init__(self) -> None:
        self.menuStack : list[MenuBase] = []
    
    def push(self: Self, menu: MenuBase) -> None:
        """Добавить меню на вершину стека открытых меню. Меню на вершине стека отображается контекстом.
        
        menu : Menu -- меню для добавления.
        """
        self.menuStack.append(menu)

    def pop(self: Self) -> None:
        """Убрать меню с вершины стека открытых меню. Меню на вершине стека отображается контекстом."""
        self.menuStack.pop()

    def current(self: Self) -> MenuBase:
        """Получить текущее меню на вершине стека открытых меню."""
        return self.menuStack[-1]
    
    @abc.abstractmethod
    def run(self: Self, enterAt: MenuBase | None = None) -> None:
        """
        Начать отображение меню в текущем контексте.
        Этот метод блокирующий и завершится, когда последнее меню будет закрыто.
        
        menu : Menu | None -- меню, с которого нужно начать отображение.
                              Если меню указано, то текущей стек открытых меню будет очищен.
                              Если передано значение None, то будет открыто меню на вершине стека.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def message(self: Self, message: str) -> None:
        '''
        Отобразить сообщение пользователю в текщуем контексте
        '''
        raise NotImplementedError()

    @abc.abstractmethod
    def input[T](self: Self, prompt: str, convert: Callable[[str], T], validate: Callable[[T], bool], errorMessage: str) -> T | None:
        '''
        Получить ввод от пользователя в текущем контексте.

        Аргументы:
        prompt : str -- Отображаемое при запросе ввода сообщение
        convert : Callable[[str], T] -- функция-конвертер для преобразования входной строки к желаемому типу. Может поднимать исключение ValueError.
        validate : Callable[[T], bool] -- функция-валидатор для валидации преобразованного значения. Должна возвращать True, если значение валидно, False иначе.
        errorMessage : str -- сообщение, которое будет выведено, если будет поднято исключение ValueError или validate вернёт False.
        '''
        raise NotImplementedError()