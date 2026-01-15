# Getting Started with GPO Analysis Tool

A step-by-step guide to download and run the GPO Analysis Tool on your computer.

---

## Prerequisites

You need **one** of the following installed:

| Option | Best For | Download |
|--------|----------|----------|
| **Docker Desktop** | Windows, Mac | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Podman Desktop** | Mac, Linux | [podman-desktop.io](https://podman-desktop.io/) |

> **Windows Users**: Docker Desktop is recommended. Make sure WSL2 is enabled during installation.

> **Mac Users**: Either Docker Desktop or Podman works. Podman is free and lighter weight.

---

## Step 1: Download the Tool

### Option A: Using Git (Recommended)

Open a terminal (PowerShell on Windows, Terminal on Mac) and run:

```bash
git clone https://github.com/sevostianvitalii/GPOanalysis.git
cd GPOanalysis
```

### Option B: Download ZIP

1. Go to [github.com/sevostianvitalii/GPOanalysis](https://github.com/sevostianvitalii/GPOanalysis)
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP to a folder of your choice
5. Open a terminal and navigate to that folder

---

## Step 2: Build and Run

### Using Docker

```bash
# Build and start the container
docker compose up --build

# Wait for the build to complete (first time takes 2-5 minutes)
# You'll see: "uvicorn running on http://127.0.0.1:8000"
```

### Using Podman

```bash
# Build the image
podman build -t gpo-analyzer .

# Run the container
podman run -d -p 8080:80 --name gpo-analyzer gpo-analyzer
```

---

## Step 3: Access the Tool

Open your web browser and go to:

### **<http://localhost:8080>**

You should see the GPO Analysis Tool welcome page with a file upload area.

---

## Step 4: Export GPO Reports from Windows

On a Windows machine with Active Directory tools, run PowerShell as Administrator:

### Export All GPOs (Recommended)

```powershell
# HTML format (most compatible)
Get-GPOReport -All -ReportType HTML -Path "C:\GPOExports\all_gpos.html"

# XML format (more detailed)
Get-GPOReport -All -ReportType XML -Path "C:\GPOExports\all_gpos.xml"
```

### Export Single GPO

```powershell
Get-GPOReport -Name "Default Domain Policy" -ReportType HTML -Path "C:\GPOExports\ddp.htm"
```

### Export Current Machine's Applied Policies

```powershell
gpresult /H C:\GPOExports\gpresult.html
```

> **Tip**: Create the folder first: `mkdir C:\GPOExports`

---

## Step 5: Analyze Your GPOs

1. **Open** <http://localhost:8080> in your browser
2. **Drag and drop** your exported `.html`, `.htm`, or `.xml` files onto the upload zone
3. **Click** "Analyze GPOs"
4. **Review** the results:
   - **Dashboard**: Overall health score and statistics
   - **Conflicts**: Settings that contradict each other
   - **Duplicates**: Redundant policies
   - **Improvements**: Best practice suggestions
5. **Export** reports as CSV or PDF using the export buttons

---

## Stopping the Tool

### Docker

```bash
# Press Ctrl+C in the terminal, or:
docker compose down
```

### Podman

```bash
podman stop gpo-analyzer
podman rm gpo-analyzer
```

---

## Starting Again Later

### Docker

```bash
cd GPOanalysis
docker compose up
```

### Podman

```bash
podman start gpo-analyzer
```

---

## Troubleshooting

### "Port 8080 already in use"

Change the port in `docker-compose.yml`:

```yaml
ports:
  - "8081:80"  # Change 8080 to 8081
```

Then access at <http://localhost:8081>

### "Docker daemon not running"

- **Windows**: Start Docker Desktop from the Start Menu
- **Mac**: Start Docker Desktop or Podman Desktop from Applications

### "Cannot connect to <http://localhost:8080>"

1. Wait 30 seconds for the container to fully start
2. Check if container is running: `docker ps` or `podman ps`
3. Check logs: `docker compose logs` or `podman logs gpo-analyzer`

### "No GPOs found in uploaded file"

- Make sure the file is from `Get-GPOReport` or `gpresult`
- Check the file opens properly in a browser first
- Try both HTML and XML formats

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2 GB | 4 GB |
| Disk Space | 500 MB | 1 GB |
| OS | Windows 10, macOS 11, Linux | Latest versions |

---

## Need Help?

- **Issues**: [github.com/sevostianvitalii/GPOanalysis/issues](https://github.com/sevostianvitalii/GPOanalysis/issues)
- **Documentation**: See `docs/` folder in the repository
