import sqlite3
from pathlib import Path


DB_PATH = Path("output/leads.db")


def get_connection():
    """SQLite database connection return karta hai."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Table create karta hai aur existing database ko update karta hai."""

    with get_connection() as connection:

        # Nayi database ke liye complete table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                domain TEXT,
                city TEXT,
                country TEXT,
                niche TEXT,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                contact_page TEXT DEFAULT '',
                contact_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Existing database ke columns check karna
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(leads)"
            ).fetchall()
        }

        # Purani table mein missing columns add karna
        new_columns = {
            "email": "TEXT DEFAULT ''",
            "phone": "TEXT DEFAULT ''",
            "contact_page": "TEXT DEFAULT ''",
            "contact_status": "TEXT DEFAULT 'pending'",
        }

        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE leads ADD COLUMN "
                    f"{column_name} {column_type}"
                )


def save_leads(
    leads: list[dict],
    niche: str,
    city: str,
    country: str,
) -> int:
    """New leads save karta hai aur duplicate URLs skip karta hai."""

    initialize_database()
    saved_count = 0

    with get_connection() as connection:
        for lead in leads:
            url = lead.get("url", "").strip()

            if not url:
                continue

            business_name = (
                lead.get("business_name")
                or lead.get("title")
                or "Unknown business"
            )

            cursor = connection.execute("""
                INSERT OR IGNORE INTO leads (
                    business_name,
                    url,
                    domain,
                    city,
                    country,
                    niche,
                    email,
                    phone,
                    contact_page,
                    contact_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                business_name,
                url,
                lead.get("domain", ""),
                city,
                country,
                niche,
                lead.get("email", ""),
                lead.get("phone", ""),
                lead.get("contact_page", ""),
                lead.get("contact_status", "pending"),
            ))

            saved_count += cursor.rowcount

    return saved_count


def update_lead_contact(
    url: str,
    email: str = "",
    phone: str = "",
    contact_page: str = "",
    contact_status: str = "success",
) -> bool:
    """Existing lead ki contact information update karta hai."""

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE leads
            SET email = ?,
                phone = ?,
                contact_page = ?,
                contact_status = ?
            WHERE url = ?
        """, (
            email,
            phone,
            contact_page,
            contact_status,
            url.strip(),
        ))

        return cursor.rowcount > 0


def get_all_leads() -> list[dict]:
    """Database se tamam leads aur contact details return karta hai."""

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM leads
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
    print(f"Database location: {DB_PATH}")