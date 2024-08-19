from dataclasses import dataclass
from datetime import date

@dataclass
class Client:
    ID: int | None
    Name: str
    RegistrationDate: date