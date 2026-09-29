#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create a superuser if one doesn't exist
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@iqms.com').exists() or User.objects.create_superuser('admin@iqms.com', 'Admin User', '08000000000', 'admin123')"

# Collect static files for WhiteNoise
python manage.py collectstatic --no-input