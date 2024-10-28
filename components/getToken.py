import jwt
from fastapi import Request, HTTPException
from typing import Optional
import os

SECRET_KEY = os.getenv("SECRET_KEY")

def get_current_user_from_cookie(request: Request) -> Optional[dict]:
    print("Cookies:", request.cookies)  # Log all cookies
    token = request.cookies.get("token")  # Get the token from cookies
    print("Request:", request)
    if not token:
        print("No token found in cookies")
        return None

    try:
        # Decode the JWT token
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")