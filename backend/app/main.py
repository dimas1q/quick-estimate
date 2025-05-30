from http.client import HTTPException
import os
from urllib.request import Request
from fastapi import FastAPI
from app.api import estimates
from app.api import auth
from app.api import user
from app.api import templates
from app.api import clients
from app.api import versions
from app.api import analytics
from app.core.database import create_tables
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

app = FastAPI(title="QuickEstimate")

# CORS (только для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await create_tables()

# API
app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/users")
app.include_router(estimates.router, prefix="/api/estimates")
app.include_router(templates.router, prefix="/api/templates")
app.include_router(clients.router, prefix="/api/clients")
app.include_router(versions.router, prefix="/api/versions")
app.include_router(analytics.router, prefix="/api/analytics")

# SPA frontend fallback
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
index_file = os.path.join(frontend_path, "index.html")

if os.path.exists(index_file):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_vue_app(request: Request, full_path: str):
        if request.url.path.startswith("/api"):
            raise HTTPException(status_code=404, detail="API route not found")
        return FileResponse(index_file)
