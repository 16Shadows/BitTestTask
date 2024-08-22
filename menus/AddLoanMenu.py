from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import MenuEntryBack, StaticMenuEntry, SubmenuEntry
from modules.menu.pagination import SelectorPaginationMenu
from modules.events import WeakSubscriber

from collections.abc import Sequence

from components.books.book import Book
from components.books.repository import IBookRepository, BookSearchPredicate
from components.clients.client import Client
from components.clients.repository import IClientRepository, ClientSearchPredicate
from components.loans.loan import Loan
from components.loans.repository import ILoanRepository

from typing import Self
from datetime import date

from .common import book_to_text, client_to_text
from .FindBookMenu import FindBookMenu
from .FindClientMenu import FindClientMenu

class AddLoanMenu(MenuBase):
    def __init__(self, bookRepo : IBookRepository, clientRepo : IClientRepository, loanRepo : ILoanRepository) -> None:
        self._book : Book | None = None
        self._client : Client | None = None
        self._startDate : date = date.today()
        self._endDate : date = date.today()
        self._bookRepo = bookRepo
        self._clientRepo = clientRepo
        self._loanRepo = loanRepo

    @MenuBase.text.getter
    def text(self: Self) -> str:
        return (
            "Добавление взятия книги:\n"
            f"Книга: {(book_to_text(self._book) if self._book is not None else "не выбрана")}.\n"
            f"Читатель: {(client_to_text(self._client) if self._client is not None else "не выбран")}.\n"
            f"Дата выдачи (ГГГГ-ММ-ДД): {self._startDate.isoformat()}\n"
            f"Ожидаемая дата возврата (ГГГГ-ММ-ДД): {self._endDate.isoformat()}"
        )
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res : list[MenuEntryBase] = [
            SubmenuEntry("Выбрать книгу", FindBookMenu(self._on_search_book)),
            SubmenuEntry("Выбрать читателя", FindClientMenu(self._on_search_client)),
            StaticMenuEntry("Изменить дату выдачи", self._set_start_date),
            StaticMenuEntry("Изменить ожидаемую дату возврата", self._set_end_date)
        ]

        if self._client is not None and self._book is not None:
            res.append(StaticMenuEntry("Добавить", self._add_new_loan))

        res.append(MenuEntryBack())

        return res
    
    def _on_search_client(self: Self, host: MenuHostBase, predicate: ClientSearchPredicate):
        menu = SelectorPaginationMenu(
            self._clientRepo.get_clients(predicate),
            client_to_text
        )
        menu.on_item_selected += WeakSubscriber(self._on_client_selected)
        host.push(menu)

    def _on_client_selected(self: Self, host: MenuHostBase, client: Client):
        # Выходим из 2 вложенных меню (поиск и выбор)
        host.pop()
        host.pop()
        self._client = client

    def _on_search_book(self: Self, host: MenuHostBase, predicate: BookSearchPredicate):
        menu = SelectorPaginationMenu(
            self._bookRepo.get_unloaned_books_at(date.today(), predicate),
            book_to_text
        )
        menu.on_item_selected += WeakSubscriber(self._on_book_selected)
        host.push(menu)

    def _on_book_selected(self: Self, host: MenuHostBase, book: Book):
        # Выходим из 2 вложенных меню (поиск и выбор)
        host.pop()
        host.pop()
        self._book = book

    def _set_start_date(self: Self, host: MenuHostBase):
        when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      lambda x: x <= self._endDate,
                      "Дата должна быть в корректном формате и не позже ожидаемой даты возврата!")
        if when is None:
            return
        self._startDate = when

    def _set_end_date(self: Self, host: MenuHostBase):
        when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      lambda x: x >= self._startDate,
                      "Дата должна быть в корректном формате и не раньше даты выдачи!")
        if when is None:
            return
        self._endDate = when

    def _add_new_loan(self: Self, host: MenuHostBase):
        loan = Loan(
            self._startDate,
            self._endDate,
            self._client.ID, #type: ignore
            self._book.ID #type: ignore
        )
        self._loanRepo.add_loan(loan)
        host.pop()