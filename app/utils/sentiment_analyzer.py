import os
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
os.environ['GOOGLE_API_KEY'] = "AIzaSyAkwOJZV94Wuq-96EFe17HP-O5VRk7sKyc"


class SentimentAnalyzer:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = ("Use this telephone call transcription {transcript} to detect the customer who is calling and the call "
                    "operator who is handling the call. then identify the emotion of the customer and categorize the "
                    "emotion into one of these categories. {categories} only output should be the category")

        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["transcript", "categories"])

    def analyze(self, call_transcription: str, sentiment_categories: list[str]) -> str:
        chain = self.__prompt_template | self.__model | self.__output_parser
        sentiment = chain.invoke({"transcript": call_transcription, "categories": sentiment_categories})
        return sentiment

    # def analyze_sentiment(self, text: str):
    #     testimonial = TextBlob(text)
    #     sentiment_polarity = testimonial.sentiment.polarity
    #     sentiment_subjectivity = testimonial.sentiment.subjectivity
    # 
    #     if sentiment_polarity > 0:
    #         sentiment = "Positive"
    #     elif sentiment_polarity < 0:
    #         sentiment = "Negative"
    #     else:
    #         sentiment = "Neutral"
    # 
    #     return sentiment, sentiment_polarity