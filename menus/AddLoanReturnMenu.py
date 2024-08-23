from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import MenuEntryBack, StaticMenuEntry, SubmenuEntry
from modules.menu.pagination import SelectorPaginationMenu
from modules.menu.input import validator_always
from modules.events import WeakSubscriber

from collections.abc import Sequence

from components.books.book import Book
from components.clients.client import Client
from components.loans.loan import Loan
from components.loans.repository import ILoanRepository, LoanSearchPredicate

from typing import Self
from datetime import date

from .common import book_to_text, client_to_text, loan_to_text
from .FindLoanMenu import FindLoanMenu

class AddLoanReturnMenu(MenuBase):
    """
        Меню добавления факта возврата книги
    """

    def __init__(self, loanRepo : ILoanRepository) -> None:
        self._loan : tuple[Loan, Book, Client] | None = None
        self._returnDate : date = date.today()
        self._loanRepo = loanRepo

    @MenuBase.text.getter
    def text(self: Self) -> str:
        return (
            "Добавление возврата книги:\n"
            f"Книга: {(book_to_text(self._loan[1]) if self._loan is not None else "не выбрана")}.\n"
            f"Читатель: {(client_to_text(self._loan[2]) if self._loan is not None else "не выбран")}.\n"
            f"Дата взятия: {(self._loan[0].StartDate.isoformat() if self._loan is not None else "не выбрана")}.\n"
            f"Дата возврата (ГГГГ-ММ-ДД): {self._returnDate.isoformat()}"
        )
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res : list[MenuEntryBase] = [
            SubmenuEntry("Выбрать книгу", FindLoanMenu(self._on_search_loan)),
            StaticMenuEntry("Изменить дату возврата", self._set_return_date)
        ]

        if self._loan is not None:
            res.append(StaticMenuEntry("Зафиксировать возврат", self._return_loan))

        res.append(MenuEntryBack())

        return res

    def _on_search_loan(self: Self, host: MenuHostBase, predicate: LoanSearchPredicate):
        menu = SelectorPaginationMenu(
            self._loanRepo.get_unreturned_loans(predicate),
            loan_to_text
        )
        menu.on_item_selected += WeakSubscriber(self._on_loan_selected)
        host.push(menu)

    def _on_loan_selected(self: Self, host: MenuHostBase, loan: tuple[Loan, Book, Client]):
        # Выходим из 2 вложенных меню (поиск и выбор)
        host.pop()
        host.pop()
        self._loan = loan

    def _set_return_date(self: Self, host: MenuHostBase):
        when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      validator_always,
                      "Неверный формат даты!")
        if when is None:
            return
        self._returnDate = when

    def _return_loan(self: Self, host: MenuHostBase):
        loan = self._loan[0] #type: ignore
        loan.ReturnDate = self._returnDate
        self._loanRepo.update_loan(loan) #type: ignore
        host.pop()