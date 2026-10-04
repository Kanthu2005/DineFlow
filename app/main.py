import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse

from app.config.settings import settings
from app.database.mongodb import client, db, users_collection
from app.database.indexes import create_indexes
from app.services.auth_service import hash_password
from app.services.common import now_utc
from app.routes.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    try:
        client.admin.command("ping")

        print("========================================")
        print("MongoDB connection successful")
        print(f"Database: {settings.DATABASE_NAME}")
        print("========================================")

        is_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))
        has_admin = users_collection.find_one({"email": "admin@dineflow.com"}, {"_id": 1}) is not None
        has_menu = db["menu_categories"].find_one({"name": "Biryani"}, {"_id": 1}) is not None

        if not is_vercel or not has_admin:
            create_indexes(db)

        # Auto-seed default roles if not already present
        if not has_admin:
            default_roles = [
                ("admin@dineflow.com", "System Administrator", "ADMIN"),
                ("manager@dineflow.com", "General Manager", "MANAGER"),
                ("chef@dineflow.com", "Head Chef", "CHEF"),
                ("waiter@dineflow.com", "Floor Waiter", "WAITER"),
                ("cashier@dineflow.com", "Billing Cashier", "CASHIER"),
            ]
            for email, name, role in default_roles:
                if not users_collection.find_one({"email": email.lower()}):
                    users_collection.insert_one({
                        "name": name,
                        "email": email.lower(),
                        "password": hash_password("Password123!"),
                        "role": role,
                        "is_active": True,
                        "created_at": now_utc(),
                        "updated_at": now_utc(),
                    })
        print("Default staff role accounts verified")

        try:
            from app.database.clean_and_fix_menu import clean_and_seed_menu
            clean_and_seed_menu()
            print("Canonical restaurant menu catalog verified")
        except Exception as me:
            print(f"Canonical menu seed warning: {me}")

        try:
            from app.database.seed_20_tables import seed_20_tables
            seed_20_tables()
            print("20 Standard restaurant tables verified (T1 - T20)")
        except Exception as te:
            print(f"Tables seed warning: {te}")

    except Exception as e:
        print("========================================")
        print("MongoDB connection failed")
        print(f"Error: {e}")
        print("========================================")

    yield

    # Shutdown (keep client pool alive in serverless warm containers)
    if not (os.getenv("VERCEL") or os.getenv("VERCEL_ENV")):
        try:
            client.close()
            print("MongoDB connection closed")
        except Exception as e:
            print(f"Error closing MongoDB connection: {e}")


tags_metadata = [
    {
        "name": "Authentication",
        "description": "User login, registration, and profile (`/api/auth/*`). Use the **Authorize 🔓** button with your JWT token.",
    },
    {
        "name": "Menu",
        "description": "Food & beverage catalog management, category filtering, search, and availability toggling.",
    },
    {
        "name": "Recipes",
        "description": "Recipe mappings linking menu items to required ingredient quantities with unit normalization.",
    },
    {
        "name": "Ingredients",
        "description": "Warehouse raw materials, stock adjustments, low-stock alerts, and serving capacity estimation.",
    },
    {
        "name": "Tables",
        "description": "Dining tables, occupancy status, and seating assignments.",
    },
    {
        "name": "Reservations",
        "description": "Table reservations with guest capacity validation and overlap collision detection.",
    },
    {
        "name": "Orders",
        "description": "Customer order lifecycle, item price snapshots, subtotal/tax calculations, confirmation, and cancellations.",
    },
    {
        "name": "Kitchen",
        "description": "Kitchen tickets, priority queueing, preparation time estimation, and staff workload management.",
    },
    {
        "name": "Billing & Payments",
        "description": "Invoice generation, Decimal precision tax/discount calculations, duplicate-protected payments, and table release.",
    },
    {
        "name": "Activity Logs",
        "description": "MongoDB event-sourcing and audit trail for order actions.",
    },
    {
        "name": "Kitchen Events",
        "description": "MongoDB kitchen status transitions and workload events.",
    },
    {
        "name": "Feedback",
        "description": "Customer ratings (1-5) and reviews for completed dining orders.",
    },
    {
        "name": "Reports & Analytics",
        "description": "Daily sales performance, kitchen workload analytics, and dish serving capacity reports.",
    },
    {
        "name": "Users",
        "description": "User accounts and role-based permissions management.",
    },
    {
        "name": "Customers",
        "description": "Customer directory, contact numbers, and order history.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "defaultModelsExpandDepth": 1,
    },
    lifespan=lifespan,
)

# Enable CORS for frontend UI connecting from any origin/port (Vercel, Render, Localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router under /api for clean canonical Swagger documentation
app.include_router(
    router,
    prefix="/api",
)
# Include root router silently for backward compatibility
app.include_router(
    router,
    include_in_schema=False,
)

# Mount frontend directory for seamless standalone or integrated UI access
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")
STATIC_DIR = FRONTEND_DIST if os.path.exists(FRONTEND_DIST) else FRONTEND_DIR

if os.path.exists(STATIC_DIR):
    app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="frontend_app")

# Mount static images directory at /images for direct asset access
PUBLIC_IMAGES = os.path.join(FRONTEND_DIR, "public", "images")
DIST_IMAGES = os.path.join(FRONTEND_DIST, "images")
IMAGES_DIR = DIST_IMAGES if os.path.exists(DIST_IMAGES) else PUBLIC_IMAGES

if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="static_images")


@app.get("/", include_in_schema=False)
def home():
    if os.path.exists(STATIC_DIR):
        return RedirectResponse(url="/app/index.html")

    return {
        "message": "Restaurant Management System API is running",
        "database": "MongoDB",
        "version": "2.0.0",
    }


@app.get("/login", include_in_schema=False)
@app.get("/app/login", include_in_schema=False)
def login_page():
    return RedirectResponse(url="/app/index.html")



@app.get("/health")
@app.get("/api/health")
def health_check():

    try:
        client.admin.command("ping")

        return {
            "status": "healthy",
            "database": "MongoDB",
            "database_name": settings.DATABASE_NAME,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "MongoDB",
            "error": str(e),
        }

