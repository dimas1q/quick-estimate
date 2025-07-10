import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from app.api import estimates, auth, user, templates, clients, versions, analytics, notes
from app.core.database import create_tables
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="QuickEstimate")

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
app.include_router(notes.router, prefix="/api/notes")

# Path to built frontend (dist)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
index_file = os.path.join(frontend_path, "index.html")

if os.path.exists(index_file):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc):
        if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
            if getattr(exc, "detail", None) and exc.detail != "Not Found":
                return await http_exception_handler(request, exc)
        if request.url.path.startswith("/api"):
            return JSONResponse(status_code=404, content={"detail": "API route not found"})
        if os.path.splitext(request.url.path)[1]:
            return await app.default_exception_handler(request, exc)
        return FileResponse(index_file)
