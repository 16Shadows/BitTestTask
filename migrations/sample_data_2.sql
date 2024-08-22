/*
    Скрипт для заполнения первой миграции БД (1_return_dates.sql) тестовыми данными.
    Скрипт безопасно запускать только на пустой БД, т.к. он использует фиксированные ID для целостности вставляемых данных.
*/
BEGIN TRANSACTION;

INSERT INTO Client (ID, Name, RegistrationDate, Address) VALUES (0, 'Петров Александ Михайлович', '2024-01-01', 'ш. Космонавтов, 111Д, Пермь');
INSERT INTO Client (ID, Name, RegistrationDate, Address) VALUES (1, 'Неверов Леонид Васильевич', '2024-01-01', 'ул. Ленина, 53, Пермь');
INSERT INTO Client (ID, Name, RegistrationDate, Address) VALUES (2, 'Некрасов Никита Валерьевич', '2024-01-01', 'Парковая ул., 16, Пермь');

INSERT INTO Book (ID, Name, PublicationYear, Author, Genre, AddedAtDate) VALUES (0, 'Война и мир', '1873', 'Л.Н. Толстой', 'Роман-эпопея', '2024-01-01');
INSERT INTO Book (ID, Name, PublicationYear, Author, Genre, AddedAtDate) VALUES (1, 'Война и мир', '1875', 'Л.Н. Толстой', 'Роман-эпопея', '2024-01-01');

INSERT INTO Book (ID, Name, PublicationYear, Author, Genre, AddedAtDate) VALUES (2, 'Евгений Онегин', '1875', 'А.С. Пушкин', 'Роман в стихах', '2024-01-01');
INSERT INTO Book (ID, Name, PublicationYear, Author, Genre, AddedAtDate) VALUES (3, 'Евгений Онегин', '1899', 'А.С. Пушкин', 'Роман в стихах', '2024-01-01');

INSERT INTO Loan (StartDate, EndDate, ReturnDate, BookID, ClientID) VALUES ('2024-06-23', '2024-07-23', '2024-07-17', 2, 1);
INSERT INTO Loan (StartDate, EndDate, ReturnDate, BookID, ClientID) VALUES ('2024-07-16', '2024-08-16', '2024-08-22', 1, 1);

INSERT INTO Loan (StartDate, EndDate, ReturnDate, BookID, ClientID) VALUES ('2024-06-22', NULL, 0, 2);

INSERT INTO Loan (StartDate, EndDate, ReturnDate, BookID, ClientID) VALUES ('2024-06-25', NULL, 3, 2);

END TRANSACTION;