from dataclasses import dataclass
from datetime import date

@dataclass
class Client:
    ID: int
    Name: str
    RegistrationDate: date