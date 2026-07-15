import jwt
import os
import sys
from datetime import datetime, timedelta, timezone

def generate_test_token(user_id: str, email: str, roles: list[str], session_id: str = "test-session") -> str:
    # Read the JWT secret key
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-change-me")
    
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "sid": session_id,
        "aud": "coreason-platform",
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m src.core.security.generate_token [user_id] [email] [role1,role2,...]")
        print("Example: python -m src.core.security.generate_token dev_test_user dev@coreason.ai Developer,Supervisor")
        sys.exit(1)
        
    user_id = sys.argv[1]
    email = sys.argv[2]
    roles = sys.argv[3].split(",") if len(sys.argv) > 3 else ["Developer"]
    
    print(generate_test_token(user_id, email, roles))
