from __future__ import annotations

from typing import Self, Protocol, Sequence
from .loan import Loan

class ILoanRepository(Protocol):
    """Протокол для репозитория взятий книг"""

    def get_loans(self: Self) -> Sequence[Loan]:
        """
            Все взятия книг.
        """
        raise NotImplementedError()
    
    def add_loan(self: Self, loan: Loan) -> None:
        """
            Добавить новое взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID уже существует или существует невозвращённое взятие этой книги и это взятие не является возвращённым, будет поднята ошибка.
        """
        raise NotImplementedError()
