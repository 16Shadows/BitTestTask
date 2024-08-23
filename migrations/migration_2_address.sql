/*
    Скрипт для обновления схемы БД и добавления адресов читателей.
*/

PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

/*
    Эти триггеры зависят от Client, но, т.к. они срабатывают не на изменения в Client, то SQLite не считает их зависимыми
*/
DROP TRIGGER TRG_LoanClientDateConsistency_Insert;
DROP TRIGGER TRG_LoanClientDateConsistency_Update;

CREATE TABLE IF NOT EXISTS New_Client (
    ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL COLLATE NOCASE, --Используем сравнение без регистра, чтобы избежать проблем из-за опечаток в регистре (Петров и петров)
    RegistrationDate TEXT NOT NULL, --Дата регистрации читателя в библиотеке
    Address TEXT NOT NULL -- Адрес проживания читателя
);

INSERT INTO New_Client (ID, Name, RegistrationDate, Address)
SELECT ID, Name, RegistrationDate, "Unknown" FROM Client;

DROP TABLE Client;

ALTER TABLE New_Client RENAME TO Client;

/*
    Восстанавливаем удалённые триггеры.
*/
-- Триггерами проверяем соответствие между датой регистрации читателя и датой начала взятия книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanClientDateConsistency_Insert
BEFORE INSERT ON Loan
WHEN EXISTS ( SELECT * FROM Client WHERE Client.ID = NEW.ClientID AND NEW.StartDate < Client.RegistrationDate)
BEGIN
    SELECT RAISE(FAIL, "The loan starts earlier than the client is registered in the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanClientDateConsistency_Update
BEFORE UPDATE OF StartDate, ClientID ON Loan
WHEN EXISTS ( SELECT * FROM Client WHERE Client.ID = NEW.ClientID AND NEW.StartDate < Client.RegistrationDate)
BEGIN
    SELECT RAISE(FAIL, "The loan starts earlier than the client is registered in the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanClientDateConsistency_ClientUpdate
BEFORE UPDATE OF RegistrationDate ON Client
WHEN EXISTS (SELECT * FROM Loan WHERE Loan.ClientID = NEW.ID AND NEW.RegistrationDate > Loan.StartDate)
BEGIN
    SELECT RAISE(FAIL, "The client is registered in the library later than they loan a book for the first time.");
END;

PRAGMA foreign_key_check;

END TRANSACTION;

PRAGMA foreign_keys=ON;