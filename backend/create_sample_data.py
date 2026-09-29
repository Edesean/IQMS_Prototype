# backend/create_sample_data.py

import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iqms_backend.settings')
django.setup()

from api.models import Branch, ServiceCategory, User


def create_sample_data():
    print("Creating sample data...\n")

    # Create branch
    branch, created = Branch.objects.get_or_create(
        code="BR001",
        defaults={
            'name': "Marina Branch",
            'location': "1, Marina Road, Lagos Island",
            'city': "Lagos",
            'state': "Lagos",
            'contact_phone': "01-2345678",
            'contact_email': "marina@bank.com",
            'opening_time': time(8, 0),
            'closing_time': time(17, 0),
        }
    )
    print(f"[OK] Branch: {branch.name}")

    # Create service categories
    services = [
        {"name": "Cash Deposit",     "desc": "Deposit cash into account",              "avg": 300, "min": 120, "max": 600},
        {"name": "Cash Withdrawal",  "desc": "Withdraw cash from account",             "avg": 180, "min": 60,  "max": 300},
        {"name": "Cheque Deposit",   "desc": "Deposit cheque into account",            "avg": 420, "min": 180, "max": 900},
        {"name": "OTC Transfer",     "desc": "Over-the-counter funds transfer",        "avg": 240, "min": 120, "max": 480},
        {"name": "Account Inquiry",  "desc": "Account balance and statement inquiry",  "avg": 120, "min": 60,  "max": 300},
    ]

    for s in services:
        obj, _ = ServiceCategory.objects.get_or_create(
            name=s["name"],
            branch=branch,
            defaults={
                'description': s["desc"],
                'average_service_time': s["avg"],
                'min_service_time': s["min"],
                'max_service_time': s["max"],
                'is_active': True,
            }
        )
        print(f"[OK] Service: {obj.name}")

    # Create manager user
    manager, created = User.objects.get_or_create(
        email="manager@bank.com",
        defaults={
            'full_name': "Branch Manager",
            'phone_number': "08012345678",
            'role': 'manager',
            'branch': branch,
            'is_staff': True,
            'is_superuser': False,
        }
    )
    manager.set_password("manager123")
    manager.save()
    print(f"[OK] Manager: {manager.email}")

    # Create teller user
    teller, created = User.objects.get_or_create(
        email="teller@bank.com",
        defaults={
            'full_name': "Teller One",
            'phone_number': "08087654321",
            'role': 'teller',
            'branch': branch,
            'is_staff': False,
            'is_superuser': False,
        }
    )
    teller.set_password("teller123")
    teller.save()
    print(f"[OK] Teller: {teller.email}")

    print("\n=========================================")
    print("Sample data created successfully!")
    print("=========================================")
    print("\nLogin Credentials:")
    print("  Manager: manager@bank.com / manager123")
    print("  Teller:  teller@bank.com  / teller123")
    print("  Admin:   admin@iqms.com   / admin123")


if __name__ == "__main__":
    create_sample_data()