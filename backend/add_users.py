from api.models import Branch, ServiceCategory
from datetime import time
b, created = Branch.objects.get_or_create(
    code='BR009',
    defaults={
        'name': 'Ekrejeta Branch',
        'location': 'Ekrejeta, Delta State',
        'city': 'Warri',
        'state': 'Delta',
        'contact_phone': '053-111222',
        'contact_email': 'ekrejeta@bank.com',
        'opening_time': time(8, 0),
        'closing_time': time(16, 0),
    }
)
print(f"[BRANCH] {b.name} created={created}")
services = [
    ('Cash Deposit',    'Deposit cash',    300, 120, 600),
    ('Cash Withdrawal', 'Withdraw cash',   180,  60, 300),
    ('Cheque Deposit',  'Deposit cheque',  420, 180, 900),
    ('OTC Transfer',    'Funds transfer',  240, 120, 480),
    ('Account Inquiry', 'Balance inquiry', 120,  60, 300),
]
for name, desc, avg, mn, mx in services:
    ServiceCategory.objects.get_or_create(
        name=name, branch=b,
        defaults={
            'description': desc,
            'average_service_time': avg,
            'min_service_time': mn,
            'max_service_time': mx,
            'is_active': True,
        }
    )
print("[SERVICES] 5 services added")