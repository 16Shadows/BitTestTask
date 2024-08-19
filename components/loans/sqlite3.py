import sqlite3
from typing import Self, Sequence
from .loan import Loan

class LoanRepositorySqlite3:
    """Репозиторий взятий книг на SQLite3"""
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def get_loans(self: Self) -> Sequence[Loan]:
        """
            Все взятия книг.
        """
        #TODO: все взятия загружать в память неэффективно, т.к. БД может вырасти.
        #Можно добавить некоторую форму пагинации или коллекцию, реализующую запрос части записей из БД по срезу.
        cur = self._connection.execute("SELECT * FROM Loan")
        cur.row_factory = sqlite3.Row #type: ignore
        return [Loan(**row) for row in cur.fetchall()]
    
    def add_loan(self: Self, loan: Loan) -> None:
        """
            Добавить новое взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID уже существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        if loan.ID is None:
            cur = self._connection.execute(
                "BEGIN TRANSACTION; "
                "INSERT INTO Loan (StartDate, ReturnDate, BookID, ClientID) "
                "VALUES (:startDate, :returnDate, :bookID, :clientID); "
                "SELECT last_row_id(); "
                "END TRANSACTION;",
                {
                    "startDate": loan.StartDate,
                    "returnDate": loan.ReturnDate,
                    "bookID": loan.BookID,
                    "clientID": loan.ClientID
                }
            )
            cur.row_factory = None
            loan.ID = cur.fetchone()[0]
        else:
            self._connection.execute(
                "INSERT INTO Loan (ID, StartDate, ReturnDate, BookID, ClientID) "
                "VALUES (:id, :startDate, :returnDate, :bookID, :clientID); ",
                {
                    "id": loan.ID,
                    "startDate": loan.StartDate,
                    "returnDate": loan.ReturnDate,
                    "bookID": loan.BookID,
                    "clientID": loan.ClientID
                }
            )

    def update_loan(self: Self, loan: Loan) -> None:
        """
            Обновить существующее взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID не существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        if loan.ID is None:
            raise ValueError("The loan's ID is not set.")
        
        self._connection.execute(
            "UPDATE Loan SET "
            "StartDate=:startDate,ReturnDate=:returnDate,BookID=:bookID,ClientID=:clientID "
            "WHERE ID=:id;",
            {
                "id": loan.ID,
                "startDate": loan.StartDate,
                "returnDate": loan.ReturnDate,
                "bookID": loan.BookID,
                "clientID": loan.ClientID
            }
        )