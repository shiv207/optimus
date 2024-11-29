import os
import logging
import re
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Generator, Any
from concurrent.futures import ThreadPoolExecutor
import functools
import hashlib
import time
from uuid import uuid4
from time import sleep, time
from threading import Thread
from json import loads, dumps
from random import getrandbits
from websocket import WebSocketApp
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import json

# Google Search API
from googleapiclient.discovery import build

# NVIDIA OpenAI-compatible client
from openai import OpenAI

# DuckDuckGo image search
from duckduckgo_search import DDGS

class Perplexity:
    def __init__(self) -> None:
        # Load environment variables
        load_dotenv()
        
        # Configure NVIDIA OpenAI client
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv('NVIDIA_API_KEY')
        )
        
        # Configure Google Custom Search
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('SEARCH_ENGINE_ID')
        
        # Initialize News API
        self.newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        
        # Initialize Google Custom Search service
        self.google_service = build("customsearch", "v1", developerKey=self.google_api_key)
        
        # Advanced caching system with TTL
        self.url_cache = {}
        self.cache_ttl = 3600  # 1 hour cache lifetime
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Enhanced session with retry mechanism
        self.session = self._create_session_with_retry()
        
        # Add DuckDuckGo session
        self.ddg = DDGS()

    def _create_session_with_retry(self):
        """Create a session with retry mechanism and proper headers"""
        session = Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Add adapters with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set common headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        return session

    def google_search(self, query: str, num_results: int = 8) -> List[Dict]:
        """
        Perform Google search with optimized processing
        """
        try:
            if not self.google_api_key or not self.google_cse_id:
                logging.error("Google API key or Custom Search Engine ID is missing")
                return []

            # Add retry mechanism for the API call
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    search_results = self.google_service.cse().list(
                        q=query,
                        cx=self.google_cse_id,
                        num=num_results,
                        fields="items(title,link,snippet)",
                        safe="off"  # Remove safe search restriction
                    ).execute()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Google Search API failed after {max_retries} attempts: {str(e)}")
                        return []
                    time.sleep(1)  # Wait before retry

            if not search_results.get('items', []):
                logging.warning(f"No search results found for query: {query}")
                return []

            processed_results = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for item in search_results['items']:
                    url = item.get('link', '')
                    if self._is_valid_url(url):
                        future = executor.submit(
                            self._process_search_result,
                            url,
                            item.get('title', ''),
                            item.get('snippet', '')
                        )
                        futures.append(future)

                # Collect results, skipping any that failed
                for future in futures:
                    try:
                        result = future.result(timeout=10)
                        if result:
                            processed_results.append(result)
                    except Exception as e:
                        logging.error(f"Error processing search result: {str(e)}")
                        continue

            return processed_results

        except Exception as e:
            logging.error(f"Error in google_search: {str(e)}")
            return []

    def duckduckgo_image_search(self, query: str, num_results: int = 8) -> List[Dict]:
        """
        Perform image search using DuckDuckGo
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Construct the DuckDuckGo image search URL
            search_url = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
            
            # Get the search page
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            # Extract the vqd parameter needed for the API request
            vqd_match = re.search(r'vqd="([^"]+)"', response.text)
            if not vqd_match:
                return []
            vqd = vqd_match.group(1)
            
            # Make the actual API request
            api_url = f"https://duckduckgo.com/i.js?q={query}&o=json&vqd={vqd}"
            api_response = requests.get(api_url, headers=headers)
            api_response.raise_for_status()
            
            # Parse the results
            results = api_response.json().get('results', [])[:num_results]
            
            # Format the results
            image_results = []
            for result in results:
                image_results.append({
                    'title': result.get('title', 'Image'),
                    'image_url': result.get('image'),
                    'context_url': result.get('url'),
                    'thumbnail': result.get('thumbnail')
                })
            
            return image_results
            
        except Exception as e:
            logging.error(f"DuckDuckGo Image Search Error: {str(e)}")
            return []

    def search_images(self, query: str, max_results: int = 4) -> List[Dict]:
        """
        Search for images using DuckDuckGo
        """
        try:
            images = list(self.ddg.images(
                query,
                max_results=max_results,
                safesearch='on'
            ))
            
            return [{
                'url': img['image'],
                'thumbnail': img.get('thumbnail', img['image']),
                'title': img.get('title', ''),
                'source': img.get('url', '')
            } for img in images]
        except Exception as e:
            logging.error(f"Image Search Error: {str(e)}")
            return []

    def fetch_news_articles(self, query: str, days_back: int = 3) -> List[Dict]:
        """
        Fetch and format recent news articles
        """
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            news_results = self.newsapi.get_everything(
                q=query,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=3  # Reduced for faster response
            )
            
            if not news_results.get('articles'):
                return []
                
            processed_news = []
            for article in news_results['articles']:
                # Format the date nicely
                published_date = datetime.strptime(
                    article.get('publishedAt', ''), 
                    '%Y-%m-%dT%H:%M:%SZ'
                ).strftime('%B %d, %Y')
                
                # Clean and format the content
                content = article.get('content', '').split('[')[0].strip()  # Remove [...chars] suffix
                if not content:
                    content = article.get('description', '')
                
                processed_news.append({
                    'title': article.get('title', '').split(' - ')[0],  # Remove source suffix
                    'url': article.get('url', ''),
                    'description': article.get('description', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': published_date,
                    'content': content
                })
                
            return processed_news
            
        except Exception as e:
            logging.error(f"News API Error: {str(e)}")
            return []

    def fetch_search_results(self, query: str) -> Dict:
        """
        Optimized fetch_search_results with parallel processing
        """
        try:
            # Check cache first
            cache_key = hashlib.md5(query.encode()).hexdigest()
            if cache_key in self.url_cache:
                return self.url_cache[cache_key]
            
            # Parallel execution of searches with reduced timeout
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit searches with timeouts
                google_future = executor.submit(self.google_search, query, num_results=3)  # Reduced results
                news_future = executor.submit(self.fetch_news_articles, query, days_back=1)  # Reduced days
                
                # Get results with timeout
                search_results = google_future.result(timeout=5)
                news_results = news_future.result(timeout=3)
            
            if not search_results and not news_results:
                return {
                    'response': "No relevant information found. Please try rephrasing your question.",
                    'search_results': [],
                    'news_results': []
                }
            
            # Combine and format results
            formatted_results = []
            
            # Add news results first for recency (limit to 2)
            for news in news_results[:2]:
                formatted_results.append({
                    'url': news['url'],
                    'title': news['title'],
                    'hostname': urlparse(news['url']).netloc,
                    'content': news.get('content', ''),
                    'is_news': True,
                    'published_at': news['published_at']
                })
            
            # Add regular search results (limit to 3)
            for result in search_results[:3]:
                formatted_results.append({
                    'url': result['url'],
                    'title': result['title'],
                    'hostname': result['hostname'],
                    'content': result.get('content', ''),
                    'is_news': False
                })
            
            # Generate response
            response = self.generate_response(query, formatted_results)
            
            result = {
                'response': response,
                'search_results': formatted_results,
                'news_results': news_results[:2]
            }
            
            # Cache the result
            self.url_cache[cache_key] = result
            return result
            
        except Exception as e:
            logging.error(f"Search Result Fetching Error: {str(e)}")
            return {
                'response': "An error occurred. Please try again.",
                'search_results': [],
                'news_results': []
            }

    def generate_response(self, query: str, search_results: List[Dict]) -> str:
        """
        Enhanced response generation with news awareness
        """
        try:
            # Separate news and regular content
            news_sources = [result for result in search_results if result.get('is_news', False)]
            regular_sources = [result for result in search_results if not result.get('is_news', False)]
            
            # Format sources with priority on recent news
            formatted_sources = []
            
            # Add recent news first
            for i, news in enumerate(news_sources):
                formatted_sources.append(
                    f"Recent News {i+1}: {news.get('content', '')} "
                    f"(Published: {news.get('published_at', '')})"
                )
            
            # Add regular sources
            for i, result in enumerate(regular_sources):
                formatted_sources.append(f"Source {i+1}: {result.get('content', '')}")
            
            # Join all sources
            all_sources = "\n\n".join(formatted_sources)
            
            prompt = f"""
