# Star College Chatbot

A chatbot for Star College in Durban that answers questions based on uploaded information about the school using LangChain and ChromaDB.

## Features

- Upload and process various file types (PDFs, Word documents, images, text files)
- Scrape and process websites for information
- Beautiful, responsive chat interface to ask questions about Star College
- Retrieval-augmented generation using LangChain with ChromaDB
- Support for all Star College schools (Boys High, Girls High, Primary, Pre-Primary)
- Markdown rendering for structured responses
- Sources display for transparent information
- Dark/light mode support
- Embeddable chatbot widget for integration into other websites

## Architecture

```
Client (frontend) → FastAPI on Render

FastAPI Routes:
├── /upload        → Upload files (PDFs, Docs, Images, Text)
├── /scrape        → Scrape and process websites
├── /chat          → Accepts user question → returns LLM answer
```

## Data Flow

### Preprocessing:
- Document Processing: LangChain document loaders
  - PDFs → PyMuPDFLoader
  - Docs → Docx2txtLoader
  - Images → UnstructuredImageLoader
  - Text → TextLoader
- Web Scraping: LangChain WebBaseLoader

### Embedding:
- Uses BAAI/bge-small-en-v1.5 for embeddings via LangChain HuggingFaceEmbeddings
- Stores in ChromaDB

### Chat Logic:
- User input → embedding → retrieve top-k chunks from vector store
- Prompt LLM with retrieved context and user question using LangChain

## Technologies Used

- **Backend**: FastAPI
- **LangChain**: For document loading, embedding, vector stores, and LLM integration
- **Embedding Model**: BAAI/bge-small-en-v1.5 via HuggingFaceEmbeddings
- **Vector Store**: ChromaDB: For persistent, high-quality vector storage
- **LLM**: DeepSeek-Chat 7B via HuggingFaceHub
- **File Processing**: LangChain document loaders
- **Web Scraping**: LangChain WebBaseLoader
- **Frontend**: HTML, CSS, JavaScript with modern UI design
  - Responsive layout for all devices
  - School-specific theming
  - Markdown rendering with marked.js
  - Embeddable widget version

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example` and add your API keys
5. Run the application:
   ```
   python -m app.main
   ```
6. Open your browser and navigate to `http://localhost:8080`

## Using the Chatbot

1. **Upload Information**:
   - Go to the Upload Files page
   - Select files containing information about Star College
   - Upload the files

2. **Scrape Websites**:
   - Enter URLs of websites containing information about Star College
   - Scrape the websites

3. **Ask Questions**:
   - Go to the Chat page
   - Type your question about Star College
   - Get answers based on the uploaded information
   - View sources used to generate the answer

## Frontend Options

### Main Chatbot Interface

Access the full-featured chatbot interface at `http://localhost:8080`:

```bash
python serve.py
```

### Embeddable Widget

To embed the chatbot widget in any webpage:

```html
<!-- Include Font Awesome and Marked.js -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<!-- Include the widget script -->
<script src="static/js/chatbot-widget.js"></script>

<!-- Initialize the widget -->
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const chatbot = new StarCollegeChatbotWidget({
            apiUrl: 'http://localhost:8000/chat',
            position: 'bottom-right', // or 'bottom-left'
            title: 'Star College Assistant',
            welcomeMessage: 'Hello! How can I help you?',
            theme: 'light' // or 'dark'
        });
    });
</script>
```

View a demo of the widget at `http://localhost:8080/widget`.

## Deployment on Render

This application is optimized for deployment on Render:

1. Use Render's Background Worker for indexing (processing PDFs, websites)
2. Deploy FastAPI app as a Web Service
3. For LLM integration, use Hugging Face Inference API

## License

This project is licensed under the MIT License - see the LICENSE file for details.
