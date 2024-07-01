from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List

load_dotenv()

class SummaryAnalyzer:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = "Generate a summary of the following text: {text}."
        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["text"])
        self.__input_token_limit = 2097000  # 2,097,000 tokens
        self.__output_token_limit = 8000  # 8,000 tokens

    def _split_text(self, text: str, max_tokens: int) -> List[str]:
        # Split the text into chunks, ensuring each chunk is within the max token limit
        # This is a simplified example; you'll need a more sophisticated approach to accurately count tokens
        words = text.split()
        chunks = []
        current_chunk = []

        current_length = 0
        for word in words:
            current_length += len(word) + 1  # +1 for the space
            if current_length > max_tokens:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word) + 1
            else:
                current_chunk.append(word)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def generate_summary(self, input_text: str) -> str:
        try:
            # Split the input text into manageable chunks
            chunks = self._split_text(input_text, self.__input_token_limit)

            summaries = []
            for chunk in chunks:
                chain = self.__prompt_template | self.__model | self.__output_parser
                summary = chain.invoke({"text": chunk})
                summaries.append(summary)

            # Combine the summaries into one final summary if necessary
            final_summary = ' '.join(summaries)
            if len(final_summary) > self.__output_token_limit:
                final_summary = final_summary[:self.__output_token_limit]

            return final_summary

        except Exception as e:
            return "Error: Unable to generate summary. Please try again later."
