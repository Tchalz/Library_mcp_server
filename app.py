"""
Library Server — a standalone MCP (Model Context Protocol) server.

Models a tiny library: searching books, checking copy availability, and
borrowing/returning books on behalf of members. Built with FastMCP, the
high-level Python SDK for MCP servers.

Run it directly for local dev/testing:
    python app.py

Inspect it (schema + counts) without a client:
    fastmcp inspect app.py

Run it under the MCP Inspector (interactive browser UI):
    fastmcp dev app.py
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Library Server", port=8001)


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------
# Keyed by ISBN so every tool can do an O(1) lookup once it has one.

BOOKS: dict[str, dict] = {
    "978-0-441-01359-3": {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "978-0-441-01359-3",
        "genre": "science fiction",
        "tags": ["space", "desert planet", "politics", "epic"],
        "available_copies": 2,
    },
    "978-0-06-085052-4": {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "isbn": "978-0-06-085052-4",
        "genre": "science fiction",
        "tags": ["dystopia", "society", "classic"],
        "available_copies": 0,
    },
    "978-0-14-303943-3": {
        "title": "The Old Man and the Sea",
        "author": "Ernest Hemingway",
        "isbn": "978-0-14-303943-3",
        "genre": "literary fiction",
        "tags": ["sea", "fishing", "classic", "short"],
        "available_copies": 1,
    },
    "978-0-544-00341-5": {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "isbn": "978-0-544-00341-5",
        "genre": "fantasy",
        "tags": ["adventure", "dragons", "quest"],
        "available_copies": 3,
    },
    "978-1-4767-3529-8": {
        "title": "The Martian",
        "author": "Andy Weir",
        "isbn": "978-1-4767-3529-8",
        "genre": "science fiction",
        "tags": ["space", "mars", "survival", "astronaut"],
        "available_copies": 1,
    },
    "978-0-7432-7356-5": {
        "title": "Angels & Demons",
        "author": "Dan Brown",
        "isbn": "978-0-7432-7356-5",
        "genre": "thriller",
        "tags": ["mystery", "conspiracy", "fast-paced"],
        "available_copies": 2,
    },
    "978-0-345-53980-5": {
        "title": "Ready Player One",
        "author": "Ernest Cline",
        "isbn": "978-0-345-53980-5",
        "genre": "science fiction",
        "tags": ["virtual reality", "gaming", "space", "future"],
        "available_copies": 0,
    },
    "978-0-06-231609-7": {
        "title": "Sapiens: A Brief History of Humankind",
        "author": "Yuval Noah Harari",
        "isbn": "978-0-06-231609-7",
        "genre": "nonfiction",
        "tags": ["history", "science", "anthropology"],
        "available_copies": 4,
    },
}

# Borrow history, keyed by member_id. Each entry is appended to on
# borrow_book and updated in place (return date filled) on return_book.
MEMBER_HISTORY: dict[str, list[dict]] = {
    "M001": [
        {"isbn": "978-0-441-01359-3", "title": "Dune", "status": "returned"},
    ],
    "M002": [],
}

LIBRARY_HOURS = (
    "Monday–Friday: 9:00 AM – 8:00 PM\n"
    "Saturday: 10:00 AM – 6:00 PM\n"
    "Sunday: Closed"
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_books(query: str) -> str:
    """
    Search the library catalog by title, author, genre, or theme (e.g.
    'space', 'dystopia', 'mystery') — case-insensitive, partial match. Use
    this whenever the user wants to find books, browse by topic, or look up
    an author's work, before doing anything else — you'll need the ISBN
    from these results to check availability or borrow a book.

    Args:
        query: A title, partial title, author name, genre, or theme keyword to search for.

    Returns:
        A newline-separated list of matching books (title, author, ISBN,
        copies available), or a message saying nothing matched.
    """
    q = query.strip().lower()
    if not q:
        return "Please provide a search term (a title, author, genre, or theme)."

    matches = [
        b for b in BOOKS.values()
        if q in b["title"].lower()
        or q in b["author"].lower()
        or q in b["genre"].lower()
        or any(q in tag for tag in b["tags"])
    ]

    if not matches:
        return f"No books found matching '{query}'."

    lines = [
        f"{b['title']} by {b['author']} — ISBN {b['isbn']} — {b['available_copies']} copies available"
        for b in matches
    ]
    return "\n".join(lines)


@mcp.tool()
def check_availability(isbn: str) -> str:
    """
    Check how many copies of a specific book are currently available to
    borrow. Use this after search_books has given you an ISBN, or whenever
    the user asks if a specific book is in stock — always check this before
    calling borrow_book so you can tell the user up front if none are left.

    Args:
        isbn: The ISBN of the book to check, exactly as returned by search_books.

    Returns:
        A string stating the title and number of available copies, or an
        error string if the ISBN isn't in the catalog.
    """
    book = BOOKS.get(isbn)
    if not book:
        return f"Error: no book found with ISBN '{isbn}'."

    if book["available_copies"] <= 0:
        return f"'{book['title']}' has no copies available right now."
    return f"'{book['title']}' has {book['available_copies']} copies available."


@mcp.tool()
def borrow_book(isbn: str, member_id: str) -> str:
    """
    Borrows a copy of a book on behalf of a library member, decrementing its
    available copy count by one and recording it in that member's borrow
    history. Only call this after confirming with check_availability (or a
    recent search_books result) that at least one copy is available — if
    none are left, this returns an error string rather than raising, so
    always check the return value before telling the user it succeeded.

    Args:
        isbn: The ISBN of the book to borrow.
        member_id: The library member's ID, e.g. 'M001'.

    Returns:
        A confirmation string on success, or an error string if the ISBN
        doesn't exist or no copies are currently available.
    """
    book = BOOKS.get(isbn)
    if not book:
        return f"Error: no book found with ISBN '{isbn}'."

    if book["available_copies"] <= 0:
        return f"Error: no copies of '{book['title']}' are currently available to borrow."

    book["available_copies"] -= 1
    MEMBER_HISTORY.setdefault(member_id, []).append(
        {"isbn": isbn, "title": book["title"], "status": "borrowed"}
    )
    return (
        f"'{book['title']}' borrowed successfully by member {member_id}. "
        f"{book['available_copies']} copies remaining."
    )


@mcp.tool()
def return_book(isbn: str, member_id: str) -> str:
    """
    Returns a previously borrowed book on behalf of a member, incrementing
    its available copy count by one and marking the corresponding entry in
    that member's borrow history as returned. Use this when a user says
    they're bringing a book back or wants to return something they borrowed.

    Args:
        isbn: The ISBN of the book being returned.
        member_id: The library member's ID, e.g. 'M001'.

    Returns:
        A confirmation string on success, or an error string if the ISBN
        doesn't exist or this member has no matching active loan on record.
    """
    book = BOOKS.get(isbn)
    if not book:
        return f"Error: no book found with ISBN '{isbn}'."

    history = MEMBER_HISTORY.get(member_id, [])
    loan = next(
        (h for h in reversed(history) if h["isbn"] == isbn and h["status"] == "borrowed"),
        None,
    )
    if loan is None:
        return f"Error: member {member_id} has no active loan for '{book['title']}' on record."

    loan["status"] = "returned"
    book["available_copies"] += 1
    return (
        f"'{book['title']}' returned successfully by member {member_id}. "
        f"{book['available_copies']} copies now available."
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("library://info/hours")
def get_hours() -> str:
    """Static resource: the library's weekly operating hours."""
    return LIBRARY_HOURS


@mcp.resource("member://{member_id}/history")
def get_member_history(member_id: str) -> str:
    """Dynamic resource template: a specific member's borrow history."""
    history = MEMBER_HISTORY.get(member_id)
    if history is None:
        return f"No record found for member '{member_id}'."
    if not history:
        return f"Member {member_id} has no borrow history yet."

    lines = [f"{h['title']} — {h['status']}" for h in history]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt()
def recommend_books(genre: str, mood: Optional[str] = None) -> str:
    """Generates a reusable prompt template for recommending books by genre and mood."""
    mood_clause = f" that would suit a '{mood}' mood" if mood else ""
    return (
        f"Recommend 3 books in the '{genre}' genre{mood_clause}. "
        "For each, use search_books to confirm it's actually in the library "
        "catalog before recommending it, and mention whether copies are "
        "currently available."
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
