import os
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class PDFDownloader:
    def __init__(self):
        self.session = None
        self.failed_urls = set()  # 缓存已知失败的URL，避免重复尝试
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]
        # 确保有.pdf扩展名
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        return filename
    
    def _is_valid_pdf_url(self, url: str) -> bool:
        """检查URL是否可能是PDF链接"""
        if not url:
            return False
        
        # 检查URL是否包含PDF相关的路径或参数
        pdf_indicators = ['.pdf', 'pdf', 'download', 'attachment']
        url_lower = url.lower()
        
        return any(indicator in url_lower for indicator in pdf_indicators)
    
    def _extract_pdf_urls(self, article_url: str) -> List[str]:
        """从文章URL中提取可能的PDF链接"""
        pdf_urls = []
        
        # 特殊处理：ETH Zurich - 只尝试最基本的变体，避免重复失败
        if 'research-collection.ethz.ch' in article_url and 'bitstream/handle' in article_url:
            # 首先添加原始URL
            pdf_urls.append(article_url)
            
            # 只尝试移除sequence参数的版本
            if '?sequence=' in article_url:
                direct_pdf_url = article_url.split('?sequence=')[0]
                if direct_pdf_url != article_url:
                    pdf_urls.append(direct_pdf_url)
            
            # 对于ETH，我们知道/download不会工作，所以跳过
            # 这样可以避免不必要的重复尝试
            logger.info(f"ETH URL detected, limiting attempts to avoid known failures: {article_url}")
            return pdf_urls
        
        # 如果URL本身就是PDF链接
        if self._is_valid_pdf_url(article_url):
            pdf_urls.append(article_url)
        
        # 对于其他网站，尝试常见的PDF URL模式
        base_url = article_url.rstrip('/')
        
        # 常见的PDF URL后缀
        pdf_suffixes = [
            '/pdf',
            '.pdf',
            '/download',
            '/attachment',
            '?format=pdf',
            '&format=pdf'
        ]
        
        for suffix in pdf_suffixes:
            pdf_url = base_url + suffix
            if pdf_url != article_url:  # 避免重复
                pdf_urls.append(pdf_url)
        
        return pdf_urls
    
    async def _handle_auto_download_page(self, url: str, content: str) -> Optional[str]:
        """处理自动下载页面，提取实际的PDF下载链接"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            base_url = '/'.join(url.split('/')[:-1]) + '/'
            
            # 特殊处理：ETH Zurich类型的PDF查看器页面
            # 如果页面包含PDF查看器，尝试直接使用原URL但修改参数
            if 'research-collection.ethz.ch' in url and 'bitstream/handle' in url:
                # ETH的PDF链接通常可以通过移除?sequence参数来直接访问
                if '?sequence=' in url:
                    direct_pdf_url = url.split('?sequence=')[0]
                    if direct_pdf_url not in self.failed_urls:
                        logger.info(f"ETH direct PDF URL attempt: {direct_pdf_url}")
                        return direct_pdf_url
                
                # 如果已经是/download结尾，说明这种方法不行，记录失败并返回None
                if url.endswith('/download'):
                    logger.warning(f"ETH download URL failed, adding to failed cache: {url}")
                    self.failed_urls.add(url)
                    return None
                
                # 尝试添加/download参数，但先检查是否已经在失败缓存中
                download_url = url.rstrip('/') + '/download'
                if download_url not in self.failed_urls:
                    logger.info(f"ETH download URL attempt: {download_url}")
                    return download_url
                else:
                    logger.info(f"Skipping known failed URL: {download_url}")
                    return None
            
            # 检查meta refresh重定向
            meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
            if meta_refresh:
                content_attr = meta_refresh.get('content', '')
                # 解析meta refresh内容，格式通常是 "5;URL=http://example.com/file.pdf"
                if 'url=' in content_attr.lower():
                    redirect_url = content_attr.lower().split('url=')[1].strip()
                    if redirect_url.startswith('http'):
                        return redirect_url
                    else:
                        return urljoin(base_url, redirect_url)
            
            # 检查JavaScript重定向
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_content = script.string.lower()
                    # 查找window.location或location.href重定向
                    if 'window.location' in script_content or 'location.href' in script_content:
                        # 尝试提取URL
                        url_patterns = [
                            r'window\.location\s*=\s*[\'"]([^\'"]+)[\'"]',
                            r'location\.href\s*=\s*[\'"]([^\'"]+)[\'"]',
                            r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]'
                        ]
                        for pattern in url_patterns:
                            match = re.search(pattern, script_content)
                            if match:
                                redirect_url = match.group(1)
                                if redirect_url.startswith('http'):
                                    return redirect_url
                                else:
                                    return urljoin(base_url, redirect_url)
            
            # 查找"Now downloading"或类似文本附近的链接
            download_indicators = [
                'now downloading', 'download will start', 'downloading',
                'click here if download', 'if your download does not start'
            ]
            
            for indicator in download_indicators:
                text_elements = soup.find_all(text=re.compile(indicator, re.I))
                for element in text_elements:
                    # 查找附近的链接
                    parent = element.parent
                    if parent:
                        links = parent.find_all('a', href=True)
                        for link in links:
                            href = link.get('href')
                            if href and self._is_valid_pdf_url(href):
                                if href.startswith('http'):
                                    return href
                                else:
                                    return urljoin(base_url, href)
            
            # 查找所有PDF链接作为后备
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href and href.lower().endswith('.pdf'):
                    if href.startswith('http'):
                        return href
                    else:
                        return urljoin(base_url, href)
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling auto download page: {e}")
            return None
    
    async def _download_single_pdf(self, url: str, filepath: str, recursion_depth: int = 0) -> bool:
        """下载单个PDF文件"""
        # 防止无限递归
        if recursion_depth > 3:
            logger.warning(f"Maximum recursion depth reached for URL: {url}")
            return False
        
        # 检查是否为已知失败的URL
        if url in self.failed_urls:
            logger.info(f"Skipping known failed URL: {url}")
            return False
            
        try:
            logger.info(f"Attempting to download PDF from: {url} (depth: {recursion_depth})")
            
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # 检查是否为PDF内容
                    if 'application/pdf' in content_type or 'application/octet-stream' in content_type:
                        content = await response.read()
                        
                        # 验证PDF文件头
                        if content.startswith(b'%PDF'):
                            # 确保目录存在
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            
                            logger.info(f"Successfully downloaded PDF: {filepath}")
                            return True
                        else:
                            logger.warning(f"Downloaded content is not a valid PDF: {url}")
                    
                    # 如果不是PDF内容，检查是否为HTML自动下载页面
                    elif 'text/html' in content_type:
                        logger.info(f"Detected HTML page, checking for auto-download: {url}")
                        content = await response.text()
                        
                        # 尝试从HTML页面中提取实际的PDF下载链接
                        actual_pdf_url = await self._handle_auto_download_page(url, content)
                        if actual_pdf_url and actual_pdf_url != url:  # 避免同一个URL的无限递归
                            logger.info(f"Found actual PDF URL: {actual_pdf_url}")
                            # 递归调用下载实际的PDF链接
                            return await self._download_single_pdf(actual_pdf_url, filepath, recursion_depth + 1)
                        else:
                            logger.warning(f"Could not extract PDF URL from HTML page: {url}")
                    else:
                        logger.warning(f"Content type is not PDF or HTML: {content_type} for URL: {url}")
                else:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
        
        return False
    
    def _should_use_browser(self, url: str) -> bool:
        """判断是否需要使用浏览器自动化"""
        browser_required_sites = [
            'research-collection.ethz.ch',
            'ieeexplore.ieee.org',
            'link.springer.com',
            'dl.acm.org'
        ]
        return any(site in url for site in browser_required_sites)
    
    async def _download_with_browser(self, url: str, filepath: str) -> bool:
        """使用浏览器自动化下载PDF（实验性功能）"""
        if not self._should_use_browser(url):
            return False
        
        try:
            # 尝试导入playwright
            from playwright.async_api import async_playwright
            
            logger.info(f"Attempting browser automation for: {url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # 设置超时和用户代理
                page.set_default_timeout(30000)
                await page.set_extra_http_headers({
                    'User-Agent': self.headers['User-Agent']
                })
                
                # 导航到页面
                await page.goto(url, wait_until='networkidle')
                
                # 方法1: 等待PDF响应
                try:
                    response = await page.wait_for_response(
                        lambda r: (r.url.endswith('.pdf') or 'application/pdf' in r.headers.get('content-type', ''))
                                 and r.status == 200,
                        timeout=15000
                    )
                    pdf_content = await response.body()
                    
                    if pdf_content and pdf_content.startswith(b'%PDF'):
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(pdf_content)
                        logger.info(f"Browser automation successful: {filepath}")
                        await browser.close()
                        return True
                        
                except Exception as e:
                    logger.info(f"PDF response wait failed: {e}")
                
                # 方法2: 查找并点击下载链接
                download_selectors = [
                    'a[href*=".pdf"]',
                    'a[href*="download"]',
                    'button:has-text("Download")',
                    'a:has-text("PDF")',
                    'a:has-text("Download")',
                    '.download-link',
                    '[data-download]'
                ]
                
                for selector in download_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            logger.info(f"Found download element: {selector}")
                            
                            # 尝试直接获取href
                            href = await element.get_attribute('href')
                            if href and href.endswith('.pdf'):
                                # 直接下载PDF链接
                                pdf_url = urljoin(url, href)
                                if await self._download_single_pdf(pdf_url, filepath, 0):
                                    await browser.close()
                                    return True
                            
                            # 尝试点击下载
                            async with page.expect_download(timeout=10000) as download_info:
                                await element.click()
                            download = await download_info.value
                            await download.save_as(filepath)
                            logger.info(f"Browser download successful: {filepath}")
                            await browser.close()
                            return True
                            
                    except Exception as e:
                        logger.debug(f"Download attempt failed for {selector}: {e}")
                        continue
                
                await browser.close()
                
        except ImportError:
            logger.warning("Playwright not installed. To enable browser automation, install with: pip install playwright && playwright install chromium")
        except Exception as e:
            logger.error(f"Browser automation failed for {url}: {e}")
        
        return False
    
    async def download_article_pdf(self, article_title: str, article_url: str,
                                 download_path: Optional[str] = None) -> Optional[str]:
        """下载单篇文章的PDF"""
        
        # 设置下载路径
        if download_path:
            base_path = Path(download_path)
        else:
            base_path = Path.home() / "Downloads" / "ScholarDock_PDFs"
        
        # 创建文件名
        filename = self._sanitize_filename(article_title)
        filepath = base_path / filename
        
        # 如果文件已存在，跳过下载
        if filepath.exists():
            logger.info(f"File already exists, skipping: {filepath}")
            return str(filepath)
        
        # 获取可能的PDF链接
        pdf_urls = self._extract_pdf_urls(article_url)
        
        # 尝试下载每个可能的PDF链接
        for pdf_url in pdf_urls:
            if await self._download_single_pdf(pdf_url, str(filepath)):
                return str(filepath)
        
        # 如果常规方法都失败了，尝试浏览器自动化（实验性功能）
        if self._should_use_browser(article_url):
            logger.info(f"Attempting browser automation as fallback for: {article_title}")
            if await self._download_with_browser(article_url, str(filepath)):
                return str(filepath)
        
        logger.warning(f"Failed to download PDF for: {article_title}")
        return None
    
    async def download_multiple_pdfs(self, articles: List[dict],
                                   download_path: Optional[str] = None,
                                   max_concurrent: int = 3) -> dict:
        """批量下载多个PDF文件"""
        results = {
            'successful': [],
            'failed': [],
            'total': len(articles)
        }
        
        # 并发下载，但限制并发数量避免过载
        semaphore = asyncio.Semaphore(max_concurrent)  # 使用传入的并发数量
        
        async def download_with_semaphore(article):
            async with semaphore:
                filepath = await self.download_article_pdf(
                    article['title'], 
                    article.get('pdf_url', article['url']),  # 优先使用pdf_url
                    download_path
                )
                if filepath:
                    results['successful'].append({
                        'title': article['title'],
                        'filepath': filepath
                    })
                else:
                    results['failed'].append({
                        'title': article['title'],
                        'url': article.get('pdf_url', article['url'])
                    })
        
        # 创建所有下载任务
        tasks = [download_with_semaphore(article) for article in articles]
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
