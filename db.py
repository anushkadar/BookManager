import sqlite3

DB_NAME = "library.db"  # Changed to single database file


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Books table
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

    # Inventory table
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

    # Users table (now in the same database)
    cur.execute('''
                CREATE TABLE IF NOT EXISTS users
                (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    name            TEXT NOT NULL,
                    email           TEXT NOT NULL UNIQUE,
                    phone           TEXT,
                    membership_type TEXT,
                    status          TEXT
                )
                ''')

    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_number ON books(book_number)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_name ON users(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    conn.commit()
    conn.close()


# ===== BOOK FUNCTIONS =====
def insert_book(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
                INSERT INTO books (book_number, title, author, translator, pub_date,
                                   isbn, language, genre, edition, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(data.values()))
    book_id = cur.lastrowid
    cur.execute("INSERT INTO inventory (book_id) VALUES (?)", (book_id,))
    conn.commit()
    conn.close()


def find_book_by_title(title):
    conn = sqlite3.connect(DB_NAME)
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


# ... (keep all your existing book functions, just change DB_NAME to "library.db")

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
                SELECT *
                FROM books
                WHERE CAST(book_number AS TEXT) = ?
                   OR LOWER(title) = ?
                   OR LOWER(author) = ?
                """
        c.execute(query, (term_lower, term_lower, term_lower))
    else:
        term_like = f"%{term.strip().lower()}%"
        query = """
                SELECT *
                FROM books
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


# ===== USER FUNCTIONS =====
def insert_user(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
                INSERT INTO users (name, email, phone, membership_type, status)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    data['name'],
                    data['email'],
                    data['phone'],
                    data['membership_type'],
                    data['status']
                ))
    conn.commit()
    conn.close()


def update_user(user_id, data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
                UPDATE users
                SET name            = ?,
                    email           = ?,
                    phone           = ?,
                    membership_type = ?,
                    status          = ?
                WHERE id = ?
                ''', (
                    data['name'],
                    data['email'],
                    data['phone'],
                    data['membership_type'],
                    data['status'],
                    user_id
                ))
    conn.commit()
    conn.close()


def get_users_paginated(page, page_size):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    offset = (page - 1) * page_size
    cur.execute('''
                SELECT *
                FROM users
                ORDER BY id
                LIMIT ? OFFSET ?
                ''', (page_size, offset))
    users = cur.fetchall()
    conn.close()
    return users


def get_total_users_count():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


def search_users(term, exact=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    if exact:
        query = '''
                SELECT *
                FROM users
                WHERE name = ?
                   OR email = ?
                   OR phone = ? \
                '''
        params = (term, term, term)
    else:
        query = '''
                SELECT *
                FROM users
                WHERE name LIKE ?
                   OR email LIKE ?
                   OR phone LIKE ? \
                '''
        params = (f"%{term}%", f"%{term}%", f"%{term}%")

    cur.execute(query, params)
    users = cur.fetchall()
    conn.close()
    return users


# ... (keep all other existing functions, updating DB_NAME to "library.db")

# db.py (add these functions)
def create_user_tables():
    # Create users table
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     id              INTEGER PRIMARY KEY AUTOINCREMENT,
                     name            TEXT NOT NULL,
                     email           TEXT NOT NULL UNIQUE,
                     phone           TEXT,
                     membership_type TEXT,
                     status          TEXT
                 )''')
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
