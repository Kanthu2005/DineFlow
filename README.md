# 🍽️ DineFlow — Restaurant Order & Kitchen Operations System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Pytest](https://img.shields.io/badge/Tests-35%20Passing-brightgreen?logo=pytest&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An **Advanced Real-World Restaurant POS & Kitchen Operations Backend** built with **FastAPI**, **Python OOP**, and **100% MongoDB**. This system simulates end-to-end restaurant workflows: order creation, multi-unit recipe availability checks, transactional inventory deduction, kitchen ticket queueing with staff workload balancing, preparation time estimation, accurate Decimal billing, duplicate-resistant payments, multi-step refunds, and real-time MongoDB activity event logs.

---

## 🌟 Highlights & Architecture

- **100% MongoDB Backend**: Uses MongoDB and PyMongo for all transactional business data, inventory movements, kitchen events, audit logs, and feedback.
- **Python OOP Domain Models**: Rich domain entity classes (`MenuItem`, `OrderItem`, `Order`, `Ingredient`, `Recipe`, `RestaurantTable`, `Reservation`, `KitchenTicket`, `Invoice`) enforcing encapsulation and business rules.
- **Repository Pattern**: Strict decoupling of database operations from business logic via specialized repository classes in `app/repositories/`.
- **JWT & Role-Based Access Control (RBAC)**: Supports `ADMIN`, `MANAGER`, `CHEF`, `WAITER`, and `CASHIER` with endpoint security guards.
- **Precise Financial Calculations**: Powered by Python's `Decimal` and MongoDB `Decimal128` to avoid floating-point inaccuracies.
- **Unit Normalization & Recipe Math**: Automatically translates metric units (KG/G, L/ML, PCS) to check recipe requirements against warehouse inventory.
- **Automated Test Suite**: 35 comprehensive Pytest test cases covering all 30 assignment test cases plus advanced scenarios with 100% pass rate.

---

## 📁 Project Structure

```text
dineflow-main/
├── app/
│   ├── main.py                     # FastAPI application entry point with CORS & dual-routing
│   ├── config/
│   │   └── settings.py             # App configuration & JWT settings
│   ├── database/
│   │   ├── mongodb.py              # PyMongo client & collection bindings
│   │   └── indexes.py              # MongoDB indexing (unique & sparse indexes)
│   ├── models/
│   │   ├── entities.py             # Python OOP Domain entities with business logic
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── base_repository.py      # Generic CRUD repository
│   │   ├── menu_repository.py      # Menu items & categories
│   │   ├── inventory_repository.py # Ingredients & stock movements
│   │   ├── table_repository.py     # Tables & reservations
│   │   ├── order_repository.py     # Orders & order items
│   │   ├── kitchen_repository.py   # Kitchen tickets & assignments
│   │   ├── billing_repository.py   # Invoices, payments & refunds
│   │   ├── audit_log_repository.py # MongoDB activity logs, kitchen events & feedback
│   │   └── __init__.py
│   ├── schemas/                    # Pydantic v2 validation models
│   ├── services/                   # Service layer with core restaurant logic
│   │   ├── common.py               # Shared serialization & utility helpers
│   │   ├── menu_service.py         # Menu CRUD & category filtering
│   │   ├── ingredient_service.py   # Stock updates, low-stock alerts & serving capacity
│   │   ├── recipe_service.py       # Recipe mapping & ingredient availability checks
│   │   ├── table_service.py        # Table statuses & active order occupancy guards
│   │   ├── reservation_service.py  # Overlap collision logic & guest capacity
│   │   ├── order_service.py        # Order lifecycle, inventory deduction & cancellation
│   │   ├── kitchen_service.py      # Ticket progression, workload caps & prep time formula
│   │   ├── billing_service.py      # Invoices, taxes & discount calculations
│   │   ├── payment_service.py      # Duplicate references, overpayment checks & table release
│   │   ├── refund_service.py       # Multi-step refund approvals & audit
│   │   ├── feedback_service.py     # Customer ratings & reviews
│   │   └── report_service.py       # Daily sales, serving capacity & kitchen performance
│   ├── routes/                     # FastAPI route controllers
│   └── utils/
│       └── units.py                # Metric unit conversion utility
├── frontend/                   # Modern Luxury Dark-Theme SPA Web Application
│   ├── css/style.css           # Glassmorphism design system & responsive layout
│   ├── js/                     # Modular frontend controllers (api, pos, kds, tables, billing, etc.)
│   ├── index.html              # Complete SPA interface
│   ├── server.py               # Standalone frontend development server
│   └── README.md               # Frontend feature guide
├── tests/
│   ├── conftest.py             # Pytest environment setup
│   └── test_api.py             # Full 35-test suite (covers all assignment requirements)
├── run_dineflow.bat            # 1-Click launcher: starts backend & opens frontend in browser
├── open_frontend.bat           # 1-Click shortcut to open UI in browser
├── seed_roles.py               # Automated database seeder with default users & menu
├── requirements.txt            # Project dependencies
├── .env.example                # Environment template
└── README.md
```

