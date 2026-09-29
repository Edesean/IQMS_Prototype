from api.models import Branch, ServiceCategory, User
from datetime import time

# ---- 1. Create branches ----
branches = [
    {'name': 'Lekki Branch',  'code': 'BR005', 'city': 'Lagos',  'state': 'Lagos',
     'location': 'Admiralty Way, Lekki', 'phone': '01-9999999', 'email': 'lekki@bank.com'},
    {'name': 'Kano Branch',   'code': 'BR006', 'city': 'Kano',   'state': 'Kano',
     'location': '12, Zoo Road, Kano',   'phone': '064-111222', 'email': 'kano@bank.com'},
    {'name': 'Enugu Branch',  'code': 'BR007', 'city': 'Enugu',  'state': 'Enugu',
     'location': '5, Ogui Road, Enugu',  'phone': '042-333444', 'email': 'enugu@bank.com'},
]

for b in branches:
    if Branch.objects.filter(code=b['code']).exists():
        print(f"[EXISTS] {b['name']}")
    else:
        Branch.objects.create(
            name=b['name'], code=b['code'],
            location=b['location'], city=b['city'], state=b['state'],
            contact_phone=b['phone'], contact_email=b['email'],
            opening_time=time(8, 0), closing_time=time(16, 0),
        )
        print(f"[CREATED] {b['name']}")

# ---- 2. Add services for each new branch ----
services = [
    ('Cash Deposit',    'Deposit cash into account',             300, 120, 600),
    ('Cash Withdrawal', 'Withdraw cash from account',            180,  60, 300),
    ('Cheque Deposit',  'Deposit cheque into account',           420, 180, 900),
    ('OTC Transfer',    'Over-the-counter funds transfer',       240, 120, 480),
    ('Account Inquiry', 'Account balance and statement inquiry', 120,  60, 300),
]

for b in Branch.objects.filter(code__in=['BR005', 'BR006', 'BR007']):
    for name, desc, avg, mn, mx in services:
        if not ServiceCategory.objects.filter(name=name, branch=b).exists():
            ServiceCategory.objects.create(
                name=name, description=desc, branch=b,
                average_service_time=avg, min_service_time=mn,
                max_service_time=mx, is_active=True,
            )
    print(f"[SERVICES] 5 services for {b.name}")

# ---- 3. Summary ----
print("\n=== DONE ===")
print(f"Total branches: {Branch.objects.count()}")
print(f"Total services: {ServiceCategory.objects.count()}")
print(f"Total users:    {User.objects.count()}")