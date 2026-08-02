# AegisAI

AI-powered Road Accident Hotspot Prediction & Prevention Platform.

This repository contains a frontend dashboard, a FastAPI backend, and AI dataset tools to visualize and report roadway incidents.

---

## 🔧 Setup Guide

Follow these steps after cloning the repository.

### 1. Clone the repository

```bash
git clone https://github.com/archanaaravin/AegisAI.git
```

### 2. Open the project folder

```bash
cd AegisAI
```

### 3. Create a Python virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

On Git Bash / WSL:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 4. Install backend dependencies

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

If you want to save the installed dependencies after testing, create a requirements file:

```bash
pip freeze > backend/requirements.txt
```

---

## 🚀 Run the application

### 1. Start the backend server

From the repository root:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend API will be available at:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/frontend`
- `http://127.0.0.1:8000/app`

### 2. Open the frontend dashboard

Open this URL in your browser:

```text
http://127.0.0.1:8000/frontend
```

This loads the dashboard and connects it to the backend APIs.

---

## 📁 Project Structure

- `ai/` — Dataset and AI utilities
- `backend/` — FastAPI backend and API routers
- `frontend/` — Single-page dashboard UI

---

## 🧪 Available APIs

- `GET /accidents/summary` — Dataset summary with counts
- `GET /accidents/history` — Recent incident history from the dataset
- `POST /accidents/report` — Save a citizen incident report to JSON
- `GET /accidents/reports` — Retrieve saved incident reports
- `GET /accidents/route` — Calculate route options between locations
- `POST /predict/` — Run AI risk prediction

---

## 📝 Report Submission

Use the frontend report modal to submit an incident report.
The backend saves reports to `backend/data/reports.json` and updates the `Citizen Reports Processed` counter.

---

## ⚠️ Notes

- If the frontend does not load, confirm the backend server is running on port `8000`.
- If report submission fails, refresh the page and verify the backend logs.
- If a dependency is missing, rerun `pip install fastapi uvicorn sqlalchemy pydantic`.

---

## 💡 Quick Commands

Activate the virtual environment:

```bash
# PowerShell
.\.venv\Scripts\Activate.ps1

# Cmd
.venv\Scripts\activate.bat

# Bash / WSL
source .venv/bin/activate
```

Run the backend:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature/your-feature-name
```

3. Make your changes
4. Commit your work

```bash
git commit -m "Add feature"
```

5. Push the branch

```bash
git push origin feature/your-feature-name
```

6. Open a pull request

---

## 📄 License

This repository currently does not include a license file.

If you make this project public, add a license such as MIT or Apache 2.0.
