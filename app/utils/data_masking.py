from typing import Optional
from transformers import pipeline


class DataMasker:
    def __init__(self):
        self.__model_name = "Isotonic/distilbert_finetuned_ai4privacy_v2"
        self.masker = pipeline("token-classification", model=self.__model_name, tokenizer=self.__model_name, device=-1)
        self.text_message = ""

    def mask_text(self, text: str) -> Optional[str]:
        self.text_message = text
        model_output = self.masker(text, aggregation_strategy="simple")
        if isinstance(model_output, list):
            entity_map = self.__create_entity_map(model_output)
            masked_data = self.__replace_entities(entity_map)
            return masked_data
        else:
            print("Anonymizer output is not in the expected format")
        return None

    def __create_entity_map(self, model_output: list[dict]) -> dict[str, str]:
        entity_map = {}
        for token in model_output:
            start = token["start"]
            end = token["end"]
            entity = self.text_message[start: end]
            entity_map[entity] = token["entity_group"]
        return entity_map

    def __replace_entities(self, entity_map: dict[str, str]) -> str:
        for word, entity_group in entity_map.items():
            self.text_message = self.text_message.replace(word, f"[{entity_group}]")
        return self.text_message
