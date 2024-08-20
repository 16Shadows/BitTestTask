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
    
@dataclass
class ClientSearchPredicate:
    NameContains : str | None = None
    """
        Имя читателя должно содержать эту подстроку.
    """