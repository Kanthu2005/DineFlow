from bson import ObjectId
from app.database.mongodb import kitchen_events_collection
from app.services.common import (
    now_utc,
    to_object_id,
    serialize_document,
    serialize_documents,
)


class KitchenEventService:

    @staticmethod
    def create_event(
        order_id,
        event_type,
        kitchen_ticket_id=None,
        details=None,
    ):

        event = {
            "order_id": to_object_id(order_id),
            "kitchen_ticket_id": (
                to_object_id(kitchen_ticket_id)
                if kitchen_ticket_id
                else None
            ),
            "event_type": event_type,
            "details": details,
            "created_at": now_utc(),
        }

        result = kitchen_events_collection.insert_one(
            event
        )

        event["_id"] = result.inserted_id

        return serialize_document(event)

    @staticmethod
    def get_order_events(order_id):
        oid = to_object_id(order_id)
        events = kitchen_events_collection.find(
            {"$or": [{"order_id": oid}, {"order_id": str(order_id)}]}
        ).sort([("created_at", -1), ("_id", -1)])

        return serialize_documents(events)
