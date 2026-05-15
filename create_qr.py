# create_qr.py
# Simple QR Code Generator for Toll Pass System

import qrcode
from datetime import datetime

def create_tollpass_qr(user_id, filename=None):
    """
    Create a QR code for Toll Pass System
    
    Args:
        user_id (str): User ID (e.g., "1")
        filename (str): Output filename (optional)
    
    Returns:
        str: Filename of saved QR code
    """
    
    # Format the data that goes inside QR code
    # Your toll scanner expects this exact format
    qr_data = f"TOLLPASS|{user_id}|{datetime.now().date()}"
    
    # Create QR code
    qr = qrcode.make(qr_data)
    
    # Set filename (if not provided)
    if filename is None:
        filename = f"tollpass_qr_user_{user_id}.png"
    
    # Save QR code image
    qr.save(filename)
    
    print(f"✅ QR Code created successfully!")
    print(f"📦 Data inside QR: {qr_data}")
    print(f"📁 Saved as: {filename}")
    
    return filename


# ============================================
# Run this section when you execute the file
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🛣️ Toll Pass QR Code Generator")
    print("=" * 50)
    
    # Ask for user ID
    user_id = input("Enter User ID (default: 1): ").strip()
    if not user_id:
        user_id = "1"
    
    # Create QR code
    create_tollpass_qr(user_id)
    
    print("\n✨ You can now upload this QR code to your Toll Scanner!")