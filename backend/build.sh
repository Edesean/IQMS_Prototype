#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@iqms.com').exists() or User.objects.create_superuser('admin@iqms.com', 'Admin User', '08000000000', 'admin123')"

# Seed database ONLY if it is empty
python manage.py shell <<'EOF'
from api.models import Branch, ServiceCategory, User
from datetime import time

if not Branch.objects.exists():
    print("=== Seeding database (first time only) ===")

    # --- 1. Create branches ---
    BRANCHES = [
        {'name': 'Marina Branch', 'location': '1, Marina Road, Lagos Island',
         'city': 'Lagos', 'state': 'Lagos', 'contact_phone': '01-2345678',
         'contact_email': 'marina@bank.com', 'code': 'BR001'},
        {'name': 'Ikeja Branch', 'location': '45, Allen Avenue, Ikeja',
         'city': 'Lagos', 'state': 'Lagos', 'contact_phone': '01-8765432',
         'contact_email': 'ikeja@bank.com', 'code': 'BR002'},
        {'name': 'Abuja Main Branch', 'location': '12, Wuse 2, Abuja',
         'city': 'Abuja', 'state': 'FCT', 'contact_phone': '09-1234567',
         'contact_email': 'abuja@bank.com', 'code': 'BR003'},
        {'name': 'Port Harcourt Branch', 'location': '8, Aba Road, Port Harcourt',
         'city': 'Port Harcourt', 'state': 'Rivers', 'contact_phone': '084-555666',
         'contact_email': 'ph@bank.com', 'code': 'BR004'},
    ]

    SERVICES = [
        {'name': 'Cash Deposit',    'desc': 'Deposit cash into account',             'avg': 300, 'min': 120, 'max': 600},
        {'name': 'Cash Withdrawal', 'desc': 'Withdraw cash from account',            'avg': 180, 'min': 60,  'max': 300},
        {'name': 'Cheque Deposit',  'desc': 'Deposit cheque into account',           'avg': 420, 'min': 180, 'max': 900},
        {'name': 'OTC Transfer',    'desc': 'Over-the-counter funds transfer',       'avg': 240, 'min': 120, 'max': 480},
        {'name': 'Account Inquiry', 'desc': 'Account balance and statement inquiry', 'avg': 120, 'min': 60,  'max': 300},
    ]

    for b in BRANCHES:
        branch, _ = Branch.objects.get_or_create(
            code=b['code'],
            defaults={
                'name': b['name'], 'location': b['location'],
                'city': b['city'], 'state': b['state'],
                'contact_phone': b['contact_phone'],
                'contact_email': b['contact_email'],
                'opening_time': time(8, 0), 'closing_time': time(16, 0),
            }
        )
        print(f"[BRANCH] {branch.name}")

        for s in SERVICES:
            ServiceCategory.objects.get_or_create(
                name=s['name'], branch=branch,
                defaults={
                    'description': s['desc'],
                    'average_service_time': s['avg'],
                    'min_service_time': s['min'],
                    'max_service_time': s['max'],
                    'is_active': True,
                }
            )

    # --- 2. Create demo users ---
    marina = Branch.objects.get(code='BR001')
    abuja  = Branch.objects.get(code='BR003')

    for email, name, phone, pwd, role, br in [
        ('teller@bank.com',          'Marina Teller',   '08011111111', 'teller123',  'teller',  marina),
        ('teller.marina@bank.com',   'Marina Teller 2', '08011111112', 'teller123',  'teller',  marina),
        ('teller.abuja@bank.com',    'Abuja Teller',    '08022222222', 'teller123',  'teller',  abuja),
        ('manager@bank.com',         'Branch Manager',  '08012345678', 'manager123', 'manager', marina),
        ('manager.abuja@bank.com',   'Abuja Manager',   '08055555555', 'manager123', 'manager', abuja),
    ]:
        if not User.objects.filter(email=email).exists():
            User.objects.create_user(
                email=email, full_name=name, phone_number=phone,
                password=pwd, role=role, branch=br
            )
            print(f"[USER] {email}")

    print("=== Seeding complete ===")
else:
    print("=== Database already has data — skipping seed ===")
EOF

# Collect static files
python manage.py collectstatic --no-input