from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import MenuEntryBack, StaticMenuEntry
from modules.menu.input import validator_always, converter_string, validator_string_not_empty

from collections.abc import Sequence

from components.clients.client import Client
from components.clients.repository import IClientRepository

from typing import Self
from datetime import date

class AddClientMenu(MenuBase):
    """
        Меню добавления нового читателя.
    """
    def __init__(self, clientRepo : IClientRepository) -> None:
        self._regDate : date = date.today()
        self._clientName : str | None = None
        self._clientAddress : str | None = None
        self._clientRepo = clientRepo

    @MenuBase.text.getter
    def text(self: Self) -> str:
        return (
            "Добавление взятия книги:\n"
            f"Имя: {(self._clientName if self._clientName is not None else "не выбрано")}.\n"
            f"Адрес: {(self._clientAddress if self._clientAddress is not None else "не выбран")}.\n"
            f"Дата регистрации (ГГГГ-ММ-ДД): {self._regDate.isoformat()}"
        )
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res : list[MenuEntryBase] = [
            StaticMenuEntry("Изменить имя", self._set_name),
            StaticMenuEntry("Изменить адрес", self._set_address),
            StaticMenuEntry("Изменить дату регистрации", self._set_reg_date)
        ]

        if self._clientName is not None and self._clientAddress is not None:
            res.append(StaticMenuEntry("Добавить", self._add_new_client))

        res.append(MenuEntryBack())

        return res
    
    def _set_reg_date(self: Self, host: MenuHostBase):
        when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      validator_always,
                      "Дата должна быть в корректном формате!")
        if when is None:
            return
        self._regDate = when

    def _set_name(self: Self, host: MenuHostBase):
        name = host.input("Введите имя (или используйте Ctrl + C, чтобы отменить ввод): ",
                      converter_string,
                      validator_string_not_empty,
                      "Имя должно быть не пустым!")
        if name is None:
            return
        self._clientName = name

    def _set_address(self: Self, host: MenuHostBase):
        address = host.input("Введите адрес (или используйте Ctrl + C, чтобы отменить ввод): ",
                      converter_string,
                      validator_string_not_empty,
                      "Адрес должен быть не пустым!")
        if address is None:
            return
        self._clientAddress = address

    def _add_new_client(self: Self, host: MenuHostBase):
        client = Client(
            self._clientName, #type: ignore
            self._regDate,
            self._clientAddress #type: ignore
        )
        self._clientRepo.add_client(client)
        host.pop()