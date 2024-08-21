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
    Name TEXT NOT NULL COLLATE NOCASE, --Используем сравнение без регистра, чтобы избежать проблем из-за опечаток в регистре (Петров и петров)
    RegistrationDate TEXT NOT NULL --Дата регистрации читателя в библиотеке
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
    SELECT RAISE(FAIL, 'The book is already loaned during the specified period.');
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
    SELECT RAISE(FAIL, 'The book is already loaned during the specified period.');
END;

-- Триггерами проверяем соответствие между датой добавления книги в БД и датой начала взятия книги
CREATE TRIGGER IF NOT EXISTS TRG_LoanBookDateConsistency_Insert
BEFORE INSERT ON Loan
WHEN EXISTS ( SELECT * FROM Book WHERE Book.ID = NEW.BookID AND NEW.StartDate < Book.AddedAtDate)
BEGIN
    SELECT RAISE(FAIL, "The loan starts earlier than the book is added to the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanBookDateConsistency_Update
BEFORE UPDATE OF BookID, StartDate ON Loan
WHEN EXISTS ( SELECT * FROM Book WHERE Book.ID = NEW.BookID AND NEW.StartDate < Book.AddedAtDate)
BEGIN
    SELECT RAISE(FAIL, "The loan starts earlier than the book is added to the library.");
END;

CREATE TRIGGER IF NOT EXISTS TRG_LoanBookDateConsistency_BookUpdate
BEFORE UPDATE OF AddedAtDate ON Book
WHEN EXISTS (SELECT * FROM Loan WHERE Loan.BookID = NEW.ID AND NEW.AddedAtDate > Loan.StartDate)
BEGIN
    SELECT RAISE(FAIL, "The book is added to the library later than it is loaned for the first time.");
END;

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