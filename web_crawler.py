import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
import time
from collections import defaultdict

class WebsiteCrawler:
    def __init__(self, start_url, max_pages=10, same_domain_only=True):
        """
        Initialize the crawler with a starting URL and constraints.
        
        Args:
            start_url: The URL to start crawling from
            max_pages: Maximum number of pages to crawl
            same_domain_only: Whether to restrict crawling to the same domain
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.visited_urls = set()
        self.to_visit = [start_url]
        self.domain = urlparse(start_url).netloc
        self.pages_data = []
        self.structured_data = []
        self.site_metadata = {
            "title": "",
            "description": "",
            "domain": self.domain,
            "pages_crawled": 0,
            "total_word_count": 0,
            "heading_count": defaultdict(int),
            "has_schema_markup": False,
            "internal_links": 0,
            "external_links": 0,
            "image_count": 0,
            "pages_with_thin_content": 0
        }
    
    def is_valid_url(self, url):
        """Check if a URL should be crawled based on our constraints."""
        if not url or url in self.visited_urls:
            return False
            
        # Skip URLs with fragments or query parameters to avoid duplicates
        url_parts = urlparse(url)
        if url_parts.fragment:
            return False
            
        # If we're restricting to the same domain, check the domain
        if self.same_domain_only and url_parts.netloc != self.domain:
            return False
            
        # Skip common non-content file types
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.css', '.js')):
            return False
            
        return True
    
    def extract_links(self, soup, current_url):
        """Extract all links from a page."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            if href and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                # Convert relative URLs to absolute
                full_url = urljoin(current_url, href)
                if self.is_valid_url(full_url):
                    links.append(full_url)
                    
                    # Count internal vs external links
                    if urlparse(full_url).netloc == self.domain:
                        self.site_metadata["internal_links"] += 1
                    else:
                        self.site_metadata["external_links"] += 1
        return links
    
    def extract_structured_data(self, soup, url):
        """Extract JSON-LD structured data from the page."""
        structured_data = []
        
        # Look for JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append({
                    "url": url,
                    "type": "JSON-LD",
                    "data": data
                })
                self.site_metadata["has_schema_markup"] = True
            except (json.JSONDecodeError, TypeError):
                pass
                
        # Look for microdata
        items = []
        for element in soup.find_all(itemscope=True):
            item_type = element.get('itemtype', '')
            if item_type:
                items.append({
                    "type": item_type,
                    "url": url
                })
                self.site_metadata["has_schema_markup"] = True
                
        if items:
            structured_data.append({
                "url": url,
                "type": "Microdata",
                "data": items
            })
            
        return structured_data
    
    def extract_page_content(self, soup, url):
        """Extract and analyze the content of a page."""
        # Basic page information
        title = soup.title.string.strip() if soup.title else ""
        
        # If this is the home page, use it for the site title
        if url == self.start_url:
            self.site_metadata["title"] = title
            
        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')
            
            # If this is the home page, use it for the site description
            if url == self.start_url:
                self.site_metadata["description"] = meta_desc
        
        # Extract all text content (excluding scripts, styles, etc.)
        for script in soup(['script', 'style', 'noscript', 'iframe', 'head']):
            script.extract()
            
        text_content = soup.get_text(separator=' ', strip=True)
        cleaned_text = re.sub(r'\s+', ' ', text_content).strip()
        word_count = len(cleaned_text.split())
        
        # Update site metadata
        self.site_metadata["total_word_count"] += word_count
        if word_count < 300:
            self.site_metadata["pages_with_thin_content"] += 1
            
        # Count headings by level
        for i in range(1, 7):
            heading_count = len(soup.find_all(f'h{i}'))
            self.site_metadata["heading_count"][f"h{i}"] += heading_count
            
        # Count images
        self.site_metadata["image_count"] += len(soup.find_all('img'))
        
        # Extract headings with their text
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    "level": i,
                    "text": heading.get_text(strip=True)
                })
                
        # Extract paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        
        # Look for question-answer patterns
        qa_pairs = []
        question_elements = soup.find_all(['h2', 'h3', 'h4', 'strong'], string=lambda s: s and '?' in s)
        for question_el in question_elements:
            question = question_el.get_text(strip=True)
            # Look for the next paragraph as a potential answer
            answer_el = question_el.find_next('p')
            if answer_el:
                answer = answer_el.get_text(strip=True)
                qa_pairs.append({
                    "question": question,
                    "answer": answer
                })
        
        return {
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "word_count": word_count,
            "headings": headings,
            "paragraphs": paragraphs,
            "qa_pairs": qa_pairs,
            "full_text": cleaned_text
        }
    
    def crawl(self):
        """Crawl the website and collect data."""
        while self.to_visit and len(self.visited_urls) < self.max_pages:
            # Get the next URL to visit
            current_url = self.to_visit.pop(0)
            
            # Skip if we've already visited this URL
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling: {current_url}")
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            try:
                # Add a small delay to be respectful
                time.sleep(1)
                
                # Fetch the page
                response = requests.get(current_url, timeout=10)
                
                # Skip if not a successful HTML response
                if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                    
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract links and add to the to-visit list
                links = self.extract_links(soup, current_url)
                for link in links:
                    if link not in self.visited_urls and link not in self.to_visit:
                        self.to_visit.append(link)
                
                # Extract structured data
                page_structured_data = self.extract_structured_data(soup, current_url)
                if page_structured_data:
                    self.structured_data.extend(page_structured_data)
                
                # Extract and analyze page content
                page_data = self.extract_page_content(soup, current_url)
                self.pages_data.append(page_data)
                
                # Increment pages crawled
                self.site_metadata["pages_crawled"] += 1
                
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
        
        # Finalize site metadata
        if self.site_metadata["pages_crawled"] > 0:
            self.site_metadata["avg_word_count"] = self.site_metadata["total_word_count"] / self.site_metadata["pages_crawled"]
        
        return {
            "metadata": self.site_metadata,
            "pages": self.pages_data,
            "structured_data": self.structured_data
        }

# Example usage
if __name__ == "__main__":
    crawler = WebsiteCrawler("https://ribin.in", max_pages=5)
    results = crawler.crawl()
    print(json.dumps(results, indent=2))
    # Save the results to a file
    website_name = urlparse(crawler.start_url).netloc.replace('.', '_')
    output_file = f"{website_name}_crawl_results.json"
    with open(output_file, "w") as f:
        f.write(json.dumps(results, indent=2))
    print(f"Results saved to {output_file}")