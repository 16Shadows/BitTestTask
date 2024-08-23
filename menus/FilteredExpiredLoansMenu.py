from datetime import date
from typing import Self
import math

from menus.common import loan_to_text

from components.loans.repository import LoanSearchPredicate, ILoanRepository

from modules.menu.core import MenuHostBase
from modules.menu.static import StaticMenu, StaticMenuEntry, MenuEntryBack, SubmenuEntry
from modules.menu.pagination import PaginationMenu
from modules.menu.input import converter_string, validator_string_not_empty

from menus.FindLoanMenu import FindLoanMenu

class FilteredExpiredLoansMenu(FindLoanMenu):
    """
        Меню для вывода поиска и вывода всех просроченных на указанную дату книг.
        Реализует также сохранение результата в tab-файл.
    """
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