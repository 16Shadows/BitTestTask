import sqlite3
from typing import Self, Sequence
from datetime import date
from .book import Book

class BookRepositorySqlite3:
    """
        Репозиторий книг, реализованный для SQLite
    """
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def count_unloaned_books_at(self: Self, date: date) -> int:
        """
            Вычислить число свободных книг на указанную дату.
            
            date: date -- дата, для которой нужно подсчитать число свободных книг
        """
        return self._connection.execute(
            "SELECT (t.total - u.in_use) as cnt FROM "
            "(SELECT COUNT(*) as total FROM Book WHERE Book.AddedAtDate <= :date) as t, "
            "(SELECT COUNT(*) AS in_use FROM Loan "
            "WHERE Loan.StartDate <= :date AND (Loan.ReturnDate IS NULL OR Loan.ReturnDate >= :date)) as u;",
            { "date": date.isoformat() }
        ).fetchone()[0]

    def get_genre_scores(self: Self) -> Sequence[tuple[str, int]]:
        """
            Вычислить количество взятий книг каждого жанра (популярность жанра).
            Возвращает последовательность с парами жанр-количество взятий.
        """
        cur = self._connection.execute(
            "SELECT Book.Genre, COUNT(Loan.ID) AS Cnt FROM "
            "Book LEFT JOIN Loan ON Book.ID = Loan.BookID "
            "GROUP BY Book.Genre "
            "ORDER BY Cnt DESC;"
        )
        return cur.fetchall()
    
    def get_books(self: Self) -> Sequence[Book]:
        """
            Все книги в библиотеке
        """
        #TODO: все книги загружать в память неэффективно, т.к. БД может вырасти.
        #Можно добавить некоторую форму пагинации или коллекцию, реализующую запрос части записей из БД по срезу.
        cur = self._connection.execute("SELECT * FROM Book")
        headers = [i[0] for i in cur.description]
        res : list[Book] = []
        for row in cur.fetchall():
            columns = dict(zip(headers, row))
            columns['AddedAtDate'] = date.fromisoformat(columns['AddedAtDate'])
            res.append(Book(**columns))
        return res