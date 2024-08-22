from dataclasses import dataclass
from datetime import date

@dataclass
class Loan:
    StartDate: date
    EndDate: date
    ClientID: int
    BookID: int
    
    ID: int | None = None
    ReturnDate: date | None = None