---

## 💻 Modern Frontend Web Application

DineFlow includes a rich, responsive SPA frontend built with modern vanilla JavaScript and glassmorphic CSS, connected directly to the FastAPI + MongoDB backend:

- **Point of Sale (POS)**: Visual dish browser with category tabs, keyword search, guest table assignment, live tax/subtotal calculation, and 1-click order submission.
- **Kitchen Display System (KDS)**: Real-time Kanban board with 4 operational stages (*Queued*, *Preparing*, *Ready*, *Served*), priority tags, and 1-click status transitions.
- **Table Floor Plan & Reservations**: Visual dining floor plan, table status toggles, and reservation booking with overlap conflict protection.
- **Cashier & Billing**: Invoice generation, multiple payment methods (Cash, Card, UPI, Digital Wallet), and thermal customer receipt preview with 1-click printing.
- **Stock & Low-Stock Alerts**: Live warehouse inventory monitors with progress bar alerts and restock forms.
- **Menu & Recipe Management**: Catalog CRUD, price updates, recipe mappings, and sold-out toggling.
- **Customer Feedback**: Guest rating submissions (1-5 stars) and review analytics.
- **1-Click Role Switcher**: Quick test pill in header to switch between `ADMIN`, `MANAGER`, `CHEF`, `WAITER`, and `CASHIER` without re-entering credentials.

### Accessing the Web UI:
1. **Primary URL (Hosted alongside Backend)**:
   - Navigate to: **`http://localhost:8000/app/`** (or simply `http://localhost:8000/`)
2. **Windows 1-Click Launcher**:
   - Double-click `run_dineflow.bat` in the project root to start both backend & frontend.
   - Or double-click `open_frontend.bat` if the server is already active.
3. **Standalone UI Server (Alternative)**:
   ```bash
   python frontend/server.py
   ```
   - Opens on `http://localhost:3000` (auto-proxies requests to backend at `:8000/api`).

---

## 🔐 User Roles & Default Credentials

Run `python seed_roles.py` to seed default accounts:

