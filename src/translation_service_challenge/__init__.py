"""FastAPI app for the translation service challenge."""

from contextlib import asynccontextmanager
from typing import Optional

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query, Response, status

from .db import (
    Details,
    DetailsCollection,
    details_collection,
    mongo_client,
)
from .utils import parse_translation_metadata, parse_translations, translate_text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager that creates an unique index and tears down the database connection."""
    # Startup logic that creates a unique index on 'text' and 'source_language'
    await details_collection.create_index(
        [("text", 1), ("source_language", 1)],
        unique=True,
    )
    yield
    # Shutdown logic that closes the database connection
    mongo_client.close()


app = FastAPI(
    title="Translation Service Challenge API",
    summary="A sample JSON API working with the Google Translate API.",
    lifespan=lifespan,
)


@app.get(
    "/details",
    response_model=Details,
    response_model_by_alias=False,
    tags=["details"],
)
async def get_details(
    text: str,
    source_language: str = "en",
    target_language: str = "es",
):
    """
    Get the details of a text.

    First, the function checks if the details are already stored in the database.
    If they are, they are directly returned.

    If the details are not stored in the database, they are fetched from the Google Translate API.
    If the API returns an error, a 502 error is raised.
    If the API returns a list instead of a single translation, a 502 error is raised.
    If the translation does not have extra data, a 502 error is raised.
    The response is then parsed and the details are stored in the database. Finally, the details are returned.
    """

    # Check if the details are already stored in the database
    stored_details = await details_collection.find_one(
        {
            "text": text,
            "source_language": source_language,
        }
    )

    # If the details are stored in the database
    if stored_details:
        details = Details(**stored_details)

        # If the target language is not in the stored translations, fetch the translation
        if details.translations.get(target_language, None) is None:
            translation_metadata = translate_text(
                text, source_language, target_language
            )
            translation = parse_translations(translation_metadata, target_language)
            details.translations[target_language] = translation[target_language]

            # Update the stored details with the new translation
            await details_collection.update_one(
                {"_id": ObjectId(details.id)},
                {"$set": {"translations": details.translations}},
            )

        # Return the stored details
        return details

    # If the details are not stored in the database, fetch them from the Google Translate API
    translation_metadata = translate_text(text, source_language, target_language)

    # Parse the translation metadata
    details = parse_translation_metadata(
        text, source_language, target_language, translation_metadata
    )

    # Store the details in the database
    inserted_details = await details_collection.insert_one(details.model_dump())

    # Update the details with the inserted id
    details.id = str(inserted_details.inserted_id)

    return details


@app.get("/", tags=["details"])
async def list_details(
    page: int = Query(
        1, ge=1, alias="page", description="Page number, starting from 1"
    ),
    limit: int = Query(10, ge=1, alias="limit", description="Number of items per page"),
    sort: str = Query("text", description="Field name to sort by"),
    order: str = Query(
        "asc", description="Sort order: 'asc' for ascending, 'desc' for descending"
    ),
    text: Optional[str] = None,
    source_language: Optional[str] = None,
    definitions: bool = Query(False, description="Include definitions in the response"),
    synonyms: bool = Query(False, description="Include synonyms in the response"),
    examples: bool = Query(True, description="Include examples in the response"),
    translations: bool = Query(
        False, description="Include translations in the response"
    ),
):
    """
    List the entries stored in the `details` collection with pagination, sorting and partial match filtering.
    Definitions, synonyms and translations are not included by default.
    """

    # Convert order from 'asc' and 'desc' to 1 and -1
    if order == "asc":
        order_value = 1
    elif order == "desc":
        order_value = -1
    else:
        raise HTTPException(
            status_code=400, detail="Order must be either 'asc' or 'desc'"
        )

    # Building the query for filtering
    query: dict = {}
    # Text filtering with case-insensitive partial match
    if text:
        query["text"] = {
            "$regex": text,
            "$options": "i",
        }
    # Exact match filtering for source language
    if source_language:
        query["source_language"] = source_language

    # Specifying fields to include in  the database response
    projection = {
        "_id": 1,
        "text": 1,
        "source_language": 1,
    }

    # Specifying fields that need to be included to remove default fields from the Model
    include: dict[str, dict] = {
        "details": {
            "__all__": {
                "id": {},
                "text": {},
                "source_language": {},
            }
        }
    }

    # Conditionally include additional fields based on flags
    if definitions:
        projection["definitions.text"] = 1
        include["details"]["__all__"]["definitions"] = {"__all__": {"text"}}
        if synonyms:
            projection["definitions.synonyms"] = 1
            include["details"]["__all__"]["definitions"]["__all__"].add("synonyms")
    if examples:
        projection["examples"] = 1
        include["details"]["__all__"]["examples"] = {"__all__"}
    if translations:
        projection["translations"] = 1
        include["details"]["__all__"]["translations"] = {"__all__"}

    # Calculating the number of documents to skip
    skip = (page - 1) * limit

    # Fetching documents from the database
    details = (
        await details_collection.find(query, projection)
        .sort(sort, order_value)
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    return DetailsCollection(details=details).model_dump(include=include)


@app.delete("/details/{id}", tags=["details"])
async def delete_details(id: str):
    """
    Delete an entry stored in the `details` collection by its `id`.

    If the `id` is invalid, a 400 error is raised.
    If the entry is not found, a 404 error is raised.
    If the entry is found and deleted, a 204 response is returned.
    """
    try:
        object_id = ObjectId(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Details {id} is invalid") from e

    delete_result = await details_collection.delete_one({"_id": object_id})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Details {id} not found")
