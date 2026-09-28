# Vendor Registration & Agreement Management System (NDA, MSA & SOW)

A complete automated legal agreement generator and vendor onboarding portal built with **Python, Flask, docxtpl, and Bootstrap 5**.

---

## 🌟 Key Features

1. **Unique Code Generation**:
   - Automated prefix-based unique identifiers:
     - **B2B / C2C**: `VND-C2C-2026-0001`, `VND-C2C-2026-0002`...
     - **Consultant**: `VND-CON-2026-0001`, `VND-CON-2026-0002`...
     - **Candidate SOW**: `SOW-2026-0001`...

2. **Dual Registration Workflows**:
   - **Company to Company (B2B)**: Company Name, Corporate Address, GSTIN, Signatory Name & Designation, PAN, CIN, Email, Phone.
   - **Company to Consultant (Individual)**: Consultant Full Name, 12-digit Aadhaar Card Number, Residential Address, PAN Card, Mobile, Email.

3. **Commercials & Pricing Terms in MSA & SOW**:
   - Configurable billing frequencies:
     - `INR 3,00,000/- per month + GST as applicable`
     - `INR 1,500/- per hour + GST as applicable`
   - Auto-generated legal representation in words (e.g., *Rupees Three Lakh Only per month plus applicable GST*).

4. **Candidate Statement of Work (SOW)**:
   - For Company to Company vendor deployments:
     - Candidate Name, Designation / Technical Role, Client & Project Name.
     - Candidate-specific billing rate, start date, duration, work location, and notice period.

5. **Custom Word (.docx) Format Upload**:
   - Upload your own company-branded Word templates preserving your exact letterheads, logos, fonts, and legal clauses.
   - Simple placeholder tags: `{{ company_name }}`, `{{ company_gst }}`, `{{ vendor_code }}`, `{{ consultant_name }}`, `{{ aadhar_no }}`, `{{ rate_formatted }}`, `{{ candidate_name }}`, etc.

6. **Extensible Custom Fields**:
   - Add dynamic fields anytime via the UI without code changes (e.g. Branch Office, Bank Details, Escalation Manager).

7. **Export Formats**:
   - 1-Click editable Word (`.docx`) file download.
   - 1-Click high-resolution PDF download.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- Microsoft Word (optional, for native PDF generation)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Run Application
Double-click `run.bat` or run:
```bash
python app.py
```
Open your browser at: **`http://127.0.0.1:8000`**

### 4. Default Login Credentials
- **Username**: `admin`
- **Password**: `admin123`

---

## 📁 Repository Structure
```
vendor-agreement-system/
├── app.py                     # Flask web app & API routes
├── database.py                # SQLite database models & counters
├── doc_generator.py           # docxtpl engine & Indian currency formatting
├── template_builder.py        # Generates standard default Word templates
├── test_system.py             # Automated unit tests
├── run.bat                    # Windows 1-click launcher
├── templates/                 # Jinja2 HTML UI templates
├── static/                    # CSS & JavaScript assets
├── sample_templates/          # Built-in standard legal templates
├── uploaded_templates/        # User-uploaded custom Word templates
└── generated_docs/            # Output DOCX and PDF documents
```

---

## 📜 License
Internal / Proprietary.
