import sqlite3
from typing import Self, Sequence
from datetime import date
from .client import Client

class ClientRepositorySqlite3:
    """Репозиторий читателей на SQLite3"""
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def get_clients(self: Self) -> Sequence[Client]:
        """
            Все читатели библиотеки
        """
        #TODO: всех читателей загружать в память неэффективно, т.к. БД может вырасти.
        #Можно добавить некоторую форму пагинации или коллекцию, реализующую запрос части записей из БД по срезу.
        cur = self._connection.execute("SELECT * FROM Client")
        cur.row_factory = sqlite3.Row #type: ignore
        return [Client(**row) for row in cur.fetchall()]
    
    def get_last_visit_dates(self: Self) -> Sequence[tuple[Client, date]]:
        """
            Дата последнего посещения библиотеки каждым читателем.
        """
        #TODO: всех читателей загружать в память неэффективно, т.к. БД может вырасти.
        #Можно добавить некоторую форму пагинации или коллекцию, реализующую запрос части записей из БД по срезу.
        cur = self._connection.execute(
            "SELECT Client.ID, Client.Name, Client.RegistrationDate, "
            "COALESCE(MAX(COALESCE(Loan.ReturnDate, Loan.StartDate)), Client.RegistrationDate) as last_visit_date "
            "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
            "GROUP BY Client.ID "
            "ORDER BY Client.Name DESC;"
        )
        cur.row_factory = sqlite3.Row #type: ignore
        return [
            (
                Client(row['ID'], row['Name'], date.fromisoformat(row['RegistrationDate'])),
                date.fromisoformat(row['last_visit_date'])
            )
            for row in cur.fetchall()
        ]
    
    def get_total_loans_per_client(self: Self) -> Sequence[tuple[Client, int]]:
        """
            Общее количество взятых книг каждым читателем.
        """
        #TODO: всех читателей загружать в память неэффективно, т.к. БД может вырасти.
        #Можно добавить некоторую форму пагинации или коллекцию, реализующую запрос части записей из БД по срезу.
        cur = self._connection.execute(
            "SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans "
            "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
            "GROUP BY Client.ID "
            "ORDER BY Client.Name DESC;"
        )
        cur.row_factory = sqlite3.Row #type: ignore
        return [
            (
                Client(row['ID'], row['Name'], date.fromisoformat(row['RegistrationDate'])),
                row['total_loans']
            )
            for row in cur.fetchall()
        ]
    
    def get_total_unreturned_loans_per_client(self: Self) -> Sequence[tuple[Client, int]]:
        """
            Количество невозвращённых каждым читателем книг.
        """
        #TODO: всех читателей загружать в память неэффективно, т.к. БД может вырасти.
        #Можно добавить некоторую форму пагинации или коллекцию, реализующую запрос части записей из БД по срезу.
        cur = self._connection.execute(
            "SELECT Client.ID, Client.Name, Client.RegistrationDate, COUNT(Loan.ID) as total_loans "
            "FROM Client LEFT JOIN Loan ON Loan.ClientID = Client.ID "
            "WHERE Loan.ReturnDate IS NULL "
            "GROUP BY Client.ID "
            "ORDER BY Client.Name DESC;"
        )
        cur.row_factory = sqlite3.Row #type: ignore
        return [
            (
                Client(row['ID'], row['Name'], date.fromisoformat(row['RegistrationDate'])),
                row['total_loans']
            )
            for row in cur.fetchall()
        ]