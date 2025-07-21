# Star College Chatbot

A virtual assistant for Star College information using DeepSeek AI and LangChain with ChromaDB for local vector storage.

![Star College Chatbot](app/static/images/logo.png)

## Features

- Upload and process PDF files with information about Star College
- Scrape and process websites for information
- Beautiful, responsive chat interface to ask questions about Star College
- Retrieval-augmented generation using LangChain with **ChromaDB**
- Support for all Star College schools (Boys High, Girls High, Primary, Pre-Primary)
- Concise, direct answers to questions about Star College
- Sources display for transparent information
- Dark mode interface
- Green text for better visibility of chatbot responses

## Architecture

```
Client (frontend) → FastAPI on localhost

FastAPI Routes:
├── /              → Serves the web interface
├── /chat          → Accepts user question → returns LLM answer
```

## Data Flow

### Preprocessing:
- Document Processing: LangChain document loaders
  - PDFs → PyMuPDFLoader
- Web Scraping: LangChain WebBaseLoader

### Embedding:
- Uses BAAI/bge-small-en-v1.5 for embeddings via LangChain HuggingFaceEmbeddings
- Stores in **ChromaDB** (local vector database)

### Chat Logic:
- User input → embedding → retrieve top-k chunks from vector store
- Prompt DeepSeek LLM with retrieved context and user question
- Return concise, direct answers based on the retrieved information

## Technologies Used

- **Backend**: FastAPI
- **LangChain**: For document loading, embedding, vector stores, and LLM integration
- **Embedding Model**: BAAI/bge-small-en-v1.5 via HuggingFaceEmbeddings
- **Vector Store**: **ChromaDB** (local vector database)
- **LLM**: DeepSeek API for natural language generation
- **File Processing**: PyMuPDF for PDF processing
- **Web Scraping**: LangChain WebBaseLoader
- **Frontend**: HTML, CSS, JavaScript with modern UI design
  - Responsive layout for all devices
  - School-specific theming
  - Dark mode interface

## Deployment Options

### Option 1: Deploy to Vercel (Recommended)

1. **Fork or clone this repository**

2. **Set up your Vercel account**:
   - Go to [vercel.com](https://vercel.com) and sign up/login
   - Connect your GitHub account

3. **Deploy to Vercel**:
   - Click "New Project" in your Vercel dashboard
   - Import your repository
   - Vercel will automatically detect it as a Python project

4. **Configure Environment Variables**:
   - In your Vercel project settings, go to "Environment Variables"
   - Add the following variables:
     ```
     DEEPSEEK_API_KEY=your_deepseek_api_key_here
     ```
   - Other variables are pre-configured in `vercel.json`

5. **Deploy**:
   - Click "Deploy" and wait for the build to complete
   - Your app will be available at `https://your-project-name.vercel.app`

### Option 2: Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your DEEPSEEK_API_KEY
   ```
5. Run the application:
   ```bash
   python -m app.main
   ```
6. Open your browser and navigate to `http://127.0.0.1:8000`

## Data Preparation

### For Local Development

Before using the chatbot locally, you need to prepare the data:

1. **Add PDF documents**:
   - Place PDF files with Star College information in the `data/uploads/` folder

2. **Add website URLs**:
   - Edit `data/links/links.txt` to include URLs to scrape for Star College information
   - Each URL should be on a separate line

3. **Process the data**:
   ```bash
   python process_uploads.py
   python scrape_star_college.py
   ```

### For Production Deployment

**Note**: The current version includes pre-processed data. For production use with new data:

1. **Upload Interface**: Use the `/upload-page` endpoint to upload new documents
2. **API Integration**: The app includes endpoints for processing new data
3. **Persistent Storage**: Consider integrating with cloud storage services for production data persistence

## Using the Chatbot

### Web Interface

1. **Access the interface**:
   - **Production**: Visit your deployed Vercel URL
   - **Local**: Open your browser and go to http://127.0.0.1:8000

2. **Ask Questions**:
   - Type your question about Star College in the chat input
   - Get concise answers based on the processed information
   - Click "Show sources" to view the sources used to generate the answer

3. **Select School** (optional):
   - Use the dropdown in the top-right to select a specific Star College school
   - This will customize the interface and potentially filter responses

### Terminal Interface (Local Development Only)

For local development, you can use the terminal interface:

```bash
python answer_question.py
```

## Example Questions

Here are some example questions you can ask the chatbot:

- "What is the history of Star College?"
- "Where is Star College located?"
- "What facilities does Star College have?"
- "What are the matric results for Star College?"
- "What extracurricular activities are offered at Star College?"

## Troubleshooting

### Common Issues

1. **DeepSeek API errors**:
   - Verify your API key is correct in environment variables
   - Check your internet connection
   - Ensure you haven't exceeded API rate limits
   - Get your API key from: https://platform.deepseek.com/

2. **"I don't have enough information" responses**:
   - The app includes pre-processed data about Star College
   - For additional data, use the upload interface at `/upload-page`
   - Ensure your questions are related to Star College

3. **Deployment issues**:
   - Check Vercel build logs for any errors
   - Ensure all environment variables are set correctly
   - Verify that the `DEEPSEEK_API_KEY` is properly configured

### Production Considerations

- **Data Persistence**: Consider integrating with cloud storage for uploaded files
- **Rate Limiting**: Implement rate limiting for production use
- **Monitoring**: Set up monitoring and logging for production deployments
- **Security**: Review and implement additional security measures as needed

## Project Structure

```
StarBot-FINAL/
├── app/                    # Main application code
│   ├── config.py           # Configuration settings
│   ├── main.py             # FastAPI application (entry point)
│   ├── routes/             # API endpoints
│   ├── services/           # Core services (vector store, LLM, etc.)
│   └── utils/              # Utility functions
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
├── images/                 # School logos and assets
├── data/                   # Data storage (local development)
├── processed/              # Pre-processed data
├── index.html              # Main web interface
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment configuration
├── .env.example            # Environment variables template
├── .vercelignore           # Files to exclude from deployment
├── answer_question.py      # Terminal interface (dev only)
├── process_uploads.py      # PDF processing script (dev only)
└── scrape_star_college.py  # Web scraping script (dev only)
```

## Deployment Files

- **`vercel.json`**: Vercel deployment configuration
- **`.env.example`**: Template for environment variables
- **`.vercelignore`**: Excludes development files from deployment
- **`Procfile`**: Alternative deployment configuration for other platforms
