from pymongo import MongoClient
from app.config.settings import settings


# MongoDB Client with 5-second server selection timeout for resilience
client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000)
db = client[settings.DATABASE_NAME]

# Collections for DineFlow data models
users_collection = db["users"]
customers_collection = db["customers"]
menu_categories_collection = db["menu_categories"]
menu_items_collection = db["menu_items"]
ingredients_collection = db["ingredients"]
recipes_collection = db["recipes"]
restaurant_tables_collection = db["restaurant_tables"]
reservations_collection = db["reservations"]
orders_collection = db["orders"]
order_items_collection = db["order_items"]
kitchen_tickets_collection = db["kitchen_tickets"]
kitchen_ticket_items_collection = db["kitchen_ticket_items"]
staff_assignments_collection = db["staff_assignments"]
stock_movements_collection = db["stock_movements"]
invoices_collection = db["invoices"]
payments_collection = db["payments"]
refunds_collection = db["refunds"]
order_activity_logs_collection = db["order_activity_logs"]
kitchen_events_collection = db["kitchen_events"]
customer_feedback_collection = db["customer_feedback"]


def get_database():
    return db