import sqlite3

DB_NAME = "books.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute('''
                CREATE TABLE IF NOT EXISTS books
                (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_number INTEGER UNIQUE,
                    title       TEXT UNIQUE,
                    author      TEXT,
                    translator  TEXT,
                    pub_date    TEXT,
                    isbn        TEXT,
                    language    TEXT,
                    genre       TEXT,
                    edition     TEXT,
                    status      TEXT
                )
                ''')

    cur.execute('''
                CREATE TABLE IF NOT EXISTS inventory
                (
                    book_id   INTEGER PRIMARY KEY,
                    available INTEGER DEFAULT 0,
                    lent      INTEGER DEFAULT 0,
                    missing   INTEGER DEFAULT 0,
                    damaged   INTEGER DEFAULT 0,
                    FOREIGN KEY (book_id) REFERENCES books (id)
                )
                ''')

    # 🔍 Indexes for faster search
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_number ON books(book_number);")

    conn.commit()
    conn.close()

def insert_book(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
                INSERT INTO books (book_number, title, author, translator, pub_date, isbn,
                                   language, genre, edition, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(data.values()))
    book_id = cur.lastrowid
    cur.execute("INSERT INTO inventory (book_id) VALUES (?)", (book_id,))
    conn.commit()
    conn.close()

def find_book_by_title(title):
    conn = sqlite3.connect("books.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE title = ?", (title,))
    result = cur.fetchone()
    conn.close()
    return result

def get_books_paginated(page: int, page_size: int = 100):
    offset = (page - 1) * page_size
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
                SELECT id,
                       book_number,
                       title,
                       author,
                       translator,
                       pub_date,
                       isbn,
                       language,
                       genre,
                       edition,
                       status
                FROM books
                ORDER BY id
                LIMIT ? OFFSET ?
                """, (page_size, offset))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_total_books_count():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books")
    total = cur.fetchone()[0]
    conn.close()
    return total

def update_book(book_id, data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    values = list(data.values())
    values.append(book_id)
    cur.execute('''
                UPDATE books
                SET book_number=?,
                    title=?,
                    author=?,
                    translator=?,
                    pub_date=?,
                    isbn=?,
                    language=?,
                    genre=?,
                    edition=?,
                    status=?
                WHERE id = ?
                ''', values)
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id=?", (book_id,))
    cur.execute("DELETE FROM inventory WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()

def search_books(term, exact=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if exact:
        term_lower = term.strip().lower()
        query = """
                SELECT * FROM books
                WHERE CAST(book_number AS TEXT) = ?
                   OR LOWER(title) = ?
                   OR LOWER(author) = ?
                """
        c.execute(query, (term_lower, term_lower, term_lower))
    else:
        term_like = f"%{term.strip().lower()}%"
        query = """
                SELECT * FROM books
                WHERE LOWER(CAST(book_number AS TEXT)) LIKE ?
                   OR LOWER(title) LIKE ?
                   OR LOWER(author) LIKE ?
                """
        c.execute(query, (term_like, term_like, term_like))

    results = c.fetchall()
    conn.close()
    return results

def export_books():
    import pandas as pd
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
                           SELECT b.*, i.available, i.lent, i.missing, i.damaged
                           FROM books b
                                    LEFT JOIN inventory i ON b.id = i.book_id
                           """, conn)
    df.to_excel("books_export.xlsx", index=False)
    conn.close()

def get_copy_summary(book_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT available, lent, missing, damaged FROM inventory WHERE book_id = ?", (book_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        available, lent, missing, damaged = row
        return {
            "Available": available,
            "Lent": lent,
            "Missing": missing,
            "Damaged": damaged,
            "total": available + lent + missing + damaged
        }
    else:
        return {"Available": 0, "Lent": 0, "Missing": 0, "Damaged": 0, "total": 0}


def update_inventory(book_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM inventory WHERE book_id = ?", (book_id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO inventory (book_id, available, lent, missing, damaged) VALUES (?, 0, 0, 0, 0)",
            (book_id,)
        )

    sets = []
    values = []
    for field in ["available", "lent", "missing", "damaged"]:
        if field in kwargs:
            sets.append(f"{field} = ?")
            values.append(kwargs[field])

    if sets:
        values.append(book_id)
        cur.execute(f"UPDATE inventory SET {', '.join(sets)} WHERE book_id = ?", values)

    conn.commit()
    conn.close()
