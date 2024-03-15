import os
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ['GOOGLE_API_KEY'] = "AIzaSyAkwOJZV94Wuq-96EFe17HP-O5VRk7sKyc"


class SummaryAnalyzer:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = ("Analyze the given summary {summary} and extract relevant information. Provide the analysis result.")

        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["summary"])

    def analyze(self, summary: str) -> str:
        chain = self.__prompt_template | self.__model | self.__output_parser
        analysis_result = chain.invoke({"summary": summary})
        return analysis_result


