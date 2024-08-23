/*
    Скрипт для обновления схемы БД и добавления возможности удаления читателей.
*/

PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

/*
    Эти триггеры зависят от Loan, но, т.к. они срабатывают не на изменения в Loan, то SQLite не считает их зависимыми
*/
DROP TRIGGER TRG_LoanBookDateConsistency_BookUpdate;
DROP TRIGGER TRG_LoanClientDateConsistency_ClientUpdate;

CREATE TABLE IF NOT EXISTS New_Loan (
    ID INTEGER PRIMARY KEY,
    StartDate TEXT NOT NULL, -- Дата выдачи книги.
    EndDate TEXT NOT NULL CHECK(EndDate >= StartDate), -- Ожидаемая дата завершения возврата
    ReturnDate TEXT CHECK(ReturnDate >= StartDate), -- Дата фактического возврата опциональна на записи, т.к. она, очевидно, неизвестна на момент взятия книги. Должна быть не меньше даты выдачи книги.

    BookID INTEGER NOT NULL,
    ClientID INTEGER NOT NULL,

    FOREIGN KEY(BookID) REFERENCES Book(ID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(ClientID) REFERENCES Client(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

INSERT INTO New_Loan (ID, StartDate, EndDate, ReturnDate, BookID, ClientID)
SELECT ID, StartDate, EndDate, ReturnDate, BookID, ClientID FROM Loan;

DROP TABLE Loan;

ALTER TABLE New_Loan RENAME TO Loan;

/*
    Восстанавливаем все триггеры, которые зависят от Loan
*/
-- Предотвращаем триггерами несколько невозвращённых взятий одной и той же книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanOnce_Insert
BEFORE INSERT ON Loan
WHEN
CASE
    WHEN NEW.ReturnDate IS NULL THEN
        EXISTS(SELECT * FROM Loan WHERE Loan.BookID = NEW.BookID AND (Loan.ReturnDate IS NULL OR NEW.StartDate < Loan.ReturnDate))
    ELSE
        EXISTS(SELECT * FROM Loan WHERE Loan.BookID = NEW.BookID AND 
            CASE
            WHEN Loan.ReturnDate IS NULL THEN
                Loan.StartDate < NEW.ReturnDate
            ELSE
                Loan.StartDate < NEW.ReturnDate OR NEW.StartDate < Loan.ReturnDate
            END
            LIMIT 1
        )
END
BEGIN
    SELECT RAISE(ABORT, 'The book is already loaned during the specified period.');
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanOnce_Update
BEFORE UPDATE OF ReturnDate, BookID ON Loan
WHEN
CASE
    WHEN NEW.ReturnDate IS NULL THEN
        EXISTS(SELECT * FROM Loan WHERE Loan.BookID = NEW.BookID AND Loan.ID != NEW.ID AND (Loan.ReturnDate IS NULL OR NEW.StartDate < Loan.ReturnDate))
    ELSE
        EXISTS(SELECT * FROM Loan WHERE Loan.BookID = NEW.BookID AND Loan.ID != NEW.ID AND
            CASE
            WHEN Loan.ReturnDate IS NULL THEN
                Loan.StartDate < NEW.ReturnDate
            ELSE
                Loan.StartDate < NEW.ReturnDate OR NEW.StartDate < Loan.ReturnDate
            END
            LIMIT 1
        )
END
BEGIN
    SELECT RAISE(ABORT, 'The book is already loaned during the specified period.');
END;

-- Триггерами проверяем соответствие между датой добавления книги в БД и датой начала взятия книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanBookDateConsistency_Insert
BEFORE INSERT ON Loan
WHEN EXISTS ( SELECT * FROM Book WHERE Book.ID = NEW.BookID AND NEW.StartDate < Book.AddedAtDate)
BEGIN
    SELECT RAISE(ABORT, "The loan starts earlier than the book is added to the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanBookDateConsistency_Update
BEFORE UPDATE OF BookID, StartDate ON Loan
WHEN EXISTS ( SELECT * FROM Book WHERE Book.ID = NEW.BookID AND NEW.StartDate < Book.AddedAtDate)
BEGIN
    SELECT RAISE(ABORT, "The loan starts earlier than the book is added to the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanBookDateConsistency_BookUpdate
BEFORE UPDATE OF AddedAtDate ON Book
WHEN EXISTS (SELECT * FROM Loan WHERE Loan.BookID = NEW.ID AND NEW.AddedAtDate > Loan.StartDate)
BEGIN
    SELECT RAISE(ABORT, "The book is added to the library later than it is loaned for the first time.");
END;

-- Триггерами проверяем соответствие между датой регистрации читателя и датой начала взятия книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanClientDateConsistency_Insert
BEFORE INSERT ON Loan
WHEN EXISTS ( SELECT * FROM Client WHERE Client.ID = NEW.ClientID AND NEW.StartDate < Client.RegistrationDate)
BEGIN
    SELECT RAISE(ABORT, "The loan starts earlier than the client is registered in the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanClientDateConsistency_Update
BEFORE UPDATE OF StartDate, ClientID ON Loan
WHEN EXISTS ( SELECT * FROM Client WHERE Client.ID = NEW.ClientID AND NEW.StartDate < Client.RegistrationDate)
BEGIN
    SELECT RAISE(ABORT, "The loan starts earlier than the client is registered in the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanClientDateConsistency_ClientUpdate
BEFORE UPDATE OF RegistrationDate ON Client
WHEN EXISTS (SELECT * FROM Loan WHERE Loan.ClientID = NEW.ID AND NEW.RegistrationDate > Loan.StartDate)
BEGIN
    SELECT RAISE(ABORT, "The client is registered in the library later than they loan a book for the first time.");
END;

PRAGMA foreign_key_check;

END TRANSACTION;

PRAGMA foreign_keys=ON;