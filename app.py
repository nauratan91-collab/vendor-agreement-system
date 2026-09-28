import os
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, jsonify, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    init_db, get_db_connection, generate_vendor_code, generate_sow_code
)
from doc_generator import (
    generate_document_from_template, format_rate_string, format_inr,
    UPLOADED_DIR, GENERATED_DIR, SAMPLE_DIR
)
from template_builder import generate_all_sample_templates

app = Flask(__name__)
app.secret_key = "super_secure_vendor_agreement_system_secret_key_2026"
app.config['UPLOAD_FOLDER'] = UPLOADED_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload

# Initialize database and default templates on startup
init_db()
generate_all_sample_templates(SAMPLE_DIR)

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Kripya pehle login karein.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- AUTH ROUTES -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f"Swagat hai, {user['full_name']}!", "success")
            next_url = request.args.get('next') or url_for('dashboard')
            return redirect(next_url)
        else:
            flash("Galat Username ya Password! Kripya dobara koshish karein.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Aap safaltapoorvak logout ho gaye hain.", "info")
    return redirect(url_for('login'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_pwd = request.form.get('current_password')
    new_pwd = request.form.get('new_password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if user and check_password_hash(user['password_hash'], current_pwd):
        hashed = generate_password_hash(new_pwd)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, session['user_id']))
        conn.commit()
        conn.close()
        flash("Password safaltapoorvak badal diya gaya hai!", "success")
    else:
        conn.close()
        flash("Current password galat hai!", "danger")
    return redirect(url_for('dashboard'))

# ----------------- DASHBOARD -----------------
@app.route('/')
@login_required
def dashboard():
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('type', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # KPI Metrics
    cursor.execute("SELECT COUNT(*) FROM vendors")
    total_vendors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vendors WHERE vendor_type = 'c2c'")
    c2c_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vendors WHERE vendor_type = 'consultant'")
    consultant_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates_sow")
    total_sows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM generated_documents")
    total_docs = cursor.fetchone()[0]

    # Vendor List Query
    query = "SELECT * FROM vendors WHERE 1=1"
    params = []

    if filter_type in ('c2c', 'consultant'):
        query += " AND vendor_type = ?"
        params.append(filter_type)

    if search:
        query += """ AND (
            vendor_code LIKE ? OR 
            company_name LIKE ? OR 
            consultant_name LIKE ? OR 
            company_gst LIKE ? OR 
            aadhar_no LIKE ?
        )"""
        p = f"%{search}%"
        params.extend([p, p, p, p, p])

    query += " ORDER BY id DESC LIMIT 50"
    cursor.execute(query, params)
    vendors = cursor.fetchall()

    # Recent Generated Documents
    cursor.execute("""
    SELECT g.*, v.vendor_code, v.vendor_type
    FROM generated_documents g
    LEFT JOIN vendors v ON g.vendor_id = v.id
    ORDER BY g.id DESC LIMIT 10
    """)
    recent_docs = cursor.fetchall()

    conn.close()

    return render_template(
        'index.html',
        total_vendors=total_vendors,
        c2c_count=c2c_count,
        consultant_count=consultant_count,
        total_sows=total_sows,
        total_docs=total_docs,
        vendors=vendors,
        recent_docs=recent_docs,
        search=search,
        filter_type=filter_type
    )

# ----------------- VENDOR REGISTRATION & EDIT -----------------
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register_vendor():
    if request.method == 'POST':
        vendor_type = request.form.get('vendor_type', 'c2c')
        vendor_code = generate_vendor_code(vendor_type)
        
        # C2C fields
        company_name = request.form.get('company_name', '').strip()
        company_address = request.form.get('company_address', '').strip()
        company_gst = request.form.get('company_gst', '').strip().upper()
        company_pan = request.form.get('company_pan', '').strip().upper()
        company_cin = request.form.get('company_cin', '').strip().upper()
        signatory_name = request.form.get('signatory_name', '').strip()
        signatory_designation = request.form.get('signatory_designation', '').strip()

        # Consultant fields
        consultant_name = request.form.get('consultant_name', '').strip()
        aadhar_no = request.form.get('aadhar_no', '').strip()
        residential_address = request.form.get('residential_address', '').strip()
        consultant_pan = request.form.get('consultant_pan', '').strip().upper()

        # Common contacts
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        # Commercials
        try:
            rate_amount = float(request.form.get('rate_amount') or 0)
        except ValueError:
            rate_amount = 0.0
            
        rate_unit = request.form.get('rate_unit', 'per_month')
        gst_type = request.form.get('gst_type', 'plus_gst')
        payment_terms = request.form.get('payment_terms', 'Net 30 Days from invoice submission')
        
        rate_formatted, rate_in_words = format_rate_string(rate_amount, rate_unit, gst_type)

        # Dynamic Custom Fields (User requirement: "agar kuch add karna ho to")
        custom_keys = request.form.getlist('custom_key[]')
        custom_values = request.form.getlist('custom_val[]')
        custom_dict = {}
        for k, v in zip(custom_keys, custom_values):
            k_clean = k.strip()
            if k_clean:
                custom_dict[k_clean] = v.strip()
        custom_fields_json = json.dumps(custom_dict)
        
        special_terms = request.form.get('special_terms', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO vendors (
            vendor_code, vendor_type,
            company_name, company_address, company_gst, company_pan, company_cin,
            signatory_name, signatory_designation,
            consultant_name, aadhar_no, residential_address, consultant_pan,
            contact_email, contact_phone,
            rate_amount, rate_unit, gst_type, rate_formatted, payment_terms,
            custom_fields, special_terms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vendor_code, vendor_type,
            company_name, company_address, company_gst, company_pan, company_cin,
            signatory_name, signatory_designation,
            consultant_name, aadhar_no, residential_address, consultant_pan,
            contact_email, contact_phone,
            rate_amount, rate_unit, gst_type, rate_formatted, payment_terms,
            custom_fields_json, special_terms
        ))
        vendor_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Auto-generation checkbox check
        auto_generate = request.form.get('auto_generate_docs')
        if auto_generate:
            conn = get_db_connection()
            v_row = conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
            conn.close()
            v_dict = dict(v_row)
            
            nda_type = 'c2c_nda' if vendor_type == 'c2c' else 'consultant_nda'
            msa_type = 'c2c_msa' if vendor_type == 'c2c' else 'consultant_msa'
            try:
                generate_document_from_template(nda_type, v_dict)
                generate_document_from_template(msa_type, v_dict)
                flash(f"Vendor '{vendor_code}' safalta-purvak register ho gaya aur NDA tatha MSA generate ho gaye!", "success")
            except Exception as e:
                flash(f"Vendor registered ({vendor_code}), par document generate karne me error aaya: {str(e)}", "warning")
        else:
            flash(f"Vendor safalta-purvak register ho gaya! Unique Code: {vendor_code}", "success")

        return redirect(url_for('view_vendor', vendor_id=vendor_id))

    return render_template('register.html')

@app.route('/vendor/<int:vendor_id>')
@login_required
def view_vendor(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
    vendor = cursor.fetchone()

    if not vendor:
        conn.close()
        flash("Vendor nahi mila!", "danger")
        return redirect(url_for('dashboard'))

    # SOWs if C2C
    cursor.execute("SELECT * FROM candidates_sow WHERE vendor_id = ? ORDER BY id DESC", (vendor_id,))
    sows = cursor.fetchall()

    # Generated documents for this vendor
    cursor.execute("SELECT * FROM generated_documents WHERE vendor_id = ? ORDER BY id DESC", (vendor_id,))
    docs = cursor.fetchall()

    conn.close()

    # Parse custom fields
    try:
        custom_fields = json.loads(vendor['custom_fields']) if vendor['custom_fields'] else {}
    except Exception:
        custom_fields = {}

    return render_template(
        'view_vendor.html',
        vendor=vendor,
        sows=sows,
        docs=docs,
        custom_fields=custom_fields
    )

@app.route('/vendor/<int:vendor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vendor(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
    vendor = cursor.fetchone()

    if not vendor:
        conn.close()
        flash("Vendor nahi mila!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        company_address = request.form.get('company_address', '').strip()
        company_gst = request.form.get('company_gst', '').strip().upper()
        company_pan = request.form.get('company_pan', '').strip().upper()
        signatory_name = request.form.get('signatory_name', '').strip()
        signatory_designation = request.form.get('signatory_designation', '').strip()

        consultant_name = request.form.get('consultant_name', '').strip()
        aadhar_no = request.form.get('aadhar_no', '').strip()
        residential_address = request.form.get('residential_address', '').strip()
        consultant_pan = request.form.get('consultant_pan', '').strip().upper()

        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        try:
            rate_amount = float(request.form.get('rate_amount') or 0)
        except ValueError:
            rate_amount = 0.0

        rate_unit = request.form.get('rate_unit', 'per_month')
        gst_type = request.form.get('gst_type', 'plus_gst')
        payment_terms = request.form.get('payment_terms', 'Net 30 Days')
        rate_formatted, rate_in_words = format_rate_string(rate_amount, rate_unit, gst_type)

        custom_keys = request.form.getlist('custom_key[]')
        custom_values = request.form.getlist('custom_val[]')
        custom_dict = {}
        for k, v in zip(custom_keys, custom_values):
            k_clean = k.strip()
            if k_clean:
                custom_dict[k_clean] = v.strip()
        custom_fields_json = json.dumps(custom_dict)
        special_terms = request.form.get('special_terms', '').strip()

        cursor.execute("""
        UPDATE vendors SET
            company_name = ?, company_address = ?, company_gst = ?, company_pan = ?,
            signatory_name = ?, signatory_designation = ?,
            consultant_name = ?, aadhar_no = ?, residential_address = ?, consultant_pan = ?,
            contact_email = ?, contact_phone = ?,
            rate_amount = ?, rate_unit = ?, gst_type = ?, rate_formatted = ?, payment_terms = ?,
            custom_fields = ?, special_terms = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (
            company_name, company_address, company_gst, company_pan,
            signatory_name, signatory_designation,
            consultant_name, aadhar_no, residential_address, consultant_pan,
            contact_email, contact_phone,
            rate_amount, rate_unit, gst_type, rate_formatted, payment_terms,
            custom_fields_json, special_terms, vendor_id
        ))
        conn.commit()
        conn.close()
        flash("Vendor details safaltapoorvak update ho gayi!", "success")
        return redirect(url_for('view_vendor', vendor_id=vendor_id))

    conn.close()
    try:
        custom_fields = json.loads(vendor['custom_fields']) if vendor['custom_fields'] else {}
    except Exception:
        custom_fields = {}
    return render_template('edit_vendor.html', vendor=vendor, custom_fields=custom_fields)

# ----------------- CANDIDATE SOW GENERATION (C2C) -----------------
@app.route('/sow/create', methods=['GET', 'POST'])
@login_required
def create_sow():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        vendor_id = int(request.form.get('vendor_id'))
        candidate_name = request.form.get('candidate_name', '').strip()
        role_designation = request.form.get('role_designation', '').strip()
        client_name = request.form.get('client_name', '').strip()
        project_name = request.form.get('project_name', '').strip()
        
        try:
            rate_amount = float(request.form.get('rate_amount') or 0)
        except ValueError:
            rate_amount = 0.0

        rate_unit = request.form.get('rate_unit', 'per_hour')
        gst_type = request.form.get('gst_type', 'plus_gst')
        rate_formatted, _ = format_rate_string(rate_amount, rate_unit, gst_type)

        start_date = request.form.get('start_date', datetime.now().strftime("%d-%m-%Y"))
        duration = request.form.get('duration', '6 Months').strip()
        work_location = request.form.get('work_location', 'Remote / Client Location').strip()
        notice_period = request.form.get('notice_period', '15 Days').strip()
        payment_terms = request.form.get('payment_terms', 'Monthly billing against approved timesheets').strip()

        sow_code = generate_sow_code()

        cursor.execute("""
        INSERT INTO candidates_sow (
            sow_code, vendor_id, candidate_name, role_designation, client_name, project_name,
            rate_amount, rate_unit, gst_type, rate_formatted,
            start_date, duration, work_location, notice_period, payment_terms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sow_code, vendor_id, candidate_name, role_designation, client_name, project_name,
            rate_amount, rate_unit, gst_type, rate_formatted,
            start_date, duration, work_location, notice_period, payment_terms
        ))
        sow_id = cursor.lastrowid
        conn.commit()

        # Fetch vendor data to generate SOW document
        cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
        vendor_row = cursor.fetchone()
        cursor.execute("SELECT * FROM candidates_sow WHERE id = ?", (sow_id,))
        sow_row = cursor.fetchone()
        conn.close()

        try:
            doc_res = generate_document_from_template('c2c_sow', dict(vendor_row), dict(sow_row))
            flash(f"Candidate SOW ({sow_code}) safalta-purvak generate ho gaya!", "success")
        except Exception as e:
            flash(f"SOW record ban gaya par document file me error aaya: {str(e)}", "warning")

        return redirect(url_for('view_vendor', vendor_id=vendor_id))

    # Pre-selected vendor if coming from vendor profile
    preselect_vendor_id = request.args.get('vendor_id', type=int)
    cursor.execute("SELECT id, vendor_code, company_name, company_gst, rate_amount, rate_unit, gst_type FROM vendors WHERE vendor_type = 'c2c' ORDER BY company_name ASC")
    c2c_vendors = cursor.fetchall()
    conn.close()

    return render_template('sow_create.html', c2c_vendors=c2c_vendors, preselect_vendor_id=preselect_vendor_id)

# ----------------- DOCUMENT GENERATION ACTION -----------------
@app.route('/generate-agreement/<int:vendor_id>/<doc_type>')
@login_required
def generate_agreement(vendor_id, doc_type):
    """
    doc_type: 'c2c_nda', 'c2c_msa', 'consultant_nda', 'consultant_msa'
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
    vendor_row = cursor.fetchone()
    conn.close()

    if not vendor_row:
        flash("Vendor nahi mila!", "danger")
        return redirect(url_for('dashboard'))

    vendor_data = dict(vendor_row)

    try:
        res = generate_document_from_template(doc_type, vendor_data)
        flash(f"{doc_type.upper().replace('_', ' ')} safalta-purvak generate ho gaya! Aap niche se DOCX ya PDF download kar sakte hain.", "success")
    except Exception as e:
        flash(f"Document generation me error: {str(e)}", "danger")

    return redirect(url_for('view_vendor', vendor_id=vendor_id))

# ----------------- TEMPLATE MANAGER (UPLOAD USER FORMATS) -----------------
@app.route('/templates', methods=['GET', 'POST'])
@login_required
def template_manager():
    conn = get_db_connection()
    cursor = conn.cursor()

    template_defs = [
        {'key': 'c2c_nda', 'name': 'Company to Company - NDA', 'category': 'C2C', 'desc': 'Mutual Non-Disclosure Agreement for B2B Vendor'},
        {'key': 'c2c_msa', 'name': 'Company to Company - MSA', 'category': 'C2C', 'desc': 'Master Services Agreement with commercial rates & payment terms'},
        {'key': 'c2c_sow', 'name': 'Company to Company - SOW', 'category': 'C2C', 'desc': 'Statement of Work for deployed selected candidate'},
        {'key': 'consultant_nda', 'name': 'Company to Consultant - NDA', 'category': 'Consultant', 'desc': 'Confidentiality Agreement with Aadhaar & Address'},
        {'key': 'consultant_msa', 'name': 'Company to Consultant - MSA', 'category': 'Consultant', 'desc': 'Consulting Agreement with consultant fee (Hourly/Monthly) + GST'}
    ]

    if request.method == 'POST':
        template_key = request.form.get('template_key')
        action = request.form.get('action')

        if action == 'upload':
            file = request.files.get('template_file')
            if file and file.filename.endswith('.docx'):
                filename = secure_filename(f"{template_key}_{int(datetime.now().timestamp())}_{file.filename}")
                save_path = os.path.join(UPLOADED_DIR, filename)
                file.save(save_path)

                # Record in database
                cursor.execute("""
                INSERT INTO document_templates (template_key, title, category, file_name, file_path, is_custom, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(template_key) DO UPDATE SET
                    file_name = excluded.file_name,
                    file_path = excluded.file_path,
                    is_custom = 1,
                    updated_at = CURRENT_TIMESTAMP
                """, (template_key, template_key.upper(), 'Custom', filename, save_path))
                conn.commit()
                flash(f"Aapka custom template '{file.filename}' safalta-purvak upload ho gaya!", "success")
            else:
                flash("Kripya valid Word document (.docx) file chunein!", "danger")

        elif action == 'reset':
            cursor.execute("DELETE FROM document_templates WHERE template_key = ?", (template_key,))
            conn.commit()
            flash(f"Template '{template_key}' ko default standard template par reset kar diya gaya!", "info")

    # Fetch status of each template
    templates_status = []
    for td in template_defs:
        cursor.execute("SELECT * FROM document_templates WHERE template_key = ?", (td['key'],))
        row = cursor.fetchone()
        is_custom = bool(row and row['is_custom'] and os.path.exists(row['file_path']))
        templates_status.append({
            'key': td['key'],
            'name': td['name'],
            'category': td['category'],
            'desc': td['desc'],
            'is_custom': is_custom,
            'file_name': row['file_name'] if is_custom else f"{td['key']}_template.docx",
            'updated_at': row['updated_at'] if is_custom else "Built-in Standard"
        })

    conn.close()
    return render_template('template_manager.html', templates=templates_status)

@app.route('/download-base-template/<template_key>')
@login_required
def download_base_template(template_key):
    """Allows user to download our clean pre-formatted Word template to edit in MS Word"""
    filename = f"{template_key}_template.docx"
    path = os.path.join(SAMPLE_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=filename)
    flash("Base template file nahi mili.", "danger")
    return redirect(url_for('template_manager'))

# ----------------- FILE DOWNLOAD ROUTE -----------------
@app.route('/download-doc/<file_type>/<filename>')
@login_required
def download_doc(file_type, filename):
    """
    file_type: 'docx' or 'pdf'
    """
    safe_name = secure_filename(filename)
    path = os.path.join(GENERATED_DIR, safe_name)
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=safe_name)
    abort(404, description="File nahi mili")

# ----------------- HELPER API FOR REALTIME RATE PREVIEW -----------------
@app.route('/api/format-rate', methods=['POST'])
@login_required
def api_format_rate():
    data = request.get_json() or {}
    amount = data.get('amount', 0)
    unit = data.get('unit', 'per_month')
    gst_type = data.get('gst_type', 'plus_gst')
    formatted, in_words = format_rate_string(amount, unit, gst_type)
    return jsonify({
        'formatted': formatted,
        'in_words': in_words
    })

if __name__ == '__main__':
    print("Starting Vendor Registration & Agreement Management System on http://127.0.0.1:8000 ...")
    app.run(host='127.0.0.1', port=8000, debug=False)
