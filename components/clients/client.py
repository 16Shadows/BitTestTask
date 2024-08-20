from dataclasses import dataclass
from datetime import date

@dataclass
class Client:
    Name: str
    RegistrationDate: date

    ID: int | None = None