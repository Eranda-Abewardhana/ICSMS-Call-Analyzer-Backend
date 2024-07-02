from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class TopicModeler:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = ("Categorize this masked telephone call transcription {transcript} "
                           "into suitable from these topics. {topics} "
                           "only output should be the topics, separated by comma")

        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["transcript", "topics"])

    def categorize(self, call_transcription: str, call_topics: list[str]) -> list[str]:
        chain = self.__prompt_template | self.__model | self.__output_parser
        topic = chain.invoke({"transcript": call_transcription, "topics": call_topics})
        topic_list = topic.split(',')
        topic_list = [topic.strip() for topic in topic_list]
        return topic_list

