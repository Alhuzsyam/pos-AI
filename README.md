# POS-AI SaaS

> Multi-Tenant Point of Sale dengan AI — Handle banyak cafe/toko sekaligus.

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + SQLAlchemy + MySQL |
| Frontend | Vue 3 + Vite + Tailwind CSS |
| Auth | JWT (Access + Refresh token) |
| Deploy | Docker Compose (single stack) |

---

## Fitur Utama

### Multi-Tenant SaaS
- Satu instance bisa handle **banyak cafe/toko** sekaligus
- Data tiap tenant **terisolasi** sempurna
- Superadmin bisa manage semua tenant dari 1 dashboard

### Role Management
| Role | Akses |
|------|-------|
| `superadmin` | Semua tenant, buat/hapus tenant |
| `admin` | Full access 1 tenant + manage user |
| `manager` | Laporan + kelola menu & staff |
| `kasir` | POS, transaksi, hutang, reservasi |
| `inventory` | Kelola stok & produk |

### AI per Tenant (Self-Service)
Tiap tenant setup **API key sendiri** — tidak berbagi subscription:
- **OpenAI** (GPT-4o, GPT-4o-mini)
- **Gemini** (Google, ada free tier!)
- **Groq** (Llama 3.3, gratis dan cepat!)
- **Ollama** (lokal, privat)

### Weekly AI Insights
Setiap minggu, AI otomatis generate:
- Analisis performa bisnis (revenue, transaksi, profit)
- Identifikasi menu terlaris dan stok rendah
- **5 langkah aksi konkret** untuk growth bisnis depan

### Agentic AI Endpoints
Compatible dengan LangChain, AutoGen, CrewAI, dsb:

```
GET  /api/v1/ai/tools     → Tool definitions (OpenAI format)
POST /api/v1/ai/execute   → Execute tool call
GET  /api/v1/ai/context   → Business context untuk system prompt
```

**Available Tools:**
- `get_sales_summary` — Revenue & transaksi
- `get_top_menu` — Menu terlaris
- `check_stock` — Cek & filter stok
- `add_stock_movement` — Update stok via AI
- `get_expenses_summary` — Ringkasan pengeluaran
- `get_business_insights` — Analisis bisnis otomatis
- `create_sale` — Buat transaksi (untuk chatbot kasir)

---

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/Alhuzsyam/pos-AI.git
cd pos-AI
cp .env.example .env
# Edit .env sesuai kebutuhan — WAJIB set DB_PASSWORD & SUPERADMIN_PASSWORD
# sebelum first run, karena MySQL init cuma jalan sekali
```

### 2. Deploy

```bash
docker compose up -d --build
```

> **Penting**: Selalu pakai `--build` kalau habis update kode. Dockerfile backend
> pakai `COPY . .` — tanpa `--build`, Docker akan pakai image cache dan kode
> baru tidak akan masuk ke container.

### 3. Akses

| Service | URL |
|---------|-----|
| Frontend (App) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### 4. Login Pertama

```
Username : superadmin
Password : (sesuai SUPERADMIN_PASSWORD di .env, default: superadmin123)
```

### 5. Buat Tenant

1. Login sebagai superadmin
2. Buka **Tenant** di sidebar
3. Klik **Tambah Tenant** → isi nama toko + buat admin pertama
4. Login sebagai admin tenant
5. Buka **Settings** → setup API key AI
6. Mulai operasional!

---

## API Authentication

Semua endpoint (kecuali `/api/v1/auth/login`) butuh Bearer token:

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=password"

# 2. Gunakan token
curl http://localhost:8000/api/v1/reports/dashboard \
  -H "Authorization: Bearer <access_token>"
```

---

## Agentic AI Integration Example

```python
import requests

BASE_URL = "http://localhost:3000"
TOKEN = "your_access_token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. Ambil tool definitions
tools = requests.get(f"{BASE_URL}/api/v1/ai/tools", headers=HEADERS).json()

# 2. Ambil business context untuk system prompt
context = requests.get(f"{BASE_URL}/api/v1/ai/context", headers=HEADERS).json()

# 3. Execute tool
result = requests.post(f"{BASE_URL}/api/v1/ai/execute", headers=HEADERS, json={
    "tool_name": "get_business_insights",
    "arguments": {"period": "week"}
}).json()

print(result["result"]["insights"])
```

