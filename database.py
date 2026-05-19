import sqlite3
import os
from datetime import datetime

def get_db():
    """Verbindung zur Datenbank herstellen"""
    db = sqlite3.connect('data/school.db')
    db.row_factory = sqlite3.Row  # Ermöglicht Zugriff per Spaltennamen
    return db

def init_db():
    """Initialisiert alle Tabellen der Datenbank"""
    os.makedirs('data', exist_ok=True)
    db = get_db()
    
    # ====================== USERS ======================
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('developer', 'director', 'teacher', 'student')),
            full_name TEXT NOT NULL,
            class_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ====================== SCHOOL KEYS (für Director) ======================
    db.execute('''
        CREATE TABLE IF NOT EXISTS school_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            max_users INTEGER DEFAULT 1,
            for_role TEXT DEFAULT 'director',
            used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ====================== PERSON KEYS (Lehrer & Schüler) ======================
    db.execute('''
        CREATE TABLE IF NOT EXISTS person_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
            class_name TEXT,
            used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ====================== EVALUATIONS ======================
    db.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            semester TEXT NOT NULL,
            friendliness INTEGER NOT NULL CHECK(friendliness BETWEEN 0 AND 6),
            fairness INTEGER NOT NULL CHECK(fairness BETWEEN 0 AND 6),
            patience INTEGER NOT NULL CHECK(patience BETWEEN 0 AND 6),
            teaching_quality INTEGER NOT NULL CHECK(teaching_quality BETWEEN 0 AND 6),
            organization INTEGER NOT NULL CHECK(organization BETWEEN 0 AND 6),
            comment_f TEXT,
            comment_fa TEXT,
            comment_p TEXT,
            comment_t TEXT,
            comment_o TEXT,
            status TEXT DEFAULT 'approved',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(id),
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    ''')

    # ====================== BLOCKED EVALUATIONS ======================
    db.execute('''
        CREATE TABLE IF NOT EXISTS blocked_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_data TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ====================== SETTINGS (für Bewertungsphase) ======================
    db.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Standardwert: Bewertungsphase ist AUS
    db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('evaluation_active', 'false')")

    db.commit()
    print("✅ Datenbank erfolgreich initialisiert (mit allen Tabellen)")
    print("   • users, school_keys, person_keys, evaluations, blocked_evaluations, settings")

if __name__ == "__main__":
    init_db()