"""Module that contains utility functions and variables."""

import re

from googletrans import Translator

from .db import Definition, Details

HTML_CLEANER_REGEX = re.compile("<.*?>")

translator = Translator()


def parse_translation_metadata(original_text: str, metadata: list):
    """
    Parse the translation metadata. This function extracts the definitions, examples, and translations from the metadata
    and returns a `Details` instance containing this information. The `original_text` is also stored in the `Details`
    instance. The `metadata` is a list containing the translation metadata returned by the Google Translate API.
    """
    details = Details(original_text=original_text)

    # Parse the definitions
    definition_blocks = metadata[3][1][0]
    for definition_block in definition_blocks:
        for definition_parts in definition_block[1]:
            definition = Definition(text=definition_parts[0])
            # Some definitions do not have synonyms, so we need to handle this case
            try:
                synonyms = [
                    item for sublist in definition_parts[5][0][0] for item in sublist
                ]
            except IndexError:
                synonyms = []
            definition.synonyms = synonyms
            details.definitions.append(definition)

    # Parse the examples
    example_blocks = metadata[3][2][0]
    for example_block in example_blocks:
        # Examples can contain HTML tags that we do not want to store, so we remove them
        example = re.sub(HTML_CLEANER_REGEX, "", example_block[1])
        details.examples.append(example)

    # Parse the translations
    translation_blocks = metadata[3][5][0]
    for translation_block in translation_blocks:
        for translation_parts in translation_block[1]:
            details.translations.append(translation_parts[0])

    return details
