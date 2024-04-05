"""Module that contains utility functions and variables."""

import re

from fastapi import HTTPException
from googletrans import Translator

from .db import Definition, Details

HTML_CLEANER_REGEX = re.compile("<.*?>")

translator = Translator()


def translate_text(text: str, source_language: str, target_language: str):
    """
    Translate the given text from the source language to the target language using the Google Translate API.
    """
    try:
        translation = translator.translate(text, target_language, source_language)
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
    return translation.extra_data["parsed"]


def parse_translation_metadata(
    text: str, source_language: str, target_language: str, metadata: list
):
    """
    Parse the translation metadata. This function extracts the definitions, examples, and translations from the metadata
    and returns a `Details` instance containing this information. The `text` is also stored in the `Details`
    instance. The `metadata` is a list containing the translation metadata returned by the Google Translate API.
    """
    details = Details(
        text=text,
        source_language=source_language,
    )

    # Parse the definitions
    details.definitions = parse_definitions(metadata)

    # Parse the examples
    details.examples = parse_examples(metadata)

    # Parse the translations
    details.translations = parse_translations(metadata, target_language)

    return details


def parse_definitions(metadata: list):
    """
    Parse the definitions from the metadata and return a list of `Definition` instances containing the definitions.
    """

    definitions: list[Definition] = []

    # Parse the definitions and synonyms if they exist
    try:
        definition_blocks = metadata[3][1][0]
    except (IndexError, TypeError):
        definition_blocks = []

    for definition_block in definition_blocks:
        # Skip if it does not contain parts
        try:
            definition_parts = definition_block[1]
        except (IndexError, TypeError):
            continue

        for definition_part in definition_parts:
            # Skip if it does not contain text
            try:
                definition_text = definition_part[0]
            except (IndexError, TypeError):
                continue

            definition = Definition(text=definition_text)

            # Fallback to an empty list if a definition does not have any synonyms
            try:
                synonyms_nested = definition_part[5][0][0]
            except (IndexError, TypeError):
                synonyms_nested = []

            synonyms = [synonym for synonyms in synonyms_nested for synonym in synonyms]
            definition.synonyms = synonyms
            definitions.append(definition)

    return definitions


def parse_examples(metadata: list):
    """
    Parse the examples from the metadata and return a list of strings containing the examples.
    """

    examples: list[str] = []

    # Parse the examples if they exist
    try:
        example_blocks = metadata[3][2][0]
    except (IndexError, TypeError):
        example_blocks = []

    for example_block in example_blocks:
        # Skip if it does not contain text
        try:
            example_text = example_block[1]
        except (IndexError, TypeError):
            continue

        # Examples can contain HTML tags that we do not want to store, so we remove them
        example = re.sub(HTML_CLEANER_REGEX, "", example_text)
        examples.append(example)

    return examples


def parse_translations(metadata: list, target_language: str):
    """
    Parse the translations from the metadata and return a `Translation` instance containing the translations.
    """
    translations: list[str] = []

    # Parse the translations if they exist
    try:
        translation_blocks = metadata[3][5][0]
    except (IndexError, TypeError):
        translation_blocks = []

    for translation_block in translation_blocks:
        # Skip if it does not contain parts
        try:
            translation_parts = translation_block[1]
        except (IndexError, TypeError):
            continue

        for translation_part in translation_parts:
            # Skip if it does not contain text
            try:
                translation_text = translation_part[0]
            except (IndexError, TypeError):
                continue

            translations.append(translation_text)

    return {target_language: translations}
