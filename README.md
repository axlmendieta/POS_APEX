# Nexus POS 🚀

**An Intelligent, Multi-Tenant Point of Sale & Onboarding System.**

Nexus POS is a cloud-native solution designed for modern retail and wholesale operations. It bridges the gap between proprietary stores and partner networks using a polymorphic architecture, powered by Python (FastAPI) and a minimalist, transition-rich Frontend.

---

## ✨ Key Features

### 🏢 Multi-Tenant Architecture
-   **Proprietary Stores**: Full control over inventory, pricing, and staff.
-   **Partner Network**: "Wholesale Order" logic for external partners (B2B2C).
-   **Polymorphic Stock Logic**: Automatically distinguishes between internal *Stock Transfers* and external *Wholesale Sales*.

### 🧠 Intelligence Layer
-   **Demand Forecasting**: Uses Historical Sales Data (dummy generator included) to calculate Reorder Points (ROP) and forecast demand.
-   **AI Loyalty Engine**: Analyzes cart patterns in real-time to suggest intelligent upsells (e.g., "Buy Chips with your Soda!").

### 🛡️ Security & RBAC
-   **Role-Based Access Control**:
    -   `super_admin`: Global access (God Mode).
    -   `branch_manager`: Location-specific management.
    -   `internal_cashier`: POS access only.
-   **Manager Overrides**: Sensitive actions (Void Transaction, Void Line Item) require supervisor approval.

### 🎨 Modern Frontend
-   **SPA Experience**: Hash-based routing (`#sale`, `#reports`) with smooth fade transitions.
-   **Responsive Design**: Mobile-first "Client App" for customers and Desktop POS for staff.
-   **Dynamic UI**: Real-time stock tooltips and customer metrics.

---

## 🛠️ Tech Stack

-   **Backend**: Python 3.10+, FastAPI, Uvicorn.
-   **Database**: PostgreSQL / SQLite (via SQLAlchemy ORM).
-   **Frontend**: Vanilla JS, HTML5, CSS3 (No build step required).
-   **Data Science**: Pandas, Scikit-Learn (for forecasting).

---

## 🚀 Getting Started

### 1. Prerequisites
-   Python 3.10 or higher.
-   Virtual Environment (Recommended).

### 2. Installation

```bash
# Clone the repository
git clone <repository_url>
cd POS

# Create Virtual Environment
python -m venv venv

# Activate Venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Database Setup

Create a `.env` file (optional, defaults to SQLite `test.db` if not provided, see `database.py`).

Initialize the Schema:
```bash
python init_db.py
```

Create Super Admin User:
```bash
python create_super_admin.py
```

### 4. Running the Application

Start the API Server:
```bash
uvicorn api:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## 📖 Usage Guide

### Staff POS Interface
1.  Open `http://127.0.0.1:8000/` in your browser.
2.  **Login**:
    -   **Username**: `super_admin_user`
    -   **Password**: `secure_password_123`
3.  **Explore**:
    -   **New Sale**: Add items, check AI upsells, complete transactions.
    -   **Navigation**: Use the hamburger menu to switch to "Sales Reports" or "Admin Panel" (Permissions permitting).

### Customer Loyalty App
1.  Open `http://127.0.0.1:8000/app` on a mobile device (or simulator).
2.  View Points Balance and "Just For You" offers.

---

## 📂 Project Structure

```text
.
├── api.py                 # FastAPI Entry Point & Routes
├── crud.py                # Database Operations (Repository Pattern)
├── database.py            # DB Connection & Session
├── models.py              # SQLAlchemy Models
├── schemas.py             # Pydantic Schemas
├── service_logic.py       # Core Business Logic (Sales, Transfers)
├── service_admin.py       # Admin & Onboarding Logic
├── recommendation_engine.py # AI Loyalty Logic
├── forecasting.py         # Demand Forecasting Logic
├── frontend/              # Static Assets
│   ├── pos.html           # Main POS SPA
│   ├── styles.css         # CSS Variables & Transitions
│   └── app.js             # Frontend Controller (Router & Logic)
└── requirements.txt       # Dependencies
```
