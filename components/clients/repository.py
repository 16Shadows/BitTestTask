from __future__ import annotations

from typing import Self, Protocol, Sequence
from datetime import date
from .client import Client
from dataclasses import dataclass

class IClientRepository(Protocol):
    """Протокол для репозитория читателей"""

    def get_clients(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[Client]:
        """
            Все читатели библиотеки
        """
        raise NotImplementedError()
    
    def get_last_visit_dates(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[tuple[Client, date]]:
        """
            Дата последнего посещения библиотеки каждым читателем.
        """
        raise NotImplementedError()
    
    def get_total_loans_per_client(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[tuple[Client, int]]:
        """
            Общее количество взятых книг каждым читателем.
        """
        raise NotImplementedError()
    
    def get_total_unreturned_loans_per_client(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[tuple[Client, int]]:
        """
            Количество невозвращённых каждым читателем книг.
        """
        raise NotImplementedError()
    
    def add_client(self: Self, client: Client) -> None:
        """
            Добавить нового читателя.
            
            client: Client -- читатель.

            Если читатель с таким ID уже существует, будет поднята ошибка.
        """
        raise NotImplementedError()
    
    def update_client(self: Self, client: Client) -> None:
        """
            Обновить существующего читателя.
            
            client: Client - читатель.

            Если читателя с таким ID не существует или возникает конфликт между датой регистрации клиента и датами взятий им книги, будет поднята ошибка.
        """
        raise NotImplementedError()

@dataclass
class ClientSearchPredicate:
    NameContains : str | None = None
    """
        Имя читателя должно содержать эту подстроку.
    """