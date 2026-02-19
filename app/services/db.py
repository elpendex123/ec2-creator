import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.config import settings


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = settings.DB_PATH
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create data directory and initialize database if needed."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            Path(db_dir).mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instances (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                public_ip TEXT,
                ami TEXT,
                instance_type TEXT,
                state TEXT,
                ssh_string TEXT,
                backend_used TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_instance_record(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new instance record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.utcnow()
        cursor.execute("""
            INSERT INTO instances (id, name, public_ip, ami, instance_type, state, ssh_string, backend_used, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            instance_data["id"],
            instance_data["name"],
            instance_data.get("public_ip", ""),
            instance_data.get("ami", ""),
            instance_data.get("instance_type", ""),
            instance_data.get("state", "pending"),
            instance_data.get("ssh_string", ""),
            instance_data.get("backend_used", ""),
            now,
            now,
        ))
        conn.commit()
        conn.close()
        return instance_data

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get a single instance by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM instances WHERE id = ?", (instance_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM instances ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_instance_state(self, instance_id: str, state: str, public_ip: str = None) -> Optional[Dict[str, Any]]:
        """Update instance state and optionally public IP."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.utcnow()
        if public_ip:
            cursor.execute("""
                UPDATE instances SET state = ?, public_ip = ?, updated_at = ? WHERE id = ?
            """, (state, public_ip, now, instance_id))
        else:
            cursor.execute("""
                UPDATE instances SET state = ?, updated_at = ? WHERE id = ?
            """, (state, now, instance_id))

        conn.commit()
        conn.close()

        return self.get_instance(instance_id)

    def delete_instance_record(self, instance_id: str) -> bool:
        """Delete an instance record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM instances WHERE id = ?", (instance_id,))
        conn.commit()
        conn.close()

        return True


# Global database instance
db = Database()
