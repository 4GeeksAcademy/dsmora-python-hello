import random

from app.models.book import BookCreate
from app.repositories.books_repository import BooksRepository


BASE_SEED_BOOKS = [
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

GENRES = ["fiction", "non-fiction", "mystery", "sci-fi"]
STATUSES = ["available", "checked_out"]

AUTHOR_FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen",
]
AUTHOR_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin",
]
TITLE_ADJECTIVES = [
    "Silent", "Hidden", "Broken", "Distant", "Golden", "Forgotten", "Endless", "Final",
    "Secret", "Lost", "Ancient", "Burning", "Frozen", "Whispering", "Shattered", "Rising",
]
TITLE_NOUNS = [
    "Shadow", "Kingdom", "Garden", "Storm", "River", "Horizon", "Legacy", "Empire",
    "Mirror", "Journey", "Prophecy", "Labyrinth", "Symphony", "Echo", "Path", "Flame",
]


def _generate_extra_books(count: int, rng: random.Random) -> list[dict]:
    books = []
    for i in range(count):
        title = f"The {rng.choice(TITLE_ADJECTIVES)} {rng.choice(TITLE_NOUNS)} {i + 1}"
        author = f"{rng.choice(AUTHOR_FIRST_NAMES)} {rng.choice(AUTHOR_LAST_NAMES)}"
        books.append(
            {
                "title": title,
                "author": author,
                "genre": rng.choice(GENRES),
                "pages": rng.randint(120, 800),
                "status": rng.choice(STATUSES),
            }
        )
    return books


def build_seed_books(total: int = 500, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    extra_needed = max(total - len(BASE_SEED_BOOKS), 0)
    return BASE_SEED_BOOKS + _generate_extra_books(extra_needed, rng)


def run_seed(total: int = 500) -> int:
    repository = BooksRepository()
    created_count = 0

    for raw_book in build_seed_books(total):
        if repository.exists_by_title_author(raw_book["title"], raw_book["author"]):
            continue
        repository.create(BookCreate(**raw_book))
        created_count += 1

    return created_count


if __name__ == "__main__":
    inserted = run_seed()
    print(f"Seed completed. Inserted {inserted} books.")