# backend/prediction/train_model.py

import os
import sys
import django
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Add the backend folder to the Python path so 'iqms_backend' can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iqms_backend.settings')
django.setup()

from api.models import QueueTicket

MODEL_PATH = Path(__file__).parent / 'wait_time_model.pkl'


def build_training_data():
    """Extract features and labels from historical completed tickets."""
    tickets = QueueTicket.objects.filter(
        status='completed',
        actual_wait_time__isnull=False,
    ).select_related('service_category')

    rows = []
    for t in tickets:
        rows.append({
            'queue_position': t.queue_position,
            'avg_service_time': t.service_category.average_service_time,
            'hour_of_day': t.joined_at.hour,
            'is_peak_hour': 1 if 10 <= t.joined_at.hour <= 14 else 0,
            'actual_wait_time': t.actual_wait_time,
        })

    return pd.DataFrame(rows)


def train():
    print("Loading training data...")
    df = build_training_data()

    if len(df) < 20:
        print(f"[ERROR] Not enough data ({len(df)} rows). Run seed_demo_data.py first.")
        return

    print(f"[OK] Loaded {len(df)} training samples")

    X = df[['queue_position', 'avg_service_time', 'hour_of_day', 'is_peak_hour']]
    y = df['actual_wait_time']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n========== Model Performance ==========")
    print(f"MAE  (Mean Absolute Error): {mae / 60:.2f} minutes")
    print(f"RMSE (Root Mean Sq Error):  {rmse / 60:.2f} minutes")
    print(f"R2   (Coefficient of Det.): {r2:.4f}")
    print("=======================================\n")

    joblib.dump(model, MODEL_PATH)
    print(f"[OK] Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()