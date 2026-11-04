import os

DATABASE_URL = os.environ["DATABASE_URL"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

if len(JWT_SECRET) < 32 or JWT_SECRET.lower().startswith("cambia"):
    raise RuntimeError("JWT_SECRET inseguro: define uno largo en .env (ej. python3 -c \"import secrets;print(secrets.token_hex(32))\")")
