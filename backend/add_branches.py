# backend/add_branches.py

import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iqms_backend.settings')
django.setup()

from api.models import Branch, ServiceCategory


BRANCHES = [
    {
        'name': 'Ikeja Branch',
        'location': '45, Allen Avenue, Ikeja',
        'city': 'Lagos',
        'state': 'Lagos',
        'contact_phone': '01-8765432',
        'contact_email': 'ikeja@bank.com',
        'code': 'BR002',
    },
    {
        'name': 'Abuja Main Branch',
        'location': '12, Wuse 2, Abuja',
        'city': 'Abuja',
        'state': 'FCT',
        'contact_phone': '09-1234567',
        'contact_email': 'abuja@bank.com',
        'code': 'BR003',
    },
    {
        'name': 'Port Harcourt Branch',
        'location': '8, Aba Road, Port Harcourt',
        'city': 'Port Harcourt',
        'state': 'Rivers',
        'contact_phone': '084-555666',
        'contact_email': 'ph@bank.com',
        'code': 'BR004',
    },
]

SERVICES = [
    {'name': 'Cash Deposit',    'desc': 'Deposit cash into account',             'avg': 300, 'min': 120, 'max': 600},
    {'name': 'Cash Withdrawal', 'desc': 'Withdraw cash from account',            'avg': 180, 'min': 60,  'max': 300},
    {'name': 'Cheque Deposit',  'desc': 'Deposit cheque into account',           'avg': 420, 'min': 180, 'max': 900},
    {'name': 'OTC Transfer',    'desc': 'Over-the-counter funds transfer',       'avg': 240, 'min': 120, 'max': 480},
    {'name': 'Account Inquiry', 'desc': 'Account balance and statement inquiry', 'avg': 120, 'min': 60,  'max': 300},
]


def create_branches():
    for b in BRANCHES:
        branch, created = Branch.objects.get_or_create(
            code=b['code'],
            defaults={
                'name': b['name'],
                'location': b['location'],
                'city': b['city'],
                'state': b['state'],
                'contact_phone': b['contact_phone'],
                'contact_email': b['contact_email'],
                'opening_time': time(8, 0),
                'closing_time': time(17, 0),
            }
        )
        status = 'CREATED' if created else 'already exists'
        print(f"[{status}] Branch: {branch.name}")

        # Add the services for this branch
        for s in SERVICES:
            ServiceCategory.objects.get_or_create(
                name=s['name'],
                branch=branch,
                defaults={
                    'description': s['desc'],
                    'average_service_time': s['avg'],
                    'min_service_time': s['min'],
                    'max_service_time': s['max'],
                    'is_active': True,
                }
            )
        print(f"  -> {len(SERVICES)} services added")


if __name__ == '__main__':
    create_branches()
    print("\nDone! Visit the customer page to see the new branches.")