import requests
from bs4 import BeautifulSoup
import re

def extract_article_text(url):
    """
    Scrapes the full text of an article from a URL.
    Uses BeautifulSoup with a clean-up pipeline for maximum compatibility.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Failed to fetch article (HTTP {response.status_code})",
                "title": "",
                "text": ""
            }
        
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Meta tags check
        meta_title = soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            title = meta_title.get("content").strip()
            
        # Clean the document
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
            element.decompose()
            
        # Try to find the main content body
        article_body = None
        # Common selectors for main content
        selectors = [
            "article", "[role='main']", ".main-content", ".article-body", 
            ".post-content", ".entry-content", "#article-body", "#story-body"
        ]
        
        for selector in selectors:
            found = soup.select(selector)
            if found:
                # Use the first match that has significant text content
                for candidate in found:
                    if len(candidate.get_text().strip()) > 300:
                        article_body = candidate
                        break
                if article_body:
                    break
        
        # If no main article block is found, use soup body
        if not article_body:
            article_body = soup.body if soup.body else soup
            
        # Extract paragraphs
        paragraphs = article_body.find_all(["p", "h1", "h2", "h3", "h4"])
        text_blocks = []
        for p in paragraphs:
            text = p.get_text().strip()
            # Filter out short fragments, social media share text, or cookies notices
            if len(text) > 40 and not re.search(r'(share on|follow us|cookie policy|sign up|subscribe|read more|privacy policy)', text, re.I):
                text_blocks.append(text)
                
        full_text = "\n\n".join(text_blocks)
        
        # If the extracted text is too short, grab all text from body
        if len(full_text.strip()) < 150:
            all_p = soup.find_all("p")
            full_text = "\n\n".join([p.get_text().strip() for p in all_p if len(p.get_text().strip()) > 20])
            
        # If still empty, try meta description fallback
        if len(full_text.strip()) < 100:
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                full_text = meta_desc.get("content").strip()
                
        if len(full_text.strip()) < 50:
            return {
                "success": False,
                "error": "Could not extract sufficient text content from this website.",
                "title": title,
                "text": ""
            }
            
        return {
            "success": True,
            "title": title or "Untitled Article",
            "text": full_text,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error scraping article: {str(e)}",
            "title": "",
            "text": ""
        }
