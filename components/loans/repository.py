from __future__ import annotations

from typing import Self, Protocol
from collections.abc import Sequence
from .loan import Loan
from ..books.book import Book
from ..clients.client import Client

from dataclasses import dataclass
from datetime import date

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
    
    def get_unreturned_loans(self: Self, predicate: LoanSearchPredicate | None = None) -> Sequence[tuple[Loan, Book, Client]]:
        """
            Вывести список всех невозвращённых книг (взятий книг), удовлетворяющих предикату
        """
        raise NotImplementedError()
    
    def get_expired_loans_at(self: Self, at: date, predicate: LoanSearchPredicate | None = None) -> Sequence[tuple[Loan, Book, Client, int]]:
        """
            Получить список всех просроченных на указанную дату взятий книг, удовлетворяющих предикату.
            Аргументы:
                at : date -- дата, для которой формируется список.
                             Книги, которые были просроченны позже этой даты, не будут отображены.
                             Число дней, на которое книги были просрочены, будет отсчитываться до этой даты.
                predicate: LoanSearchPredicate -- предикат для фильтрации взятых книг.
        """
        raise NotImplementedError()
    
    def get_book_history(self: Self, book: Book) -> Sequence[tuple[Loan, Client]]:
        """
            Вернуть всю историю взятий книги в хронологическом порядке.
        """
        raise NotImplementedError()
    
    def is_book_loaned_during(self: Self, book: Book, start: date, end: date) -> bool:
        """
            Проверить, выдана ли указанная книга в какой-то момент на протяжении указанного промежутка времени.
            
            Аргументы:
            book: Book - книга
            start : date - начало промежутка (включительно)
            end: date - конец промежутка (включительно)
        """
        raise NotImplementedError()

@dataclass    
class LoanSearchPredicate:
    ClientNameContains : str | None = None
    BookNameContains : str | None = None
    AuthorContains : str | None = None
    GenreContains : str | None = None
    PublicationYearMin : int | None = None
    PublicationYearMax : int | None = None
    StartDateMin : date | None = None
    StartDateMax : date | None = None