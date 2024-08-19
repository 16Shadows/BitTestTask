from dataclasses import dataclass
from datetime import date

@dataclass
class Book:
    ID: int | None
    Name: str
    PublicationYear: int
    Author: str
    Genre: str
    AddedAtDate: date