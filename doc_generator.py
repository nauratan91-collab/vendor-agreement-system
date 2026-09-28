import os
import json
import subprocess
from datetime import datetime
from docxtpl import DocxTemplate
from num2words import num2words
from database import get_db_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_templates")
UPLOADED_DIR = os.path.join(BASE_DIR, "uploaded_templates")
GENERATED_DIR = os.path.join(BASE_DIR, "generated_docs")

os.makedirs(UPLOADED_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

def format_inr(amount):
    """Formats number to Indian currency format: 3,00,000 or 1,500"""
    try:
        val = float(amount)
        if val.is_integer():
            s = str(int(val))
        else:
            s = f"{val:.2f}"
            
        parts = s.split('.')
        integer_part = parts[0]
        
        if len(integer_part) > 3:
            last3 = integer_part[-3:]
            rest = integer_part[:-3]
            # Group in 2s
            groups = []
            while len(rest) > 2:
                groups.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.insert(0, rest)
            formatted = ",".join(groups) + "," + last3
        else:
            formatted = integer_part
            
        if len(parts) > 1 and parts[1] != '00':
            formatted += "." + parts[1]
        return formatted
    except Exception:
        return str(amount)

def format_rate_string(amount, unit, gst_type):
    """Generates standard legal rate string and amount in words"""
    try:
        amount_num = float(amount)
    except (ValueError, TypeError):
        amount_num = 0.0

    inr_formatted = format_inr(amount_num)
    
    # Unit display
    unit_map = {
        'per_month': 'per month',
        'per_hour': 'per hour',
        'per_day': 'per day',
        'fixed': 'fixed lump sum'
    }
    unit_str = unit_map.get(unit, unit)
    
    # GST display
    gst_map = {
        'plus_gst': '+ GST as applicable',
        'inclusive_gst': '(Inclusive of GST)',
        'exempt': '(GST Exempt / Nil)'
    }
    gst_str = gst_map.get(gst_type, '+ GST as applicable')
    
    rate_formatted = f"INR {inr_formatted}/- {unit_str} {gst_str}"
    
    # Words
    try:
        words = num2words(int(amount_num), lang='en_IN').replace(',', '').title()
        rate_in_words = f"Rupees {words} Only {unit_str}"
        if gst_type == 'plus_gst':
            rate_in_words += " plus applicable GST"
        elif gst_type == 'inclusive_gst':
            rate_in_words += " inclusive of GST"
    except Exception:
        rate_in_words = rate_formatted

    return rate_formatted, rate_in_words

def get_template_path(template_key):
    """Returns custom template path if uploaded, otherwise returns sample template path"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM document_templates WHERE template_key = ? AND is_custom = 1", (template_key,))
    row = cursor.fetchone()
    conn.close()

    if row and row['file_path'] and os.path.exists(row['file_path']):
        return row['file_path']

    # Fallback to default sample template
    default_name = f"{template_key}_template.docx"
    sample_path = os.path.join(SAMPLE_DIR, default_name)
    if os.path.exists(sample_path):
        return sample_path
    
    raise FileNotFoundError(f"Template for {template_key} not found at {sample_path}")

def convert_docx_to_pdf_winword(docx_path, pdf_path):
    """Converts DOCX to PDF using installed MS Word via PowerShell COM automation"""
    try:
        ps_script = f"""
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        try {{
            $doc = $word.Documents.Open('{docx_path.replace("'", "''")}')
            $doc.SaveAs([ref]'{pdf_path.replace("'", "''")}', [ref]17)
            $doc.Close([ref]0)
        }} finally {{
            $word.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
        }}
        """
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=30)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            return True
        return False
    except Exception as e:
        print(f"PDF conversion error: {e}")
        return False

def generate_document_from_template(doc_type, vendor_data, sow_data=None, custom_notes=None):
    """
    Renders DOCX document and saves generated file.
    doc_type: 'c2c_nda', 'c2c_msa', 'c2c_sow', 'consultant_nda', 'consultant_msa'
    """
    template_path = get_template_path(doc_type)
    doc = DocxTemplate(template_path)
    
    today = datetime.now().strftime("%d-%m-%Y")
    today_formal = datetime.now().strftime("%B %d, %Y")
    
    # Commercials
    rate_amt = vendor_data.get('rate_amount') or 0
    rate_u = vendor_data.get('rate_unit') or 'per_month'
    gst_t = vendor_data.get('gst_type') or 'plus_gst'
    
    if sow_data:
        rate_amt = sow_data.get('rate_amount') or rate_amt
        rate_u = sow_data.get('rate_unit') or rate_u
        gst_t = sow_data.get('gst_type') or gst_t
        
    rate_formatted, rate_in_words = format_rate_string(rate_amt, rate_u, gst_t)

    # Base context
    context = {
        'date': today,
        'effective_date': today_formal,
        'current_date': today,
        'vendor_code': vendor_data.get('vendor_code', ''),
        'company_name': vendor_data.get('company_name', ''),
        'company_address': vendor_data.get('company_address', ''),
        'company_gst': vendor_data.get('company_gst', 'N/A'),
        'company_pan': vendor_data.get('company_pan', 'N/A'),
        'company_cin': vendor_data.get('company_cin', 'N/A'),
        'signatory_name': vendor_data.get('signatory_name', 'Authorized Signatory'),
        'signatory_designation': vendor_data.get('signatory_designation', 'Director / Manager'),
        
        # Consultant fields
        'consultant_name': vendor_data.get('consultant_name', ''),
        'aadhar_no': vendor_data.get('aadhar_no', 'N/A'),
        'residential_address': vendor_data.get('residential_address', vendor_data.get('company_address', '')),
        'consultant_pan': vendor_data.get('consultant_pan', 'N/A'),
        
        # Contacts
        'contact_email': vendor_data.get('contact_email', ''),
        'contact_phone': vendor_data.get('contact_phone', ''),
        
        # Financials
        'rate_amount': rate_amt,
        'rate_unit': rate_u,
        'rate_formatted': rate_formatted,
        'rate_in_words': rate_in_words,
        'payment_terms': vendor_data.get('payment_terms', 'Net 30 Days'),
        'special_terms': custom_notes or vendor_data.get('special_terms', '')
    }

    # If SOW data exists
    if sow_data:
        context.update({
            'sow_code': sow_data.get('sow_code', ''),
            'candidate_name': sow_data.get('candidate_name', ''),
            'role_designation': sow_data.get('role_designation', ''),
            'client_name': sow_data.get('client_name', ''),
            'project_name': sow_data.get('project_name', ''),
            'start_date': sow_data.get('start_date', today),
            'duration': sow_data.get('duration', '6 Months'),
            'work_location': sow_data.get('work_location', 'Remote'),
            'notice_period': sow_data.get('notice_period', '15 Days'),
            'payment_terms': sow_data.get('payment_terms', context['payment_terms'])
        })

    # Unpack custom fields (JSON dict)
    custom_fields_raw = vendor_data.get('custom_fields')
    if custom_fields_raw:
        try:
            if isinstance(custom_fields_raw, str):
                c_dict = json.loads(custom_fields_raw)
            elif isinstance(custom_fields_raw, dict):
                c_dict = custom_fields_raw
            else:
                c_dict = {}
            for k, v in c_dict.items():
                context[k] = v
                context[k.lower()] = v
                context[k.replace(' ', '_').lower()] = v
        except Exception:
            pass

    # Render docxtpl
    doc.render(context)
    
    # Save output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_code = (vendor_data.get('vendor_code') or 'VND').replace('/', '_')
    if sow_data:
        file_prefix = f"{sow_data.get('sow_code')}_{clean_code}"
    else:
        file_prefix = f"{doc_type.upper()}_{clean_code}_{timestamp}"
        
    docx_filename = f"{file_prefix}.docx"
    pdf_filename = f"{file_prefix}.pdf"
    
    docx_path = os.path.join(GENERATED_DIR, docx_filename)
    pdf_path = os.path.join(GENERATED_DIR, pdf_filename)
    
    doc.save(docx_path)
    
    # Attempt PDF generation
    pdf_success = convert_docx_to_pdf_winword(docx_path, pdf_path)
    final_pdf_path = pdf_path if pdf_success else None
    
    # Save to generated_documents in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    recipient = vendor_data.get('company_name') if vendor_data.get('vendor_type') == 'c2c' else vendor_data.get('consultant_name')
    if sow_data:
        recipient = f"{recipient} (Candidate: {sow_data.get('candidate_name')})"

    cursor.execute("""
    INSERT INTO generated_documents (doc_code, doc_type, vendor_id, sow_id, recipient_name, file_path_docx, file_path_pdf)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        file_prefix,
        doc_type,
        vendor_data.get('id', 0),
        sow_data.get('id') if sow_data else None,
        recipient or 'Unknown',
        docx_path,
        final_pdf_path
    ))
    conn.commit()
    conn.close()

    return {
        'docx_filename': docx_filename,
        'docx_path': docx_path,
        'pdf_filename': pdf_filename if pdf_success else None,
        'pdf_path': final_pdf_path,
        'doc_code': file_prefix,
        'context': context
    }
