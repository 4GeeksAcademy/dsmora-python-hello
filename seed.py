from app.models.book import BookCreate
from app.repositories.books_repository import BooksRepository


SEED_BOOKS = [
    {
        "title": "The Pragmatic Programmer",
        "author": "Hunt & Thomas",
        "genre": "non-fiction",
        "pages": 352,
        "status": "available",
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "genre": "sci-fi",
        "pages": 412,
        "status": "available",
    },
    {
        "title": "The Big Sleep",
        "author": "Raymond Chandler",
        "genre": "mystery",
        "pages": 231,
        "status": "checked_out",
    },
    {
        "title": "Nineteen Eighty-Four",
        "author": "George Orwell",
        "genre": "fiction",
        "pages": 328,
        "status": "available",
    },
]


def run_seed() -> int:
    repository = BooksRepository()
    created_count = 0

    for raw_book in SEED_BOOKS:
        if repository.exists_by_title_author(raw_book["title"], raw_book["author"]):
            continue
        repository.create(BookCreate(**raw_book))
        created_count += 1

    return created_count


if __name__ == "__main__":
    inserted = run_seed()
    print(f"Seed completed. Inserted {inserted} books.")