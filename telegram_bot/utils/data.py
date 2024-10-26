import os
import sqlite3
from contextlib import contextmanager
from typing import Generator


QUERY_RECORDS_FP = "data/query_records.db"


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database
    """

    # if not os.path.exists(QUERY_RECORDS_FP):
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(QUERY_RECORDS_FP)
    try:
        yield conn
    except sqlite3.Error as err:
        print(f"Error connecting to query records database: {err}")
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialise sqlite database
    """

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Query_rec (
                query_id TEXT PRIMARY KEY,
                query TEXT
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Schemes_rec (
                id INTEGER PRIMARY KEY,
                query_id TEXT NOT NULL,
                scheme TEXT,
                agency TEXT,
                description TEXT,
                image TEXT,
                link TEXT,
                scraped_text TEXT,
                what_it_gives TEXT,
                scheme_type TEXT,
                similarity FLOAT,
                quintile INTEGER,
                FOREIGN KEY (query_id) REFERENCES Query_rec(query_id) ON DELETE CASCADE
            )""")

        conn.commit()


def update_query_records(query_id: str, schemes) -> None:
    """
    Updates SQLite DB with query records
    """

    if len(schemes) < 1:
        return

    with get_db() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO Query_rec (query_id, query) VALUES (?, ?)
                """,
                (query_id, schemes[0]["query"]),
            )
            for scheme in schemes:
                cursor.execute(
                    """
                    INSERT INTO Schemes_rec (
                        query_id,
                        scheme,
                        agency,
                        description,
                        image,
                        link,
                        scraped_text,
                        what_it_gives,
                        scheme_type,
                        similarity,
                        quintile
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        query_id,
                        scheme["Scheme"],
                        scheme["Agency"],
                        scheme["Description"],
                        scheme["Image"],
                        scheme["Link"],
                        scheme["Scraped Text"],
                        scheme["What it gives"],
                        scheme["Scheme Type"],
                        scheme["Similarity"],
                        scheme["Quintile"],
                    ),
                )
            conn.commit()
        except sqlite3.IntegrityError as err:
            print(f"Error inserting query records: {err}")
        finally:
            return


def read_query_records(query_id: str) -> dict | None:
    """
    Read query records from SQLite DB
    """

    with get_db() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, scheme, agency, description, link, similarity
                FROM Schemes_rec
                where query_id = ?
                ORDER BY id ASC
                """,
                (query_id,),
            )
            results = cursor.fetchall()
            return [
                {
                    "Scheme": result[1],
                    "Agency": result[2],
                    "Description": result[3],
                    "Link": result[4],
                    "Similarity": result[5],
                }
                for result in results
            ]
        except sqlite3.IntegrityError as err:
            print(f"Error fetching query records: {err}")
            return
