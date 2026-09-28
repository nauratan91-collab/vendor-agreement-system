import unittest
import os
import json
from app import app
from database import init_db, get_db_connection

class TestVendorAgreementSystem(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def login(self, username, password):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_01_login_flows(self):
        # Invalid login
        res_fail = self.login('admin', 'wrong_password')
        self.assertIn(b'Galat Username ya Password', res_fail.data)

        # Valid login
        res_ok = self.login('admin', 'admin123')
        self.assertIn(b'Dashboard Overview', res_ok.data)
        print("[OK] Login flow verified successfully")

    def test_02_register_c2c_vendor_and_generate_docs(self):
        self.login('admin', 'admin123')
        
        # Register C2C vendor with auto generate checked
        res = self.client.post('/register', data={
            'vendor_type': 'c2c',
            'company_name': 'CloudTech Infra Solutions Pvt Ltd',
            'company_gst': '07AAACC9999M1Z8',
            'company_address': 'DLF Cyber City, Tower B, Gurugram, Haryana',
            'signatory_name': 'Sanjay Singhania',
            'signatory_designation': 'Chief Operating Officer',
            'company_pan': 'AAACC9999M',
            'contact_email': 'contact@cloudtech.example.com',
            'contact_phone': '+91 9988776655',
            'rate_amount': '300000',
            'rate_unit': 'per_month',
            'gst_type': 'plus_gst',
            'payment_terms': 'Within 30 days of verified monthly invoice',
            'auto_generate_docs': '1'
        }, follow_redirects=True)

        self.assertIn(b'CloudTech Infra Solutions Pvt Ltd', res.data)
        self.assertIn(b'VND-C2C', res.data)
        print("[OK] C2C Vendor registration & auto NDA/MSA generation verified")

    def test_03_register_consultant_and_generate_docs(self):
        self.login('admin', 'admin123')

        # Register Consultant with hourly rate + GST
        res = self.client.post('/register', data={
            'vendor_type': 'consultant',
            'consultant_name': 'Dr. Vikram Malhotra',
            'aadhar_no': '9876 5432 1098',
            'residential_address': 'A-54, Defence Colony, New Delhi 110024',
            'consultant_pan': 'BLRPM8877K',
            'contact_email': 'vikram.m@consultant.example.com',
            'contact_phone': '+91 9811223344',
            'rate_amount': '1500',
            'rate_unit': 'per_hour',
            'gst_type': 'plus_gst',
            'payment_terms': 'Monthly against verified timesheets',
            'auto_generate_docs': '1'
        }, follow_redirects=True)

        self.assertIn(b'Dr. Vikram Malhotra', res.data)
        self.assertIn(b'VND-CON', res.data)
        print("[OK] Consultant registration & auto NDA/MSA generation verified")

    def test_04_create_candidate_sow(self):
        self.login('admin', 'admin123')

        conn = get_db_connection()
        vendor = conn.execute("SELECT id FROM vendors WHERE vendor_type = 'c2c' LIMIT 1").fetchone()
        conn.close()
        self.assertIsNotNone(vendor)

        res = self.client.post('/sow/create', data={
            'vendor_id': vendor['id'],
            'candidate_name': 'Rohan Deshmukh',
            'role_designation': 'Senior Python AI Engineer',
            'client_name': 'Tata Digital Enterprise',
            'project_name': 'GenAI Automation Pipeline',
            'rate_amount': '1800',
            'rate_unit': 'per_hour',
            'gst_type': 'plus_gst',
            'start_date': '2026-10-01',
            'duration': '12 Months',
            'work_location': 'Hybrid (Bangalore)',
            'notice_period': '15 Days',
            'payment_terms': 'Monthly timesheet billing'
        }, follow_redirects=True)

        self.assertIn(b'Rohan Deshmukh', res.data)
        self.assertIn(b'SOW-', res.data)
        print("[OK] Candidate SOW creation & document generation verified")

    def test_05_format_rate_api(self):
        self.login('admin', 'admin123')

        # Test Monthly 3,00,000 + GST
        res1 = self.client.post('/api/format-rate', json={
            'amount': 300000,
            'unit': 'per_month',
            'gst_type': 'plus_gst'
        })
        data1 = json.loads(res1.data)
        self.assertIn('3,00,000', data1['formatted'])
        self.assertIn('+ GST', data1['formatted'])
        self.assertIn('Three Lakh', data1['in_words'])

        # Test Hourly 1500 + GST
        res2 = self.client.post('/api/format-rate', json={
            'amount': 1500,
            'unit': 'per_hour',
            'gst_type': 'plus_gst'
        })
        data2 = json.loads(res2.data)
        self.assertIn('1,500', data2['formatted'])
        self.assertIn('per hour', data2['formatted'])
        self.assertIn('One Thousand Five Hundred', data2['in_words'])
        print("[OK] Commercial rates and words formatting verified")

if __name__ == '__main__':
    unittest.main()
