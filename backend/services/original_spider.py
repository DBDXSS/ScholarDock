import requests
import time
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from core.config import settings
from models.article import ArticleSchema

# Selenium imports (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class OriginalScholarSpider:
    """Based on the original working google_scholar_spider.py"""
    
    def __init__(self):
        self.base_url = 'https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,5'
        self.startyear_url = '&as_ylo={}'
        self.endyear_url = '&as_yhi={}'
        self.sort_url = '&scisbd={}'  # Sort parameter
        self.robot_keywords = ['unusual traffic from your computer network', 'not a robot', 'We\'re sorry', 'blocked']
        self.session = None
        self.driver = None
        
        # Enhanced headers to mimic real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
    async def __aenter__(self):
        # Create a requests session with enhanced headers
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.quit()
    
    def _create_main_url(self, start_year: Optional[int] = None, end_year: Optional[int] = None, sort_by: str = 'relevance') -> str:
        """Create main URL based on year filters and sort option"""
        gscholar_main_url = self.base_url
        
        if start_year:
            gscholar_main_url = gscholar_main_url + self.startyear_url.format(start_year)
            
        if end_year and end_year != datetime.now().year:
            gscholar_main_url = gscholar_main_url + self.endyear_url.format(end_year)
        
        # Add sort parameter
        # relevance: 0 (default), date: 1
        if sort_by == 'date':
            gscholar_main_url = gscholar_main_url + self.sort_url.format(1)
        elif sort_by == 'relevance':
            gscholar_main_url = gscholar_main_url + self.sort_url.format(0)
            
        return gscholar_main_url
    
    def _get_citations(self, content: str) -> int:
        """Extract citation count from content with improved parsing"""
        # Try multiple patterns for citation extraction
        patterns = [
            r'Cited by (\d+)',
            r'被引用 (\d+)',
            r'citations?[:\s]*(\d+)',
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # Fallback to original method
        citation_start = content.find('Cited by ')
        if citation_start == -1:
            return 0
        citation_end = content.find('<', citation_start)
        if citation_end == -1:
            citation_end = citation_start + 20  # reasonable limit
        try:
            citation_text = content[citation_start + 9:citation_end].strip()
            # Extract only digits
            citation_digits = re.findall(r'\d+', citation_text)
            if citation_digits:
                return int(citation_digits[0])
        except (ValueError, IndexError):
            pass
        return 0
    
    def _get_year(self, content: str) -> int:
        """Extract year from content with improved parsing"""
        import re
        
        # Try multiple year patterns
        year_patterns = [
            r'\b(19|20)\d{2}\b',  # 4-digit years starting with 19 or 20
            r'(\d{4})',           # Any 4-digit number
            r'- (\d{4})',         # Year after dash
        ]
        
        current_year = datetime.now().year
        found_years = []
        
        for pattern in year_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    year = int(match if isinstance(match, str) else match[0])
                    # Validate year range (1900 to current year + 1)
                    if 1900 <= year <= current_year + 1:
                        found_years.append(year)
                except (ValueError, IndexError):
                    continue
        
        # Return the most recent valid year found
        if found_years:
            return max(found_years)
        
        # Fallback to original method
        try:
            for char in range(len(content)):
                if content[char] == '-':
                    out = content[char - 5:char - 1]
                    if out.isdigit() and len(out) == 4:
                        year = int(out)
                        if 1900 <= year <= current_year + 1:
                            return year
        except:
            pass
        return 0
    
    def _get_author(self, content: str) -> str:
        """Extract author from content"""
        try:
            author_end = content.find('-')
            return content[2:author_end - 1] if author_end > 2 else content
        except:
            return "Author not found"
    
    def _setup_driver(self):
        """Setup Chrome driver like the original code"""
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not available")
            return None
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # Don't use headless mode for CAPTCHA solving
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return None
    
    def _get_element(self, driver, xpath, attempts=5, count=0):
        """Safe get_element method with multiple attempts (from original code)"""
        try:
            element = driver.find_element(By.XPATH, xpath)
            return element
        except Exception as e:
            if count < attempts:
                time.sleep(1)
                return self._get_element(driver, xpath, attempts=attempts, count=count + 1)
            else:
                print("Element not found")
                return None
    
    def _get_content_with_selenium(self, url):
        """Get content with Selenium (adapted from original code)"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            if not self.driver:
                self.driver = self._setup_driver()
                
            if not self.driver:
                return None
            
            print(f"🌐 Opening URL with Selenium: {url}")
            self.driver.get(url)
            
            el = self._get_element(self.driver, "/html/body")
            if not el:
                return None
                
            content = el.get_attribute('innerHTML')
            
            if any(kw in content for kw in self.robot_keywords):
                print("🚨 CAPTCHA detected! Please solve manually...")
                print("The browser window should be open. Solve the CAPTCHA and the search will continue automatically.")
                
                # Wait for user to solve CAPTCHA
                # In a production environment, you might implement a more sophisticated solution
                time.sleep(30)  # Give user time to solve CAPTCHA
                
                # Get content again after CAPTCHA solving
                self.driver.get(url)
                el = self._get_element(self.driver, "/html/body")
                if el:
                    content = el.get_attribute('innerHTML')
            
            return content.encode('utf-8')
            
        except Exception as e:
            print(f"❌ Selenium error: {e}")
            return None
    
    def _parse_gs_or_div(self, div) -> Optional[ArticleSchema]:
        """Parse a single gs_or div element to extract article data with improved error handling"""
        try:
            # Initialize default values
            title = "Unknown Title"
            url = None
            citations = 0
            year = 0
            author = "Unknown Author"
            publisher = "Unknown Publisher"
            venue = "Unknown Venue"
            description = None
            pdf_url = None
            
            # Extract PDF link from Google Scholar page
            pdf_url = self._extract_pdf_link(div)
            
            # Title and link - try multiple selectors with more aggressive approach
            title_elem = div.find('h3')
            if not title_elem:
                # Try more alternative selectors
                title_elem = (div.find('div', {'class': 'gs_rt'}) or
                             div.find('a') or
                             div.find('div', {'class': 'gs_r'}) or
                             div.find('span'))
            
            if title_elem:
                title_link = title_elem.find('a')
                if title_link:
                    title = title_link.text.strip()
                    url = title_link.get('href', '')
                else:
                    title = title_elem.text.strip()
                
                # Clean up title - be more lenient
                if title and title.strip() and title != 'Could not catch title':
                    title = title.replace('\n', ' ').replace('\r', ' ').strip()
                    # Remove excessive whitespace
                    title = ' '.join(title.split())
                else:
                    title = "Unknown Title"
            else:
                # If no title element found, try to extract from any text in the div
                all_text = div.get_text().strip()
                if all_text:
                    # Take the first meaningful line as title
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    if lines:
                        title = lines[0][:100]  # First line, max 100 chars
                        print(f"📝 Extracted title from div text: {title[:50]}...")
                    else:
                        title = "Unknown Title"
                else:
                    title = "Unknown Title"
            
            # Citations with improved extraction
            citations = self._get_citations(str(div))
            
            # Author info from gs_a div
            gs_a_div = div.find('div', {'class': 'gs_a'})
            if gs_a_div:
                gs_a_text = gs_a_div.text.strip()
                
                # Year with improved parsing
                year = self._get_year(gs_a_text)
                
                # Author with improved parsing
                author = self._get_author(gs_a_text)
                if not author or author == "Author not found":
                    # Try to extract first part before comma or dash
                    try:
                        first_part = gs_a_text.split(',')[0].split('-')[0].strip()
                        if first_part and len(first_part) > 2:
                            author = first_part
                    except:
                        author = "Unknown Author"
                
                # Publisher and venue with improved parsing
                try:
                    parts = gs_a_text.split("-")
                    if len(parts) > 1:
                        publisher = parts[-1].strip()
                        if not publisher:
                            publisher = "Unknown Publisher"
                    
                    if len(parts) > 2:
                        venue_part = parts[-2]
                        venue = " ".join(venue_part.split(",")[:-1]).strip()
                        if not venue:
                            venue = "Unknown Venue"
                    elif len(parts) > 1:
                        # Try to extract venue from the middle part
                        middle_parts = gs_a_text.split(",")
                        if len(middle_parts) > 1:
                            venue = middle_parts[-2].strip()
                except Exception as e:
                    print(f"Warning: Failed to parse publisher/venue: {e}")
                    # Keep default values
            
            # Description from gs_rs div
            gs_rs_div = div.find('div', {'class': 'gs_rs'})
            if gs_rs_div:
                description = gs_rs_div.text.strip()
                if description:
                    # Clean up description
                    description = description.replace('\n', ' ').replace('\r', ' ').strip()
            
            # Calculate citations per year
            citations_per_year = 0.0
            if year > 0 and citations > 0:
                years_passed = max(1, datetime.now().year - year)
                citations_per_year = round(citations / years_passed, 2)
            
            # Be more lenient with title requirements - accept any non-empty title
            if not title or title.strip() == "" or title == "Unknown Title":
                # Try to get any text from the div as fallback
                all_text = div.get_text().strip()
                if all_text and len(all_text) > 5:  # Lowered threshold from 10 to 5
                    title = all_text[:100] + "..." if len(all_text) > 100 else all_text
                    print(f"📝 Using fallback title: {title[:50]}...")
                else:
                    # Even if we can't get a good title, still try to extract the article
                    # as it might have useful citation/author information
                    title = f"Article from {datetime.now().strftime('%Y-%m-%d')}"
                    print(f"⚠️  Using generic title for article with citation data")
            
            return ArticleSchema(
                title=title,
                authors=author,
                venue=venue,
                publisher=publisher,
                year=year if year > 0 else None,
                citations=citations,
                citations_per_year=citations_per_year,
                description=description,
                url=url,
                pdf_url=pdf_url
            )
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            # Try to extract at least basic info - be more aggressive about saving articles
            try:
                basic_text = div.get_text().strip()
                if basic_text and len(basic_text) > 5:  # Lowered threshold
                    # Try to extract any citations even in fallback mode
                    fallback_citations = self._get_citations(str(div))
                    return ArticleSchema(
                        title=basic_text[:100] + "..." if len(basic_text) > 100 else basic_text,
                        authors="Unknown Author",
                        venue="Unknown Venue",
                        publisher="Unknown Publisher",
                        year=None,
                        citations=fallback_citations,
                        citations_per_year=0.0,
                        description=basic_text,
                        url=None,
                        pdf_url=None
                    )
                else:
                    # Even if we have very little info, create a minimal record
                    print(f"⚠️  Creating minimal record for div with limited content")
                    return ArticleSchema(
                        title=f"Untitled Article {datetime.now().strftime('%H:%M:%S')}",
                        authors="Unknown Author",
                        venue="Unknown Venue",
                        publisher="Unknown Publisher",
                        year=None,
                        citations=0,
                        citations_per_year=0.0,
                        description="Content could not be parsed",
                        url=None,
                        pdf_url=None
                    )
            except Exception as fallback_error:
                print(f"❌ Complete fallback failed: {fallback_error}")
                # Last resort - return a minimal record rather than None
                return ArticleSchema(
                    title=f"Parse Error Article {datetime.now().strftime('%H:%M:%S')}",
                    authors="Parse Error",
                    venue="Parse Error",
                    publisher="Parse Error",
                    year=None,
                    citations=0,
                    citations_per_year=0.0,
                    description="Article parsing completely failed",
                    url=None,
                    pdf_url=None
                )
    
    def _extract_pdf_link(self, div) -> Optional[str]:
        """
        Extract PDF link from Google Scholar article div
        """
        try:
            # Look for PDF links in various formats
            # 1. Look for direct PDF links in anchor tags
            pdf_links = div.find_all('a', href=True)
            for link in pdf_links:
                href = link.get('href', '')
                text = link.get_text().strip().lower()
                
                # Check if this is a PDF link
                if (href.endswith('.pdf') or
                    'pdf' in text or
                    'filetype:pdf' in href or
                    '.pdf' in href):
                    # Make sure it's a valid URL
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return f"https://scholar.google.com{href}"
            
            # 2. Look for PDF links in specific Google Scholar patterns
            # Sometimes PDFs are in gs_or_ggsm divs with specific classes
            gs_or_divs = div.find_all('div', {'class': ['gs_or_ggsm', 'gs_md_wp gs_ttss']})
            for gs_div in gs_or_divs:
                pdf_links = gs_div.find_all('a', href=True)
                for link in pdf_links:
                    href = link.get('href', '')
                    if href.endswith('.pdf') or '.pdf' in href:
                        if href.startswith('http'):
                            return href
            
            # 3. Look for arxiv, researchgate, or other repository links that might have PDFs
            for link in pdf_links:
                href = link.get('href', '')
                if any(domain in href.lower() for domain in ['arxiv.org', 'researchgate.net', 'ieee.org', 'acm.org']):
                    # These sites often have PDF versions
                    if 'arxiv.org' in href and '/abs/' in href:
                        # Convert arxiv abstract link to PDF link
                        pdf_href = href.replace('/abs/', '/pdf/') + '.pdf'
                        return pdf_href
                    elif href.startswith('http'):
                        return href
            
            return None
            
        except Exception as e:
            print(f"Error extracting PDF link: {e}")
            return None
    
    async def search(self, keyword: str, num_results: int = 50,
                    start_year: Optional[int] = None,
                    end_year: Optional[int] = None,
                    sort_by: str = 'relevance') -> List[ArticleSchema]:
        """Search Google Scholar using the original working method
        
        Args:
            keyword: Search term
            num_results: Number of results to fetch
            start_year: Start year filter
            end_year: End year filter
            sort_by: Sort order - 'relevance' (default) or 'date'
        """
        
        articles = []
        gscholar_main_url = self._create_main_url(start_year, end_year, sort_by)
        
        print(f"🔍 Searching Google Scholar for '{keyword}' (target: {num_results} results)")
        print(f"📊 Sort by: {sort_by}")
        print(f"🌐 Using URL pattern: {gscholar_main_url}")
        
        # Get content from URLs in batches of 10
        for n in range(0, num_results, 10):
            url = gscholar_main_url.format(str(n), keyword.replace(' ', '+'))
            print(f"📖 Fetching page {n//10 + 1}, URL: {url}")
            
            try:
                # Make request
                page = self.session.get(url)
                content = page.content
                
                # Check for robot detection
                content_str = content.decode('ISO-8859-1', errors='ignore')
                if any(kw in content_str for kw in self.robot_keywords):
                    print("🤖 Robot checking detected, trying Selenium...")
                    # Use Selenium fallback like the original code
                    try:
                        content = self._get_content_with_selenium(url)
                        if not content:
                            print("❌ Selenium fallback failed")
                            continue
                    except Exception as e:
                        print(f"❌ Selenium error: {e}")
                        continue
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
                
                # Find articles using the original selector
                mydivs = soup.findAll("div", {"class": "gs_or"})
                print(f"📄 Found {len(mydivs)} article divs on this page")
                
                if not mydivs:
                    print("⚠️  No articles found, might be blocked or end of results")
                    break
                
                # Parse each article with comprehensive logging
                page_articles = 0
                failed_articles = 0
                skipped_articles = 0
                
                print(f"🔍 Processing {len(mydivs)} article divs on page {n//10 + 1}")
                
                for i, div in enumerate(mydivs):
                    if len(articles) >= num_results:
                        skipped_articles += 1
                        continue
                        
                    print(f"📝 Processing article {i+1}/{len(mydivs)} on page {n//10 + 1}")
                    
                    article = self._parse_gs_or_div(div)
                    if article:
                        articles.append(article)
                        page_articles += 1
                        print(f"✅ Parsed: {article.title[:60]}... ({article.citations} citations, {article.year or 'N/A'})")
                    else:
                        failed_articles += 1
                        print(f"❌ Failed to parse article {i+1} - this should not happen with new fallback logic")
                        # Debug: print the div content that failed
                        div_text = div.get_text()[:200] if div else "No div content"
                        print(f"🔍 Failed div content preview: {div_text}...")
                
                print(f"📊 Page {n//10 + 1} Summary:")
                print(f"   - Found {len(mydivs)} divs")
                print(f"   - Successfully parsed: {page_articles}")
                print(f"   - Failed to parse: {failed_articles}")
                print(f"   - Skipped (limit reached): {skipped_articles}")
                print(f"   - Total articles so far: {len(articles)}")
                
                # If we got no articles from this page, it might indicate end of results
                if page_articles == 0 and len(mydivs) > 0:
                    print("⚠️  No articles parsed from this page despite finding divs - investigating...")
                    # Debug: show what divs we found
                    for i, div in enumerate(mydivs[:3]):  # Show first 3 divs
                        print(f"🔍 Div {i+1} classes: {div.get('class', [])}")
                        print(f"🔍 Div {i+1} content preview: {div.get_text()[:100]}...")
                
                if len(articles) >= num_results:
                    break
                
                # Original delay
                print("⏳ Waiting 0.5s before next request...")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error fetching page {n//10 + 1}: {e}")
                continue
        
        print(f"🎉 Search completed: {len(articles)} articles found")
        return articles