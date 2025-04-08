from fastapi import FastAPI
from app.api import estimates
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

app.include_router(estimates.router, prefix="/api/estimates")
