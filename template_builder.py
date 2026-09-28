import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{margin_name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_base_document(title, subtitle):
    doc = Document()
    
    # Page setup - 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    # Header Title
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_header.add_run(title.upper())
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(30, 41, 59)
    
    if subtitle:
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_sub = p_sub.add_run(subtitle)
        run_sub.font.name = 'Arial'
        run_sub.font.size = Pt(11)
        run_sub.font.italic = True
        run_sub.font.color.rgb = RGBColor(100, 116, 139)
        
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_after = Pt(10)
    
    return doc

def build_c2c_nda(output_path):
    doc = create_base_document("MUTUAL NON-DISCLOSURE AGREEMENT", "(Company to Company)")
    
    p = doc.add_paragraph()
    p.add_run("This Mutual Non-Disclosure Agreement (\"Agreement\") is entered into on this ").font.name = 'Arial'
    r_date = p.add_run("{{ date }}")
    r_date.bold = True
    p.add_run(" (\"Effective Date\"), by and between:\n\n").font.name = 'Arial'
    
    # First Party
    p1 = doc.add_paragraph()
    r1 = p1.add_run("THE COMPANY: ")
    r1.bold = True
    p1.add_run("A company incorporated under the Companies Act, having its principal office at India (hereinafter referred to as the \"First Party\" or \"Disclosing Party\").\n\n").font.name = 'Arial'
    
    # Second Party
    p2 = doc.add_paragraph()
    r2 = p2.add_run("AND\n\nTHE VENDOR: ")
    r2.bold = True
    r_cname = p2.add_run("{{ company_name }}")
    r_cname.bold = True
    p2.add_run(", having its principal place of business at ")
    p2.add_run("{{ company_address }}").bold = True
    p2.add_run(", with GSTIN: ")
    p2.add_run("{{ company_gst }}").bold = True
    p2.add_run(" and Registered Vendor Code: ")
    p2.add_run("{{ vendor_code }}").bold = True
    p2.add_run(" (hereinafter referred to as the \"Second Party\" or \"Receiving Party\").\n").font.name = 'Arial'
    
    # Meta box table
    table = doc.add_table(rows=4, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Vendor Reference Code", "{{ vendor_code }}"),
        ("Company Name", "{{ company_name }}"),
        ("GSTIN", "{{ company_gst }}"),
        ("Principal Address", "{{ company_address }}")
    ]
    for i, (label, val) in enumerate(meta_info):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_background(c0, "F1F5F9")
        set_cell_margins(c0, 80, 80, 120, 120)
        set_cell_margins(c1, 80, 80, 120, 120)
        
        r_lbl = c0.paragraphs[0].add_run(label)
        r_lbl.bold = True
        r_lbl.font.size = Pt(9.5)
        r_val = c1.paragraphs[0].add_run(val)
        r_val.font.size = Pt(9.5)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Recitals & Clauses
    clauses = [
        ("1. Purpose", "The Parties intend to explore and engage in mutual business discussions, recruitment/staffing services, software consulting, and related commercial opportunities (\"Purpose\"). In connection with the Purpose, each party may disclose to the other certain proprietary and non-public information."),
        ("2. Definition of Confidential Information", "\"Confidential Information\" means any and all non-public, proprietary information disclosed by either Party to the other, whether disclosed orally, visually, in writing, or electronically, including candidate resumes, client identities, commercial rates, source code, workflows, business strategies, and technical architectures."),
        ("3. Non-Disclosure Obligations", "The Receiving Party agrees to: (a) hold Confidential Information in strict confidence using the same degree of care it uses for its own confidential info, but not less than reasonable care; (b) restrict disclosure only to employees, contractors, and legal advisors on a strict need-to-know basis; (c) not disclose, duplicate, or distribute any information to any third party without prior written consent."),
        ("4. Commercial Terms & Non-Circumvention", "Both parties agree not to directly or indirectly solicit, contract with, or bypass the other party in dealing with candidates, clients, or projects introduced pursuant to this Agreement."),
        ("5. Term & Termination", "This Agreement shall remain in effect for a period of two (2) years from the Effective Date. The confidentiality obligations regarding trade secrets shall survive indefinitely."),
        ("6. Governing Law & Dispute Resolution", "This Agreement shall be governed by and construed in accordance with the laws of India. Any disputes arising out of this Agreement shall be subject to the exclusive jurisdiction of the competent courts in India.")
    ]
    
    for title_txt, body_txt in clauses:
        p_c = doc.add_paragraph()
        r_h = p_c.add_run(title_txt + "\n")
        r_h.bold = True
        r_h.font.size = Pt(11)
        r_h.font.color.rgb = RGBColor(15, 23, 42)
        r_b = p_c.add_run(body_txt)
        r_b.font.size = Pt(10)
        p_c.paragraph_format.space_after = Pt(8)
        
    # Signatures Table
    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    sig_p = doc.add_paragraph()
    sig_p.add_run("IN WITNESS WHEREOF, the Parties have executed this Agreement by their duly authorized representatives:").bold = True
    
    sig_table = doc.add_table(rows=5, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = [("For FIRST PARTY", "For SECOND PARTY: {{ company_name }}")]
    c0 = sig_table.rows[0].cells[0]
    c1 = sig_table.rows[0].cells[1]
    c0.paragraphs[0].add_run("For: FIRST PARTY (The Company)").bold = True
    c1.paragraphs[0].add_run("For: {{ company_name }}").bold = True
    
    sig_table.rows[1].cells[0].paragraphs[0].add_run("Signature: _______________________")
    sig_table.rows[1].cells[1].paragraphs[0].add_run("Signature: _______________________")
    
    sig_table.rows[2].cells[0].paragraphs[0].add_run("Name: Authorized Signatory")
    sig_table.rows[2].cells[1].paragraphs[0].add_run("Name: {{ signatory_name }}")
    
    sig_table.rows[3].cells[0].paragraphs[0].add_run("Designation: Director / Manager")
    sig_table.rows[3].cells[1].paragraphs[0].add_run("Designation: {{ signatory_designation }}")
    
    sig_table.rows[4].cells[0].paragraphs[0].add_run("Date: {{ date }}")
    sig_table.rows[4].cells[1].paragraphs[0].add_run("Date: {{ date }}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)

def build_c2c_msa(output_path):
    doc = create_base_document("MASTER SERVICES AGREEMENT", "(Company to Company / B2B)")
    
    p = doc.add_paragraph()
    p.add_run("This Master Services Agreement (\"Agreement\" or \"MSA\") is executed on this ").font.name = 'Arial'
    r_date = p.add_run("{{ date }}")
    r_date.bold = True
    p.add_run(" (\"Effective Date\") at India, by and between:\n\n").font.name = 'Arial'
    
    # Parties
    p1 = doc.add_paragraph()
    p1.add_run("THE SERVICE RECIPIENT: ").bold = True
    p1.add_run("A premier corporate organization incorporated under the laws of India (hereinafter \"Client\" / \"First Party\").\n\n")
    
    p2 = doc.add_paragraph()
    p2.add_run("AND\n\nTHE SERVICE PROVIDER / VENDOR: ").bold = True
    p2.add_run("{{ company_name }}").bold = True
    p2.add_run(", having its registered office at ")
    p2.add_run("{{ company_address }}").bold = True
    p2.add_run(", GSTIN: ")
    p2.add_run("{{ company_gst }}").bold = True
    p2.add_run(", Vendor Code: ")
    p2.add_run("{{ vendor_code }}").bold = True
    p2.add_run(" (hereinafter \"Vendor\" / \"Second Party\").\n")
    
    # Table Summary
    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Vendor Unique ID", "{{ vendor_code }}"),
        ("Registered Company Name", "{{ company_name }}"),
        ("GST Identification Number", "{{ company_gst }}"),
        ("Corporate Address", "{{ company_address }}"),
        ("Agreed Commercial Rate", "{{ rate_formatted }}"),
        ("Payment / Invoicing Terms", "{{ payment_terms }}")
    ]
    for i, (label, val) in enumerate(meta_info):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_background(c0, "F8FAFC")
        set_cell_margins(c0, 70, 70, 100, 100)
        set_cell_margins(c1, 70, 70, 100, 100)
        c0.paragraphs[0].add_run(label).bold = True
        c1.paragraphs[0].add_run(val)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    clauses = [
        ("1. Purpose & Scope of Services", "The Vendor shall provide IT consulting, technical staffing, software engineering, and recruitment services as set forth in individual Statements of Work (\"SOW\") signed by both parties from time to time. Each SOW shall form an integral part of this MSA."),
        ("2. Commercials & Billing Rates", "The agreed commercial consideration for the services rendered shall be as follows:\n- Agreed Rate: {{ rate_formatted }}\n- Commercials in Words: {{ rate_in_words }}\nAll billing shall strictly align with the executed SOWs for individual projects or resources."),
        ("3. Taxes & Invoicing", "Applicable Goods & Services Tax (GST) shall be charged extra in compliance with statutory Indian GST laws. All tax invoices submitted by Vendor must clearly reflect the Vendor Code ({{ vendor_code }}), Client details, and GSTIN ({{ company_gst }})."),
        ("4. Payment Terms", "Invoices shall be processed as per: {{ payment_terms }}. The Client reserves the right to withhold payments in the event of disputed timesheets or non-delivery until reconciled."),
        ("5. Statement of Work (SOW) & Resource Allocation", "For each candidate or resource deployed, a formal SOW specifying Candidate Name, Role, Billing Rate, Duration, and Project Scope shall be executed prior to deployment."),
        ("6. Confidentiality & Intellectual Property", "All work product, code, documentation, and IP created by Vendor or its deployed candidates shall be the sole and exclusive property of the Client (Work for Hire). Vendor shall strictly adhere to non-disclosure obligations."),
        ("7. Non-Solicitation & Non-Compete", "During the term of this Agreement and for a period of twelve (12) months thereafter, neither party shall solicit, hire, or engage the other party's employees or clients directly without written consent."),
        ("8. Termination & Notice Period", "Either party may terminate this Agreement or any SOW by giving thirty (30) days prior written notice, or immediately in the event of material breach.")
    ]
    
    for title_txt, body_txt in clauses:
        p_c = doc.add_paragraph()
        r_h = p_c.add_run(title_txt + "\n")
        r_h.bold = True
        r_h.font.size = Pt(11)
        r_h.font.color.rgb = RGBColor(15, 23, 42)
        r_b = p_c.add_run(body_txt)
        r_b.font.size = Pt(10)
        p_c.paragraph_format.space_after = Pt(8)
        
    # Signatures
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    sig_p = doc.add_paragraph()
    sig_p.add_run("IN WITNESS WHEREOF, the Parties hereto have caused this Master Services Agreement to be executed:").bold = True
    
    sig_table = doc.add_table(rows=5, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.rows[0].cells[0].paragraphs[0].add_run("For: FIRST PARTY (Client)").bold = True
    sig_table.rows[0].cells[1].paragraphs[0].add_run("For: {{ company_name }}").bold = True
    
    sig_table.rows[1].cells[0].paragraphs[0].add_run("Signature: _______________________")
    sig_table.rows[1].cells[1].paragraphs[0].add_run("Signature: _______________________")
    
    sig_table.rows[2].cells[0].paragraphs[0].add_run("Name: Authorized Signatory")
    sig_table.rows[2].cells[1].paragraphs[0].add_run("Name: {{ signatory_name }}")
    
    sig_table.rows[3].cells[0].paragraphs[0].add_run("Designation: Director")
    sig_table.rows[3].cells[1].paragraphs[0].add_run("Designation: {{ signatory_designation }}")
    
    sig_table.rows[4].cells[0].paragraphs[0].add_run("Date: {{ date }}")
    sig_table.rows[4].cells[1].paragraphs[0].add_run("Date: {{ date }}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)

def build_c2c_sow(output_path):
    doc = create_base_document("STATEMENT OF WORK (SOW)", "Candidate Deployment Schedule")
    
    p = doc.add_paragraph()
    p.add_run("This Statement of Work (\"SOW\") Reference No: ").font.name = 'Arial'
    p.add_run("{{ sow_code }}").bold = True
    p.add_run(" is executed on ")
    p.add_run("{{ date }}").bold = True
    p.add_run(", pursuant and subject to the Master Services Agreement executed between the parties.\n\n")
    
    p_intro = doc.add_paragraph()
    p_intro.add_run("Vendor Details: ").bold = True
    p_intro.add_run("{{ company_name }} (Vendor Code: {{ vendor_code }}, GSTIN: {{ company_gst }})\n")
    
    # Candidate SOW Table
    sow_table = doc.add_table(rows=10, cols=2)
    sow_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sow_fields = [
        ("SOW Reference Number", "{{ sow_code }}"),
        ("Vendor Company Name", "{{ company_name }} (Code: {{ vendor_code }})"),
        ("Selected Candidate Name", "{{ candidate_name }}"),
        ("Designation / Technical Role", "{{ role_designation }}"),
        ("Client / Project Name", "{{ client_name }} - {{ project_name }}"),
        ("Commercial Billing Rate", "{{ rate_formatted }}"),
        ("Deployment Start Date", "{{ start_date }}"),
        ("Estimated Duration", "{{ duration }}"),
        ("Work Location & Mode", "{{ work_location }}"),
        ("Notice Period for Release", "{{ notice_period }}")
    ]
    for i, (label, val) in enumerate(sow_fields):
        row = sow_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_background(c0, "F1F5F9")
        set_cell_margins(c0, 70, 70, 100, 100)
        set_cell_margins(c1, 70, 70, 100, 100)
        c0.paragraphs[0].add_run(label).bold = True
        c1.paragraphs[0].add_run(val)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    clauses = [
        ("1. Candidate Responsibilities & Performance", "The deployed Candidate ({{ candidate_name }}) shall provide full-time professional services as a {{ role_designation }}. The Candidate shall report to designated Client project managers and follow client coding/security standards."),
        ("2. Commercials & Invoicing", "Client shall pay Vendor at the agreed rate of {{ rate_formatted }}. Invoices shall be raised monthly accompanied by verified client timesheets or attendance reports."),
        ("3. Replacement Guarantee", "In the event the Candidate departs or performance is deemed unsatisfactory within the first 30 days, Vendor shall provide a suitable qualified replacement within 7 business days at no additional onboarding cost."),
        ("4. Statutory Compliance & Non-Solicitation", "Vendor guarantees full compliance with all labor laws, statutory dues, and PF/ESI where applicable. The non-solicitation clauses of the parent MSA apply strictly to this deployment.")
    ]
    for title_txt, body_txt in clauses:
        p_c = doc.add_paragraph()
        r_h = p_c.add_run(title_txt + "\n")
        r_h.bold = True
        r_h.font.size = Pt(10.5)
        r_b = p_c.add_run(body_txt)
        r_b.font.size = Pt(10)
        p_c.paragraph_format.space_after = Pt(8)
        
    # Signatures
    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    sig_table = doc.add_table(rows=4, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.rows[0].cells[0].paragraphs[0].add_run("Accepted by CLIENT").bold = True
    sig_table.rows[0].cells[1].paragraphs[0].add_run("Accepted by VENDOR: {{ company_name }}").bold = True
    
    sig_table.rows[1].cells[0].paragraphs[0].add_run("Signature: _______________________")
    sig_table.rows[1].cells[1].paragraphs[0].add_run("Signature: _______________________")
    
    sig_table.rows[2].cells[0].paragraphs[0].add_run("Name & Title: Authorized Signatory")
    sig_table.rows[2].cells[1].paragraphs[0].add_run("Name: {{ signatory_name }}")
    
    sig_table.rows[3].cells[0].paragraphs[0].add_run("Date: {{ date }}")
    sig_table.rows[3].cells[1].paragraphs[0].add_run("Date: {{ date }}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)

def build_consultant_nda(output_path):
    doc = create_base_document("NON-DISCLOSURE & CONFIDENTIALITY AGREEMENT", "(Company to Independent Consultant)")
    
    p = doc.add_paragraph()
    p.add_run("This Non-Disclosure Agreement (\"Agreement\") is made on this ").font.name = 'Arial'
    p.add_run("{{ date }}").bold = True
    p.add_run(" (\"Effective Date\"), by and between:\n\n")
    
    # First Party
    p1 = doc.add_paragraph()
    p1.add_run("THE COMPANY: ").bold = True
    p1.add_run("A company incorporated under the laws of India, having its office in India (hereinafter \"Company\").\n\n")
    
    # Second Party
    p2 = doc.add_paragraph()
    p2.add_run("AND\n\nTHE CONSULTANT: ").bold = True
    p2.add_run("{{ consultant_name }}").bold = True
    p2.add_run(", residing at ")
    p2.add_run("{{ residential_address }}").bold = True
    p2.add_run(", having Aadhaar Card No: ")
    p2.add_run("{{ aadhar_no }}").bold = True
    p2.add_run(", PAN No: ")
    p2.add_run("{{ consultant_pan }}").bold = True
    p2.add_run(", and Assigned Unique Code: ")
    p2.add_run("{{ vendor_code }}").bold = True
    p2.add_run(" (hereinafter \"Consultant\").\n")
    
    # Meta box table
    table = doc.add_table(rows=4, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Consultant Unique Code", "{{ vendor_code }}"),
        ("Consultant Full Name", "{{ consultant_name }}"),
        ("Aadhaar Card Number", "{{ aadhar_no }}"),
        ("Permanent / Residential Address", "{{ residential_address }}")
    ]
    for i, (label, val) in enumerate(meta_info):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_background(c0, "F1F5F9")
        set_cell_margins(c0, 70, 70, 100, 100)
        set_cell_margins(c1, 70, 70, 100, 100)
        c0.paragraphs[0].add_run(label).bold = True
        c1.paragraphs[0].add_run(val)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    clauses = [
        ("1. Purpose of Engagement", "The Company desires to retain the services of the Consultant, and in the course of such consultation, the Consultant will have access to confidential business records, proprietary software, customer databases, technical architectures, and financial data."),
        ("2. Strict Confidentiality", "The Consultant shall keep confidential and not disclose to any third party, directly or indirectly, any Confidential Information without the express prior written consent of the Company."),
        ("3. Intellectual Property Assignment", "All inventions, software code, designs, algorithms, and documentation developed by the Consultant during the period of engagement shall immediately belong to the Company as \"Work for Hire\"."),
        ("4. Return of Assets & Materials", "Upon termination of services or request by the Company, the Consultant shall promptly return all documents, laptops, access tokens, customer records, and copies thereof."),
        ("5. Term & Remedies", "The confidentiality obligations shall survive for a period of three (3) years from cessation of services. The Consultant acknowledges that breach causes irreparable harm entitling the Company to injunctive relief.")
    ]
    for title_txt, body_txt in clauses:
        p_c = doc.add_paragraph()
        r_h = p_c.add_run(title_txt + "\n")
        r_h.bold = True
        r_h.font.size = Pt(10.5)
        r_b = p_c.add_run(body_txt)
        r_b.font.size = Pt(10)
        p_c.paragraph_format.space_after = Pt(8)
        
    # Signatures
    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    sig_table = doc.add_table(rows=4, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.rows[0].cells[0].paragraphs[0].add_run("For: THE COMPANY").bold = True
    sig_table.rows[0].cells[1].paragraphs[0].add_run("THE CONSULTANT").bold = True
    
    sig_table.rows[1].cells[0].paragraphs[0].add_run("Signature: _______________________")
    sig_table.rows[1].cells[1].paragraphs[0].add_run("Signature: _______________________")
    
    sig_table.rows[2].cells[0].paragraphs[0].add_run("Name: Authorized Signatory")
    sig_table.rows[2].cells[1].paragraphs[0].add_run("Name: {{ consultant_name }}")
    
    sig_table.rows[3].cells[0].paragraphs[0].add_run("Date: {{ date }}")
    sig_table.rows[3].cells[1].paragraphs[0].add_run("Date: {{ date }}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)

def build_consultant_msa(output_path):
    doc = create_base_document("MASTER CONSULTING SERVICES AGREEMENT", "(Company to Independent Consultant)")
    
    p = doc.add_paragraph()
    p.add_run("This Master Consulting Services Agreement (\"Agreement\" or \"MSA\") is made on this ").font.name = 'Arial'
    p.add_run("{{ date }}").bold = True
    p.add_run(" (\"Effective Date\") by and between:\n\n")
    
    p1 = doc.add_paragraph()
    p1.add_run("THE COMPANY: ").bold = True
    p1.add_run("A company duly organized and operating under the laws of India (hereinafter \"Company\").\n\n")
    
    p2 = doc.add_paragraph()
    p2.add_run("AND\n\nTHE INDEPENDENT CONSULTANT: ").bold = True
    p2.add_run("{{ consultant_name }}").bold = True
    p2.add_run(", residing at ")
    p2.add_run("{{ residential_address }}").bold = True
    p2.add_run(", holding Aadhaar Card No: ")
    p2.add_run("{{ aadhar_no }}").bold = True
    p2.add_run(", PAN No: ")
    p2.add_run("{{ consultant_pan }}").bold = True
    p2.add_run(", Consultant Code: ")
    p2.add_run("{{ vendor_code }}").bold = True
    p2.add_run(" (hereinafter \"Consultant\").\n")
    
    # Table Summary
    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Consultant Unique Code", "{{ vendor_code }}"),
        ("Full Legal Name", "{{ consultant_name }}"),
        ("Aadhaar Card Number", "{{ aadhar_no }}"),
        ("Permanent Address", "{{ residential_address }}"),
        ("Consulting Fee / Rate", "{{ rate_formatted }}"),
        ("Payment & Invoicing Terms", "{{ payment_terms }}")
    ]
    for i, (label, val) in enumerate(meta_info):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_background(c0, "F8FAFC")
        set_cell_margins(c0, 70, 70, 100, 100)
        set_cell_margins(c1, 70, 70, 100, 100)
        c0.paragraphs[0].add_run(label).bold = True
        c1.paragraphs[0].add_run(val)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    clauses = [
        ("1. Nature of Services", "The Consultant shall render high-level professional consulting, technical advisory, and development services in according with project goals mutually agreed from time to time."),
        ("2. Professional Fees & Commercials", "The Company shall compensate the Consultant at the agreed rate of:\n- Agreed Rate: {{ rate_formatted }}\n- Commercials in Words: {{ rate_in_words }}\nPayment shall be disbursed as per: {{ payment_terms }} subject to statutory TDS deduction under Indian Income Tax Act."),
        ("3. Independent Contractor Relationship", "The Consultant acts strictly as an independent contractor and nothing herein creates an employer-employee, partnership, or agency relationship. The Consultant is solely responsible for their personal income tax, health insurance, and statutory filings."),
        ("4. Work Standards & Deliverables", "The Consultant agrees to perform all obligations with utmost professional diligence, adhering to delivery schedules, quality benchmarks, and ethical standards."),
        ("5. Termination", "Either party may terminate this Agreement without cause by giving fifteen (15) days prior written notice, or immediately for non-performance or ethical misconduct.")
    ]
    for title_txt, body_txt in clauses:
        p_c = doc.add_paragraph()
        r_h = p_c.add_run(title_txt + "\n")
        r_h.bold = True
        r_h.font.size = Pt(10.5)
        r_b = p_c.add_run(body_txt)
        r_b.font.size = Pt(10)
        p_c.paragraph_format.space_after = Pt(8)
        
    # Signatures
    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    sig_table = doc.add_table(rows=4, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.rows[0].cells[0].paragraphs[0].add_run("For: THE COMPANY").bold = True
    sig_table.rows[0].cells[1].paragraphs[0].add_run("THE CONSULTANT").bold = True
    
    sig_table.rows[1].cells[0].paragraphs[0].add_run("Signature: _______________________")
    sig_table.rows[1].cells[1].paragraphs[0].add_run("Signature: _______________________")
    
    sig_table.rows[2].cells[0].paragraphs[0].add_run("Name: Authorized Signatory")
    sig_table.rows[2].cells[1].paragraphs[0].add_run("Name: {{ consultant_name }}")
    
    sig_table.rows[3].cells[0].paragraphs[0].add_run("Date: {{ date }}")
    sig_table.rows[3].cells[1].paragraphs[0].add_run("Date: {{ date }}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)

def generate_all_sample_templates(base_dir):
    templates = {
        'c2c_nda': ('c2c_nda_template.docx', build_c2c_nda),
        'c2c_msa': ('c2c_msa_template.docx', build_c2c_msa),
        'c2c_sow': ('c2c_sow_template.docx', build_c2c_sow),
        'consultant_nda': ('consultant_nda_template.docx', build_consultant_nda),
        'consultant_msa': ('consultant_msa_template.docx', build_consultant_msa)
    }
    
    created = {}
    for key, (filename, builder_fn) in templates.items():
        file_path = os.path.join(base_dir, filename)
        builder_fn(file_path)
        created[key] = file_path
        print(f"Generated default template: {file_path}")
    return created

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(script_dir, "sample_templates")
    generate_all_sample_templates(sample_dir)
