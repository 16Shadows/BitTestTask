from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import StaticMenuEntry, MenuEntryBack
from modules.menu.input import validator_string_not_empty, converter_string
from typing import Self, Callable
from collections.abc import Sequence
from copy import deepcopy

from components.clients.repository import ClientSearchPredicate

class FindClientMenu(MenuBase):
    def __init__(self, on_search: Callable[[MenuHostBase, ClientSearchPredicate], None]) -> None:
        self._predicate = ClientSearchPredicate()
        self._on_search = on_search

    @MenuBase.text.getter
    def text(self: Self) -> str:
        res = "Поиск читателя\n"
        
        if self._predicate.NameContains is not None:
            res += "Имя содержит: " + self._predicate.NameContains

        return res
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res : list[MenuEntryBase] = []
        
        res.append(StaticMenuEntry("Изменить поиск по имени", self._set_name_filter))

        if self._predicate.NameContains is not None:
            res.append(StaticMenuEntry("Очистить поиск по названию", self._clear_name_filter))

        res.append(StaticMenuEntry("Найти", lambda host: self._on_search(host, deepcopy(self._predicate))))

        res.append(MenuEntryBack())

        return res

    def _set_name_filter(self: Self, host : MenuHostBase):
        value = host.input("Введите частичное или полное имя читателя (или нажмите Ctrl + C, чтобы отменить ввод): ",
                            converter_string,
                            validator_string_not_empty,
                            "Имя должено быть не пустым!"
        )
        if value is None:
            return
        self._predicate.NameContains = value

    def _clear_name_filter(self: Self, host: MenuHostBase):
        self._predicate.NameContains = None