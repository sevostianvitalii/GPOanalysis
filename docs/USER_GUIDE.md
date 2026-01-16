# GPO Analysis Tool - User Guide

## Introduction

The GPO Analysis Tool helps system administrators audit, analyze, and optimize Active Directory Group Policy Objects. It detects conflicts, identifies duplicates, suggests security improvements, and allows for object-based policy lookup.

---

## 🚀 Installation & Setup

### Prerequisites
- **Docker** or **Podman** installed on your system.

### Running the Tool (Container)

1. **Pull the image** (Recommended):
   ```bash
   podman pull ghcr.io/sevostianvitalii/gpoanalysis:latest
   ```

2. **Run the container**:
   ```bash
   podman run -d -p 8080:80 --name gpo-analyzer ghcr.io/sevostianvitalii/gpoanalysis:latest
   ```

3. **Access the Interface**:
   Open a web browser and go to: `http://localhost:8080`

---

## 📥 Getting GPO Data

The tool analyzes GPO reports exported from your Windows environment. It does NOT connect directly to Active Directory.

### 1. Export All GPOs (Recommended)
Run this command in PowerShell on a Domain Controller or machine with RSAT:

```powershell
Get-GPOReport -All -ReportType HTML -Path "all_gpos.html"
```

### 2. Export Specific GPO
```powershell
Get-GPOReport -Name "Default Domain Policy" -ReportType HTML -Path "ddp.html"
```

### 3. Machine Policy Report (GPResult)
To analyze policies applied to a specific machine/user:
```powershell
gpresult /H report.html
```

---

## 🛠️ Using the Tool

### 1. Uploading Files
- Navigate to the **Dashboard** (default view) or **Upload** tab.
- Click "Choose Files" or drag & drop your `.html` or `.xml` reports.
- Click **Upload**.
- The files are parsed and stored in the **Persistent Library**.

### 2. Using the Library
Go to the **Library** tab to manage your GPO collection.
- **View**: See all uploaded GPOs, their modify dates, and link counts.
- **Select**: Check the boxes next to the GPOs you want to analyze.
- **Delete**: Select GPOs and click the **Delete** button to remove them from the database.
- **Analyze**: Select GPOs and click **Analyze Selected** to run a fresh analysis.

### 3. Analysis Dashboard
Once an analysis is running, you will see:
- **Dashboard**: High-level summary of issues (Critical, High, Medium, Low).
- **Conflicts**: Table showing settings that contradict each other across different GPOs.
- **Duplicates**: List of redundant settings defined in multiple places.
- **Improvements**: Security and best-practice recommendations (e.g., "Enable Audit Logging").

### 4. Object Lookup
To find out what policies apply to a specific User, Computer, or OU:
1. Go to the **Object Lookup** tab.
2. Enter the name (e.g., `PC-01`, `JohnDoe`) or OU Distinguished Name (`OU=Sales,DC=example,DC=com`).
3. Click **Search**.
4. The tool will show:
   - **Direct Matches**: If you uploaded a `gpresult` for that object.
   - **Linked GPOs**: GPOs linked to the OU path you provided.
5. Click **Export CSV** to download the findings.

### 5. Exporting Results
- **Save Analysis**: Click "💾 Save" to store the current session for later.
- **Load Analysis**: Click "📂 Load Previous" on the Dashboard to recall a saved session.
- **Export CSV/PDF**: Use the buttons in the top right to download comprehensive reports.

---

## ❓ Troubleshooting

**"Upload failed" / "Server Error"**
- Check if your HTML files are valid GPO reports.
- Ensure the file size is not massive (files >50MB might time out).

**"Analysis failed"**
- Ensure you have selected at least one GPO from the library.
- If the error persists, try removing the problematic GPO from the library.

**"No GPOs found"**
- Verify the exported file contains GPO data (open it in a browser to check).
