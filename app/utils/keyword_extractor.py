from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class KeywordExtractor:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = ("Extract most important keywords from this masked call transcription. {transcript}. "
                           "The only output should be a comma-seperated keywords list. "
                           "There can be only 5 keywords of maximum. "
                           "Also, a keyword should be one word and should not be masked word")
        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["transcript"])

    def extract_keywords(self, transcript: str) -> list[str]:
        chain = self.__prompt_template | self.__model | self.__output_parser
        keywords_string = chain.invoke({"transcript": transcript})
        keywords = keywords_string.split(",")
        return keywords