| Role | Default Email | Password | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@dineflow.com` | `Password123!` | System settings, user management, full access |
| **MANAGER** | `manager@dineflow.com` | `Password123!` | Orders, inventory, staff assignments, reports, refund approvals |
| **CHEF** | `chef@dineflow.com` | `Password123!` | Kitchen tickets, preparation status, recipe management |
| **WAITER** | `waiter@dineflow.com` | `Password123!` | Customer orders, table management, reservations, order delivery |
| **CASHIER** | `cashier@dineflow.com` | `Password123!` | Bill generation, payment processing, refund requests |

---

## ⚡ Core Business Rules & Formulas

### 1. Recipe & Stock Deduction
When confirming an order, the system calculates exact ingredient needs based on recipe quantities multiplied by order item quantities with metric unit conversion (e.g. 250 g per Biryani × 4 = 1 KG deducted from KG inventory). Stock cannot become negative; if any ingredient is insufficient, confirmation is halted.

### 2. Price Snapshots
When an order item is added, the system freezes `unit_price_snapshot` and calculates `item_total`. Menu item price changes never mutate historical orders or invoices.

### 3. Kitchen Workload & Preparation Time Estimation
- **Workload Protection**: Staff cannot be assigned more than their `maximum_active_orders` limit.
- **Estimated Prep Time Formula**:
  $$\text{Estimated Time} = \max(\text{Item Prep Times}) + \text{Queue Delay}$$
  where $\text{Queue Delay} = \text{Queued Tickets} \times 5\text{ mins}$.

### 4. Financial Precision & Payments
- Standard 5% GST tax calculation with consistent rounding to 2 Decimal places.
- Overpayment prevention: payments exceeding invoice outstanding balance are rejected.
- Duplicate transaction references are rejected via MongoDB sparse unique indexing.
- Releasing tables: Completing a payment for a `DINE_IN` order automatically transitions the table to `AVAILABLE`.

### 5. Reservation Overlap Collision
A reservation is rejected if another confirmed reservation exists on the same table such that:
$$\text{new\_start} < \text{existing\_end} \quad \text{and} \quad \text{new\_end} > \text{existing\_start}$$

### 6. MongoDB Event Logging & Auditing
All significant events are logged to dedicated collections:
- `order_activity_logs`: `ORDER_CREATED`, `ORDER_CONFIRMED`, `ORDER_CANCELLED`, `ORDER_SERVED`, `PAYMENT_COMPLETED`.
- `kitchen_events`: Status transitions (`QUEUED` $\to$ `PREPARING` $\to$ `READY` $\to$ `HANDED_OVER`), staff assignments, and delays.
- `customer_feedback`: Ratings (1–5) linked to completed orders with duplicate submission prevention.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12 and 3.14)
- Local or Cloud MongoDB instance running on `mongodb://localhost:27017`

### 2. Installation
```bash
git clone <repo-url>
cd dineflow-main
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Setup
Copy `.env.example` to `.env`:
```env
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=restaurant_management
APP_NAME=Restaurant Management System
DEBUG=True
JWT_SECRET_KEY=supersecretjwtkeyforrestaurantmanagementsystem2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 4. Database Seeding
Initialize collections, indexes, demo users, tables, ingredients, and menu items:
```bash
python seed_roles.py
```

### 5. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Automated Testing

The project includes an automated test suite verifying all 30 assignment test requirements plus advanced endpoints:

```bash
pytest tests/test_api.py -v
```

### Test Suite Summary (35/35 Passing):
```text
tests/test_api.py::test_01_create_menu_item_successfully PASSED          [  2%]
tests/test_api.py::test_02_reject_negative_price PASSED                  [  5%]
tests/test_api.py::test_03_reject_zero_preparation_time PASSED           [  8%]
tests/test_api.py::test_04_disable_unavailable_menu_item PASSED          [ 11%]
tests/test_api.py::test_05_search_menu_by_category PASSED                [ 14%]
tests/test_api.py::test_06_add_ingredient_stock PASSED                   [ 17%]
tests/test_api.py::test_07_deduct_available_stock PASSED                 [ 20%]
tests/test_api.py::test_08_reject_deduction_when_stock_is_insufficient PASSED [ 22%]
tests/test_api.py::test_09_prevent_negative_stock PASSED                 [ 25%]
tests/test_api.py::test_10_generate_low_stock_alert PASSED               [ 28%]
tests/test_api.py::test_11_create_order_with_valid_items PASSED          [ 31%]
tests/test_api.py::test_12_reject_unavailable_menu_item PASSED           [ 34%]
tests/test_api.py::test_13_reject_empty_order PASSED                     [ 37%]
tests/test_api.py::test_14_calculate_subtotal_correctly PASSED           [ 40%]
tests/test_api.py::test_15_store_price_snapshot PASSED                   [ 42%]
tests/test_api.py::test_16_reject_invalid_quantity PASSED                [ 45%]
tests/test_api.py::test_17_prevent_invalid_status_transition PASSED      [ 48%]
tests/test_api.py::test_18_cancel_eligible_order PASSED                  [ 51%]
tests/test_api.py::test_19_create_kitchen_ticket_after_confirmation PASSED [ 54%]
tests/test_api.py::test_20_assign_active_kitchen_staff PASSED            [ 57%]
tests/test_api.py::test_21_reject_assignment_to_inactive_staff PASSED    [ 60%]
tests/test_api.py::test_22_update_kitchen_status_correctly PASSED        [ 62%]
tests/test_api.py::test_23_estimate_preparation_time PASSED              [ 65%]
tests/test_api.py::test_24_generate_invoice_correctly PASSED             [ 68%]
tests/test_api.py::test_25_reject_duplicate_payment PASSED               [ 71%]
tests/test_api.py::test_26_reject_payment_exceeding_outstanding_amount PASSED [ 74%]
tests/test_api.py::test_27_record_successful_payment PASSED              [ 77%]
tests/test_api.py::test_28_reject_refund_exceeding_paid_amount PASSED    [ 80%]
tests/test_api.py::test_29_store_order_activity_log PASSED               [ 82%]
tests/test_api.py::test_30_store_kitchen_status_change_event PASSED      [ 85%]
tests/test_api.py::test_31_table_management_occupy_and_release PASSED    [ 88%]
tests/test_api.py::test_32_reservation_overlap_and_capacity_check PASSED [ 91%]
tests/test_api.py::test_33_customer_feedback_validation_and_duplicate_prevention PASSED [ 94%]
tests/test_api.py::test_34_serving_capacity_report PASSED                [ 97%]
tests/test_api.py::test_35_daily_sales_report PASSED                     [100%]
======================= 35 passed in 3.96s ========================
```

