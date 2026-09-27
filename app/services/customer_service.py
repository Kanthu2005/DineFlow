from bson import ObjectId
from app.database.mongodb import customers_collection
from app.services.common import (
    now_utc,
    to_object_id,
    serialize_document,
    serialize_documents,
)


class CustomerService:

    @staticmethod
    def create_customer(data):

        if customers_collection.find_one(
            {"phone": data.phone}
        ):
            raise ValueError("Phone number already exists")

        customer = {
            "name": data.name,
            "phone": data.phone,
            "email": (
                data.email.lower()
                if data.email
                else None
            ),
            "created_at": now_utc(),
        }

        result = customers_collection.insert_one(customer)

        customer["_id"] = result.inserted_id

        return serialize_document(customer)

    @staticmethod
    def get_customer(customer_id):

        customer = customers_collection.find_one(
            {"_id": to_object_id(customer_id)}
        )

        if not customer:
            raise ValueError("Customer not found")

        return serialize_document(customer)

    @staticmethod
    def get_customers():

        customers = customers_collection.find().sort(
            "created_at",
            -1
        )

        return serialize_documents(customers)

    @staticmethod
    def update_customer(customer_id, data):

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "email" in update_data and update_data["email"]:
            update_data["email"] = update_data["email"].lower()

        result = customers_collection.update_one(
            {"_id": to_object_id(customer_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ValueError("Customer not found")

        return CustomerService.get_customer(customer_id)



#menucategoryservice...
