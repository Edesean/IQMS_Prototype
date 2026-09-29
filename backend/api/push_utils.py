# backend/api/push_utils.py

import os
import json
from pathlib import Path
from pywebpush import webpush, WebPushException


VAPID_PRIVATE_KEY_PATH = os.getenv('VAPID_PRIVATE_KEY_PATH', 'vapid_private.pem')
VAPID_CLAIMS_EMAIL = os.getenv('VAPID_CLAIMS_EMAIL', 'mailto:admin@example.com')


def send_push_to_customer(customer, title, body, ticket_number=None):
    """Send a browser push notification to all devices of a customer."""
    from .models import PushSubscription

    subs = PushSubscription.objects.filter(customer=customer)
    if not subs.exists():
        return

    payload = json.dumps({
        'title': title,
        'body': body,
        'ticket_number': ticket_number or '',
    })

    private_key_path = str(Path(__file__).resolve().parent.parent / VAPID_PRIVATE_KEY_PATH)

    sent = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=private_key_path,
                vapid_claims={'sub': VAPID_CLAIMS_EMAIL},
            )
            sent += 1
        except WebPushException as e:
            if e.response is not None and e.response.status_code in (404, 410):
                sub.delete()
        except Exception as e:
            print(f"[PUSH ERROR] {e}")

    print(f"[PUSH] sent={sent} to {customer.phone_number}")