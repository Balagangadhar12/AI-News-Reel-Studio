import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from config import Config

def clean_headline(title):
    title = (title or "").strip()
    title = re.sub(r"\s+-\s+[^-]{2,80}$", "", title).strip()
    return title

def clean_description(description):
    description = BeautifulSoup(description or "", "html.parser").get_text(" ")
    if "\xa0\xa0" in description:
        description = description.split("\xa0\xa0", 1)[0].strip()
    description = re.split(r"\s{2,}", description, maxsplit=1)[0]
    description = re.sub(r"\s+", " ", description).strip()
    return description

def get_latest_news(topic="top stories", api_key=None):
    """
    Fetch the latest headlines for the home page picker.
    Uses NewsAPI top-headlines when configured, then falls back to Google News RSS.
    """
    api_key = api_key or Config.NEWS_API_KEY
    if api_key:
        try:
            params = {
                "country": "us",
                "pageSize": 12,
                "apiKey": api_key
            }
            if topic and topic.lower() not in ("top stories", "latest", "latest news"):
                params = {
                    "q": topic,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 12,
                    "apiKey": api_key
                }
                url = "https://newsapi.org/v2/everything"
            else:
                url = "https://newsapi.org/v2/top-headlines"

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = normalize_newsapi_articles(response.json().get("articles", []))
                if articles:
                    return articles
        except Exception as e:
            print(f"NewsAPI latest error (falling back to RSS): {e}")

    return fetch_google_news_rss(topic or "top stories")

def normalize_newsapi_articles(raw_articles):
    articles = []
    for art in raw_articles:
        title = art.get("title") or ""
        if not title or "[Removed]" in title or not art.get("url"):
            continue
        articles.append({
            "title": clean_headline(title),
            "description": clean_description(art.get("description") or ""),
            "url": art.get("url"),
            "source": art.get("source", {}).get("name") or "NewsAPI",
            "publishedAt": (art.get("publishedAt") or "")[:10],
            "content": art.get("content") or ""
        })
    return articles

def search_news(query, api_key=None):
    """
    Search for news articles based on a query.
    Tries NewsAPI first if an API key is available, then falls back to Google News RSS.
    """
    api_key = api_key or Config.NEWS_API_KEY
    articles = []
    
    if api_key:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": "en",
                "sortBy": "relevance",
                "pageSize": 10,
                "apiKey": api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = normalize_newsapi_articles(data.get("articles", []))
                if articles:
                    return articles
        except Exception as e:
            print(f"NewsAPI error (falling back to RSS): {e}")

    # Fallback to Google News RSS
    return fetch_google_news_rss(query)

def fetch_google_news_rss(query):
    """
    Fetch news from Google News RSS feed for a query.
    No API key required.
    """
    articles = []
    try:
        clean_query = (query or "").strip()
        if clean_query.lower() in ("", "top stories", "latest", "latest news"):
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        else:
            encoded_query = quote_plus(clean_query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:12]:
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                source_elem = item.find('source')
                source = source_elem.text if source_elem is not None else "Google News"
                description = item.find('description').text if item.find('description') is not None else ""
                
                # Strip HTML tags from description if present
                if description:
                    description = clean_description(description)

                if title and link:
                    articles.append({
                        "title": clean_headline(title),
                        "description": description,
                        "url": link,
                        "source": source,
                        "publishedAt": pub_date,
                        "content": ""
                    })
    except Exception as e:
        print(f"Error fetching Google News RSS: {e}")
        
    return articles
