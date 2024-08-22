from typing import Self, Protocol
import math

from components.loans.repository import LoanSearchPredicate, ILoanRepository

from modules.menu.core import MenuHostBase
from modules.menu.static import StaticMenu, StaticMenuEntry, MenuEntryBack, SubmenuEntry
from modules.menu.pagination import PaginationMenu
from modules.menu.input import converter_string, validator_string_not_empty

from .FindLoanMenu import FindLoanMenu
from .common import loan_to_text, book_to_text, client_to_text

class IGeocodingProvider(Protocol):
    def address_to_coordinates(self: Self, address: str) -> tuple[float, float] | None:
       """
            Преобразует указаннный адрес в координаты точки на планете.
            Если адрес преобразовать невозможно, то возвращает None.
            Координаты возвращаются в виде tuple, с элементами в порядке долгота-широта
       """
       raise NotImplementedError()

class FilteredLoansListMenu(FindLoanMenu):
    def __init__(self, repo: ILoanRepository, geoprovider: IGeocodingProvider) -> None:
        super().__init__(self._do_search)
        self._repo = repo
        self._geoprovider = geoprovider

    def _do_search(self: Self, host: MenuHostBase, predicate: LoanSearchPredicate):
        host.push(StaticMenu("Выберите действие:", [
            SubmenuEntry("Просмотреть отчёт.", 
                lambda: PaginationMenu(self._repo.get_unreturned_loans(predicate), text_generator=loan_to_text)
            ),
            StaticMenuEntry("Сохранить в GeoJSON", lambda host: self._save_to_geojson(host, predicate)),
            MenuEntryBack()
        ]))

    def _save_to_geojson(self: Self, host: MenuHostBase, predicate: LoanSearchPredicate):
        filename = host.input(
            "Введите название файла для сохранения отчёта (или нажмите Ctrl + C для отмены):",
            converter_string,
            validator_string_not_empty,
            "Название файла должно быть не пустой строкой"
        )
        if filename is None:
            return
        
        dataset = self._repo.get_unreturned_loans(predicate)
        chunkSize = 100

        #Т.к. размер данных в БД неизвестен, будем стримить генерируемый geojson прямо в файл, поэтому без отдельной библиотеки
        with open(f'{filename}.json', "w", encoding="utf-8") as report:
            first = True
            print('{"type": "FeatureCollection","features": [', file=report, end='')
            chunkCount =  math.ceil(len(dataset) / chunkSize)
            for chunkIndex in range(chunkCount):
                for loan in dataset[chunkIndex*chunkSize:(chunkIndex+1)*chunkSize]:
                    coords = self._geoprovider.address_to_coordinates(loan[2].Address)

                    if coords is None:
                        continue

                    if first:
                        first = False
                    else:
                        print(',', file=report,end='')

                    print(
                        '{'
                            '"type": "Feature",'
                            '"geometry":'
                            '{'
                                '"type": "Point",'
                                f'"coordinates": [{coords[0]},{coords[1]}]'
                            '},'
                            '"properties":'
                            '{'
                                f'"book": "{book_to_text(loan[1])}",'
                                f'"client": "{client_to_text(loan[2])}"'
                            '}'
                        '}',
                        file=report,
                        end=''
                    )
            print(']}', file=report, end='')