from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Star College Chatbot",
    description="A chatbot for Star College in Durban",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple test route
@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Star College Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #0a3d62; }
            .status { background: #2ecc71; color: white; padding: 10px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌟 Star College Chatbot</h1>
            <div class="status">✅ Deployment Successful!</div>
            <p>Welcome to the Star College Chatbot. The application is now running on Vercel!</p>
            <p><strong>Next steps:</strong></p>
            <ul>
                <li>✅ Basic FastAPI app is working</li>
                <li>🔄 Loading full chatbot functionality...</li>
                <li>🔑 API Key configured</li>
            </ul>
            <p><a href="/health">Check API Health</a></p>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Star College Chatbot API is running on Vercel"}

# This is required for Vercel
app = app
