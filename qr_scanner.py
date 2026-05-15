import cv2
import numpy as np
import tensorflow as tf
from pyzbar.pyzbar import decode

def enhance_low_light(image):
    img_tensor = tf.convert_to_tensor(image, dtype=tf.float32)
    gamma = 1.5
    img_tensor = tf.image.adjust_gamma(img_tensor, gamma)
    img_tensor = tf.image.adjust_contrast(img_tensor, 2.0)
    return np.array(img_tensor, dtype=np.uint8)

def scan_qr_from_camera():
    cap = cv2.VideoCapture(0)
    qr_data = None
    confidence = 0.0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        enhanced_frame = enhance_low_light(frame)
        decoded_objects = decode(enhanced_frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            confidence = 0.95
            break
        cv2.imshow("QR Scanner - Press 'q' to quit", enhanced_frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or qr_data is not None:
            break
    cap.release()
    cv2.destroyAllWindows()
    return qr_data, confidence

if __name__ == "__main__":
    data, conf = scan_qr_from_camera()
    print(f"Decoded QR: {data}, Confidence: {conf}")