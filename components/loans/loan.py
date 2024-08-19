from dataclasses import dataclass
from datetime import date

@dataclass
class Loan:
    ID: int | None
    StartDate: date
    ReturnDate: date
    ClientID: int
    BookID: int
