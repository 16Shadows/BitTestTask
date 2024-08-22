import sqlite3
from typing import Self, Any
from collections.abc import Sequence

from modules.view import CachingView
from modules.events import Event, WeakSubscriber

from datetime import date

from .loan import Loan
from ..books.book import Book
from ..clients.client import Client
from .repository import LoanSearchPredicate

class LoanRepositorySqlite3:
    """Репозиторий взятий книг на SQLite3"""
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._reset_cache_event = Event[()]()
    
    def add_loan(self: Self, loan: Loan) -> None:
        """
            Добавить новое взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID уже существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        try:
            if loan.ID is None:
                self._connection.execute(
                    "INSERT INTO Loan (StartDate, EndDate, ReturnDate, BookID, ClientID) "
                    "VALUES (:startDate, :endDate, :returnDate, :bookID, :clientID); ",
                    {
                        "startDate": loan.StartDate,
                        "returnDate": loan.ReturnDate,
                        "endDate": loan.EndDate,
                        "bookID": loan.BookID,
                        "clientID": loan.ClientID
                    }
                )
                cur = self._connection.execute(
                    "SELECT last_insert_rowid();"
                )
                cur.row_factory = None
                loan.ID = cur.fetchone()[0]
            else:
                self._connection.execute(
                    "INSERT INTO Loan (ID, StartDate, EndDate, ReturnDate, BookID, ClientID) "
                    "VALUES (:id, :startDate, :endDate, :returnDate, :bookID, :clientID); ",
                    {
                        "id": loan.ID,
                        "startDate": loan.StartDate,
                        "returnDate": loan.ReturnDate,
                        "endDate": loan.EndDate,
                        "bookID": loan.BookID,
                        "clientID": loan.ClientID
                    }
                )
        except:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()
            self._reset_cache_event()

    def update_loan(self: Self, loan: Loan) -> None:
        """
            Обновить существующее взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID не существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        if loan.ID is None:
            raise ValueError("The loan's ID is not set.")
        
        try:
            self._connection.execute(
                "UPDATE Loan SET "
                "StartDate=:startDate,EndDate=:endDate,ReturnDate=:returnDate,BookID=:bookID,ClientID=:clientID "
                "WHERE ID=:id;",
                {
                    "id": loan.ID,
                    "startDate": loan.StartDate,
                    "returnDate": loan.ReturnDate,
                    "endDate": loan.EndDate,
                    "bookID": loan.BookID,
                    "clientID": loan.ClientID
                }
            )
        except:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()
            self._reset_cache_event()

    def get_unreturned_loans(self: Self, predicate: LoanSearchPredicate | None = None) -> Sequence[tuple[Loan, Book, Client]]:
        """
            Вывести список всех невозвращённых книг (взятий книг), удовлетворяющих предикату
        """
        view = UnreturnedLoansView(self._connection, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
    def get_expired_loans_at(self: Self, at: date, predicate: LoanSearchPredicate | None = None) -> Sequence[tuple[Loan, Book, Client, int]]:
        """
            Получить список всех просроченных на указанную дату взятий книг, удовлетворяющих предикату.
            Аргументы:
                at : date -- дата, для которой формируется список.
                             Книги, которые были просроченны позже этой даты, не будут отображены.
                             Число дней, на которое книги были просрочены, будет отсчитываться до этой даты.
                predicate: LoanSearchPredicate -- предикат для фильтрации взятых книг.
        """
        view = ExpiredLoansView(self._connection, at, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view

def generate_predicate_query(predicate: LoanSearchPredicate) -> tuple[str, dict[str, Any]] | None:
    predicates : list[str] = []
    params : dict[str, Any] = {}

    if predicate.AuthorContains is not None:
        predicates.append("Book.Author LIKE :author")
        params['author'] = f"%{predicate.AuthorContains}%"

    if predicate.BookNameContains is not None:
        predicates.append("Book.Name LIKE :bookName")
        params['bookName'] = f"%{predicate.BookNameContains}%"

    if predicate.GenreContains is not None:
        predicates.append("Book.Genre LIKE :genre")
        params['genre'] = f"%{predicate.GenreContains}%"

    if predicate.ClientNameContains is not None:
        predicates.append("Client.Name LIKE :clientName")
        params['clientName'] = f"%{predicate.ClientNameContains}%"

    if predicate.PublicationYearMin is not None:
        predicates.append("Book.PublicationYear >= :yearmin")
        params['yearmin'] = predicate.PublicationYearMin

    if predicate.PublicationYearMax is not None:
        predicates.append("Book.PublicationYear <= :yearmax")
        params['yearmax'] = predicate.PublicationYearMax

    if predicate.StartDateMin is not None:
        predicates.append("Loan.StartDateMin >= :startDateMin")
        params['startDateMin'] = predicate.StartDateMin.isoformat()

    if predicate.StartDateMax is not None:
        predicates.append("Loan.StartDateMax <= :startDateMax")
        params['startDateMax'] = predicate.StartDateMax.isoformat()

    if len(predicates) < 1:
        return None
    
    return (" AND ".join(predicates), params)

class UnreturnedLoansView(CachingView[tuple[Loan, Book, Client]]):
    def __init__(self, connection: sqlite3.Connection, predicate: LoanSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[tuple[Loan, Book, Client]]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.ClientName, t.RegistrationDate,  "
                "t.BookName, t.Author, t.Genre, t.PublicationYear, t.AddedAtDate, "
                "t.StartDate, t.EndDate, t.BookID, t.ClientID "
                "FROM (SELECT *, Client.Name as ClientName, Book.Name as BookName, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                "WHERE Loan.ReturnDate IS NULL "
                "ORDER BY Book.Name "
                "LIMIT :start,:precount;) as t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.Name as ClientName, Client.RegistrationDate,  "
                "Book.Name as BookName, Book.Author, Book.Genre, Book.PublicationYear, Book.AddedAtDate, "
                "Loan.ID, Loan.StartDate, Loan.EndDate, Loan.BookID, Loan.ClientID "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                "WHERE Loan.ReturnDate IS NULL "
                "ORDER BY Book.Name "
                "LIMIT :start,:count;"
            )
        else:
            query = (
                "SELECT t.ID, t.ClientName, t.RegistrationDate,  "
                "t.BookName, t.Author, t.Genre, t.PublicationYear, t.AddedAtDate, "
                "t.StartDate, t.EndDate, t.BookID, t.ClientID "
                "FROM (SELECT *, Client.Name as ClientName, Book.Name as BookName, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                f"WHERE Loan.ReturnDate IS NULL AND ({self._predicate}) "
                "ORDER BY Book.Name "
                "LIMIT :start,:precount;) as t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.Name as ClientName, Client.RegistrationDate,  "
                "Book.Name as BookName, Book.Author, Book.Genre, Book.PublicationYear, Book.AddedAtDate, "
                "Loan.ID, Loan.StartDate, Loan.EndDate, Loan.BookID, Loan.ClientID "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                f"WHERE Loan.ReturnDate IS NULL AND ({self._predicate}) "
                "ORDER BY Book.Name "
                "LIMIT :start,:count;"
            )

        self._params["start"] = start
        self._params["precount"] = count*stride - 1
        self._params["count"] = count
        self._params["stride"] = stride

        cur = self._connection.execute(
            query,
            self._params
        )
        cur.row_factory = sqlite3.Row #type: ignore
        return [
            (
                Loan(date.fromisoformat(row["StartDate"]), date.fromisoformat(row["EndDate"]), row["ClientID"], row["BookID"], row["ID"]),
                Book(row["BookName"], row["PublicationYear"], row["Author"], row["Genre"], date.fromisoformat(row["AddedAtDate"]), row["BookID"]),
                Client(row['ClientName'], date.fromisoformat(row['RegistrationDate']), row['ClientID'])
            )
            for row in cur.fetchall()
        ]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Loan WHERE Loan.ReturnDate IS NULL;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID WHERE Loan.ReturnDate IS NULL AND ({self._predicate});",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
class ExpiredLoansView(CachingView[tuple[Loan, Book, Client, int]]):
    def __init__(self, connection: sqlite3.Connection, at: date, predicate: LoanSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})
        self._params["at"] = at.isoformat()

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Loan WHERE (Loan.ReturnDate IS NULL OR Loan.ReturnDate > Loan.EndDate) AND Loan.EndDate < :at;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID WHERE (Loan.ReturnDate IS NULL OR Loan.ReturnDate > Loan.EndDate) AND Loan.EndDate < :at AND ({self._predicate});",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[tuple[Loan, Book, Client, int]]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.ClientName, t.RegistrationDate,  "
                "t.BookName, t.Author, t.Genre, t.PublicationYear, t.AddedAtDate, "
                "t.StartDate, t.EndDate, t.BookID, t.ClientID, t.ExpiredUntil, t.ReturnDate "
                "FROM (SELECT Client.Name as ClientName, Client.RegistrationDate,  "
                "Book.Name as BookName, Book.Author, Book.Genre, Book.PublicationYear, Book.AddedAtDate, "
                "Loan.ID, Loan.StartDate, Loan.EndDate, Loan.BookID, Loan.ClientID, Loan.ReturnDate, "
                "(CASE WHEN Loan.ReturnDate IS NULL OR Loan.ReturnDate > :at THEN :at "
	            "ELSE Loan.ReturnDate END) AS ExpiredUntil, "
                "ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                "WHERE (Loan.ReturnDate IS NULL OR Loan.ReturnDate > Loan.EndDate) AND Loan.EndDate < :at "
                "ORDER BY Book.Name "
                "LIMIT :start,:precount;) as t"
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.Name as ClientName, Client.RegistrationDate,  "
                "Book.Name as BookName, Book.Author, Book.Genre, Book.PublicationYear, Book.AddedAtDate, "
                "Loan.ID, Loan.StartDate, Loan.EndDate, Loan.BookID, Loan.ClientID, Loan.ReturnDate, "
                "(CASE WHEN Loan.ReturnDate IS NULL OR Loan.ReturnDate > :at THEN :at "
	            "ELSE Loan.ReturnDate END) AS ExpiredUntil "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                "WHERE (Loan.ReturnDate IS NULL OR Loan.ReturnDate > Loan.EndDate) AND Loan.EndDate < :at "
                "ORDER BY Book.Name "
                "LIMIT :start,:count;"
            )
        else:
            query = (
                "SELECT t.ID, t.ClientName, t.RegistrationDate,  "
                "t.BookName, t.Author, t.Genre, t.PublicationYear, t.AddedAtDate, "
                "t.StartDate, t.EndDate, t.BookID, t.ClientID, t.ExpiredUntil, t.ReturnDate "
                "FROM (SELECT Client.Name as ClientName, Client.RegistrationDate,  "
                "Book.Name as BookName, Book.Author, Book.Genre, Book.PublicationYear, Book.AddedAtDate, "
                "Loan.ID, Loan.StartDate, Loan.EndDate, Loan.BookID, Loan.ClientID, Loan.ReturnDate, "
                "(CASE WHEN Loan.ReturnDate IS NULL OR Loan.ReturnDate > :at THEN :at "
	            "ELSE Loan.ReturnDate END) AS ExpiredUntil, "
                "ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                "WHERE (Loan.ReturnDate IS NULL OR Loan.ReturnDate > Loan.EndDate) AND Loan.EndDate < :at "
                f"AND {self._predicate} "
                "ORDER BY Book.Name "
                "LIMIT :start,:precount;) as t"
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.Name as ClientName, Client.RegistrationDate,  "
                "Book.Name as BookName, Book.Author, Book.Genre, Book.PublicationYear, Book.AddedAtDate, "
                "Loan.ID, Loan.StartDate, Loan.EndDate, Loan.BookID, Loan.ClientID, Loan.ReturnDate, "
                "(CASE WHEN Loan.ReturnDate IS NULL OR Loan.ReturnDate > :at THEN :at "
	            "ELSE Loan.ReturnDate END) AS ExpiredUntil "
                "FROM Loan INNER JOIN Book ON Loan.BookID = Book.ID INNER JOIN Client ON Loan.ClientID = Client.ID "
                "WHERE (Loan.ReturnDate IS NULL OR Loan.ReturnDate > Loan.EndDate) AND Loan.EndDate < :at "
                f"AND {self._predicate} "
                "ORDER BY Book.Name "
                "LIMIT :start,:count;"
            )

        self._params["start"] = start
        self._params["precount"] = count*stride - 1
        self._params["count"] = count
        self._params["stride"] = stride

        cur = self._connection.execute(
            query,
            self._params
        )
        cur.row_factory = sqlite3.Row #type: ignore
        return [
            (
                Loan(date.fromisoformat(row["StartDate"]), date.fromisoformat(row["EndDate"]), row["ClientID"], row["BookID"], row["ID"], date.fromisoformat(row["ReturnDate"]) if row["ReturnDate"] is not None else None),
                Book(row["BookName"], row["PublicationYear"], row["Author"], row["Genre"], date.fromisoformat(row["AddedAtDate"]), row["BookID"]),
                Client(row['ClientName'], date.fromisoformat(row['RegistrationDate']), row['ClientID']),
                (date.fromisoformat(row["ExpiredUntil"]) - date.fromisoformat(row["EndDate"])).days
            )
            for row in cur.fetchall()
        ]