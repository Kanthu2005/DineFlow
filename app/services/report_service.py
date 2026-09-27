"""
Report Service.
Generates Daily Sales, Most-Ordered Items, Kitchen Performance, and Staff Performance reports.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson.decimal128 import Decimal128

from app.database.mongodb import (
    orders_collection,
    order_items_collection,
    kitchen_tickets_collection,
    users_collection,
    menu_items_collection,
)
from app.services.common import to_object_id, serialize_documents


class ReportService:

    @staticmethod
    def get_daily_sales_report(target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns daily sales metrics:
        Total Orders, Completed Orders, Cancelled Orders, Pending Orders, Gross Sales, Discounts, Tax, Net Sales.
        """
        today_str = target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Find orders created on that date (supports both datetime and date string prefixes)
        start = datetime.strptime(today_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        orders = list(orders_collection.find({
            "$or": [
                {"created_at": {"$gte": start, "$lt": end}},
                {"created_at": {"$regex": f"^{today_str}"}},
            ]
        }))

        total_orders = len(orders)
        completed_orders = sum(1 for o in orders if o.get("status") == "COMPLETED")
        cancelled_orders = sum(1 for o in orders if o.get("status") in ["CANCELLED", "REFUNDED"])
        pending_orders = total_orders - completed_orders - cancelled_orders

        gross_sales = Decimal("0")
        total_discount = Decimal("0")
        total_tax = Decimal("0")
        net_sales = Decimal("0")

        for o in orders:
            if o.get("status") != "CANCELLED":
                sub_val = o.get("subtotal")
                sub = sub_val.to_decimal() if isinstance(sub_val, Decimal128) else Decimal(str(sub_val if sub_val is not None else 0))
                disc_val = o.get("discount_amount")
                disc = disc_val.to_decimal() if isinstance(disc_val, Decimal128) else Decimal(str(disc_val if disc_val is not None else 0))
                tax_val = o.get("tax_amount")
                tax = tax_val.to_decimal() if isinstance(tax_val, Decimal128) else Decimal(str(tax_val if tax_val is not None else 0))
                tot_val = o.get("total_amount")
                tot = tot_val.to_decimal() if isinstance(tot_val, Decimal128) else Decimal(str(tot_val if tot_val is not None else 0))

                gross_sales += sub
                total_discount += disc
                total_tax += tax
                net_sales += tot

        return {
            "date": today_str,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "pending_orders": pending_orders,
            "gross_sales": gross_sales,
            "total_discounts": total_discount,
            "total_tax": total_tax,
            "net_sales": net_sales,
        }

    @staticmethod
    def get_most_ordered_items(limit: int = 10) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$menu_item_id",
                    "item_name": {"$first": "$item_name_snapshot"},
                    "total_quantity": {"$sum": "$quantity"},
                    "total_revenue": {"$sum": "$item_total"},
                }
            },
            {"$sort": {"total_quantity": -1}},
            {"$limit": limit},
        ]
        results = list(order_items_collection.aggregate(pipeline))
        enriched = []
        for r in results:
            rev = r["total_revenue"]
            rev_dec = rev.to_decimal() if isinstance(rev, Decimal128) else Decimal(str(rev))
            enriched.append({
                "menu_item_id": str(r["_id"]),
                "name": r["item_name"],
                "total_quantity": r["total_quantity"],
                "total_revenue": rev_dec,
            })
        return enriched

    @staticmethod
    def get_kitchen_performance() -> Dict[str, Any]:
        """
        Calculates average preparation duration across completed kitchen tickets.
        """
        tickets = list(kitchen_tickets_collection.find({
            "started_at": {"$ne": None},
            "ready_at": {"$ne": None},
        }))

        if not tickets:
            return {
                "completed_tickets_analyzed": 0,
                "average_prep_time_minutes": 0.0,
            }

        durations = []
        for t in tickets:
            start = t["started_at"]
            ready = t["ready_at"]
            if start and ready:
                dur_mins = (ready - start).total_seconds() / 60.0
                if dur_mins >= 0:
                    durations.append(dur_mins)

        avg_mins = sum(durations) / len(durations) if durations else 0.0

        return {
            "completed_tickets_analyzed": len(durations),
            "average_prep_time_minutes": round(avg_mins, 2),
        }
