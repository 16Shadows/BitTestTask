from __future__ import annotations

from typing import Self, Callable
from collections.abc import Sequence
from .core import MenuBase, MenuEntryBase, MenuHostBase


class StaticMenu(MenuBase):
    """Просто меню с фиксированными текстом и пунктами"""
    def __init__(self, text: str, entries: Sequence[MenuEntryBase] = []) -> None:
        """Создать меню с указанными пунктами и текстом.
        
        Аргументы:
        text : str -- текст меню.
        entries : list[MenuEntryBase] -- пункты меню.
        """
        self._text = text
        self._entries = entries
    
    @MenuBase.text.getter
    def text(self: Self) -> str:
        return self._text
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        return self._entries
    

class StaticMenuEntry(MenuEntryBase):
    """Пункт меню с фиксированным текстом, обработчик которого реализован передаваемой в конструктор функцией"""
    def __init__(self, text: str, handler: Callable[[MenuHostBase], None]) -> None:
        """Создать пункт меню с указанным текстом и обработчиком.
        
        Аргументы:
        text : str -- текст пункта.
        handle : Callable[[MenuHostBase], None] -- обработчик события выбора.
        """
        super().__init__()
        self._text = text
        self.handler = handler

    @MenuEntryBase.text.getter
    def text(self: Self) -> str:
        return self._text

    def on_selected(self: Self, host: MenuHostBase) -> None:
        self.handler(host)


class MenuEntryBack(StaticMenuEntry):
    """Пункт меню, реализующий логику перехода к предыдущему меню."""
    def __init__(self) -> None:
        super().__init__('Назад', lambda host: host.pop())

class SubmenuEntry(StaticMenuEntry):
    """Пункт меню, реализующий открытие дочернего меню"""
    def __init__(self, text: str, menu: MenuBase) -> None:
        super().__init__(text, lambda host: host.push(menu))