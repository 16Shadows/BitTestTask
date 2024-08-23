from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import MenuEntryBack, StaticMenuEntry
from modules.menu.input import validator_always, converter_string, validator_string_not_empty, converter_int

from collections.abc import Sequence

from components.books.book import Book
from components.books.repository import IBookRepository

from typing import Self
from datetime import date

class AddBookMenu(MenuBase):
    """
        Меню добавления новой книги.
    """
    def __init__(self, repo : IBookRepository) -> None:
        self._regDate : date = date.today()
        self._Name : str | None = None
        self._Author : str | None = None
        self._Genre : str | None = None
        self._ReleaseYear : int | None = None
        self._repo = repo

    @MenuBase.text.getter
    def text(self: Self) -> str:
        return (
            "Добавление книги:\n"
            f"Название: {(self._Name if self._Name is not None else "не выбрано")}.\n"
            f"Автор: {(self._Author if self._Author is not None else "не выбран")}.\n"
            f"Жанр: {(self._Genre if self._Genre is not None else "не выбран")}.\n"
            f"Год выпуска: {(self._ReleaseYear if self._ReleaseYear is not None else "не выбран")}.\n"
            f"Дата добавления в библиотеку (ГГГГ-ММ-ДД): {self._regDate.isoformat()}"
        )
    
    @MenuBase.entries.getter
    def entries(self: Self) -> Sequence[MenuEntryBase]:
        res : list[MenuEntryBase] = [
            StaticMenuEntry("Изменить название", self._set_name),
            StaticMenuEntry("Изменить автора", self._set_author),
            StaticMenuEntry("Изменить жанр", self._set_genre),
            StaticMenuEntry("Изменить год публикации", self._set_release_year),
            StaticMenuEntry("Изменить дату добавления", self._set_reg_date)
        ]

        if self._Name is not None and self._Author is not None and self._Genre is not None and self._ReleaseYear is not None:
            res.append(StaticMenuEntry("Добавить", self._add_new))

        res.append(MenuEntryBack())

        return res
    
    def _set_reg_date(self: Self, host: MenuHostBase):
        when = host.input("Введите дату в формате 'ГГГГ-ММ-ДД' (или используйте Ctrl + C, чтобы отменить ввод): ",
                      date.fromisoformat,
                      validator_always,
                      "Дата должна быть в корректном формате!")
        if when is None:
            return
        self._regDate = when

    def _set_name(self: Self, host: MenuHostBase):
        name = host.input("Введите название (или используйте Ctrl + C, чтобы отменить ввод): ",
                      converter_string,
                      validator_string_not_empty,
                      "Название должно быть не пустым!")
        if name is None:
            return
        self._Name = name

    def _set_author(self: Self, host: MenuHostBase):
        author = host.input("Введите имя автора (или используйте Ctrl + C, чтобы отменить ввод): ",
                      converter_string,
                      validator_string_not_empty,
                      "Имя автора должно быть не пустым!")
        if author is None:
            return
        self._Author = author

    def _set_genre(self: Self, host: MenuHostBase):
        genre = host.input("Введите жанр (или используйте Ctrl + C, чтобы отменить ввод): ",
                      converter_string,
                      validator_string_not_empty,
                      "Жанр должен быть не пустым!")
        if genre is None:
            return
        self._Genre = genre

    def _set_release_year(self: Self, host: MenuHostBase):
        year = host.input("Введите год публикации (или используйте Ctrl + C, чтобы отменить ввод): ",
                      converter_int,
                      validator_always,
                      "Год публикации должен быть не пустым!")
        if year is None:
            return
        self._ReleaseYear = year

    def _add_new(self: Self, host: MenuHostBase):
        book = Book(
            self._Name, #type: ignore
            self._ReleaseYear, #type: ignore
            self._Author, #type: ignore
            self._Genre, #type: ignore
            self._regDate
        )
        self._repo.add_book(book)
        host.pop()