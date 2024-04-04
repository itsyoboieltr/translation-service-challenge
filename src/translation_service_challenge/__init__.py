"""FastAPI app for the translation service challenge."""

import re
from typing import TypedDict

from fastapi import FastAPI, HTTPException
from googletrans import Translator

HTML_CLEANER_REGEX = re.compile("<.*?>")

translator = Translator()

app = FastAPI()


class Definition(TypedDict):
    """Type that represents a definition of a word."""

    text: str
    synonyms: list[str]


@app.get("/details")
async def get_details(text: str, sl: str = "auto", tl: str = "es"):
    """Root endpoint for the FastAPI app."""
    translation = translator.translate(text, tl, sl)

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

    metadata = translation.extra_data["parsed"]

    # Parse the definitions
    definitions: list[Definition] = []
    definition_blocks = metadata[3][1][0]
    for definition_block in definition_blocks:
        for definition_parts in definition_block[1]:
            definition: Definition = {"text": definition_parts[0], "synonyms": []}
            # Some definitions do not have synonyms, so we need to handle this case
            try:
                synonyms = [
                    item for sublist in definition_parts[5][0][0] for item in sublist
                ]
            except IndexError:
                synonyms = []
            definition["synonyms"] = synonyms
            definitions.append(definition)

    # Parse the examples
    examples: list[str] = []
    example_blocks = metadata[3][2][0]
    for example_block in example_blocks:
        # Examples can contain HTML tags that we do not want to store, so we remove them
        example = re.sub(HTML_CLEANER_REGEX, "", example_block[1])
        examples.append(example)

    # Parse the translations
    translations: list[str] = []
    translation_blocks = metadata[3][5][0]
    for translation_block in translation_blocks:
        for translation_parts in translation_block[1]:
            translations.append(translation_parts[0])

    return {
        "definitions": definitions,
        "examples": examples,
        "translations": translations,
    }
