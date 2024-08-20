import sqlite3
from typing import Self, Any
from collections.abc import Sequence
from datetime import date

from modules.view import CachingView
from modules.events import Event, WeakSubscriber

from .client import Client
from .repository import ClientSearchPredicate

class ClientRepositorySqlite3:
    """Репозиторий читателей на SQLite3"""
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._reset_cache_event = Event[()]()

    def get_clients(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[Client]:
        """
            Все читатели библиотеки
        """
        view = AllClientsView(self._connection, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
    def get_last_visit_dates(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[tuple[Client, date]]:
        """
            Дата последнего посещения библиотеки каждым читателем.
        """
        view = LastVisitDatesView(self._connection, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
    def get_total_loans_per_client(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[tuple[Client, int]]:
        """
            Общее количество взятых книг каждым читателем.
        """
        view = TotalLoansView(self._connection, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
    def get_total_unreturned_loans_per_client(self: Self, predicate: ClientSearchPredicate | None = None) -> Sequence[tuple[Client, int]]:
        """
            Количество невозвращённых каждым читателем книг.
        """
        view = UnreturnedLoansView(self._connection, predicate)
        self._reset_cache_event += WeakSubscriber(view.reset_cache)
        return view
    
def generate_predicate_query(predicate: ClientSearchPredicate) -> tuple[str, dict[str, Any]] | None:
    predicates : list[str] = []
    params : dict[str, Any] = {}

    if predicate.NameContains is not None:
        predicates.append("Name LIKE :name")
        params['name'] = f"%{predicate.NameContains}%"

    if len(predicates) < 1:
        return None
    
    return (" AND ".join(predicates), params)

class AllClientsView(CachingView[Client]):
    def __init__(self, connection: sqlite3.Connection, predicate: ClientSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[Client]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate FROM "
                "(SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Client ORDER BY Client.Name LIMIT :start,:precount) as t "
                "WHERE row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else ( "SELECT * FROM Client ORDER BY Client.Name LIMIT :start,:count;" )
        else:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate FROM "
                f"(SELECT *, ROW_NUMBER() OVER (ORDER BY Book.Name) as row_cnt FROM Client WHERE {self._predicate} ORDER BY Client.Name LIMIT :start,:precount) as t "
                "WHERE row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else ( f"SELECT * FROM Client WHERE {self._predicate} ORDER BY Client.Name LIMIT :start,:count;" )

        self._params["start"] = start
        self._params["precount"] = count*stride - 1
        self._params["count"] = count
        self._params["stride"] = stride

        cur = self._connection.execute(
            query,
            self._params
        )
        cur.row_factory = sqlite3.Row #type:ignore
        return [Client(**row) for row in cur.fetchall()]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Client;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Client WHERE {self._predicate};",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
class LastVisitDatesView(CachingView[tuple[Client, date]]):
    def __init__(self, connection: sqlite3.Connection, predicate: ClientSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[tuple[Client, date]]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate, t.last_visit_date FROM "
                "(SELECT Client.ID, Client.Name, Client.RegistrationDate, "
                "COALESCE(MAX(COALESCE(Loan.ReturnDate, Loan.StartDate)), Client.RegistrationDate) as last_visit_date, "
                "ROW_NUMBER() OVER (ORDER BY Client.Name) as row_cnt "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name LIMIT :start,:precount) AS t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.ID, Client.Name, Client.RegistrationDate, "
                "COALESCE(MAX(COALESCE(Loan.ReturnDate, Loan.StartDate)), Client.RegistrationDate) as last_visit_date "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name LIMIT :start,:count"
            )
        else:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate, t.last_visit_date FROM "
                "(SELECT Client.ID, Client.Name, Client.RegistrationDate, "
                "COALESCE(MAX(COALESCE(Loan.ReturnDate, Loan.StartDate)), Client.RegistrationDate) as last_visit_date, "
                "ROW_NUMBER() OVER (ORDER BY Client.Name) as row_cnt "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                f"WHERE {self._predicate} "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name LIMIT :start,:precount) AS t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.ID, Client.Name, Client.RegistrationDate, "
                "COALESCE(MAX(COALESCE(Loan.ReturnDate, Loan.StartDate)), Client.RegistrationDate) as last_visit_date "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                f"WHERE {self._predicate} "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name LIMIT :start,:count"
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
                Client(row['Name'], date.fromisoformat(row['RegistrationDate']), row['ID']),
                date.fromisoformat(row['last_visit_date'])
            )
            for row in cur.fetchall()
        ]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Client;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Client WHERE {self._predicate};",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
class TotalLoansView(CachingView[tuple[Client, int]]):
    def __init__(self, connection: sqlite3.Connection, predicate: ClientSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[tuple[Client, int]]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate, t.last_visit_date FROM "
                "(SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans, "
                "ROW_NUMBER() OVER (ORDER BY Client.Name) as row_cnt "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
                "LIMIT :start,:precount) AS t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
                "LIMIT :start,:count;"
            )
        else:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate, t.last_visit_date FROM "
                "(SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans, "
                "ROW_NUMBER() OVER (ORDER BY Client.Name) as row_cnt "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                f"WHERE {self._predicate} "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
                "LIMIT :start,:precount) AS t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                f"WHERE {self._predicate} "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
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
                Client(row['Name'], date.fromisoformat(row['RegistrationDate']), row['ID']),
                row['total_loans']
            )
            for row in cur.fetchall()
        ]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Client;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Client WHERE {self._predicate};",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]
    
class UnreturnedLoansView(CachingView[tuple[Client, int]]):
    def __init__(self, connection: sqlite3.Connection, predicate: ClientSearchPredicate | None = None):
        self._connection = connection
        
        pred = generate_predicate_query(predicate) if predicate is not None else None    
        self._predicate, self._params = pred if pred is not None else (None, {})

    def _get_slice(self: Self, start: int, count: int, stride: int) -> Sequence[tuple[Client, int]]:
        #Запрос меняется в зависимости от наличия предиката
        #Если stide равен 1, то можно упростить запрос, игнорируя row_cnt и stride
        if self._predicate is None:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate, t.last_visit_date FROM "
                "(SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans, "
                "ROW_NUMBER() OVER (ORDER BY Client.Name) as row_cnt "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                "WHERE Loan.ReturnDate IS NULL "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
                "LIMIT :start,:precount) AS t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                "WHERE Loan.ReturnDate IS NULL "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
                "LIMIT :start,:count;"
            )
        else:
            query = (
                "SELECT t.ID, t.Name, t.RegistrationDate, t.last_visit_date FROM "
                "(SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans, "
                "ROW_NUMBER() OVER (ORDER BY Client.Name) as row_cnt "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                f"WHERE Loan.ReturnDate IS NULL AND ({self._predicate}) "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
                "LIMIT :start,:precount) AS t "
                "WHERE t.row_cnt % :stride = 1 LIMIT :count;"
            ) if stride > 1 else (
                "SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans "
                "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
                f"WHERE Loan.ReturnDate IS NULL AND ({self._predicate}) "
                "GROUP BY Client.ID "
                "ORDER BY Client.Name "
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
                Client(row['Name'], date.fromisoformat(row['RegistrationDate']), row['ID']),
                row['total_loans']
            )
            for row in cur.fetchall()
        ]

    def _get_len(self: Self) -> int:
        cur = self._connection.execute(
            "SELECT COUNT(*) FROM Client;" if self._predicate is None
            else f"SELECT COUNT(*) FROM Client WHERE {self._predicate};",
            self._params
        )
        cur.row_factory = None
        return cur.fetchone()[0]