---

## Environment Variables

| Variable | Keterangan | Default |
|----------|------------|---------|
| `DB_PASSWORD` | Password MySQL | - |
| `SECRET_KEY` | JWT secret (min 32 char) | - |
| `SUPERADMIN_PASSWORD` | Password superadmin pertama | `superadmin123` |
| `BACKEND_PORT` | Port backend | `8000` |
| `FRONTEND_PORT` | Port frontend | `3000` |

> API key AI **tidak** disimpan di `.env`. Tiap tenant setup sendiri via UI Settings.

---

## Troubleshooting

### Backend restart-loop dengan SQLAlchemy `InvalidRequestError`

Kalau backend terus restart dan log-nya penuh `Mapper has no property ...`,
itu berarti salah satu model relationship belum di-declare balik (missing
`back_populates` pair). Fix sudah ada di commit `f706275` — pastikan kode
lokal up-to-date (`git pull origin main`) dan **rebuild image**:

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

### Deploy di Windows Server — `entrypoint.sh` error (line ending CRLF)

Kalau backend langsung exit saat startup dengan error seperti:

```
exec /entrypoint.sh: no such file or directory
```

atau

```
/bin/sh^M: bad interpreter
```

Penyebabnya: Git di Windows otomatis convert line ending dari **LF → CRLF**
saat clone. Shell script di Linux container **harus** pakai LF — CRLF bikin
interpreter-nya gagal baca file.

**Fix — convert `entrypoint.sh` ke LF sebelum build:**

Pakai `dos2unix` (kalau tersedia di server):

```bash
dos2unix backend/entrypoint.sh
docker compose up -d --build
```

Atau via PowerShell:

```powershell
(Get-Content backend\entrypoint.sh -Raw) -replace "`r`n", "`n" | Set-Content backend\entrypoint.sh -NoNewline
```

Atau cegah dari awal — set Git supaya tidak auto-convert line ending sebelum clone:

```bash
git config --global core.autocrlf false
git clone https://github.com/Alhuzsyam/pos-AI.git
```

> **VS Code**: Buka `entrypoint.sh`, klik **CRLF** di status bar pojok kanan bawah → pilih **LF** → Save.

---

### Login gagal 422 / 401 setelah fresh deploy

Cek log backend dulu:

```bash
docker compose logs --tail=50 backend
```

Yang harus nongol: `Superadmin created.` → `Uvicorn running on http://0.0.0.0:8000`.
Kalau tidak ada `Superadmin created.`, seeder-nya gagal — biasanya karena DB
connection issue (lihat section di atas).

### Kode terbaru tidak kepake setelah `git pull`

Backend image di-cache. **Selalu** `--build` atau `--no-cache`:

```bash
docker compose down
docker compose build --no-cache backend
docker compose up -d
```

---

## Struktur Project

```
pos-AI/
├── backend/
│   ├── app/
│   │   ├── models/         # SQLAlchemy models (multi-tenant)
│   │   ├── routers/        # FastAPI routers
│   │   │   ├── auth.py     # JWT auth
│   │   │   ├── tenants.py  # Tenant management (superadmin)
│   │   │   ├── users.py    # User & role management
│   │   │   ├── inventory.py
│   │   │   ├── pos.py      # Kasir, menu, hutang, reservasi
│   │   │   ├── reports.py  # Analytics & dashboard
│   │   │   ├── ai.py       # Agentic AI endpoints
│   │   │   └── settings.py # API key + weekly insights
│   │   ├── core/
│   │   │   ├── security.py # JWT utils
│   │   │   └── deps.py     # Role guards & tenant filter
│   │   └── main.py
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/          # Semua halaman
│   │   ├── stores/auth.js  # Pinia auth store
│   │   ├── composables/    # axios instance
│   │   └── router/
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

Made with FastAPI + Vue 3 + Tailwind + ❤️
