# app_streamlit.py
# Toll Pass Token System - Professional Toll Plaza Style

import streamlit as st
import sqlite3
import qrcode
import uuid
import os
import re
from datetime import datetime, timedelta

from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode


# ---------------------------
# Constants
# ---------------------------
MAX_CROSSINGS = 500
LOW_BALANCE_WARNING = 5
CROSSING_RATE = 100
# NO VALIDITY DAYS - Crossings never expire


# ---------------------------
# Helper Functions
# ---------------------------
def is_valid_user_id(user_id):
    if not user_id:
        return False
    return bool(re.fullmatch(r'\d{8}', str(user_id).strip()))


def init_db():
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY,
                  name TEXT,
                  vehicle_number TEXT,
                  remaining_crossings INTEGER DEFAULT 0,
                  total_purchased INTEGER DEFAULT 0,
                  created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (transaction_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  amount REAL,
                  crossings_purchased INTEGER,
                  timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS toll_scans
                 (scan_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  qr_data TEXT,
                  timestamp TEXT,
                  location TEXT,
                  status TEXT)''')
    conn.commit()
    conn.close()


init_db()


def user_exists(user_id):
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None


def get_or_create_user(user_id):
    if not is_valid_user_id(user_id):
        return None
    
    if user_exists(user_id):
        conn = sqlite3.connect('tollpass.db')
        c = conn.cursor()
        c.execute("SELECT name, vehicle_number, remaining_crossings FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        return {"name": user[0], "vehicle_number": user[1], "remaining_crossings": user[2]}
    
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    name = f"User {user_id}"
    vehicle_number = f"AUTO{user_id}"
    created_date = datetime.now().isoformat()
    
    c.execute("""
        INSERT INTO users (user_id, name, vehicle_number, remaining_crossings, total_purchased, created_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, name, vehicle_number, 0, 0, created_date))
    conn.commit()
    conn.close()
    
    return {"name": name, "vehicle_number": vehicle_number, "remaining_crossings": 0}


def get_current_balance(user_id):
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    c.execute("SELECT remaining_crossings FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0


def update_balance(user_id, crossings):
    current_balance = get_current_balance(user_id)
    new_balance = current_balance + crossings
    
    if new_balance > MAX_CROSSINGS:
        return False, f"Cannot add. Maximum is {MAX_CROSSINGS}."
    
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    c.execute("""
        UPDATE users 
        SET remaining_crossings = remaining_crossings + ?, 
            total_purchased = total_purchased + ?
        WHERE user_id = ?
    """, (crossings, crossings, user_id))
    conn.commit()
    conn.close()
    return True, new_balance


def add_transaction(user_id, amount, crossings):
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    transaction_id = str(uuid.uuid4())[:8]
    c.execute("""
        INSERT INTO transactions (transaction_id, user_id, amount, crossings_purchased, timestamp) 
        VALUES (?, ?, ?, ?, ?)
    """, (transaction_id, user_id, amount, crossings, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def deduct_crossing(user_id):
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    
    c.execute("SELECT remaining_crossings FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        return False, "❌ User not found", 0, None
    
    remaining = result[0]
    if remaining <= 0:
        conn.close()
        return False, "❌ Insufficient balance", 0, None
    
    c.execute("UPDATE users SET remaining_crossings = remaining_crossings - 1 WHERE user_id = ?", (user_id,))
    
    scan_id = str(uuid.uuid4())[:8]
    qr_data = f"TOLLPASS|{user_id}|{datetime.now().date()}"
    new_remaining = remaining - 1
    
    if new_remaining <= LOW_BALANCE_WARNING and new_remaining > 0:
        message = f"✅ VALID: Toll paid! ⚠️ Low balance: Only {new_remaining} left"
    elif new_remaining == 0:
        message = "✅ VALID: Toll paid! ❌ Balance now zero"
    else:
        message = "✅ VALID: Toll paid! Gate opening..."
    
    c.execute("""
        INSERT INTO toll_scans (scan_id, user_id, qr_data, timestamp, location, status) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (scan_id, user_id, qr_data, datetime.now().isoformat(), 'Toll Plaza', 'success'))
    
    conn.commit()
    conn.close()
    
    return True, message, new_remaining, remaining


def generate_static_qr():
    """Generate a static QR code for admin display"""
    qr_data = "TOLLPASS|ADMIN|2026-04-11|STATIC"
    qr = qrcode.make(qr_data)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    return buffered.getvalue()


# ---------------------------
# Custom CSS for Professional Toll Plaza Look
# ---------------------------
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Section title styling */
    .section-title {
        color: #1a1a2e;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 3px solid #e94560;
        display: inline-block;
    }
    
    /* Info row styling */
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }
    
    .info-label {
        font-weight: bold;
        color: #555;
    }
    
    .info-value {
        color: #1a1a2e;
        font-weight: 500;
    }
    
    /* Balance amount styling */
    .balance-amount {
        font-size: 36px;
        font-weight: bold;
        color: #e94560;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46a0 100%);
        color: white;
    }
    
    /* Success message styling */
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    
    /* Warning message styling */
    .warning-message {
        background: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    
    /* Error message styling */
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
    
    /* QR Code container */
    .qr-container {
        text-align: center;
        padding: 20px;
        background: white;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Toll Plaza Booth styling */
    .toll-booth {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
    }
    
    /* Divider styling */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, #e94560, #667eea, #e94560);
        margin: 20px 0;
    }
    
    /* Centered content */
    .centered {
        text-align: center;
    }
    
    /* Price tag styling */
    .price-tag {
        background: #e94560;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
    }
    
    /* Three column stats */
    .stats-container {
        display: flex;
        justify-content: space-around;
        text-align: center;
        margin-top: 10px;
    }
    .stat-box {
        flex: 1;
        padding: 10px;
    }
    .stat-value {
        font-size: 28px;
        font-weight: bold;
    }
    .stat-label {
        font-size: 11px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Toll Pass Token System", page_icon="🛣️", layout="wide")

# ============================================
# TOLL PLAZA BOOTH SECTION
# ============================================
st.markdown("""
<div class="toll-booth">
    <h2 style='margin: 0;'>🚗 TOLL PLAZA BOOTH #01</h2>
    <p style='margin: 5px 0 0 0; opacity: 0.9;'>Please have your QR code ready for scanning</p>
    <p style='margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;'>📍 Electronic Toll Collection (ETC) Lane</p>
</div>
""", unsafe_allow_html=True)

# Generate static QR code
static_qr_image = generate_static_qr()

# QR Code Display - Centered
qr_col1, qr_col2, qr_col3 = st.columns([1, 2, 1])
with qr_col2:
    st.markdown("""
    <div class="qr-container">
        <h3 style='color: #1a1a2e; margin-bottom: 10px;'>📷 QR CODE SCANNER</h3>
        <p style='color: #666; font-size: 14px;'>Position your QR code in front of the camera</p>
        <span class="price-tag">₹100 per crossing</span>
    </div>
    """, unsafe_allow_html=True)
    st.image(static_qr_image, width=220, caption="Toll Plaza Scanner")
    st.markdown("<p style='text-align: center; color: #22c55e; font-size: 14px; font-weight: bold;'>✅ SCANNER ACTIVE - READY</p>", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Two Column Layout - Equal Balance
left_col, right_col = st.columns(2, gap="large")

# ============================================
# LEFT COLUMN: User ID & Purchase Section
# ============================================
with left_col:
    st.markdown("""
    <div class="card">
        <h3 class="section-title">🎫 TOLL PASS PURCHASE</h3>
        <p style='color: #666; font-size: 13px;'>Purchase crossings for seamless travel</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.text_input("🔢 Enter User ID (8 digits)", max_chars=8, key="main_user_id", 
                           placeholder="Example: 12345678", help="Enter your 8-digit User ID")
    
    if user_id:
        if not is_valid_user_id(user_id):
            st.markdown("""
            <div class="error-message">
                ❌ Invalid User ID! Must be exactly 8 digits (0-9)
            </div>
            """, unsafe_allow_html=True)
        else:
            user = get_or_create_user(user_id)
            if user:
                current_balance = get_current_balance(user_id)
                
                # Balance Display
                st.markdown(f"""
                <div class="card">
                    <h4 style='color: #1a1a2e; margin-bottom: 15px;'>💰 CURRENT BALANCE</h4>
                    <div class="centered">
                        <span class="balance-amount">{current_balance}</span>
                        <span style='font-size: 18px; color: #666;'> crossings</span>
                    </div>
                    <div style='margin-top: 15px;'>
                        <div style='background: #e0e0e0; border-radius: 10px; height: 10px;'>
                            <div style='background: linear-gradient(90deg, #667eea, #764ba2); width: {int((current_balance/MAX_CROSSINGS)*100)}%; height: 10px; border-radius: 10px;'></div>
                        </div>
                        <p style='text-align: center; margin-top: 8px; font-size: 12px; color: #666;'>{current_balance} of {MAX_CROSSINGS} crossings available</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Purchase Section
                st.markdown("""
                <div class="card">
                    <h4 style='color: #1a1a2e; margin-bottom: 15px;'>💳 PURCHASE CROSSINGS</h4>
                    <p style='color: #666; font-size: 13px;'>✨ No expiry - Crossings never expire</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_p1, col_p2 = st.columns([2, 1])
                with col_p1:
                    purchase_crossings = st.selectbox(
                        "Select Package", 
                        [10, 20, 50, 100], 
                        format_func=lambda x: f"{x} crossings - ₹{x*CROSSING_RATE}",
                        key="purchase_select"
                    )
                with col_p2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💳 BUY NOW", key="buy_now"):
                        amount = purchase_crossings * CROSSING_RATE
                        remaining_space = MAX_CROSSINGS - current_balance
                        
                        if purchase_crossings > remaining_space:
                            st.markdown(f"""
                            <div class="error-message">
                                ❌ Cannot add {purchase_crossings} crossings. Only {remaining_space} spots left.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            success, result = update_balance(user_id, purchase_crossings)
                            if success:
                                add_transaction(user_id, amount, purchase_crossings)
                                st.markdown(f"""
                                <div class="success-message">
                                    ✅ Added {purchase_crossings} crossings! New balance: {result}
                                </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                                st.rerun()
                            else:
                                st.markdown(f"""
                                <div class="error-message">
                                    ❌ {result}
                                </div>
                                """, unsafe_allow_html=True)

# ============================================
# RIGHT COLUMN: User Information (Simplified)
# ============================================
with right_col:
    if user_id and is_valid_user_id(user_id):
        # Get user details from database
        conn = sqlite3.connect('tollpass.db')
        c = conn.cursor()
        c.execute("SELECT name, vehicle_number, remaining_crossings, total_purchased, created_date FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        
        if user_data:
            # User Information Card
            st.markdown("""
            <div class="card">
                <h3 class="section-title">👤 USER INFORMATION</h3>
                <p style='color: #666; font-size: 13px;'>Registered user details</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card">
                <div class="info-row">
                    <span class="info-label">👤 Full Name:</span>
                    <span class="info-value">{user_data[0]}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🚗 Vehicle Number:</span>
                    <span class="info-value">{user_data[1]}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🆔 User ID:</span>
                    <span class="info-value">{user_id}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">📅 Member Since:</span>
                    <span class="info-value">{user_data[4][:19] if user_data[4] else datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Account Status Card
            st.markdown(f"""
            <div class="card">
                <h4 style='color: #1a1a2e; margin-bottom: 15px;'>💰 ACCOUNT STATUS</h4>
                <div style='display: flex; justify-content: space-around; text-align: center;'>
                    <div>
                        <p style='color: #666; font-size: 11px;'>Remaining Crossings</p>
                        <p style='font-size: 28px; font-weight: bold; color: #e94560;'>{user_data[2]}</p>
                    </div>
                    <div>
                        <p style='color: #666; font-size: 11px;'>Total Value</p>
                        <p style='font-size: 28px; font-weight: bold; color: #22c55e;'>₹{user_data[2] * CROSSING_RATE}</p>
                    </div>
                    <div>
                        <p style='color: #666; font-size: 11px;'>Usage</p>
                        <p style='font-size: 28px; font-weight: bold; color: #3b82f6;'>{int((user_data[2] / MAX_CROSSINGS) * 100)}%</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        conn.close()
    else:
        # Placeholder when no user ID entered
        st.markdown("""
        <div class="card" style='text-align: center; padding: 40px;'>
            <h3 style='color: #666;'>👤 Enter User ID</h3>
            <p style='color: #999;'>Please enter an 8-digit User ID to view details</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2 style='color: #e94560;'>📖 Toll Plaza Info</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
        <h4 style='color: #1a1a2e;'>💰 Toll Rates</h4>
        <p><b>Per Crossing:</b> ₹{CROSSING_RATE}</p>
        <p><b>10 Crossings:</b> ₹{CROSSING_RATE * 10}</p>
        <p><b>20 Crossings:</b> ₹{CROSSING_RATE * 20}</p>
        <p><b>50 Crossings:</b> ₹{CROSSING_RATE * 50}</p>
        <p><b>100 Crossings:</b> ₹{CROSSING_RATE * 100}</p>
        <p><b>✨ No Expiry!</b> Crossings never expire</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    conn = sqlite3.connect('tollpass.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT SUM(remaining_crossings) FROM users")
    total_crossings = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM toll_scans")
    total_scans = c.fetchone()[0]
    conn.close()
    
    st.markdown("""
    <div style='background: #f8f9fa; padding: 15px; border-radius: 10px;'>
        <h4 style='color: #1a1a2e;'>📊 System Stats</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Total Users", total_users)
        st.metric("Total Scans", total_scans)
    with col_b:
        st.metric("Crossings Left", total_crossings)
        st.metric("Active Users", total_users)

# Footer
st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🛣️ Toll Pass Token System | AI-Powered | ₹{CROSSING_RATE} per crossing | Max: {MAX_CROSSINGS}</p>
        <p>✨ Crossings NEVER expire - Valid forever! ✨</p>
        <p>© 2026 Toll Pass Token System | Fast | Secure | Contactless</p>
    </div>
""", unsafe_allow_html=True)