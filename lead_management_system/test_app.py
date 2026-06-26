

import sqlite3
import json
import sys

DATABASE = '/tmp/leads.db'

def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_error(text):
    print(f" ERROR: {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def test_database():
    """Test database initialization and schema"""
    print_header("Testing Database")
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Check tables exist
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        required_tables = ['lead', 'sent_email', 'email_open', 'link_click']
        
        for table in required_tables:
            if table in tables:
                print(f" Table '{table}' exists")
            else:
                print(f" Table '{table}' NOT found")
                return False
        
        conn.close()
        return True
    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        return False

def test_lead_creation():
    """Test creating a lead in the database"""
    print_header("Testing Lead Creation")
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Insert test lead
        c.execute('''
            INSERT INTO lead (full_name, email, phone, company, requirement)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'Test User',
            'test@example.com',
            '+91-9876543210',
            'Test Company',
            'Test requirement'
        ))
        conn.commit()
        lead_id = c.lastrowid
        
        # Verify lead was created
        c.execute('SELECT * FROM lead WHERE id = ?', (lead_id,))
        lead = c.fetchone()
        
        if lead:
            print(f" Lead created successfully (ID: {lead_id})")
            print(f"   Name: {lead[1]}")
            print(f"   Email: {lead[2]}")
            conn.close()
            return lead_id
        else:
            print_error("Lead not found after creation")
            return False
    except Exception as e:
        print_error(f"Lead creation test failed: {str(e)}")
        return False

def test_email_tracking(lead_id):
    """Test email creation and tracking"""
    print_header("Testing Email Tracking")
    
    try:
        import uuid
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        tracking_id = str(uuid.uuid4())
        link_id = str(uuid.uuid4())
        
        # Create sent email record
        c.execute('''
            INSERT INTO sent_email (lead_id, tracking_id, link_id)
            VALUES (?, ?, ?)
        ''', (lead_id, tracking_id, link_id))
        conn.commit()
        email_id = c.lastrowid
        
        print(f"Email record created (ID: {email_id})")
        print(f"   Tracking ID: {tracking_id}")
        print(f"   Link ID: {link_id}")
        
        # Test open tracking
        c.execute('''
            INSERT INTO email_open (email_id, ip_address)
            VALUES (?, ?)
        ''', (email_id, '192.168.1.1'))
        
        c.execute('UPDATE sent_email SET opened = 1 WHERE id = ?', (email_id,))
        conn.commit()
        
        print(f"Email open tracked")
        
        # Test click tracking
        c.execute('''
            INSERT INTO link_click (email_id, ip_address)
            VALUES (?, ?)
        ''', (email_id, '192.168.1.1'))
        conn.commit()
        
        print(f"Link click tracked")
        
        conn.close()
        return True
    except Exception as e:
        print_error(f"Email tracking test failed: {str(e)}")
        return False

def test_analytics():
    """Test analytics calculations"""
    print_header("Testing Analytics")
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Get metrics
        c.execute('SELECT COUNT(*) as count FROM lead')
        total_leads = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) as count FROM sent_email')
        total_emails = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) as count FROM sent_email WHERE opened = 1')
        opened_emails = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) as count FROM link_click')
        total_clicks = c.fetchone()[0]
        
        open_rate = (opened_emails / total_emails * 100) if total_emails > 0 else 0
        click_rate = (total_clicks / total_emails * 100) if total_emails > 0 else 0
        
        print(f"  Analytics Calculated:")
        print(f"   Total Leads: {total_leads}")
        print(f"   Total Emails Sent: {total_emails}")
        print(f"   Emails Opened: {opened_emails}")
        print(f"   Open Rate: {open_rate:.2f}%")
        print(f"   Link Clicks: {total_clicks}")
        print(f"   Click Rate: {click_rate:.2f}%")
        
        conn.close()
        return True
    except Exception as e:
        print_error(f"Analytics test failed: {str(e)}")
        return False

def test_flask_app():
    """Test Flask application structure"""
    print_header("Testing Flask Application")
    
    try:
        import os
        
        # Check required files
        files_to_check = [
            'app.py',
            'templates/base.html',
            'templates/index.html',
            'templates/dashboard.html',
            'templates/thank_you.html',
            'README.md'
        ]
        
        for file in files_to_check:
            if os.path.exists(file):
                print(f" File exists: {file}")
            else:
                print(f" File NOT found: {file}")
                return False
        
        return True
    except Exception as e:
        print_error(f"Flask app test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print(" LEAD MANAGEMENT SYSTEM - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Database Initialization", test_database),
        ("Flask App Structure", test_flask_app),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Test data operations
    lead_id = test_lead_creation()
    if lead_id:
        results.append(("Lead Creation", True))
        test_email_tracking(lead_id)
        results.append(("Email Tracking", True))
        test_analytics()
        results.append(("Analytics", True))
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = " PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Application is ready to use.")
        print("\nTo start the application, run:")
        print("  python3 app.py")
        print("\nOr use the startup script:")
        print("  ./run.sh")
        return 0
    else:
        print(f"\n {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
