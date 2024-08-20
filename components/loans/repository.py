from __future__ import annotations

from typing import Self, Protocol
from .loan import Loan

class ILoanRepository(Protocol):
    """Протокол для репозитория взятий книг"""
    def add_loan(self: Self, loan: Loan) -> None:
        """
            Добавить новое взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID уже существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        raise NotImplementedError()

    def update_loan(self: Self, loan: Loan) -> None:
        """
            Обновить существующее взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID не существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        raise NotImplementedError()