from datetime import date
from typing import Self
import math

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
from modules.menu.input import validator_always, converter_string, validator_string_not_empty


from menus.AddLoanMenu import AddLoanMenu
from menus.AddLoanReturnMenu import AddLoanReturnMenu

from menus.FindBookMenu import FindBookMenu
from menus.FindLoanMenu import FindLoanMenu
from menus.FilteredLoansMenu import FilteredLoansListMenu

from menus.common import book_to_text, client_to_text, loan_to_text

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

class FilteredExpiredLoansMenu(FindLoanMenu):
    def __init__(self, repo: ILoanRepository, at: date) -> None:
        super().__init__(self._do_search)
        self._repo = repo
        self._at = at

    def _do_search(self: Self, host: MenuHostBase, predicate: LoanSearchPredicate):
        host.push(StaticMenu("Выберите действие:", [
            SubmenuEntry("Просмотреть отчёт.", 
                lambda: PaginationMenu(
                    self._repo.get_expired_loans_at(self._at, predicate),
                    text_generator=lambda x: f"{loan_to_text((x[0], x[1], x[2]))} - {x[3]} дней."
                )
            ),
            StaticMenuEntry("Сохранить отчёт в файл", lambda host: self._save_to_file(host, predicate)),
            MenuEntryBack()
        ]))

    def _save_to_file(self: Self, host: MenuHostBase, predicate: LoanSearchPredicate):
        filename = host.input(
            "Введите название файла для сохранения отчёта (или нажмите Ctrl + C для отмены):",
            converter_string,
            validator_string_not_empty,
            "Название файла должно быть не пустой строкой"
        )
        if filename is None:
            return
        
        dataset = self._repo.get_expired_loans_at(self._at, predicate)
        chunkSize = 100

        def escape_tsv_string(val: str) -> str:
            return val.replace('"', '""')

        with open(f'{filename}.tab', "w", encoding="utf-8") as report:
            print("BookName\tAuthor\tGenre\tPublicationYear\tClientName\tClientRegDate\tLoanStartDate\tLoanEndDate\tExpiredByDays", file=report)
            chunkCount =  math.ceil(len(dataset) / chunkSize)
            for chunkIndex in range(chunkCount):
                for loan in dataset[chunkIndex*chunkSize:(chunkIndex+1)*chunkSize]:
                    print(
                        f'"{escape_tsv_string(loan[1].Name)}"\t'
                        f'"{escape_tsv_string(loan[1].Author)}"\t'
                        f'"{escape_tsv_string(loan[1].Genre)}"\t'
                        f'{loan[1].PublicationYear}\t'
                        f'"{escape_tsv_string(loan[2].Name)}"\t'
                        f'{loan[2].RegistrationDate.isoformat()}\t'
                        f'{loan[0].StartDate}\t'
                        f'{loan[0].EndDate}\t'
                        f'{loan[3]}',
                        file=report
                    )

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
                SubmenuEntry("Список выданных книг", lambda: FilteredLoansListMenu(loanRepo, DummyGeocoder())),
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