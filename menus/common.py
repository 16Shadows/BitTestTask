from components.books.book import Book
from components.clients.client import Client

def book_to_text(book: Book) -> str:
    return f'{book.Name} ({book.Author}, {book.PublicationYear} г.) [{book.Genre}]'

def client_to_text(client: Client) -> str:
    return f'{client.Name} [рег: {client.RegistrationDate}]'