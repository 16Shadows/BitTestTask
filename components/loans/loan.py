from dataclasses import dataclass
from datetime import date

@dataclass
class Loan:
    ID: int
    Name: str
    StartDate: date
    ReturnDate: date
    AuthorID: int
    BookID: int
