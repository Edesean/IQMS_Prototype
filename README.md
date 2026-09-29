# IQMS - Intelligent Queue Management System

A full-stack web application for managing customer queues in Nigerian commercial banks. Developed as a final-year project for Delta State University, Abraka.

## Features

- **Customer Self-Service**: Join queues remotely via web interface
- **Real-Time Wait Time Prediction**: ML-based estimates (Random Forest, MAE < 3 min)
- **Teller Dashboard**: Call next customer, start/complete service
- **Manager Analytics**: KPIs, wait time charts, service trends
- **SMS Notifications**: Automated alerts when turn approaches (Celery + Twilio)
- **Role-Based Access**: Customer, Teller, Manager, Admin
- **Audit Trail**: Complete logging of all system actions

## Tech Stack

**Backend**: Python 3.11, Django 4.2, Django REST Framework, PostgreSQL, Celery, Redis, scikit-learn

**Frontend**: React 18, Vite, Tailwind CSS, Chart.js, Axios

## Setup Instructions

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python create_sample_data.py
python seed_demo_data.py
python prediction/train_model.py
python manage.py runserver