You are a highly skilled AI assistant known for producing responses in the style of Perplexity. Answer the query below with a comprehensive, well-structured response based on the provided content. Pay special attention to recent news and current events.

Query: {query}

Content:
{all_sources}

Guidelines for response structure:
1. Format the response in clean HTML with proper styling classes:
   - Use <div class="perplexity-response"> as the main container
   - Use <h3 class="section-header"> for section headers
   - Use <p class="perplexity-paragraph"> for paragraphs
   - Use <ul class="perplexity-list"> for lists
   - Use <li> for list items

2. Content organization:
   - If recent news exists, start with the latest developments
   - Provide specific dates and times for news events
   - Include relevant statistics and data
   - End with broader context or background information
   - Do not mention or reference sources directly

3. Writing style:
   - Professional and authoritative tone
   - Clear and concise language
   - Proper HTML formatting
   - Logical flow between sections
   - Emphasize recency when discussing current events

Format the response to work with the Perplexity UI styling, using smaller headers and no source references.
"""
            # Generate response with lower temperature for more accuracy
            completion = self.client.chat.completions.create(
                model="nvidia/llama3-chatqa-1.5-70b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower temperature for more focused responses
                top_p=0.7,
                max_tokens=1024
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Ensure proper formatting
            if not response.startswith('<div class="perplexity-response">'):
                response = f'<div class="perplexity-response">{response}</div>'
            
            return response
            
        except Exception as e:
            logging.error(f"Response Generation Error: {str(e)}")
            return f"An error occurred while generating the response: {str(e)}"

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and accessible"""
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
                
            # Skip certain problematic domains
            if any(domain in parsed.netloc.lower() for domain in [
                'instagram.com', 'facebook.com', 'twitter.com', 
                'linkedin.com', 'youtube.com'
            ]):
                return False

            return True
        except Exception:
            return False

    def _process_search_result(self, url: str, title: str, snippet: str) -> Dict:
        """
        Process a single search result
        """
        try:
            content = self._extract_page_content(url)
            
            return {
                'title': title,
                'url': url,
                'description': snippet,
                'hostname': urlparse(url).netloc,
                'content': content
            }
        except Exception:
            return None

    def _extract_page_content(self, url: str, max_length: int = 2000) -> str:
        """Optimized content extraction with faster parsing and better error handling"""
        try:
            # Skip problematic URLs
            parsed_url = urlparse(url)
            if any(domain in parsed_url.netloc.lower() for domain in [
                'instagram.com', 'facebook.com', 'twitter.com', 'linkedin.com',
                'youtube.com', 'tiktok.com', 'reddit.com'
            ]):
                return ""

            # Check cache first
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.url_cache:
                cached_data = self.url_cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_ttl:
                    return cached_data['content']

            # Use session for requests with shorter timeout
            response = self.session.get(
                url,
                timeout=5,
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('text/html'):
                return ""

            # Use lxml parser for better performance
            soup = BeautifulSoup(response.content, 'lxml')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'aside', 'noscript']):
                tag.decompose()

            # Focus on main content areas
            main_content = soup.find(['main', 'article', 'div[role="main"]']) or soup

            # Extract text content with better formatting
            paragraphs = []
            for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = p.get_text().strip()
                if len(text) > 20:  # Skip very short snippets
                    paragraphs.append(text)

            # Join paragraphs and clean text
            text = ' '.join(paragraphs)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
            
            # Truncate to max length while keeping whole sentences
            if len(text) > max_length:
                text = text[:max_length]
                last_period = text.rfind('.')
                if last_period > 0:
                    text = text[:last_period + 1]

            # Cache the result
            self.url_cache[cache_key] = {
                'content': text,
                'timestamp': time.time()
            }

            return text

        except Exception as e:
            logging.error(f"Content Extraction Error for {url}: {str(e)}")
            return ""

    def _calculate_result_score(self, result: Dict) -> float:
        """
        Calculate result score with optimized scoring
        """
        score = 0.0
        
        # Title relevance (weighted heavily)
        score += len(result.get('title', '').split()) * 2
        
        # Snippet quality
        score += len(result.get('description', '').split())
        
        # HTTPS bonus
        if result.get('url', '').startswith('https'):
            score += 5
            
        return score

    def _initialize_websocket(self) -> WebSocketApp:
        """
        Initializes the WebSocket connection.
        Initializes the WebSocket connection.
        """
        def on_open(ws: WebSocketApp) -> None:
            ws.send("2probe")
            ws.send("5")

        def on_message(ws: WebSocketApp, message: str) -> None:
            if message == "2":
                ws.send("3")
            elif not self.is_request_finished:
                if message.startswith("42"):
                    message_data: Dict[str, Any] = loads(message[2:])
                    content: Dict[str, Any] = message_data[1]


                    if "mode" in content:
                        try:
                            content.update(loads(content["text"]))
                            content.pop("text", None)
                        except:
                            pass


                    if message_data[0] == "query_answered":
                        self.last_request_id = content.get("uuid")
                        self.is_request_finished = True
                        return

                    if "final" in content and content["final"]:
                        self.response_queue.append(content)

        cookies: str = "; ".join([f"{key}={value}" for key, value in self.session.cookies.get_dict().items()])
        return WebSocketApp(
            url=f"wss://www.perplexity.ai/socket.io/?EIO=4&transport=websocket&sid={self.session_id}",
            header=self.request_headers,
            cookie=cookies,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"WebSocket error: {err}")
        )

    def generate_answer(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generates an answer to the given query using Perplexity AI and returns references.
        """
        # Reset state
        self.is_request_finished = False
        self.message_counter = (self.message_counter + 1) % 9 or self.base_message_number * 10
        self.response_queue.clear()
        self.collected_response = {"answer": "", "references": []}

        # Send query
        self.collected_response = {"answer": "", "references": []}

        # Send query
        self.websocket.send(str(self.base_message_number + self.message_counter) + dumps(
            ["perplexity_ask", query, {
                "frontend_session_id": str(uuid4()),
                "language": "en-GB",
                "timezone": "UTC",
                "search_focus": "internet",
                "frontend_uuid": str(uuid4()),
                "mode": "concise"
            }]
        ))

        # Initialize response tracking
        start_time: float = time()
        last_update: float = start_time
        check_interval: float = 0.05

        while (not self.is_request_finished) or self.response_queue:
            current_time = time()

            if current_time - start_time > 20:
                self.is_request_finished = True
                yield {"error": "Timed out."}
                return

            if current_time - last_update > check_interval:
                sleep(check_interval)

            while self.response_queue:
                response = self.response_queue.pop(0)
                last_update = current_time


                if "answer" in response and response["answer"]:
                    self.collected_response["answer"] = response["answer"]
                    yield self.collected_response.copy()

                if "web_results" in response:
                    self.collected_response["references"] = [
                        {
                            "title": result.get("title", "Unknown Title"),
                            "url": result.get("url", "No URL"),
                            "snippet": result.get("snippet", "")
                        }
                        for result in response["web_results"]
                    ]
                    yield self.collected_response.copy()
