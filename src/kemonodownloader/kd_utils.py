"""
Utility functions for Kemono Downloader
"""

import hashlib
import sqlite3
import os
import json
import threading


def hash_file_chunked(filepath, chunk_size=8192):
    """
    Hash a file in chunks to avoid loading entire file into memory.

    Args:
        filepath: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        MD5 hash hex string, or None on error
    """
    md5_hash = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception:
        return None


class HashStorage:
    """
    SQLite-based hash storage for efficient file hash management.

    Thread-safe storage for tracking downloaded files by their URL and content hash.
    """

    def __init__(self, db_path):
        """
        Initialize hash storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
        self._migrate_from_json()

    def _init_db(self):
        """Create database schema if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_hashes (
                    url_hash TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path
                ON file_hashes(file_path)
            """)
            conn.commit()

    def _migrate_from_json(self):
        """Migrate data from old JSON format if it exists."""
        json_path = os.path.join(os.path.dirname(self.db_path), "file_hashes.json")

        if not os.path.exists(json_path):
            return

        # Check if we already migrated
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM file_hashes")
            count = cursor.fetchone()[0]
            if count > 0:
                return  # Already has data, skip migration

        try:
            with open(json_path, 'r') as f:
                old_hashes = json.load(f)

            # Migrate to SQLite
            with sqlite3.connect(self.db_path) as conn:
                for url_hash, data in old_hashes.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO file_hashes
                        (url_hash, file_path, file_hash, url)
                        VALUES (?, ?, ?, ?)
                    """, (url_hash, data.get('file_path'), data.get('file_hash'), data.get('url')))
                conn.commit()

            # Backup old JSON file
            backup_path = json_path + ".backup"
            os.rename(json_path, backup_path)

        except Exception:
            pass  # Silently fail migration, not critical

    def get(self, url_hash):
        """
        Get hash data for a URL.

        Args:
            url_hash: MD5 hash of the URL

        Returns:
            Dict with file_path, file_hash, url or None if not found
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path, file_hash, url
                    FROM file_hashes
                    WHERE url_hash = ?
                """, (url_hash,))
                row = cursor.fetchone()

                if row:
                    return {
                        'file_path': row[0],
                        'file_hash': row[1],
                        'url': row[2]
                    }
                return None

    def set(self, url_hash, file_path, file_hash, url):
        """
        Store hash data for a URL.

        Args:
            url_hash: MD5 hash of the URL
            file_path: Path where file is stored
            file_hash: MD5 hash of file content
            url: Original download URL
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO file_hashes
                    (url_hash, file_path, file_hash, url)
                    VALUES (?, ?, ?, ?)
                """, (url_hash, file_path, file_hash, url))
                conn.commit()

    def get_all_keys(self):
        """
        Get all URL hashes.

        Returns:
            List of URL hash strings
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT url_hash FROM file_hashes")
                return [row[0] for row in cursor.fetchall()]

    def cleanup_missing_files(self):
        """
        Remove hash entries for files that no longer exist.

        Returns:
            Number of entries removed
        """
        removed = 0
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT url_hash, file_path FROM file_hashes")
                to_remove = []

                for url_hash, file_path in cursor.fetchall():
                    if not os.path.exists(file_path):
                        to_remove.append(url_hash)

                for url_hash in to_remove:
                    conn.execute("DELETE FROM file_hashes WHERE url_hash = ?", (url_hash,))
                    removed += 1

                conn.commit()

        return removed
