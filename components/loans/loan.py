from dataclasses import dataclass
from datetime import date

@dataclass
class Loan:
    StartDate: date
    ClientID: int
    BookID: int
    
    ID: int | None = None
    ReturnDate: date | None = None
