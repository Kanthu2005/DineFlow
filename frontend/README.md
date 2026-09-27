# DineFlow - Modern Restaurant Management UI

A modern web interface built for the **DineFlow Restaurant Management System** backend (FastAPI + MongoDB).

---

## 🌟 Highlights & Features

- **Glassmorphic Aesthetic**: Deep luxury dark theme (`#0a0d14`), warm culinary amber accents, glowing status indicators, and clean typography with Google Fonts (*Outfit* and *Inter*).
- **Executive Dashboard**: Real-time metrics on active orders, occupied tables, settled revenue, pending kitchen tickets, and low inventory alerts.
- **Interactive Point of Sale (POS)**: Visual dish browser with Veg/Non-Veg indicators, dynamic category filter tabs, keyword search, table and customer assignment, live tax & subtotal recalculation, and 1-click **"Send to Kitchen"** dispatch.
- **Kitchen Display System (KDS)**: Kanban board for chefs featuring 4 operational columns (*Queued*, *Preparing*, *Ready to Serve*, *Handed Over*), urgency tags (*Normal*, *High*, *Urgent*), item instructions, and single-click ticket state advancement.
- **Tables & Reservations Floor Plan**: Visual interactive floor plan with table statuses (*Available*, *Occupied*, *Reserved*, *Out of Service*), table creation, and reservation booking system with customer assignment and time slots.
- **Billing & Cashier**: Invoice generation, payment settlements (Cash, Credit Card, Debit Card, UPI, Digital Wallet), and thermal customer receipt preview with 1-click printing (`window.print()`).
- **Inventory & Ingredients Tracker**: Real-time stock levels with color-coded threshold progress bars (healthy / warning / danger), one-click restocking modal, and historical stock movement logs.
- **Menu Administration**: Category creation, dish management, pricing, prep time, and direct availability / sold-out toggling.
- **Guest Feedback & Analytics**: Star ratings (overall, food, waitstaff service), customer review quotes, and rating distribution summary.
- **Staff Directory & RBAC**: Manage team accounts and restaurant roles (*Admin*, *Manager*, *Chef*, *Waiter*, *Cashier*).
- **1-Click Role Switcher**: Instant role testing via the top header pill without having to re-type passwords.
- **Live Connection Health Indicator**: Real-time ping and latency indicator with customizable Backend API URL setting.

---

## 🚀 How to Run

### Method 1: Run Frontend & Backend Independently (Recommended for UI Development)

1. **Start the Backend** (in your main project folder):
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend runs at `http://localhost:8000` with CORS enabled.*

2. **Start the Frontend UI** (in a separate terminal):
   ```bash
   python frontend/server.py
   ```
   *Open your browser at `http://localhost:3000`.*

---

### Method 2: Unified Backend + Frontend (Single Server)

Because the FastAPI backend automatically mounts the `frontend/` directory:

1. **Start the FastAPI Backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
2. **Access the UI directly**:
   - Navigate to: **`http://localhost:8000/app`** (or `http://localhost:8000/`)

---

## 👥 Demo Staff Accounts (Pre-configured)

Use the **"Switch Role"** pill in the top header bar to instantly switch between:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@dineflow.com` | `Password123!` | Complete unrestricted access across all modules |
| **General Manager** | `manager@dineflow.com` | `Password123!` | Operations, Staff, Billing, Reports, Menu & Tables |
| **Head Chef** | `chef@dineflow.com` | `Password123!` | Kitchen KDS, Dish Recipes, Stock & Ingredients |
| **Floor Waiter** | `waiter@dineflow.com` | `Password123!` | POS, Table Statuses, Reservations, Order Tracking |
| **Billing Cashier** | `cashier@dineflow.com` | `Password123!` | POS, Invoices, Payment Settlement, Receipts |
