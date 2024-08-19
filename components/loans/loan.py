from dataclasses import dataclass
from datetime import date

@dataclass
class Loan:
    ID: int | None
    Name: str
    StartDate: date
    ReturnDate: date
    AuthorID: int
    BookID: int
