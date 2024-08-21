from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import StaticMenuEntry, MenuEntryBack
from modules.menu.input import validator_string_not_empty, converter_int, converter_string, validator_int_range
from typing import Self, Callable
from collections.abc import Sequence
from copy import deepcopy

from components.books.repository import BookSearchPredicate

class FindBookMenu(MenuBase):
    def __init__(self, on_search: Callable[[MenuHostBase, BookSearchPredicate], None]) -> None:
        self._predicate = BookSearchPredicate()
        self._on_search = on_search

    @MenuBase.text.getter
    def text(self: Self) -> str:
        res = "Поиск книги"
        
        if self._predicate.AuthorContains is not None:
            res += "\nАвтор содержит: " + self._predicate.AuthorContains

        if self._predicate.NameContains is not None:
            res += "\nНазвание содержит: " + self._predicate.NameContains

        if self._predicate.GenreContains is not None:
            res += "\nЖанр содержит: " + self._predicate.GenreContains

        if self._predicate.PublicationYearMin is not None:
            res += "\nОпубликована не раньше: " + str(self._predicate.PublicationYearMin)

        if self._predicate.PublicationYearMax is not None:
            res += "\nОпубликована не позже: " + str(self._predicate.PublicationYearMax)

        return res
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res : list[MenuEntryBase] = []
        
        res.append(StaticMenuEntry("Изменить поиск по автору", self._set_author_filter))

        if self._predicate.AuthorContains is not None:
            res.append(StaticMenuEntry("Очистить поиск по автору", self._clear_author_filter))

        res.append(StaticMenuEntry("Изменить поиск по названию", self._set_name_filter))

        if self._predicate.NameContains is not None:
            res.append(StaticMenuEntry("Очистить поиск по названию", self._clear_name_filter))

        res.append(StaticMenuEntry("Изменить поиск по жанру", self._set_genre_filter))

        if self._predicate.GenreContains is not None:
            res.append(StaticMenuEntry("Очистить поиск по жанру", self._clear_genre_filter))

        res.append(StaticMenuEntry("Изменить поиск по минимальному году публикации", self._set_min_year_filter))

        if self._predicate.PublicationYearMin is not None:
            res.append(StaticMenuEntry("Очистить поиск по минимальному году публикации", self._clear_min_year_filter))

        res.append(StaticMenuEntry("Изменить поиск по максимальному году публикации", self._set_max_year_filter))

        if self._predicate.PublicationYearMax is not None:
            res.append(StaticMenuEntry("Очистить поиск по максимальному году публикации", self._clear_max_year_filter))

        res.append(StaticMenuEntry("Найти", lambda host: self._on_search(host, deepcopy(self._predicate))))

        res.append(MenuEntryBack())

        return res

    def _set_author_filter(self: Self, host: MenuHostBase):
        value = host.input("Введите частичного или полного автора (или нажмите Ctrl + C, чтобы отменить ввод): ",
                            converter_string,
                            validator_string_not_empty,
                            "Автор должен быть не пустым!"
        )
        if value is None:
            return
        self._predicate.AuthorContains = value

    def _clear_author_filter(self: Self, host: MenuHostBase):
        self._predicate.AuthorContains = None

    def _set_name_filter(self: Self, host : MenuHostBase):
        value = host.input("Введите частичное или полное название книги (или нажмите Ctrl + C, чтобы отменить ввод): ",
                            converter_string,
                            validator_string_not_empty,
                            "Название должено быть не пустым!"
        )
        if value is None:
            return
        self._predicate.NameContains = value

    def _clear_name_filter(self: Self, host: MenuHostBase):
        self._predicate.NameContains = None

    def _set_genre_filter(self: Self, host : MenuHostBase):
        value = host.input("Введите частичный или полный жанр книги (или нажмите Ctrl + C, чтобы отменить ввод): ",
                            converter_string,
                            validator_string_not_empty,
                            "Жанр должен быть не пустым!"
        )
        if value is None:
            return
        self._predicate.GenreContains = value

    def _clear_genre_filter(self: Self, host: MenuHostBase):
        self._predicate.GenreContains = None

    def _set_min_year_filter(self: Self, host : MenuHostBase):
        value = host.input("Введите минимальный год публикации (или нажмите Ctrl + C, чтобы отменить ввод): ",
                            converter_int,
                            lambda x: validator_int_range(x, max=self._predicate.PublicationYearMax),
                            "Год должен быть корректным целым числом не больше максимального года публикации!"
        )
        if value is None:
            return
        self._predicate.PublicationYearMin = value

    def _clear_min_year_filter(self: Self, host: MenuHostBase):
        self._predicate.PublicationYearMin = None

    def _set_max_year_filter(self: Self, host : MenuHostBase):
        value = host.input("Введите максимальный год публикации (или нажмите Ctrl + C, чтобы отменить ввод): ",
                            converter_int,
                            lambda x: validator_int_range(x, min=self._predicate.PublicationYearMin),
                            "Год должен быть корректным целым числом не меньше минимального года публикации!"
        )
        if value is None:
            return
        self._predicate.PublicationYearMax = value

    def _clear_max_year_filter(self: Self, host: MenuHostBase):
        self._predicate.PublicationYearMax = None