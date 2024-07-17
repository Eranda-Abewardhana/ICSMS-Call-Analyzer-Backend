from datetime import datetime, timedelta

import boto3
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.config import Configurations
from app.database.aggregation import get_overall_avg_sentiment_score_pipeline
from app.database.database_connector import DatabaseConnector

load_dotenv()


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
        self.__sentiment_categories = Configurations.sentiment_categories
        self.__analytics_db = DatabaseConnector("analytics")

    def analyze(self, call_transcription: str) -> str:
        self.__text_to_analyze = call_transcription
        chain = self.__prompt_template | self.__model | self.__output_parser
        sentiment = chain.invoke({"transcript": call_transcription, "categories": self.__sentiment_categories})
        sentiment = self._get_sentiment(sentiment)
        return sentiment

    def _get_sentiment(self, llm_response: str) -> str:
        for sentiment_category in self.__sentiment_categories:
            if sentiment_category in llm_response:
                return sentiment_category
        return "Neutral"

    @staticmethod
    def _get_date_month_before() -> datetime:
        current_date = datetime.now()

        # Try to subtract one month
        one_month_before = current_date.replace(month=current_date.month - 1)

        # If we went back to the previous year, adjust the year and month
        if one_month_before.month == current_date.month:
            if current_date.month == 1:
                one_month_before = one_month_before.replace(year=current_date.year - 1, month=12)
            else:
                # This handles cases where the previous month has fewer days
                last_day_of_previous_month = (current_date.replace(day=1) - timedelta(days=1)).day
                one_month_before = one_month_before.replace(day=min(current_date.day, last_day_of_previous_month))
        return one_month_before

    def get_overall_avg_sentiment(self) -> dict:
        today = datetime.today()
        last_month_day = self._get_date_month_before()
        action_result = self.__analytics_db.run_aggregation_sync(
            get_overall_avg_sentiment_score_pipeline(last_month_day, today))
        return action_result.data[0]

    def analyze_sentiment(self, call_transcription: str) -> tuple[str, float]:
        self.__text_to_analyze = call_transcription
        try:
            comprehend = boto3.client(service_name='comprehend', aws_access_key_id=Configurations.aws_access_key_id,
                                      aws_secret_access_key=Configurations.aws_secret_access_key,
                                      region_name=Configurations.aws_region)
            response = comprehend.detect_sentiment(Text=self.__text_to_analyze, LanguageCode='en')
            sentiment = response.get('SentimentScore')

            if sentiment is None:
                raise ValueError("Sentiment not found in response")

            positive_score: float = sentiment.get('Positive')
            negative_score: float = sentiment.get('Negative')
            neutral_score: float = sentiment.get('Neutral')
            mixed_score: float = sentiment.get('Mixed')

            sentiment_category = "Neutral"

            max_score = max(positive_score, negative_score, neutral_score, mixed_score)

            if max_score == positive_score:
                sentiment_category = "Positive"
            elif max_score == negative_score:
                sentiment_category = "Negative"

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
            return sentiment_category, sentiment_score
        except Exception as e:
            print(e)
