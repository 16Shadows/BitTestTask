import sqlite3
from typing import Self
from .loan import Loan

class LoanRepositorySqlite3:
    """Репозиторий взятий книг на SQLite3"""
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
    
    def add_loan(self: Self, loan: Loan) -> None:
        """
            Добавить новое взятие книги.
            
            loan : Loan -- взятие книги.

            Если взятие книги с таким ID уже существует или возникает конфликт интервалов с другим взятием книги, будет поднята ошибка.
        """
        try:
            if loan.ID is None:
                self._connection.execute(
                    "INSERT INTO Loan (StartDate, ReturnDate, BookID, ClientID) "
                    "VALUES (:startDate, :returnDate, :bookID, :clientID); ",
                    {
                        "startDate": loan.StartDate,
                        "returnDate": loan.ReturnDate,
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
        except:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()

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
        except:
            self._connection.rollback()
        else:
            self._connection.commit()