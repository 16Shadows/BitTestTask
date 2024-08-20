from dataclasses import dataclass
from datetime import date

@dataclass
class Book:
    Name: str
    PublicationYear: int
    Author: str
    Genre: str
    AddedAtDate: date

    ID: int | None = None