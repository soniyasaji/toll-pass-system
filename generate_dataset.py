# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

num_rows = 500000

data = {
    "user_id": [fake.uuid4() for _ in range(num_rows)],
    "name": [fake.name() for _ in range(num_rows)],
    "vehicle_number": [fake.license_plate() for _ in range(num_rows)],
    "qr_code_hash": [fake.md5(raw_output=False) for _ in range(num_rows)],
    "balance_crossings": np.random.randint(0, 50, num_rows),
    "total_purchased": np.random.randint(1, 200, num_rows),
    "last_payment_date": [fake.date_between(start_date='-1y', end_date='today') for _ in range(num_rows)],
    "expiry_date": [fake.date_between(start_date='today', end_date='+6m') for _ in range(num_rows)],
    "toll_booth_id": [fake.bothify(text='Booth-###') for _ in range(num_rows)],
    "toll_name": [fake.company() + " Toll Plaza" for _ in range(num_rows)],
    "crossing_time": [fake.date_time_between(start_date='-6m', end_date='now') for _ in range(num_rows)],
    "image_path": [f"/images/{fake.uuid4()}.jpg" for _ in range(num_rows)],
    "is_active": np.random.choice([True, False], num_rows, p=[0.95, 0.05]),
    "payment_method": np.random.choice(["UPI", "Credit Card", "Debit Card", "Net Banking"], num_rows),
    "device_id": [fake.bothify(text='CAM-####') for _ in range(num_rows)],
    "weather_condition": np.random.choice(["Clear", "Rain", "Fog", "Snow", "Cloudy"], num_rows),
    "camera_quality": np.random.choice(["low", "medium", "high"], num_rows, p=[0.2, 0.6, 0.2]),
    "detection_confidence": np.random.uniform(0.6, 1.0, num_rows),
    "processing_time_ms": np.random.uniform(50, 500, num_rows),
    "fraud_flag": np.random.choice([True, False], num_rows, p=[0.02, 0.98]),
}

df = pd.DataFrame(data)
df.to_csv("toll_dataset.csv", index=False)
print(f"Dataset generated with {len(df)} rows and {len(df.columns)} columns.")
