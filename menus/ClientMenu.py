from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import MenuEntryBack, StaticMenuEntry

from collections.abc import Sequence

from components.clients.client import Client
from components.clients.repository import IClientRepository

from modules.menu.input import validator_always, converter_string, validator_string_not_empty

from typing import Self
from datetime import date

class ClientMenu(MenuBase):
    """
        Меню управления отдельным читателем - изменение или удаление читателя.
    """
    def __init__(self, client: Client, clientRepo: IClientRepository) -> None:
        super().__init__()
        self._client = client
        self._repo = clientRepo
        self._clientName = client.Name
        self._clientAddress = client.Address
        self._regDate = client.RegistrationDate

    @MenuBase.text.getter
    def text(self: Self) -> str:
        return (
            f"Имя: {self._clientName}\n"
            f"Адрес: {self._clientAddress}\n"
            f"Дата регистрации: {self._regDate}"
        )

    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res = [
            StaticMenuEntry('Изменить имя', self._set_name),
            StaticMenuEntry('Изменить адрес', self._set_address),
            StaticMenuEntry('Изменить дату регистрации', self._set_reg_date)
        ]

        if (self._client.Name != self._clientName or
                self._client.Address != self._clientAddress or
                self._client.RegistrationDate != self._regDate):
            res.append(StaticMenuEntry('Сохранить', self._save))

        res.append(StaticMenuEntry('Удалить', self._delete))

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

    def _save(self: Self, host: MenuHostBase):
        orig_name = self._client.Name
        orig_address = self._client.Address
        orig_regDate = self._client.RegistrationDate
        try:
            self._client.Name = self._clientName
            self._client.Address = self._clientAddress
            self._client.RegistrationDate = self._regDate
            self._repo.update_client(self._client)
            host.pop()
        except Exception as e:
            self._client.Name = orig_name
            self._client.Address = orig_address
            self._client.RegistrationDate = orig_regDate
            host.message(f'Не удалось сохранить читателя. Текст ошибки:\n{e}')

    def _delete(self: Self, host: MenuHostBase):
        try:
            self._repo.delete_client(self._client)
            host.pop()
        except Exception as e:
            host.message(f'Не удалось удалить читателя. Текст ошибки:\n{e}')
