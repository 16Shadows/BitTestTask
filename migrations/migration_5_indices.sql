/*
    Создать индексы для активно используемых для поиска полей
*/

BEGIN TRANSACTION;

CREATE INDEX IDX_Book_AddedAtDate ON Book(AddedAtDate);

CREATE INDEX IDX_Client_RegistrationDate ON Client(RegistrationDate);

CREATE INDEX IDX_Loan_StartDate ON Loan(StartDate);
CREATE INDEX IDX_Loan_ReturnDate ON Loan(ReturnDate);

END TRANSACTION;