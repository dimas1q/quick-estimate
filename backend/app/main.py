from fastapi import FastAPI
from app.api import estimates
from app.api import auth
from app.api import user
from app.api import templates
from app.api import clients
from app.api import versions
from app.core.database import create_tables
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="QuickEstimate")

# ✅ Разрешаем доступ с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await create_tables()

app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/users")
app.include_router(estimates.router, prefix="/api/estimates")
app.include_router(templates.router, prefix="/api/templates")
app.include_router(clients.router, prefix="/api/clients")
app.include_router(versions.router, prefix="/api/versions")
