from datetime import date
from typing import Self

from components.books.repository import BookSearchPredicate, IBookRepository
from components.books.sqlite3 import BookRepositorySqlite3

from components.clients.repository import IClientRepository, ClientSearchPredicate
from components.clients.sqlite3 import ClientRepositorySqlite3

from components.loans.sqlite3 import LoanRepositorySqlite3
from components.loans.repository import ILoanRepository

from sqlite3 import connect

from modules.menu.hosts import SimpleConsoleMenuHost
from modules.menu.core import MenuHostBase
from modules.menu.static import StaticMenu, StaticMenuEntry, MenuEntryBack, SubmenuEntry
from modules.menu.pagination import PaginationMenu
from modules.menu.input import validator_always, converter_string


from menus.AddLoanMenu import AddLoanMenu
from menus.AddLoanReturnMenu import AddLoanReturnMenu

from menus.AddBookMenu import AddBookMenu
from menus.FindBookMenu import FindBookMenu

from menus.FilteredLoansMenu import FilteredLoansListMenu
from menus.FilteredExpiredLoansMenu import FilteredExpiredLoansMenu

from menus.AddClientMenu import AddClientMenu
from menus.ClientMenu import ClientMenu
from menus.FindClientMenu import FindClientMenu

from menus.common import book_to_text, client_to_text

def unloaned_books_at(host: MenuHostBase, bookRepo: IBookRepository):
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

def expired_loans_at(host: MenuHostBase, repo: ILoanRepository):
    when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      validator_always,
                      "Неверный формат даты!")
    if when is None:
        return
    host.push(FilteredExpiredLoansMenu(repo, when))

class FilteredBooksListMenu(FindBookMenu):
    def __init__(self, bookRepo: IBookRepository) -> None:
        super().__init__(self._do_search)
        self._bookRepo = bookRepo

    def _do_search(self: Self, host: MenuHostBase, predicate: BookSearchPredicate):
        host.push(PaginationMenu(self._bookRepo.get_books(predicate), text_generator=book_to_text))

class FilteredClientsListMenu(FindClientMenu):
    def __init__(self, clientRepo: IClientRepository) -> None:
        super().__init__(self._do_search)
        self._repo = clientRepo

    def _do_search(self: Self, host: MenuHostBase, predicate: ClientSearchPredicate):
        host.push(PaginationMenu(
            self._repo.get_clients(predicate),
            entry_generator=lambda x: SubmenuEntry(client_to_text(x), lambda: ClientMenu(x, self._repo))
        ))

def add_reader(host: MenuHostBase, clientRepo: IClientRepository):
    name = host.input(
        "Введите имя читателя (или нажмите Ctrl + C для отмены): ",
        converter_string,
        validator_always,
        "Имя читателя должно быть не пустым!"
    )
    if name is None:
        return
    

class DummyGeocoder:
    """
        Геокодер-заглушка, который нужно заменить реальным геокодером.
        Увы, у меня нет доступа к API геокодера.
    """
    def address_to_coordinates(self: Self, address: str) -> tuple[float, float] | None:
       """
            Преобразует указаннный адрес в координаты точки на планете.
            Если адрес преобразовать невозможно, то возвращает None.
            Координаты возвращаются в виде tuple, с элементами в порядке долгота-широта
       """
       if address == 'Unknown':
            return None
       else:
            return (0, 0)

if __name__ == "__main__":
    with connect("library.db") as connection:
        #Внешние ключи активируются для каждого подключения, а не для БД в целом.
        connection.execute("PRAGMA foreign_keys = ON;")
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
                SubmenuEntry("Добавить книгу", lambda: AddBookMenu(bookRepo)),
                SubmenuEntry("Список всех книг", lambda: FilteredBooksListMenu(bookRepo)),
                SubmenuEntry("Список выданных книг", lambda: FilteredLoansListMenu(loanRepo, DummyGeocoder())),
                MenuEntryBack()
            ])),
            SubmenuEntry("Читатели", StaticMenu("Действия с читателями", [
                SubmenuEntry("Добавить читателя", lambda: AddClientMenu(clientRepo)),
                SubmenuEntry("Список читателей", lambda: FilteredClientsListMenu(clientRepo)),
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
                        lambda host: unloaned_books_at(host, bookRepo)
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
                SubmenuEntry("Просроченные книги за всё время", 
                    StaticMenu("Отобразить просроченные книги на какой день", [
                        StaticMenuEntry('Сегодня', lambda host: host.push(FilteredExpiredLoansMenu(loanRepo, date.today()))),
                        StaticMenuEntry('Выбрать день', lambda host: expired_loans_at(host, loanRepo)),
                        MenuEntryBack()
                    ])
                ),
                MenuEntryBack()
            ])),
            MenuEntryBack()
        ])

        host = SimpleConsoleMenuHost()
        host.run(rootMenu)