from typing import List, Optional
from transformers import pipeline, Pipeline

def load_anonymizer(model_tag: str, use_gpu: bool = False) -> Optional[Pipeline]:
    """Loads the anonymizer pipeline."""
    device = 0 if use_gpu else -1
    try:
        return pipeline(
            "token-classification",
            model=model_tag,
            tokenizer=model_tag,
            device=device,
        )
    except Exception as exc:
        print(f"Error loading Anonymizer model: \n\n{exc}")
        return None

def create_entity_map(model_output: List[dict], text: str) -> dict:
    """Creates a dictionary mapping words to entity groups."""
    return dict(
        (text[token["start"] : token["end"]], token["entity_group"])
        for token in model_output
    )

def replace_entities(text: str, entity_map: dict) -> str:
    """Replaces words in the text with masked entities from the map."""
    for word, entity_group in entity_map.items():
        text = text.replace(word, f"[{entity_group}]")
    return text

def anonymize_text(input_sentence: str, anonymizer: Pipeline) -> Optional[str]:
    """Anonymizes PII in the input sentence using the provided pipeline."""
    output = anonymizer(input_sentence, aggregation_strategy="simple")
    if isinstance(output, list):
        entity_map = create_entity_map(output, input_sentence)
        return replace_entities(input_sentence, entity_map)
    else:
        print("Anonymizer output is not in the expected format")
    return None

# Example usage:

# if anonymizer:
    # masked_text = anonymize_text("My name is John Doe and I live at 123 Main St, Anytown, CA 12345. My phone number is (555) 123-4567.", anonymizer)
    # print(masked_text)  # Output: My name is [NAME] and I live in [LOCATION].
