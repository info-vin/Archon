import os
import base64
from dotenv import load_dotenv
from supabase import create_client
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_SERVICE_KEY starts with: {key[:20] if key else 'None'}")

supabase = create_client(url, key)

# Get encrypted credentials
settings = supabase.table("archon_settings").select("*").execute()

def derive_key(svc_key: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"static_salt_for_credentials",
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(svc_key.encode()))

def try_decrypt(encrypted_val: str, svc_key: str) -> str:
    try:
        fernet = Fernet(derive_key(svc_key))
        decrypted = fernet.decrypt(base64.urlsafe_b64decode(encrypted_val.encode("utf-8")))
        return decrypted.decode("utf-8")
    except Exception as e:
        return f"[Error] {type(e).__name__}: {e}"

for item in settings.data:
    if item["is_encrypted"] and item["encrypted_value"]:
        enc_val = item["encrypted_value"]
        print(f"\nKey: {item['key']}")
        print(f"  Encrypted val: {enc_val[:30]}...")
        
        # Test 1: Real key from .env
        res_env = try_decrypt(enc_val, key)
        print(f"  Decrypt with env key: {'SUCCESS' if not res_env.startswith('[Error]') else res_env}")
        
        # Test 2: Default key for development
        res_default = try_decrypt(enc_val, "default-key-for-development")
        print(f"  Decrypt with default key: {'SUCCESS' if not res_default.startswith('[Error]') else res_default}")
