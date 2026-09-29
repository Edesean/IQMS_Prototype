# backend/seed_demo_data.py

import os
import django
import random
from datetime import time, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iqms_backend.settings')
django.setup()

from api.models import Branch, ServiceCategory, User, Customer, QueueTicket


def clear_existing_tickets():
    count = QueueTicket.objects.count()
    QueueTicket.objects.all().delete()
    print(f"[INFO] Cleared {count} existing tickets")


def create_historical_data(days=14, tickets_per_day=25):
    branch = Branch.objects.first()
    if not branch:
        print("[ERROR] No branch found. Run create_sample_data.py first.")
        return

    services = list(ServiceCategory.objects.filter(branch=branch))
    teller = User.objects.filter(role='teller').first()

    first_names = ['John', 'Mary', 'Ahmed', 'Chioma', 'Emeka', 'Fatima',
                   'Tunde', 'Ngozi', 'Ibrahim', 'Blessing', 'Yusuf', 'Aisha',
                   'Kelechi', 'Funmi', 'Samuel', 'Zainab', 'Obinna', 'Grace']
    last_names = ['Okafor', 'Bello', 'Adeyemi', 'Ibrahim', 'Oluwaseun',
                  'Chukwu', 'Yusuf', 'Balogun', 'Eze', 'Mohammed', 'Adeleke']

    ticket_counter = 1
    created = 0

    for day_offset in range(days - 1, -1, -1):
        day = timezone.now() - timedelta(days=day_offset)
        num_tickets = random.randint(tickets_per_day - 8, tickets_per_day + 8)

        # Reset queue positions at the start of each day
        day_queue = []

        for _ in range(num_tickets):
            hour = random.choices(
                population=[8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                weights=[2, 5, 12, 15, 14, 12, 10, 8, 5, 2],
                k=1
            )[0]
            minute = random.randint(0, 59)
            joined_at = day.replace(hour=hour, minute=minute, second=0, microsecond=0)

            service = random.choice(services)
            customer = Customer.objects.create(
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                phone_number=f"080{random.randint(10000000, 99999999)}",
            )

            # ---- REALISTIC QUEUE POSITION AND WAIT TIME ----
            # Queue position cycles based on time of day (busier midday)
            is_peak = 1 if 10 <= hour <= 14 else 0
            if is_peak:
                queue_position = random.randint(3, 10)
            else:
                queue_position = random.randint(1, 5)

            # Wait time is CORRELATED with queue position and service time
            # This is what the ML model will learn from
            service_time_seconds = service.average_service_time
            base_wait_seconds = (queue_position - 1) * service_time_seconds

            # Peak hour adds 30% more wait
            if is_peak:
                base_wait_seconds *= 1.3

            # Realistic variation (±20% noise)
            noise_factor = random.uniform(0.8, 1.2)
            wait_seconds = int(base_wait_seconds * noise_factor)

            # Ensure minimum 1-minute wait
            wait_seconds = max(wait_seconds, 60)

            service_minutes = random.randint(2, 12)
            served_at = joined_at + timedelta(seconds=wait_seconds)
            completed_at = served_at + timedelta(minutes=service_minutes)

            # Small chance of cancellation
            status = 'completed'
            if random.random() < 0.08:
                status = 'cancelled'

            QueueTicket.objects.create(
                ticket_number=f"{service.name[:1].upper()}-{ticket_counter:04d}",
                branch=branch,
                service_category=service,
                customer=customer,
                teller=teller if status != 'cancelled' else None,
                status=status,
                queue_position=queue_position,
                estimated_wait_time=wait_seconds,
                actual_wait_time=wait_seconds if status == 'completed' else None,
                service_duration=service_minutes * 60 if status == 'completed' else None,
                joined_at=joined_at,
                called_at=served_at - timedelta(seconds=60),
                served_at=served_at if status == 'completed' else None,
                completed_at=completed_at if status == 'completed' else None,
            )
            ticket_counter += 1
            created += 1

    print(f"[OK] Created {created} historical tickets over {days} days")


if __name__ == "__main__":
    print("Generating demo data for IQMS manager dashboard...\n")
    clear_existing_tickets()
    create_historical_data(days=14, tickets_per_day=25)
    print("\nDone! Visit the manager dashboard to see the analytics.")
    print("Now run: python prediction/train_model.py")