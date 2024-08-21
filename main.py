from datetime import date
from typing import Self

from components.books.repository import BookSearchPredicate, IBookRepository
from components.books.sqlite3 import BookRepositorySqlite3

from components.clients.sqlite3 import ClientRepositorySqlite3

from components.loans.sqlite3 import LoanRepositorySqlite3
from components.loans.repository import LoanSearchPredicate, ILoanRepository

from sqlite3 import connect

from modules.menu.hosts import SimpleConsoleMenuHost
from modules.menu.core import MenuHostBase
from modules.menu.static import StaticMenu, StaticMenuEntry, MenuEntryBack, SubmenuEntry
from modules.menu.pagination import PaginationMenu
from modules.menu.input import validator_always


from menus.AddLoanMenu import AddLoanMenu
from menus.AddLoanReturnMenu import AddLoanReturnMenu

from menus.FindBookMenu import FindBookMenu
from menus.FindLoanMenu import FindLoanMenu

from menus.common import book_to_text, client_to_text, loan_to_text

def unloaned_books_at(host: MenuHostBase):
    when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      validator_always,
                      "Неверный формат даты!")
    if when is None:
        return
    host.push(PaginationMenu(
        bookRepo.get_unloaned_books_at(when),
        text_generator=book_to_text
    ))

class FilteredBooksListMenu(FindBookMenu):
    def __init__(self, bookRepo: IBookRepository) -> None:
        super().__init__(self._do_search)
        self._bookRepo = bookRepo

    def _do_search(self: Self, host: MenuHostBase, predicate: BookSearchPredicate):
        host.push(PaginationMenu(self._bookRepo.get_books(predicate), text_generator=book_to_text))

class FilteredLoansListMenu(FindLoanMenu):
    def __init__(self, repo: ILoanRepository) -> None:
        super().__init__(self._do_search)
        self._repo = repo

    def _do_search(self: Self, host: MenuHostBase, predicate: LoanSearchPredicate):
        host.push(PaginationMenu(self._repo.get_unreturned_loans(predicate), text_generator=loan_to_text))

if __name__ == "__main__":
    with connect("library.db") as connection:
        bookRepo = BookRepositorySqlite3(connection)
        clientRepo = ClientRepositorySqlite3(connection)
        loanRepo = LoanRepositorySqlite3(connection)
        rootMenu = StaticMenu("АРМ Помощник библиотекаря", [
            SubmenuEntry("Добавить взятие/возврат книги.", StaticMenu("Взятие/возврат книги", [
                SubmenuEntry("Добавить взятие книги", lambda: AddLoanMenu(bookRepo, clientRepo, loanRepo)),
                SubmenuEntry("Добавить возврат книги", lambda: AddLoanReturnMenu(loanRepo)),
                MenuEntryBack()
            ])),
            SubmenuEntry("Книги", StaticMenu("Действия с книгами", [
                SubmenuEntry("Список всех книг", lambda: FilteredBooksListMenu(bookRepo)),
                SubmenuEntry("Список выданных книг", lambda: FilteredLoansListMenu(loanRepo)),
                MenuEntryBack()
            ])),
            SubmenuEntry("Отчёты", StaticMenu("Отчёты", [
                SubmenuEntry("Свободные книги", StaticMenu("Свободные книги на какой момент?", [
                    StaticMenuEntry(
                        "Сегодня",
                        lambda host: host.push(
                            PaginationMenu(
                                bookRepo.get_unloaned_books_at(date.today()),
                                text_generator=book_to_text
                            )
                        )
                    ),
                    StaticMenuEntry(
                        "Выбрать день",
                        unloaned_books_at
                    ),
                    MenuEntryBack()
                ])),
                StaticMenuEntry(
                    "Число взятых за всё время книг",
                    lambda host: host.push(
                        PaginationMenu(
                            clientRepo.get_total_loans_per_client(),
                            text_generator=lambda x: f'{client_to_text(x[0])} - {x[1]}'
                        )
                    )
                ),
                StaticMenuEntry(
                    "Число книг на руках",
                    lambda host: host.push(
                        PaginationMenu(
                            clientRepo.get_total_unreturned_loans_per_client(),
                            text_generator=lambda x: f'{client_to_text(x[0])} - {x[1]}'
                        )
                    )
                ),
                StaticMenuEntry(
                    "Последние посещения",
                    lambda host: host.push(
                        PaginationMenu(
                            clientRepo.get_last_visit_dates(),
                            text_generator=lambda x: f'{client_to_text(x[0])} - {x[1].isoformat()}'
                        )
                    )
                ),
                StaticMenuEntry(
                    "Популярные жанры (по числу взятых книг жанра)",
                    lambda host: host.push(
                        PaginationMenu(
                            bookRepo.get_genre_scores(),
                            text_generator=lambda x: f'{x[0]} - {x[1]}'
                        )
                    )
                ),
                MenuEntryBack()
            ])),
            MenuEntryBack()
        ])

        host = SimpleConsoleMenuHost()
        host.run(rootMenu)