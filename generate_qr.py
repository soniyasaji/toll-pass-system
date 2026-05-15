import qrcode
from datetime import datetime

user_id = "34343456"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
qr_data = f"TOLLPASS|{user_id}|{datetime.now().date()}|{timestamp}"
qr = qrcode.make(qr_data)
qr.save(f"tollpass_{user_id}.png")
print(f"✅ QR Code saved as: tollpass_{user_id}.png")
print(f"📱 QR Data: {qr_data}")