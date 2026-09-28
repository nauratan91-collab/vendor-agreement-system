import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "agreements.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table for Login
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Vendors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_code TEXT UNIQUE NOT NULL,
        vendor_type TEXT NOT NULL, -- 'c2c' or 'consultant'
        
        -- C2C specific
        company_name TEXT,
        company_address TEXT,
        company_gst TEXT,
        company_pan TEXT,
        company_cin TEXT,
        signatory_name TEXT,
        signatory_designation TEXT,
        
        -- Consultant specific
        consultant_name TEXT,
        aadhar_no TEXT,
        residential_address TEXT,
        consultant_pan TEXT,
        
        -- Common Contact
        contact_email TEXT,
        contact_phone TEXT,
        
        -- Commercials / Rates
        rate_amount REAL DEFAULT 0,
        rate_unit TEXT DEFAULT 'per_month', -- 'per_month', 'per_hour', 'per_day', 'fixed'
        gst_type TEXT DEFAULT 'plus_gst',   -- 'plus_gst', 'inclusive_gst', 'exempt'
        rate_formatted TEXT,
        payment_terms TEXT DEFAULT 'Within 30 days of verified monthly invoice',
        
        -- Custom fields (JSON dict for extensible extra fields)
        custom_fields TEXT DEFAULT '{}',
        special_terms TEXT DEFAULT '',
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Candidates SOW Table (Company to Company candidate assignments)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates_sow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sow_code TEXT UNIQUE NOT NULL,
        vendor_id INTEGER NOT NULL,
        candidate_name TEXT NOT NULL,
        role_designation TEXT NOT NULL,
        client_name TEXT,
        project_name TEXT,
        
        -- Rates
        rate_amount REAL DEFAULT 0,
        rate_unit TEXT DEFAULT 'per_hour',
        gst_type TEXT DEFAULT 'plus_gst',
        rate_formatted TEXT,
        
        start_date TEXT,
        duration TEXT,
        work_location TEXT DEFAULT 'Remote / Client Location',
        notice_period TEXT DEFAULT '15 Days',
        payment_terms TEXT DEFAULT 'Monthly billing based on approved timesheets',
        
        custom_fields TEXT DEFAULT '{}',
        status TEXT DEFAULT 'Generated',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
    )
    """)

    # Template metadata table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_key TEXT UNIQUE NOT NULL, -- 'c2c_nda', 'c2c_msa', 'c2c_sow', 'consultant_nda', 'consultant_msa'
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        is_custom INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Generated Documents Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS generated_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_code TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        vendor_id INTEGER NOT NULL,
        sow_id INTEGER,
        recipient_name TEXT NOT NULL,
        file_path_docx TEXT NOT NULL,
        file_path_pdf TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
    )
    """)

    # Create default Admin if not exists (admin / admin123)
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed = generate_password_hash("admin123")
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES ('admin', ?, 'Administrator', 'admin')
        """, (hashed,))

    conn.commit()
    conn.close()

def generate_vendor_code(vendor_type):
    """Generates unique code like VND-C2C-2026-0001 or VND-CON-2026-0001"""
    conn = get_db_connection()
    cursor = conn.cursor()
    year = datetime.now().year
    prefix = "VND-C2C" if vendor_type == "c2c" else "VND-CON"
    search_prefix = f"{prefix}-{year}-%"

    cursor.execute("SELECT COUNT(*) FROM vendors WHERE vendor_code LIKE ?", (search_prefix,))
    count = cursor.fetchone()[0] + 1
    code = f"{prefix}-{year}-{count:04d}"
    
    # Ensure uniqueness in case of race condition or gaps
    while True:
        cursor.execute("SELECT id FROM vendors WHERE vendor_code = ?", (code,))
        if not cursor.fetchone():
            break
        count += 1
        code = f"{prefix}-{year}-{count:04d}"

    conn.close()
    return code

def generate_sow_code():
    """Generates unique SOW code like SOW-2026-0001"""
    conn = get_db_connection()
    cursor = conn.cursor()
    year = datetime.now().year
    search_prefix = f"SOW-{year}-%"

    cursor.execute("SELECT COUNT(*) FROM candidates_sow WHERE sow_code LIKE ?", (search_prefix,))
    count = cursor.fetchone()[0] + 1
    code = f"SOW-{year}-{count:04d}"

    while True:
        cursor.execute("SELECT id FROM candidates_sow WHERE sow_code = ?", (code,))
        if not cursor.fetchone():
            break
        count += 1
        code = f"SOW-{year}-{count:04d}"

    conn.close()
    return code
