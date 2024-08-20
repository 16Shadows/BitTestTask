from datetime import date

from components.books.sqlite3 import BookRepositorySqlite3

from components.clients.sqlite3 import ClientRepositorySqlite3
from components.loans.sqlite3 import LoanRepositorySqlite3
from sqlite3 import connect

from modules.menu.hosts import SimpleConsoleMenuHost
from modules.menu.core import MenuHostBase
from modules.menu.static import StaticMenu, StaticMenuEntry, MenuEntryBack, SubmenuEntry
from modules.menu.pagination import PaginationMenu
from modules.menu.input import validator_always


from menus.AddLoanMenu import AddLoanMenu

from menus.common import book_to_text

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

if __name__ == "__main__":
    with connect("library.db") as connection:
        bookRepo = BookRepositorySqlite3(connection)
        clientRepo = ClientRepositorySqlite3(connection)
        loanRepo = LoanRepositorySqlite3(connection)
        rootMenu = StaticMenu("АРМ Помощник библиотекаря", [
            SubmenuEntry("Добавить взятие/возврат книги.", StaticMenu("Взятие/возврат книги", [
                SubmenuEntry("Добавить взятие книги", AddLoanMenu(bookRepo, clientRepo, loanRepo)),
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
                MenuEntryBack()
            ])),
            MenuEntryBack()
        ])

        host = SimpleConsoleMenuHost()
        host.run(rootMenu)