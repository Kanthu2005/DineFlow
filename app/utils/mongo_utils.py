from datetime import datetime, timezone
from decimal import Decimal
from bson import ObjectId
from bson.decimal128 import Decimal128


def now_utc():
    return datetime.now(timezone.utc)


def to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    if not value or not ObjectId.is_valid(str(value)):
        raise ValueError("Invalid ID")
    return ObjectId(str(value))


def decimal128(value):
    if isinstance(value, Decimal128):
        return value
    return Decimal128(Decimal(str(value)))


def get_field(data, field_name: str, default=None):
    """Safely extracts field from either a Pydantic model, dictionary, or object."""
    if data is None:
        return default
    if hasattr(data, field_name):
        val = getattr(data, field_name)
        if val is not None:
            return val
    if isinstance(data, dict):
        val = data.get(field_name)
        if val is not None:
            return val
    return default


def clean_mongo_types(value):
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Decimal128):
        return value.to_decimal()
    if isinstance(value, dict):
        return {
            ("id" if key == "_id" else key): clean_mongo_types(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [clean_mongo_types(item) for item in value]
    return value


def convert_decimal(value):
    return clean_mongo_types(value)


def serialize_document(document):
    if not document:
        return None
    return clean_mongo_types(document)


def serialize_documents(documents):
    return [clean_mongo_types(doc) for doc in documents]
