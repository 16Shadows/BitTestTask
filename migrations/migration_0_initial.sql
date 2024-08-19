-- Скрипт для создания изначальной схемы БД
PRAGMA encoding = "UTF-8";
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Book (
    ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    PublicationYear INTEGER NOT NULL, --Только год публикации, т.к. обычно только год указывается у книги
    AddedAtDate TEXT NOT NULL, --Дата добавления книги в библиотеку

    Author TEXT NOT NULL COLLATE NOCASE, --Используем сравнение без регистра, чтобы избежать проблемы из-за опечаток в регистре (А.С. Пушкин и А.с.Пушкин)
    Genre TEXT NOT NULL COLLATE NOCASE --Используем сравнение без регистра, чтобы избежать проблемы из-за опечаток в регистре (Фантастика и фантастика)
);

CREATE TABLE IF NOT EXISTS Client (
    ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL COLLATE NOCASE --Используем сравнение без регистра, чтобы избежать проблем из-за опечаток в регистре (Петров и петров)
);

CREATE TABLE IF NOT EXISTS Loan (
    ID INTEGER PRIMARY KEY,
    StartDate TEXT NOT NULL, -- Дата выдачи книги.
    ReturnDate TEXT CHECK(ReturnDate >= StartDate), -- Дата фактического возврата опциональна на записи, т.к. она, очевидно, неизвестна на момент взятия книги. Должна быть не меньше даты выдачи книги.

    BookID INTEGER NOT NULL,
    ClientID INTEGER NOT NULL,

    FOREIGN KEY(BookID) REFERENCES Book(ID),
    FOREIGN KEY(ClientID) REFERENCES Client(ID)
);

-- Предотвращаем триггерами несколько невозвращённых взятий одной и той же книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanOnce_Insert
BEFORE INSERT ON Loan
WHEN
(SELECT 1 WHERE
NEW.ReturnDate IS NULL
AND
EXISTS(SELECT * FROM Loan WHERE Loan.BookID = NEW.BookID AND Loan.ReturnDate IS NULL LIMIT 1))
BEGIN
    SELECT RAISE(FAIL, 'The book is already loaned.');
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanOnce_Update
BEFORE UPDATE OF ReturnDate ON Loan
WHEN
(SELECT 1 WHERE
NEW.ReturnDate IS NULL
AND
EXISTS(SELECT * FROM Loan WHERE Loan.BookID = NEW.BookID AND Loan.ReturnDate IS NULL LIMIT 1))
BEGIN
    SELECT RAISE(FAIL, 'The book is already loaned.');
END;

-- Триггерами проверяем соответствие между датой добавления книги в БД и датой начала взятия книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanDateConsistency_Insert
BEFORE INSERT ON Loan
WHEN EXISTS ( SELECT * FROM Book WHERE Book.ID = NEW.BookID AND NEW.StartDate < Book.AddedAtDate LIMIT 1)
BEGIN
    SELECT RAISE(FAIL, "The loan starts earlier than the book is added to the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanDateConsistency_Update
BEFORE UPDATE OF StartDate ON Loan
WHEN EXISTS ( SELECT * FROM Book WHERE Book.ID = NEW.BookID AND NEW.StartDate < Book.AddedAtDate LIMIT 1)
BEGIN
    SELECT RAISE(FAIL, "The loan starts earlier than the book is added to the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanDateConsistency_BookUpdate
BEFORE UPDATE OF AddedAtDate ON Book
WHEN EXISTS (SELECT * FROM Loan WHERE Loan.BookID = NEW.ID AND NEW.AddedAtDate > Loan.StartDate LIMIT 1)
BEGIN
    SELECT RAISE(FAIL, "The book is added to the library later than it is loaned for the first time.");
END;