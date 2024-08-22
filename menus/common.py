from components.books.book import Book
from components.clients.client import Client
from components.loans.loan import Loan

def book_to_text(book: Book) -> str:
    return f'{book.Name} ({book.Author}, {book.PublicationYear} г.) [{book.Genre}]'

def client_to_text(client: Client) -> str:
    return f'{client.Name} [рег: {client.RegistrationDate}]'

def loan_to_text(loan: tuple[Loan, Book, Client]) -> str:
    res = f'{book_to_text(loan[1])} - {client_to_text(loan[2])} - c {loan[0].StartDate.isoformat()} по {loan[0].EndDate.isoformat()}.'
    if loan[0].ReturnDate is not None:
        res += f" - Дата возврата {loan[0].ReturnDate.isoformat()}"
    return res