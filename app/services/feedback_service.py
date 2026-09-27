"""
Customer Feedback Service.
Manages customer reviews, ratings, order linkage, and feedback summaries.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId

from app.database.mongodb import customer_feedback_collection, orders_collection
from app.repositories.order_repository import OrderRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.common import (
    now_utc,
    to_object_id,
    get_field,
    serialize_document,
    serialize_documents,
)

order_repo = OrderRepository()
audit_repo = AuditLogRepository()


class FeedbackService:

    @staticmethod
    def create_feedback(order_id: str, data: Any) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        # Business Rule: Feedback must be associated with a valid completed order
        if order["status"] not in ["COMPLETED", "SERVED"]:
            raise ValueError(f"Feedback can only be submitted for completed orders. Current status: {order['status']}")

        customer_id = get_field(data, "customer_id")
        rating = int(get_field(data, "rating", 0))
        food_rating = get_field(data, "food_rating")
        service_rating = get_field(data, "service_rating")
        comments = get_field(data, "comments")

        # Business Rule: Rating should be between 1 and 5
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be an integer between 1 and 5")
        if food_rating is not None and not (1 <= int(food_rating) <= 5):
            raise ValueError("Food rating must be an integer between 1 and 5")
        if service_rating is not None and not (1 <= int(service_rating) <= 5):
            raise ValueError("Service rating must be an integer between 1 and 5")

        # Business Rule: Duplicate feedback prevention
        query: Dict[str, Any] = {"order_id": to_object_id(order_id)}
        if customer_id:
            query["customer_id"] = to_object_id(customer_id)
        existing = customer_feedback_collection.find_one(query)
        if existing:
            raise ValueError("Feedback has already been submitted for this order")

        feedback_doc = {
            "order_id": to_object_id(order_id),
            "customer_id": to_object_id(customer_id) if customer_id else None,
            "rating": rating,
            "food_rating": int(food_rating) if food_rating is not None else rating,
            "service_rating": int(service_rating) if service_rating is not None else rating,
            "comments": comments,
            "created_at": now_utc(),
        }

        created = audit_repo.record_feedback(feedback_doc)
        return created

    @staticmethod
    def get_feedback(feedback_id: str) -> Dict[str, Any]:
        doc = customer_feedback_collection.find_one({"_id": to_object_id(feedback_id)})
        if not doc:
            raise ValueError("Feedback not found")
        return serialize_document(doc)

    @staticmethod
    def get_order_feedback(order_id: str) -> List[Dict[str, Any]]:
        docs = customer_feedback_collection.find({"order_id": to_object_id(order_id)})
        return serialize_documents(docs)

    @staticmethod
    def get_all_feedback() -> List[Dict[str, Any]]:
        return audit_repo.find_all_feedback()

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_feedback": {"$sum": 1},
                    "average_rating": {"$avg": "$rating"},
                    "average_food_rating": {"$avg": "$food_rating"},
                    "average_service_rating": {"$avg": "$service_rating"},
                }
            }
        ]
        result = list(customer_feedback_collection.aggregate(pipeline))
        if not result:
            return {
                "total_feedback": 0,
                "average_rating": 0.0,
                "average_food_rating": 0.0,
                "average_service_rating": 0.0,
            }

        res = result[0]
        return {
            "total_feedback": res["total_feedback"],
            "average_rating": round(float(res.get("average_rating") or 0), 2),
            "average_food_rating": round(float(res.get("average_food_rating") or 0), 2),
            "average_service_rating": round(float(res.get("average_service_rating") or 0), 2),
        }
