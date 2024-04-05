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
from .utils import parse_translation_metadata, translator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager that creates an unique index and tears down the database connection."""
    # Startup logic that creates a unique index on 'original_text'
    await details_collection.create_index("original_text", unique=True)
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
    sl: str = Query("auto", description="Source language"),
    tl: str = Query("es", description="Target language"),
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
    stored_details = await details_collection.find_one({"original_text": text})

    # If the details are stored in the database, return them directly
    if stored_details:
        return Details(**stored_details)

    # If the details are not stored in the database, fetch them from the Google Translate API
    try:
        translation = translator.translate(text, tl, sl)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch translation from Google Translate API.",
        ) from e

    if isinstance(translation, list):
        raise HTTPException(
            status_code=502,
            detail="Translation value is invalid! Expected a single translation, received a list.",
        )

    if not translation.extra_data:
        raise HTTPException(
            status_code=502,
            detail="Translation does not have extra data! Unable to parse.",
        )

    # Parse the translation metadata
    details = parse_translation_metadata(text, translation.extra_data["parsed"])

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
    sort: str = Query("original_text", description="Field name to sort by"),
    order: str = Query(
        "asc", description="Sort order: 'asc' for ascending, 'desc' for descending"
    ),
    text_filter: Optional[str] = None,
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

    # Building the query for filtering with case-insensitive partial match
    query = {}
    if text_filter:
        query["original_text"] = {
            "$regex": text_filter,
            "$options": "i",
        }

    # Specifying fields to include in the database response
    projection = {"_id": 1, "original_text": 1}

    # Specifying fields that need to be included to remove default fields from the Model
    include: dict[str, dict] = {
        "details": {
            "__all__": {
                "id": {},
                "original_text": {},
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
