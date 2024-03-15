import os
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ['GOOGLE_API_KEY'] = "AIzaSyAkwOJZV94Wuq-96EFe17HP-O5VRk7sKyc"


class KeywordExtractor:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = ("Extract keywords from this masked call transcription. {transcript}. Only output should be comma seperated keywords list")
        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["transcript"])

    def extract_keywords(self, transcript: str) -> list[str]:
        chain = self.__prompt_template | self.__model | self.__output_parser
        keywords_string = chain.invoke({"transcript": transcript})
        keywords = keywords_string.split(",")
        return keywords
