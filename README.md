# GPO Analysis Tool

A cross-platform, containerized tool for analyzing Active Directory Group Policy Objects. Detect conflicts, find duplicates, and get improvement suggestions with a modern web UI.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Mac%20%7C%20Linux-blue)
![Container](https://img.shields.io/badge/container-Docker%20%7C%20Podman-orange)

## Features

- **💾 Persistent Library** - Store GPOs in a local database for historical analysis
- **🔍 Object-Based Analysis** - Find policies applied to specific Users, Computers, or OUs
- **⚔️ Conflict Detection** - Find contradicting policy settings across GPOs
- **📋 Duplicate Detection** - Identify redundant policies and GPOs
- **💡 Improvement Suggestions** - Get best practice recommendations
- **📊 Export Reports** - Download analysis as CSV or PDF
- **🌙 Dark Mode** - Modern UI with light/dark theme support
- **🐳 Cross-Platform** - Runs in Docker/Podman on Windows, Mac, or Linux

## Quick Start

### 🐳 Run with Container (Recommended)

#### Option A: Docker
```bash
# Build and run with Docker Compose
docker compose up --build
```

#### Option B: Podman
```bash
# Build and run with Podman Compose (if installed)
podman-compose up --build

# OR manual build and run with Podman
podman build -t gpo-analyzer .
podman run -d -p 8080:8080 gpo-analyzer
```

In both cases, access the UI at: **http://localhost:8080**

# Access the UI at http://localhost:8080
```

### Using GitHub Container Registry (Recommended for Mac/Apple Silicon)

Since `docker.io` might be blocked or require configuration, the easiest way to run the tool is pulling the pre-built image from GHCR. This image supports both Intel (`amd64`) and Apple Silicon (`arm64`) Macs.

```bash
# Pull the latest image
podman pull ghcr.io/sevostianvitalii/gpoanalysis:latest

# Run the container (detach mode, map port 8080)
podman run -d -p 8080:80 --name gpo-analyzer ghcr.io/sevostianvitalii/gpoanalysis:latest
```

# Access the UI at http://localhost:8080
```

### Using GitHub Container Registry (Pre-built Image)

If you have issues building locally (e.g., `docker.io` is blocked), you can pull the pre-built image from GHCR:

```bash
podman pull ghcr.io/sevostianvitalii/gpoanalysis:latest
podman run -d -p 8080:80 --name gpo-analyzer gpo-analyzer
```

For more details on the setup and usage, see the [User Guide](docs/USER_GUIDE.md) and [Walkthrough](docs/walkthrough.md).

## Exporting GPO Reports

The tool analyzes exported GPO files. Here's how to export from Windows:

### PowerShell (All GPOs in domain)

```powershell
Get-GPOReport -All -ReportType HTML -Path "all_gpos.html"
```

### PowerShell (Single GPO)

```powershell
Get-GPOReport -Name "Default Domain Policy" -ReportType HTML -Path "ddp.htm"
```

### PowerShell (XML format)

```powershell
Get-GPOReport -All -ReportType XML -Path "all_gpos.xml"
```

### gpresult (Current machine policies)

```powershell
gpresult /H report.html
```

## Supported File Formats

| Format | Source | Notes |
|--------|--------|-------|
| `.htm` / `.html` | Get-GPOReport -ReportType HTML | Recommended |
| `.xml` | Get-GPOReport -ReportType XML | Full metadata |
| `.html` | gpresult /H | Applied policies only |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker/Podman Container                   │
│  ┌─────────────────┐        ┌────────────────────────────┐  │
│  │  Nginx (Port 80) │───────▶│  React Frontend            │  │
│  │                  │        │  • File Upload             │  │
│  │                  │        │  • Dashboard               │  │
│  │                  │        │  • Conflict/Duplicate View │  │
│  │       ↓ /api     │        │  • Export Controls         │  │
│  └─────────────────┘        └────────────────────────────┘  │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  FastAPI Backend (Port 8000)                             ││
│  │  • SQLite Database (Peristent Storage)                   ││
│  │  • GPO Parser (HTML/XML)                                 ││
│  │  • Conflict Detector                                     ││
│  │  • Duplicate Detector                                    ││
│  │  • Improvement Engine                                    ││
│  │  • CSV/PDF Exporters                                     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload GPO export files |
| GET | `/api/library` | List stored GPOs |
| POST | `/api/analysis/start` | Analyze selected GPOs |
| GET | `/api/analysis/object` | Lookup effective policies |
| GET | `/api/stats` | Get analysis statistics |
| GET | `/api/analysis` | Get full analysis result |
| GET | `/api/gpos` | List analyzed GPOs |
| GET | `/api/conflicts` | Get conflict reports |
| GET | `/api/duplicates` | Get duplicate reports |
| GET | `/api/improvements` | Get improvement suggestions |
| GET | `/api/export/csv` | Download CSV report |
| GET | `/api/export/pdf` | Download PDF report |
| GET | `/api/export/object` | Download Object analysis (CSV) |

## Development

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (React/Vite)

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
GPOanalysis/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API routes
│   │   ├── analyzers/     # Conflict, duplicate, improvement detection
│   │   ├── exporters/     # CSV and PDF export
│   │   ├── models/        # Pydantic data models
│   │   ├── parsers/       # HTML/XML GPO parsers
│   │   └── main.py        # FastAPI application
│   └── data/              # SQLite database storage
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── styles/        # CSS styles
│   │   ├── App.jsx        # Main application
│   │   └── main.jsx       # Entry point
│   └── package.json
├── deploy/
│   ├── nginx.conf         # Nginx configuration
│   └── supervisord.conf   # Process manager config
├── Dockerfile             # Multi-stage container build
├── docker-compose.yml     # Container orchestration
└── README.md
```

## License

See LICENSE file for details.
