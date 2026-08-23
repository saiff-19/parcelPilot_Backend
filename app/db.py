import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'actions.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_actions (
            action_id TEXT PRIMARY KEY,
            user_id TEXT,
            action_type TEXT,
            payload TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def create_pending_action(action_id: str, user_id: str, action_type: str, payload: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO pending_actions (action_id, user_id, action_type, payload, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    ''', (action_id, user_id, action_type, json.dumps(payload)))
    conn.commit()
    conn.close()

def get_pending_action(action_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT action_type, payload, status FROM pending_actions WHERE action_id = ?', (action_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"action_type": row[0], "payload": json.loads(row[1]), "status": row[2]}
    return None

def update_action_status(action_id: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE pending_actions SET status = ? WHERE action_id = ?', (status, action_id))
    conn.commit()
    conn.close()
