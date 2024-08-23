from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.static import MenuEntryBack, StaticMenuEntry
from modules.menu.input import validator_always, converter_string, validator_string_not_empty, converter_int

from collections.abc import Sequence

from components.books.book import Book
from components.books.repository import IBookRepository

from typing import Self
from datetime import date

class BookMenu(MenuBase):
    def __init__(self, book: Book, repo : IBookRepository) -> None:
        self._regDate = book.AddedAtDate
        self._book = book
        self._Name = book.Name
        self._Author = book.Author 
        self._Genre = book.Genre
        self._ReleaseYear = book.PublicationYear
        self._repo = repo

    @MenuBase.text.getter
    def text(self: Self) -> str:
        return (
            f"Название: {self._Name}.\n"
            f"Автор: {self._Author}.\n"
            f"Жанр: {self._Genre}.\n"
            f"Год выпуска: {self._ReleaseYear}.\n"
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

        if (self._Name != self._book.Name or
                self._Author != self._book.Author or
                self._Genre != self._book.Genre or
                self._ReleaseYear != self._book.PublicationYear or
                self._regDate != self._book.AddedAtDate):
            res.append(StaticMenuEntry("Сохранить", self._save))

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

    def _save(self: Self, host: MenuHostBase):
        orig_name = self._book.Name
        orig_author = self._book.Author
        orig_genre = self._book.Genre
        orig_year = self._book.PublicationYear
        orig_regDate = self._book.AddedAtDate
        try:
            self._book.Name = self._Name
            self._book.Author = self._Author
            self._book.Genre = self._Genre
            self._book.PublicationYear = self._ReleaseYear
            self._book.AddedAtDate = self._regDate
            self._repo.update_book(self._book)
            host.pop()
        except Exception as e:
            self._book.Name = orig_name
            self._book.Author = orig_author
            self._book.Genre = orig_genre
            self._book.PublicationYear = orig_year
            self._book.AddedAtDate = orig_regDate
            host.message(f'Не удалось сохранить книгу. Текст ошибки:\n{e}')