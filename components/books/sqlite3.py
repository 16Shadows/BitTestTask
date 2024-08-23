import sqlite3
from typing import Self, Sequence, Any
from datetime import date
from .book import Book
from .repository import BookSearchPredicate
from modules.view import CachingView
from modules.events import Event, WeakSubscriber

class BookRepositorySqlite3:
    """
        Репозиторий книг, реализованный для SQLite
    """
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._reset_cache_event = Event[()]()
    
    def get_unloaned_books_at(self: Self, date: date, predicate: BookSearchPredicate | None = None) -> Sequence[Book]:
        view = UnloanedBooksView(self._connection, date, predicate)
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
    
    def get_books(self: Self, predicate: BookSearchPredicate | None = None) -> Sequence[Book]:
        """
            Список книг, удовлетворяющих заданному предикату (или всех, если предикат не указан)
        """
        view = AllBooksView(self._connection, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
    def add_book(self: Self, book: Book) -> None:
        """
            Добавить новую книгу.
            
            book: Book -- книга.

            Если книга с таким ID уже существует, будет поднята ошибка.
        """
        try:
            if book.ID is None:
                cur = self._connection.execute(
                    "INSERT INTO Book (Name, Author, Genre, PublicationYear, AddedAtDate) "
                    "VALUES (:name, :author, :genre, :year, :regDate) "
                    "RETURNING ID; ",
                    {
                        "name": book.Name,
                        "author": book.Author,
                        "genre": book.Genre,
                        "year": book.PublicationYear,
                        "regDate": book.AddedAtDate
                    }
                )
                cur.row_factory = None
                book.ID = cur.fetchone()[0]
            else:
                self._connection.execute(
                    "INSERT INTO Book (ID, Name, Author, Genre, PublicationYear, AddedAtDate) "
                    "VALUES (:id, :name, :author, :genre, :year, :regDate);",
                    {
                        "id": book.ID,
                        "name": book.Name,
                        "author": book.Author,
                        "genre": book.Genre,
                        "year": book.PublicationYear,
                        "regDate": book.AddedAtDate
                    }
                )
        except:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()
            self._reset_cache_event()

    def update_book(self: Self, book: Book) -> None:
        """
            Обновить существующую книгу.
            
            book: Book - книга.

            Если книги с таким ID не существует или возникает конфликт между датой добавления книги и датами её взятия, будет поднята ошибка.
        """
        if book.ID is None:
            raise ValueError("The books's ID is not set.")
        
        try:
            self._connection.execute(
                "UPDATE Book SET "
                "Name=:name,Author=:author,Genre=:genre,PublicationYear=:year,AddedAtDate=:regDate "
                "WHERE ID=:id;",
                {
                        "id": book.ID,
                        "name": book.Name,
                        "author": book.Author,
                        "genre": book.Genre,
                        "year": book.PublicationYear,
                        "regDate": book.AddedAtDate
                    }
            )
        except:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()
            self._reset_cache_event()

    def delete_book(self: Self, book: Book) -> None:
        """
            Удалить существующую книгу.
            
            book: Book - книга.

            Если книга с таким ID не существует, будет поднята ошибка.
        """
        if book.ID is None:
            raise ValueError("The book's ID is not set.")
        
        try:
            self._connection.execute(
                "DELETE FROM Book WHERE ID=:id;",
                {
                    "id": book.ID
                }
            )
        except:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()
            self._reset_cache_event()

def generate_predicate_query(predicate: BookSearchPredicate) -> tuple[str, dict[str, Any]] | None:
    predicates : list[str] = []
    params : dict[str, Any] = {}

    if predicate.AuthorContains is not None:
        predicates.append("Author LIKE :author")
        params['author'] = f"%{predicate.AuthorContains}%"

    if predicate.NameContains is not None:
        predicates.append("Name LIKE :name")
        params['name'] = f"%{predicate.NameContains}%"

    if predicate.GenreContains is not None:
        predicates.append("Genre LIKE :genre")
        params['genre'] = f"%{predicate.GenreContains}%"

    if predicate.PublicationYearMin is not None:
        predicates.append("PublicationYear >= :yearmin")
        params['yearmin'] = predicate.PublicationYearMin

    if predicate.PublicationYearMax is not None:
        predicates.append("PublicationYear <= :yearmax")
        params['yearmax'] = predicate.PublicationYearMax

    if len(predicates) < 1:
        return None
    
    return (" AND ".join(predicates), params)


class UnloanedBooksView(CachingView[Book]):
    def __init__(self, connection: sqlite3.Connection, date: date, predicate: BookSearchPredicate | None = None):
        self._connection = connection

        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})
        self._params["date"] = date.isoformat()

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[Book]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride

        if self._predicate is None:
            query = (
                "SELECT t.ID, t.Name, t.PublicationYear, t.AddedAtDate, t.Author, t.Genre "
                "FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Book WHERE Book.ID IN "
                "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date EXCEPT "
                "SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
                "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "
                "ORDER BY Book.Name LIMIT :start,:precount) as t WHERE row_cnt % :stride = 1 LIMIT :count"
            ) if stride > 1 else (
                "SELECT * FROM Book WHERE Book.ID IN "
                "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date EXCEPT "
                "SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
                "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "
                "ORDER BY Book.Name LIMIT :start,:count"
            )
        else:
            query = (
                "SELECT t.ID, t.Name, t.PublicationYear, t.AddedAtDate, t.Author, t.Genre "
                "FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Book WHERE Book.ID IN "
                "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date "
                f"AND ({self._predicate}) "
                "EXCEPT SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
                "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "
                "ORDER BY Book.Name LIMIT :start,:precount) as t WHERE row_cnt % :stride = 1 LIMIT :count"
            ) if stride > 1 else (
                "SELECT * FROM Book WHERE Book.ID IN "
                "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date "
                f"AND ({self._predicate}) "
                "EXCEPT SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
                "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "
                "ORDER BY Book.Name LIMIT :start,:count"
            )

        self._params["start"] = start
        self._params["precount"] = count*stride - 1
        self._params["count"] = count
        self._params["stride"] = stride

        cur = self._connection.execute(
            query,
            self._params
        )
        cur.row_factory = sqlite3.Row #type:ignore
        return [
            Book(row["Name"], row["PublicationYear"], row["Author"], row["Genre"], date.fromisoformat(row["AddedAtDate"]), row["ID"])
            for row in cur.fetchall()
        ]
    
    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            ("SELECT Count(*) FROM "
            "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date EXCEPT "
            "SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
            "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) ")
            if self._predicate is None else
            ("SELECT Count(*) FROM "
            "(SELECT Book.ID FROM Book WHERE Book.AddedAtDate <= :date "
            f"AND ({self._predicate}) "
            "EXCEPT SELECT Loan.BookID FROM Loan WHERE Loan.StartDate <= :date AND "
            "CASE WHEN Loan.ReturnDate IS NULL THEN 1 ELSE Loan.ReturnDate > :date END) "),
            self._params
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
    def __init__(self, connection: sqlite3.Connection, predicate: BookSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[Book]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.Name, t.PublicationYear, t.AddedAtDate, t.Author, t.Genre FROM "
                "(SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Book ORDER BY Book.Name LIMIT :start,:precount) as t "
                "WHERE row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else ( "SELECT * FROM Book ORDER BY Book.Name LIMIT :start,:count;" )
        else:
            query = (
                "SELECT t.ID, t.Name, t.PublicationYear, t.AddedAtDate, t.Author, t.Genre FROM "
                f"(SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Book WHERE {self._predicate} ORDER BY Book.Name LIMIT :start,:precount) as t "
                "WHERE row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else ( f"SELECT * FROM Book WHERE {self._predicate} ORDER BY Book.Name LIMIT :start,:count;" )

        self._params["start"] = start
        self._params["precount"] = count*stride - 1
        self._params["count"] = count
        self._params["stride"] = stride

        cur = self._connection.execute(
            query,
            self._params
        )
        cur.row_factory = sqlite3.Row #type:ignore
        return [
            Book(row["Name"], row["PublicationYear"], row["Author"], row["Genre"], date.fromisoformat(row["AddedAtDate"]), row["ID"])
            for row in cur.fetchall()
        ]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Book;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Book WHERE {self._predicate};",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]