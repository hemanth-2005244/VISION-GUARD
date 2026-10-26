import sqlite3
import datetime
import os

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables for alert logs, registered persons, and metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Alerts Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    snapshot_path TEXT,
                    metadata TEXT
                )
            ''')

            # Registered Faces Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registered_faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_name TEXT UNIQUE NOT NULL,
                    role TEXT DEFAULT 'Staff',
                    created_at TEXT NOT NULL,
                    samples_count INTEGER DEFAULT 0
                )
            ''')

            # Daily Stats Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_intrusions INTEGER DEFAULT 0,
                    unknown_faces INTEGER DEFAULT 0,
                    drowsiness_alerts INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def log_alert(self, alert_type, severity, message, snapshot_path=None, metadata=""):
        """Log a new alert event into the database."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (timestamp, alert_type, severity, message, snapshot_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, alert_type, severity, message, snapshot_path, str(metadata)))
            conn.commit()

            # Update daily stat
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor.execute('INSERT OR IGNORE INTO system_stats (date) VALUES (?)', (today,))
            
            if alert_type == 'Intrusion':
                cursor.execute('UPDATE system_stats SET total_intrusions = total_intrusions + 1 WHERE date = ?', (today,))
            elif alert_type == 'Unknown Face':
                cursor.execute('UPDATE system_stats SET unknown_faces = unknown_faces + 1 WHERE date = ?', (today,))
            elif alert_type == 'Drowsiness':
                cursor.execute('UPDATE system_stats SET drowsiness_alerts = drowsiness_alerts + 1 WHERE date = ?', (today,))
            conn.commit()

    def get_recent_alerts(self, limit=50):
        """Retrieve recent alerts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM alerts ORDER BY id DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_alerts(self):
        """Clear all alerts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM alerts')
            conn.commit()

    def register_person(self, name, role='Staff', samples_count=0):
        """Add or update a registered face profile."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO registered_faces (person_name, role, created_at, samples_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(person_name) DO UPDATE SET samples_count=excluded.samples_count
            ''', (name, role, now, samples_count))
            conn.commit()

    def get_registered_persons(self):
        """List all registered persons."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM registered_faces ORDER BY id ASC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_summary_stats(self):
        """Get total stats for analytics dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as total FROM alerts')
            total_alerts = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as intrusions FROM alerts WHERE alert_type = 'Intrusion'")
            intrusions = cursor.fetchone()['intrusions']

            cursor.execute("SELECT COUNT(*) as unknown FROM alerts WHERE alert_type = 'Unknown Face'")
            unknown = cursor.fetchone()['unknown']

            cursor.execute("SELECT COUNT(*) as drowsiness FROM alerts WHERE alert_type = 'Drowsiness'")
            drowsiness = cursor.fetchone()['drowsiness']

            cursor.execute('SELECT COUNT(*) as persons FROM registered_faces')
            persons = cursor.fetchone()['persons']

            return {
                "total_alerts": total_alerts,
                "intrusions": intrusions,
                "unknown_faces": unknown,
                "drowsiness_alerts": drowsiness,
                "registered_persons": persons
            }
