# backend/prediction/predictor.py

import sys
from pathlib import Path
sys.path.insert(0,
str(Path(__file__).resolve().parent.parent))
import joblib
import os
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

MODEL_PATH = Path(__file__).parent / 'wait_time_model.pkl'


def _simple_predict(service_avg_time, queue_position, hour_of_day):
    """
    Fallback prediction if no trained model exists.
    Uses a weighted formula based on service time, queue position, and time of day.
    """
    # Peak hour multiplier (10am-2pm is busiest)
    peak_multiplier = 1.3 if 10 <= hour_of_day <= 14 else 1.0

    # Base estimate: average service time × position ahead in queue
    base = service_avg_time * max(queue_position - 1, 0)

    # Add some randomness to simulate real-world variation
    noise = np.random.normal(0, service_avg_time * 0.15)

    predicted = max(base * peak_multiplier + noise, 60)  # minimum 1 minute
    return int(predicted)


def predict_wait_time(service_category, queue_position):
    """
    Predict wait time for a new ticket.

    Args:
        service_category: ServiceCategory instance
        queue_position: int - position in queue (1 = first in line)

    Returns:
        int - estimated wait time in seconds
    """
    hour_of_day = datetime.now().hour

    # Try to use trained ML model
    if MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
            features = pd.DataFrame([{
                'queue_position': queue_position,
                'avg_service_time': service_category.average_service_time,
                'hour_of_day': hour_of_day,
                'is_peak_hour': 1 if 10 <= hour_of_day <= 14 else 0,
            }])
            predicted = int(model.predict(features)[0])
            return max(predicted, 60)
        except Exception as e:
            print(f"[PREDICTION] Model load failed, using fallback: {e}")

    # Fallback
    return _simple_predict(
        service_category.average_service_time,
        queue_position,
        hour_of_day
    )