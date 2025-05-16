# Star College Chatbot

A chatbot for Star College in Durban that answers questions based on uploaded information about the school using LangChain and **Qdrant Cloud** (external vector database).

## Features

- Upload and process various file types (PDFs, Word documents, images, text files)
- Scrape and process websites for information
- Beautiful, responsive chat interface to ask questions about Star College
- Retrieval-augmented generation using LangChain with **Qdrant Cloud**
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
- Stores in **Qdrant Cloud** (external vector DB)

### Chat Logic:
- User input → embedding → retrieve top-k chunks from vector store
- Prompt LLM with retrieved context and user question using LangChain

## Technologies Used

- **Backend**: FastAPI
- **LangChain**: For document loading, embedding, vector stores, and LLM integration
- **Embedding Model**: BAAI/bge-small-en-v1.5 via HuggingFaceEmbeddings
- **Vector Store**: **Qdrant Cloud** (remote, scalable vector DB)
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
4. Create a `.env` file (see below for Qdrant setup)
5. Run the application:
   ```
   python -m app.main
   ```
6. Open your browser and navigate to `http://localhost:8080`

## Qdrant Cloud Setup

1. [Sign up for Qdrant Cloud](https://cloud.qdrant.io/) and create a free cluster.
2. Copy your Qdrant Cloud **cluster URL** and **API key**.
3. Create a `.env` file in your project root with the following:
   ```env
   QDRANT_URL=https://YOUR-CLUSTER-URL:6333
   QDRANT_API_KEY=YOUR_QDRANT_API_KEY
   VECTOR_STORE_TYPE=qdrant
   ```
4. (Optional) You can use `.env.qdrant` as a template and copy it to `.env`.
5. When running locally or on Render, the app will use Qdrant Cloud for all vector storage and retrieval.

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
4. **Qdrant Cloud**: Set your QDRANT_URL and QDRANT_API_KEY as environment variables in the Render dashboard for both services.

## Migrating from ChromaDB (Legacy)

- The app previously used ChromaDB for local vector storage. All ChromaDB logic and files have been removed.
- All vector storage and retrieval is now handled by Qdrant Cloud.
- You can safely delete any `chroma` or `faiss` folders in `data/` if not using legacy data.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
