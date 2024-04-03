"""FastAPI app for the translation service challenge."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    """Root endpoint for the FastAPI app."""
    return {"Hello": "World"}