---

## 📡 Key API Endpoints Reference

All endpoints support both `/api/<endpoint>` and root `/<endpoint>`:

| Module | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/login` | Authenticate and obtain JWT token |
| **Menu** | `GET` | `/api/menu-items` | List & filter menu items |
| | `POST` | `/api/menu-items` | Create new menu item |
| | `PATCH` | `/api/menu-items/{id}/availability` | Toggle availability status |
| **Recipes** | `POST` | `/api/recipes` | Map menu item to ingredients |
| | `GET` | `/api/recipes/menu-item/{id}` | View recipe for item |
| **Inventory** | `GET` | `/api/ingredients` | View inventory stock |
| | `POST` | `/api/ingredients/{id}/stock` | Restock or manual adjustment |
| | `GET` | `/api/ingredients/low-stock` | View low & critical stock alerts |
| **Tables** | `GET` | `/api/tables` | View tables & statuses |
| | `POST` | `/api/reservations` | Reserve table (capacity & overlap guarded) |
| **Orders** | `POST` | `/api/orders` | Create draft order |
| | `POST` | `/api/orders/{id}/items` | Add item with price snapshot |
| | `POST` | `/api/orders/{id}/confirm` | Confirm order & deduct inventory |
| | `POST` | `/api/orders/{id}/cancel` | Cancel order & process inventory reversal |
| **Kitchen** | `GET` | `/api/kitchen/tickets` | View kitchen queue |
| | `POST` | `/api/kitchen/tickets/{id}/start` | Start preparation |
| | `POST` | `/api/kitchen/tickets/{id}/ready` | Mark food as ready |
| | `GET` | `/api/kitchen/estimate-time/{id}` | Calculate estimated prep time |
| | `GET` | `/api/kitchen/workload` | Staff workload & active assignments |
| **Billing** | `POST` | `/api/orders/{id}/invoice` | Generate bill with tax & discount |
| | `POST` | `/api/payments` | Record payment & auto-release table |
| | `POST` | `/api/refunds` | Request refund |
| | `PATCH` | `/api/refunds/{id}/approve` | Manager approval for refund |
| **Audit & Events** | `GET` | `/api/activity-logs/order/{id}` | View MongoDB order audit logs |
| | `GET` | `/api/kitchen-events/order/{id}` | View MongoDB kitchen status events |
| | `POST` | `/api/orders/{id}/feedback` | Customer rating & review submission |
| **Reports** | `GET` | `/api/reports/daily-sales` | Daily sales & revenue breakdown |
| | `GET` | `/api/reports/serving-capacity` | Possible servings left based on stock |
| | `GET` | `/api/reports/kitchen-performance` | Delayed orders & status counts |

---

## 📜 License
This project is open-source and available under the MIT License.
