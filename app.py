from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import uuid
import sqlite3
import threading
import os

app = Flask(__name__)
DATABASE = 'leads.db'

# ==================== Database Setup ====================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS lead (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        company TEXT,
        requirement TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sent_email (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        tracking_id TEXT UNIQUE,
        link_id TEXT UNIQUE,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        opened INTEGER DEFAULT 0,
        opened_at TEXT,
        FOREIGN KEY(lead_id) REFERENCES lead(id) ON DELETE CASCADE
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS email_open (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER NOT NULL,
        opened_at TEXT DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY(email_id) REFERENCES sent_email(id) ON DELETE CASCADE
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS link_click (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER NOT NULL,
        clicked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY(email_id) REFERENCES sent_email(id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()

# ==================== Email Sending ====================
def send_email(lead_id, email_id):
    """Send personalized email with tracking"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM lead WHERE id = ?', (lead_id,))
        lead = c.fetchone()
        conn.close()
        
        if not lead:
            return
        
        tracking_pixel = f"https://yourapp.com/track/open/{email_id}"
        trackable_link = f"https://yourapp.com/track/click/{email_id}"
        
        print(f"\n{'='*60}")
        print(f"EMAIL SENT")
        print(f"{'='*60}")
        print(f"To: {lead['email']}")
        print(f"Name: {lead['full_name']}")
        print(f"Subject: Thank You {lead['full_name']} - We Received Your Requirement")
        print(f"Requirement: {lead['requirement']}")
        print(f"Company: {lead['company'] if lead['company'] else 'Not provided'}")
        print(f"Phone: {lead['phone']}")
        print(f"\nTracking ID: {email_id}")
        print(f"Trackable Link: {trackable_link}")
        print(f"Tracking Pixel: {tracking_pixel}")
        print(f"{'='*60}\n")
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

# ==================== Routes ====================
@app.route('/')
def index():
    """Homepage with lead form"""
    return render_template('index.html')

@app.route('/api/submit-lead', methods=['POST'])
def submit_lead():
    """Submit lead form and send email"""
    try:
        data = request.json
        
        # Validate required fields
        if not all([data.get('full_name'), data.get('email'), data.get('phone'), data.get('requirement')]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Insert lead
        c.execute('''
            INSERT INTO lead (full_name, email, phone, company, requirement)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['full_name'],
            data['email'],
            data['phone'],
            data.get('company', ''),
            data['requirement']
        ))
        conn.commit()
        lead_id = c.lastrowid
        
        # Create sent email record
        tracking_id = str(uuid.uuid4())
        link_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO sent_email (lead_id, tracking_id, link_id)
            VALUES (?, ?, ?)
        ''', (lead_id, tracking_id, link_id))
        conn.commit()
        email_id = c.lastrowid
        conn.close()
        
        # Send email asynchronously
        thread = threading.Thread(target=send_email, args=(lead_id, email_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Lead submitted successfully! Email sent.',
            'lead_id': lead_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dashboard')
def get_dashboard():
    """Get analytics dashboard data"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get metrics
        c.execute('SELECT COUNT(*) as count FROM lead')
        total_leads = c.fetchone()['count']
        
        c.execute('SELECT COUNT(*) as count FROM sent_email')
        total_emails_sent = c.fetchone()['count']
        
        c.execute('SELECT COUNT(*) as count FROM sent_email WHERE opened = 1')
        opened_emails = c.fetchone()['count']
        
        c.execute('SELECT COUNT(*) as count FROM link_click')
        total_clicks = c.fetchone()['count']
        
        conn.close()
        
        open_rate = (opened_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
        click_rate = (total_clicks / total_emails_sent * 100) if total_emails_sent > 0 else 0
        
        return jsonify({
            'total_leads': total_leads,
            'total_emails_sent': total_emails_sent,
            'emails_opened': opened_emails,
            'open_rate': round(open_rate, 2),
            'link_clicks': total_clicks,
            'click_rate': round(click_rate, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/track/open/<int:email_id>')
def track_email_open(email_id):
    """Track email opens"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if email exists
        c.execute('SELECT * FROM sent_email WHERE id = ?', (email_id,))
        email = c.fetchone()
        
        if email:
            # Mark as opened
            if not email['opened']:
                c.execute('UPDATE sent_email SET opened = 1, opened_at = ? WHERE id = ?',
                         (datetime.utcnow().isoformat(), email_id))
            
            # Log open event
            c.execute('''
                INSERT INTO email_open (email_id, ip_address)
                VALUES (?, ?)
            ''', (email_id, request.remote_addr))
            
            conn.commit()
        
        conn.close()
        
        # Return 1x1 transparent pixel
        return b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x0A\x00\x01\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x54\x01\x00\x3B', 200, {'Content-Type': 'image/gif'}
    except Exception as e:
        print(f"Error tracking open: {str(e)}")
        return b'', 200

@app.route('/track/click/<int:email_id>')
def track_link_click(email_id):
    """Track link clicks"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO link_click (email_id, ip_address)
            VALUES (?, ?)
        ''', (email_id, request.remote_addr))
        
        conn.commit()
        conn.close()
        
        # Redirect to thank you page
        return redirect(url_for('thank_you'))
    except Exception as e:
        print(f"Error tracking click: {str(e)}")
        return redirect(url_for('index'))

@app.route('/thank-you')
def thank_you():
    """Thank you page after link click"""
    return render_template('thank_you.html')

@app.route('/dashboard')
def dashboard():
    """Analytics dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    """Get all leads with their email stats"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('SELECT * FROM lead ORDER BY created_at DESC')
        leads = c.fetchall()
        
        leads_data = []
        for lead in leads:
            # Get email stats for this lead
            c.execute('SELECT COUNT(*) as count FROM sent_email WHERE lead_id = ?', (lead['id'],))
            total_emails = c.fetchone()['count']
            
            c.execute('SELECT COUNT(*) as count FROM sent_email WHERE lead_id = ? AND opened = 1', (lead['id'],))
            opened_emails = c.fetchone()['count']
            
            c.execute('''
                SELECT COUNT(*) as count FROM link_click 
                WHERE email_id IN (SELECT id FROM sent_email WHERE lead_id = ?)
            ''', (lead['id'],))
            total_clicks = c.fetchone()['count']
            
            leads_data.append({
                'id': lead['id'],
                'full_name': lead['full_name'],
                'email': lead['email'],
                'phone': lead['phone'],
                'company': lead['company'],
                'requirement': lead['requirement'][:50] + '...' if len(lead['requirement']) > 50 else lead['requirement'],
                'created_at': lead['created_at'],
                'emails_sent': total_emails,
                'emails_opened': opened_emails,
                'clicks': total_clicks
            })
        
        conn.close()
        return jsonify(leads_data)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== Error Handlers ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    print(f"\n{'='*60}")
    print(" Starting Lead Management & Email Tracking System")
    print(f"{'='*60}")
    print(" Dashboard: http://localhost:5000/dashboard")
    print(" Lead Form: http://localhost:5000/")
    print(f"{'='*60}\n")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
