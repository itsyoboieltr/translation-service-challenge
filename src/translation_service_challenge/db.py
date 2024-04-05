"""Module that contains database models and connection logic."""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from pymongo.server_api import ServerApi
from typing_extensions import Annotated

from .env import env

mongo_client = AsyncIOMotorClient(env.DATABASE_URL, server_api=ServerApi("1"))
translation_service_db = mongo_client["translation-service"]
details_collection = translation_service_db.get_collection("details")


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
ObjectIdStr = Annotated[str, BeforeValidator(str)]


class Definition(BaseModel):
    """Model that represents a definition of a text."""

    text: str
    synonyms: list[str] = []


class Details(BaseModel):
    """Model that represents the details of a text."""

    id: Optional[ObjectIdStr] = Field(alias="_id", default=None)
    text: str
    source_language: str
    definitions: list[Definition] = []
    examples: list[str] = []
    translations: dict[str, list[str]] = {}


class DetailsCollection(BaseModel):
    """
    Model that represents a list of `Details` instances

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    details: list[Details] = []
