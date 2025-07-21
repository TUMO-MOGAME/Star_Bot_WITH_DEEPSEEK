import os
import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.utils.helpers import generate_unique_id

class WebScraper:
    """Scrape and process web content with Playwright for dynamic pages and LangChain fallback."""

    def __init__(self, use_playwright: bool = True):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        self.use_playwright = use_playwright

        # Credentials from env, FB_EMAIL can be phone number or email
        self.fb_email = os.getenv("FB_EMAIL")
        self.fb_password = os.getenv("FB_PASSWORD")
        self.ig_username = os.getenv("IG_USERNAME")
        self.ig_password = os.getenv("IG_PASSWORD")

    async def _fetch_with_playwright(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            domain = urlparse(url).netloc.lower()

            try:
                # Facebook login flow
                if "facebook.com" in domain and self.fb_email and self.fb_password:
                    await page.goto("https://www.facebook.com/login")
                    await page.fill('input[name="email"]', self.fb_email)
                    await page.fill('input[name="pass"]', self.fb_password)
                    await page.wait_for_selector('button[name="login"]', state='visible')
                    await page.click('button[name="login"]')
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(10)  # longer wait for homepage to load

                    # Improved login success check
                    try:
                        # Wait for profile icon or a reliable logged-in element
                        await page.wait_for_selector('[aria-label="Your profile"]', timeout=15000)
                        print("Facebook login successful.")
                    except:
                        current_url = page.url
                        if "login" in current_url.lower():
                            print("Still on login page, login likely failed.")
                        else:
                            print("Facebook login may have failed, scraping will likely be limited.")

                # Instagram login flow
                if "instagram.com" in domain and self.ig_username and self.ig_password:
                    await page.goto("https://www.instagram.com/accounts/login/")
                    await page.fill('input[name="username"]', self.ig_username)
                    await page.fill('input[name="password"]', self.ig_password)
                    await page.wait_for_selector('button[type="submit"]', state='visible')
                    await page.click('button[type="submit"]')
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(5)

                # Navigate to target URL in the logged-in session
                await page.goto(url)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(5)

                # Scroll to load dynamic content
                await page.evaluate("""async () => {
                    await new Promise(resolve => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if(totalHeight >= document.body.scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 200);
                    });
                }""")
                await asyncio.sleep(5)

                # Extract clean text content
                content = await page.evaluate("""() => {
                    const tags = document.querySelectorAll('script, style, noscript, iframe');
                    tags.forEach(t => t.remove());
                    return document.body.innerText;
                }""")

                await browser.close()
                return content

            except PlaywrightTimeoutError:
                await browser.close()
                print(f"Timeout loading page with Playwright: {url}")
                return ""

            except Exception as e:
                await browser.close()
                print(f"Playwright error for {url}: {str(e)}")
                return ""

    def _load_with_langchain(self, url: str):
        # Blocking sync call, run in executor when needed
        loader = WebBaseLoader(url)
        return loader.load()

    async def scrape_url_async(self, url: str) -> List[Dict[str, Any]]:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            print(f"Invalid URL: {url}")
            return []

        if self.use_playwright:
            content = await self._fetch_with_playwright(url)
            if content:
                chunks_with_metadata = []
                title = parsed_url.netloc  # fallback title

                splits = self.text_splitter.split_text(content)
                for chunk_text in splits:
                    chunks_with_metadata.append({
                        "id": generate_unique_id(),
                        "text": chunk_text,
                        "metadata": {
                            "source_type": "web",
                            "url": url,
                            "title": title
                        }
                    })
                return chunks_with_metadata
            else:
                print(f"No content extracted with Playwright from {url}, falling back to LangChain loader.")

        # Run blocking LangChain loader in threadpool executor
        loop = asyncio.get_running_loop()
        try:
            documents = await loop.run_in_executor(None, self._load_with_langchain, url)
        except Exception as e:
            print(f"LangChain loader error for {url}: {str(e)}")
            return []

        title = "Unknown Title"
        if documents and hasattr(documents[0], "metadata") and "title" in documents[0].metadata:
            title = documents[0].metadata["title"]

        splits = self.text_splitter.split_documents(documents)

        chunks_with_metadata = []
        for doc in splits:
            metadata = doc.metadata.copy() if hasattr(doc, "metadata") else {}
            metadata["source_type"] = "web"
            metadata["url"] = url
            if "title" not in metadata:
                metadata["title"] = title

            chunks_with_metadata.append({
                "id": generate_unique_id(),
                "text": doc.page_content,
                "metadata": metadata
            })

        return chunks_with_metadata
