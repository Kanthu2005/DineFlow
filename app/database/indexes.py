from pymongo import ASCENDING, DESCENDING


def create_indexes(db):
 
#users...
    db["users"].create_index(
        [("email", ASCENDING)],
        unique=True
    )

    db["users"].create_index(
        [("role", ASCENDING)]
    )


#customers...

    db["customers"].create_index(
        [("phone", ASCENDING)],
        unique=True
    )

    db["customers"].create_index(
        [("email", ASCENDING)],
        unique=True,
        sparse=True
    )


#menucategories...
    db["menu_categories"].create_index(
        [("name", ASCENDING)],
        unique=True
    )


#menuitems...

    db["menu_items"].create_index(
        [("name", ASCENDING)]
    )

    db["menu_items"].create_index(
        [("category_id", ASCENDING)]
    )

    db["menu_items"].create_index(
        [("is_available", ASCENDING)]
    )


#ingredients....

    db["ingredients"].create_index(
        [("name", ASCENDING)],
        unique=True
    )

    db["ingredients"].create_index(
        [("is_active", ASCENDING)]
    )


#recipies...

    db["recipes"].create_index(
        [
            ("menu_item_id", ASCENDING),
            ("ingredient_id", ASCENDING)
        ],
        unique=True
    )

    db["recipes"].create_index(
        [("menu_item_id", ASCENDING)]
    )

    db["recipes"].create_index(
        [("ingredient_id", ASCENDING)]
    )

#resturanttables

    db["restaurant_tables"].create_index(
        [("table_number", ASCENDING)],
        unique=True
    )

    db["restaurant_tables"].create_index(
        [("status", ASCENDING)]
    )

    db["restaurant_tables"].create_index(
        [("is_active", ASCENDING)]
    )


 #reservations...

    db["reservations"].create_index(
        [("customer_id", ASCENDING)]
    )

    db["reservations"].create_index(
        [("table_id", ASCENDING)]
    )

    db["reservations"].create_index(
        [
            ("reservation_date", ASCENDING),
            ("table_id", ASCENDING),
            ("start_time", ASCENDING)
        ]
    )

    db["reservations"].create_index(
        [("status", ASCENDING)]
    )


#orders...

    db["orders"].create_index(
        [("order_number", ASCENDING)],
        unique=True
    )

    db["orders"].create_index(
        [("customer_id", ASCENDING)]
    )

    db["orders"].create_index(
        [("table_id", ASCENDING)]
    )

    db["orders"].create_index(
        [("status", ASCENDING)]
    )

    db["orders"].create_index(
        [("created_at", DESCENDING)]
    )


#ordreitems...

    db["order_items"].create_index(
        [("order_id", ASCENDING)]
    )

    db["order_items"].create_index(
        [("menu_item_id", ASCENDING)]
    )


#kitchentickets....
    db["kitchen_tickets"].create_index(
        [("order_id", ASCENDING)],
        unique=True
    )

    db["kitchen_tickets"].create_index(
        [("status", ASCENDING)]
    )

    db["kitchen_tickets"].create_index(
        [("assigned_staff_id", ASCENDING)]
    )

    db["kitchen_tickets"].create_index(
        [("priority", ASCENDING)]
    )


#kitchenitemtickets...
    db["kitchen_ticket_items"].create_index(
        [("kitchen_ticket_id", ASCENDING)]
    )

    db["kitchen_ticket_items"].create_index(
        [("order_item_id", ASCENDING)]
    )


#staff assignment

    db["staff_assignments"].create_index(
        [("kitchen_ticket_id", ASCENDING)]
    )

    db["staff_assignments"].create_index(
        [("staff_id", ASCENDING)]
    )


#stockmovements...

    db["stock_movements"].create_index(
        [("ingredient_id", ASCENDING)]
    )

    db["stock_movements"].create_index(
        [("movement_type", ASCENDING)]
    )

    db["stock_movements"].create_index(
        [("created_at", DESCENDING)]
    )

    db["stock_movements"].create_index(
        [
            ("reference_type", ASCENDING),
            ("reference_id", ASCENDING)
        ]
    )
#invoice...

    db["invoices"].create_index(
        [("invoice_number", ASCENDING)],
        unique=True
    )

    db["invoices"].create_index(
        [("order_id", ASCENDING)],
        unique=True
    )

    db["invoices"].create_index(
        [("status", ASCENDING)]
    )
#payments...

    db["payments"].create_index(
        [("invoice_id", ASCENDING)]
    )

    db["payments"].create_index(
        [("payment_status", ASCENDING)]
    )

    db["payments"].create_index(
        [("transaction_reference", ASCENDING)],
        unique=True,
        sparse=True
    )

    db["payments"].create_index(
        [("paid_at", DESCENDING)]
    )


#refunds...

    db["refunds"].create_index(
        [("payment_id", ASCENDING)]
    )

    db["refunds"].create_index(
        [("order_id", ASCENDING)]
    )

    db["refunds"].create_index(
        [("status", ASCENDING)]
    )


  
#orderactivitylogs...

    db["order_activity_logs"].create_index(
        [("order_id", ASCENDING)]
    )

    db["order_activity_logs"].create_index(
        [("created_at", DESCENDING)]
    )

    db["order_activity_logs"].create_index(
        [("action", ASCENDING)]
    )

#kitchenevents...

    db["kitchen_events"].create_index(
        [("order_id", ASCENDING)]
    )

    db["kitchen_events"].create_index(
        [("kitchen_ticket_id", ASCENDING)]
    )

    db["kitchen_events"].create_index(
        [("event_type", ASCENDING)]
    )

    db["kitchen_events"].create_index(
        [("created_at", DESCENDING)]
    )

#customerfeedback...
    db["customer_feedback"].create_index(
        [("customer_id", ASCENDING)]
    )

    db["customer_feedback"].create_index(
        [("order_id", ASCENDING)]
    )

    db["customer_feedback"].create_index(
        [("rating", DESCENDING)]
    )

    db["customer_feedback"].create_index(
        [("created_at", DESCENDING)]
    )

    print("MongoDB indexes created successfully.")


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from app.database.mongodb import db
    print("Creating MongoDB indexes...")
    create_indexes(db)