from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app import models  # noqa: F401 - trigger model registration

# Import all routers
from app.routers import auth, tenants, users, inventory, pos, reports, ai, settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Buat semua tabel kalau belum ada
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="POS-AI SaaS",
    description="""
## POS-AI - Multi-Tenant Point of Sale dengan AI

### Features
- **Multi-Tenant SaaS** - Handle banyak cafe/toko sekaligus
- **Role Management** - SuperAdmin, Admin, Manager, Kasir, Inventory
- **Inventory Management** - Stok dengan auto-deduct via resep
- **POS / Kasir** - Transaksi, menu, KDS
- **AI Endpoints** - OpenAI-compatible tool definitions untuk agentic AI
- **Reports & Analytics** - Dashboard, revenue, menu performance

### Roles
| Role | Akses |
|------|-------|
| `superadmin` | Semua tenant, global settings |
| `admin` | Full access 1 tenant |
| `manager` | Reports, manage staff |
| `kasir` | POS, transaksi, hutang |
| `inventory` | Kelola stok & produk |

### Agentic AI Integration
Gunakan `GET /api/v1/ai/tools` untuk mendapatkan tool definitions dalam format OpenAI function calling.
Gunakan `POST /api/v1/ai/execute` untuk eksekusi tool call dari agent.
""",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(users.router)
app.include_router(inventory.router)
app.include_router(pos.router)
app.include_router(reports.router)
app.include_router(ai.router)
app.include_router(settings.router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/v1/health", tags=["Health"])
def api_health():
    return {"status": "ok", "version": settings.APP_VERSION}
