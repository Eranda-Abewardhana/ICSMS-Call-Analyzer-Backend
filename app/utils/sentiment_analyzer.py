import os
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ['GOOGLE_API_KEY'] = "AIzaSyAkwOJZV94Wuq-96EFe17HP-O5VRk7sKyc"


class SentimentAnalyzer:
    __model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
    __output_parser = StrOutputParser()
    __template = ("Use this telephone call transcription {transcript} to detect the customer who is calling and the call "
                "operator who is handling the call. then identify the emotion of the customer and categorize the "
                "emotion into one of these categories. {categories} only output should be the category")

    __prompt_template = PromptTemplate(template=__template, input_variables=["transcript", "categories"])

    @classmethod
    def analyze(cls, call_transcription: str, sentiment_categories: list[str]) -> str:
        chain = cls.__prompt_template | cls.__model | cls.__output_parser
        sentiment = chain.invoke({"transcript": call_transcription, "categories": sentiment_categories})
        return sentiment

