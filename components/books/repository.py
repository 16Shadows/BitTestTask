from __future__ import annotations

from typing import Self, Protocol, Sequence
from datetime import date
from .book import Book
from dataclasses import dataclass

class IBookRepository(Protocol):
    """Протокол для репозитория книг"""

    def get_unloaned_books_at(self: Self, date: date, predicate: BookSearchPredicate | None = None) -> Sequence[Book]:
        """
            Вычислить число свободных книг на указанную дату.
            
            date: date -- дата, для которой нужно подсчитать число свободных книг
        """
        raise NotImplementedError()

    def get_genre_scores(self: Self) -> Sequence[tuple[str, int]]:
        """
            Вычислить количество взятий книг каждого жанра (популярность жанра).
            Возвращает словарь с парами жанр-количество взятий.
        """
        raise NotImplementedError()
    
    def get_books(self: Self, predicate: BookSearchPredicate | None = None) -> Sequence[Book]:
        """
            Список книг, удовлетворяющих заданному предикату (или всех, если предикат не указан)
        """
        raise NotImplementedError()
    
    def add_book(self: Self, book: Book) -> None:
        """
            Добавить новую книгу.
            
            book: Book -- книга.

            Если книга с таким ID уже существует, будет поднята ошибка.
        """
        raise NotImplementedError()
    
    def update_book(self: Self, book: Book) -> None:
        """
            Обновить существующую книгу.
            
            book: Book - книга.

            Если книги с таким ID не существует или возникает конфликт между датой добавления книги и датами её взятия, будет поднята ошибка.
        """
        raise NotImplementedError()

@dataclass
class BookSearchPredicate:
    NameContains : str | None = None
    """
        Название книги должно содержать эту подстроку.
    """
    AuthorContains : str | None = None
    """
        Автор книги должен содержать эту подстроку.
    """
    GenreContains : str | None = None
    """
        Жанр книги должен содержать эту подстроку.
    """
    PublicationYearMin : int | None = None
    """
        Год публикации книги должен быть не меньше этого значения.
    """
    PublicationYearMax : int | None = None
    """
        Год публикации книги должен быть не больше этого значения.
    """