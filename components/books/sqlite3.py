import sqlite3
from typing import Self, Sequence
from datetime import date
from .book import Book
from modules.view import CachingView
from modules.events import Event, WeakSubscriber

class BookRepositorySqlite3:
    """
        Репозиторий книг, реализованный для SQLite
    """
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._reset_cache_event = Event[()]()
    
    def get_unloaned_books_at(self: Self, date: date) -> Sequence[Book]:
        view = UnloanedBooksView(self._connection, date)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view

    def get_genre_scores(self: Self) -> Sequence[tuple[str, int]]:
        """
            Вычислить количество взятий книг каждого жанра (популярность жанра).
            Возвращает последовательность с парами жанр-количество взятий.
        """
        view = GenreScoresView(self._connection)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
    def get_books(self: Self) -> Sequence[Book]:
        """
            Все книги в библиотеке
        """
        view = AllBooksView(self._connection)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
class UnloanedBooksView(CachingView[Book]):
    def __init__(self, connection: sqlite3.Connection, date: date):
        self._connection = connection
        self._date = date

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[Book]:
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        query = (
            "SELECT t.ID, t.Name, t.PublicationYear, t.AddedAtDate, t.Author, t.Genre "
            "FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Book WHERE Book.ID IN "
            "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date EXCEPT "
            "SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
            "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "
            "ORDER BY Book.Name LIMIT :start,:count) as t WHERE row_cnt % :stride = 1"
        ) if stride > 1 else (
            "SELECT * FROM Book WHERE Book.ID IN "
            "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date EXCEPT "
            "SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
            "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "
            "ORDER BY Book.Name LIMIT :start,:count"
        )
        cur = self._connection.execute(
            query,
            {
                "date": self._date.isoformat(),
                "start": start,
                "count": count*stride,
                "stride": stride
            }
        )
        cur.row_factory = sqlite3.Row #type:ignore
        return [Book(**row) for row in cur.fetchall()]
    
    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT Count(*) FROM "
            "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date EXCEPT "
            "SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
            "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) ",
            { "date": self._date.isoformat() }
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
class GenreScoresView(CachingView[tuple[str, int]]):
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[tuple[str, int]]:
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        query = (
            "SELECT Genre, Score FROM "
            "(SELECT Genre, Score, ROW_NUMBER() OVER (ORDER BY Score DESC, Genre ASC) as row_cnt FROM "
            "(SELECT Book.Genre, COUNT(Loan.ID) AS Score FROM "
            "Book LEFT JOIN Loan ON Book.ID = Loan.BookID "
            "GROUP BY Book.Genre "
            "ORDER BY Score DESC, Book.Genre ASC "
            "LIMIT :start,:count)) "
            "WHERE row_cnt % :stride = 1"
        ) if stride > 1 else (
            "SELECT Book.Genre, COUNT(Loan.ID) AS Score FROM "
            "Book LEFT JOIN Loan ON Book.ID = Loan.BookID "
            "GROUP BY Book.Genre "
            "ORDER BY Score DESC, Book.Genre ASC "
            "LIMIT :start,:count"
        )
        cur = self._connection.execute(
            query,
            {
                "start": start,
                "count": count*stride,
                "stride": stride
            }
        )
        cur.row_factory = sqlite3.Row #type:ignore
        return [(row['Genre'], row['Score']) for row in cur.fetchall()]
    
    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(DISTINCT Book.Genre) FROM Book;"
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
class AllBooksView(CachingView[Book]):
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[Book]:
        query = (
            "SELECT t.ID, t.Name, t.PublicationYear, t.AddedAtDate, t.Author, t.Genre FROM "
            "(SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Book ORDER BY Book.Name LIMIT :start,:count) as t "
            "WHERE row_cnt % :stride = 1;"
        ) if stride > 1 else (
            "SELECT * FROM Book ORDER BY Book.Name LIMIT :start,:count;"
        )
        cur = self._connection.execute(
            query,
            {
                "start": start,
                "count": count*stride,
                "stride": stride
            }
        )
        cur.row_factory = sqlite3.Row #type:ignore
        return [Book(**row) for row in cur.fetchall()]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Book;"
        )
        cur.row_factory = None
        return cur.fetchone()[0]