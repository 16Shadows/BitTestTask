from __future__ import annotations

from typing import Self, Protocol, Sequence
from datetime import date
from .book import Book

class IBookRepository(Protocol):
    """Протокол для репозитория книг"""

    def count_unloaned_books_at(self: Self, date: date) -> int:
        """
            Вычислить число свободных книг на указанную дату.
            
            date: date -- дата, для которой нужно подсчитать число свободных книг
        """
        raise NotImplementedError()

    def get_genre_scores(self: Self) -> dict[str, int]:
        """
            Вычислить количество взятий книг каждого жанра (популярность жанра).
            Возвращает словарь с парами жанр-количество взятий.
        """
        raise NotImplementedError()
    
    def get_books(self: Self) -> Sequence[Book]:
        """
            Все книги в библиотеке
        """
        raise NotImplementedError()