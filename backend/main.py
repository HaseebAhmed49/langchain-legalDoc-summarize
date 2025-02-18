from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from dotenv import load_dotenv
import os
import PyPDF2
import tempfile

# Load OpenAI API Key from Environment Variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Enable CORS for Frontend Communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI LLM Model
llm = ChatOpenAI(temperature=0.3, model="gpt-4", api_key=OPENAI_API_KEY)

# Function to Extract Text from PDF
def extract_text_from_pdf(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text.strip() if text else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")

@app.post("/extract")
async def extract_clauses(file: UploadFile = File(...), transform: bool = False):
    if not file.filename.lower().endswith(("pdf", "txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    try:
        # Save Temporary File
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Extract Text
        text = extract_text_from_pdf(temp_path) if file.filename.endswith(".pdf") else content.decode("utf-8")

        if not text:
            raise HTTPException(status_code=400, detail="No readable text found in the document.")

        # Split Text into Chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
        docs = [Document(page_content=chunk) for chunk in text_splitter.split_text(text)]

        # Define Legal Clause Extraction Prompt
        extract_prompt = PromptTemplate(
            template="""Extract key legal clauses from the following contract:

            {text}

            Focus on:
            - Confidentiality obligations
            - Liability limitations
            - Termination conditions
            - Payment terms
            - Governing law
            - Intellectual property rights

            Provide a structured summary in bullet points.
            """,
            input_variables=["text"]
        )

        # Load Summarization Chain
        chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=extract_prompt)

        # Process Extraction
        summary = chain.run(input_documents=docs)

        # **Transformation: Simplify for Layman**
        transformed_summary = None
        if transform:
            transform_prompt = PromptTemplate(
                template="""Simplify the following legal clauses so that a non-lawyer can easily understand them:

                {text}

                Use clear, everyday language while keeping the meaning intact.
                """,
                input_variables=["text"]
            )

            transformed_summary = llm.invoke(transform_prompt.format(text=summary))
            print(transformed_summary)

        return {
            "summary": summary,
            "transformed_summary": transformed_summary if transform else "Already explained in Simple Language"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)