from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class SummaryAnalyzer:
    def __init__(self):
        self.__model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.__output_parser = StrOutputParser()
        self.__template = "Generate a summary of the following text: {text}."
        self.__prompt_template = PromptTemplate(template=self.__template, input_variables=["text"])

    def generate_summary(self, input_text: str) -> str:
        try:
            chain = self.__prompt_template | self.__model | self.__output_parser
            summary = chain.invoke({"text": input_text})
            return summary
        except Exception as e:
            return "Error: Unable to generate summary. Please try again later."
