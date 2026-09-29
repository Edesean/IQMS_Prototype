# backend/generate_vapid_keys.py

from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64
import os

v = Vapid()
v.generate_keys()

# Public key (base64url) — goes to frontend
public_bytes = v.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')

# Private key (PEM) — stays on backend
private_pem = v.private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode()

with open('vapid_private.pem', 'w') as f:
    f.write(private_pem)

print("\n=========== BACKEND (.env) ===========\n")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print("VAPID_PRIVATE_KEY_PATH=vapid_private.pem")
print("VAPID_CLAIMS_EMAIL=mailto:your-email@gmail.com")
print("\n=========== FRONTEND (frontend/.env) ===========\n")
print(f"VITE_VAPID_PUBLIC_KEY={public_b64}")
print()