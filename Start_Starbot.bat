@echo off
REM Activate virtual environment if it exists
IF EXIST .venv\Scripts\activate (
    call .venv\Scripts\activate
)

REM Install dependencies
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Exiting.
    exit /b 1
)

REM Check all required libraries, but do not exit if only python_dotenv is missing
python -c "import fastapi, uvicorn, dotenv, pydantic, jinja2, langchain, langchain_community, langchain_core, pymupdf, docx2txt, pytesseract, PIL, unstructured, pdf2image, requests, bs4, sentence_transformers, chromadb, huggingface_hub, transformers" || (
    echo One or more required libraries (except python_dotenv) are missing. Exiting.
    exit /b 1
)

REM Check for python_dotenv separately, warn but do not exit if missing
python -c "import python_dotenv" 2>NUL || echo WARNING: python_dotenv is not installed. Some .env features may not work, but continuing...

REM Run scrape_star_college.py to scrape and prepare data (wait for completion)
call python scrape_star_college.py
IF %ERRORLEVEL% NEQ 0 (
    echo scrape_star_college.py failed. Exiting.
    exit /b 1
)

REM Process all uploads and add to vector store (wait for completion)
call python process_uploads.py
IF %ERRORLEVEL% NEQ 0 (
    echo process_uploads.py failed. Exiting.
    exit /b 1
)

REM Start FastAPI server
start "FastAPI" cmd /k uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM Start static file server (serve.py)
start "StaticServer" cmd /k python serve.py

REM Start answer_question.py for CLI Q&A (interactive mode)
start "AnswerQuestion" cmd /k python answer_question.py

echo All servers and answer_question.py started. Press Ctrl+C in each window to stop them.
