import math
import os
import boto3

from app.config.config import Configurations

from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ['GOOGLE_API_KEY'] = "AIzaSyAkwOJZV94Wuq-96EFe17HP-O5VRk7sKyc"


class SentimentAnalyzer:
    def __init__(self):
        self.__text_to_analyze = ""
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = (
            "Use this telephone call transcription {transcript} to detect the customer who is calling and the call "
            "operator who is handling the call. then identify the emotion of the customer and categorize the "
            "emotion into one of these categories. {categories} only output should be the category")

        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["transcript", "categories"])
        self.__default_scale = "linear"

    def analyze(self, call_transcription: str, sentiment_categories: list[str]) -> str:
        self.__text_to_analyze = call_transcription
        chain = self.__prompt_template | self.__model | self.__output_parser
        sentiment = chain.invoke({"transcript": call_transcription, "categories": sentiment_categories})
        return sentiment

    @staticmethod
    def scale_score(score: float, scale_type: str = "linear") -> float:

        match scale_type:
            case "linear":
                return score
            case "standard":
                a, b, c, d = 2, 10, 1.23, -1.7
            case "aggressive":
                a, b, c, d = 1.1, 0.5, 1.03, 1
            case "weak":
                a, b, c, d = 4, 10, 1.95, -4.9
            case _:
                raise ValueError("Invalid scale type")

        scaled_score = a * math.log10(b * (score + c)) + d

        if scaled_score < -1:
            return -1
        if scaled_score > 1:
            return 1

        rounded_scaled_score = round(scale_score, 3)  # type: ignore
        return rounded_scaled_score

    def get_sentiment_score(self) -> float:
        try:
            comprehend = boto3.client(service_name='comprehend', aws_access_key_id=Configurations.aws_comprehend_access_key_id,
                                      aws_secret_access_key=Configurations.aws_comprehend_secret_access_key,
                                      region_name=Configurations.aws_region)
            response = comprehend.detect_sentiment(Text=self.__text_to_analyze, LanguageCode='en')
            sentiment = response.get('SentimentScore')

            if sentiment is None:
                raise ValueError("Sentiment not found in response")

            positive_score: float = sentiment.get('Positive')
            negative_score: float = sentiment.get('Negative')

            # Neutral and Mixed are said to have a score of 0. Hence they do not affect the score
            # Furthermore positive + negative + (neutral + mixed) = 1. Hence when we give positive and negative
            # we are essentially supplying the (neutral + mixed) value as well as they just add up to 1

            # we consider positive, negative to be weights of +1 and -1 respectively
            # more positive weight, less negative weight -> near +1 score
            # more negative weight, less positive weight -> near -1 score
            # positive weight ~= negative weight -> near 0 score
            #   if positive & negative near 0 -> neutral high (in aws response), mixed low
            #   if positive & negative near 0 -> neutral low (in aws response), mixed high

            sentiment_score = positive_score - negative_score  # = (+1 * positive) + (-1 * negative)
            scaled_score = self.scale_score(sentiment_score)
            return scaled_score
        except Exception as e:
            print(e)
