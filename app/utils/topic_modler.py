import os
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ['GOOGLE_API_KEY'] = "AIzaSyAkwOJZV94Wuq-96EFe17HP-O5VRk7sKyc"


class TopicModeler:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = ("Use this telephone call transcription {transcript} to detect the customer who is calling and the call "
                    "operator who is handling the call. then identify the topic of the call and categorize the "
                    "call into one of these topics. {topics} only output should be the topic")

        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["transcript", "topics"])

    def categorize(self, call_transcription: str, call_topics: list[str]) -> str:
        chain = self.__prompt_template | self.__model | self.__output_parser
        topic = chain.invoke({"transcript": call_transcription, "topics": call_topics})
        return topic

