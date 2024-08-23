from dataclasses import dataclass
from datetime import date

@dataclass
class Client:
    Name: str
    RegistrationDate: date
    Address: str

    ID: int | None = None