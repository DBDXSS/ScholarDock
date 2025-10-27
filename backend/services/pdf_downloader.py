import aiohttp
import asyncio
import os
from pathlib import Path
from typing import List, Optional
import logging
from urllib.parse import urlparse, quote
import re

logger = logging.getLogger(__name__)

class PDFDownloader:
    """PDF下载服务"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        # 确保以.pdf结尾
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        return filename
    
    def _extract_pdf_urls(self, article_url: str) -> List[str]:
        """从文章URL提取可能的PDF链接"""
        pdf_urls = []
        
        if not article_url:
            return pdf_urls
        
        # 直接PDF链接
        if article_url.lower().endswith('.pdf'):
            pdf_urls.append(article_url)
            return pdf_urls
        
        # 常见的PDF获取策略
        base_patterns = [
            # arXiv
            lambda url: url.replace('arxiv.org/abs/', 'arxiv.org/pdf/') + '.pdf' if 'arxiv.org/abs/' in url else None,
            # ResearchGate
            lambda url: url + '.pdf' if 'researchgate.net' in url else None,
            # IEEE
            lambda url: url.replace('/document/', '/stamp/stamp.jsp?tp=&arnumber=') if 'ieeexplore.ieee.org' in url else None,
            # ACM
            lambda url: url + '?download=true' if 'dl.acm.org' in url else None,
        ]
        
        for pattern in base_patterns:
            try:
                pdf_url = pattern(article_url)
                if pdf_url:
                    pdf_urls.append(pdf_url)
            except:
                continue
        
        # 如果没有找到特定模式，尝试常见的PDF后缀
        if not pdf_urls:
            common_suffixes = ['.pdf', '/pdf', '/download', '/fulltext.pdf']
            for suffix in common_suffixes:
                pdf_urls.append(article_url + suffix)
        
        return pdf_urls
    
    async def _download_single_pdf(self, url: str, filepath: str) -> bool:
        """下载单个PDF文件"""
        try:
            logger.info(f"Attempting to download PDF from: {url}")
            
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
                    else:
                        logger.warning(f"Content type is not PDF: {content_type} for URL: {url}")
                else:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
        
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
            logger.info(f"PDF already exists: {filepath}")
            return str(filepath)
        
        # 获取可能的PDF URLs
        pdf_urls = self._extract_pdf_urls(article_url)
        
        # 尝试下载
        for url in pdf_urls:
            if await self._download_single_pdf(url, str(filepath)):
                return str(filepath)
        
        logger.warning(f"Failed to download PDF for article: {article_title}")
        return None
    
    async def download_multiple_pdfs(self, articles: List[dict], 
                                   download_path: Optional[str] = None,
                                   max_concurrent: int = 3) -> List[dict]:
        """批量下载PDF文件"""
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(article):
            async with semaphore:
                filepath = await self.download_article_pdf(
                    article['title'], 
                    article['url'], 
                    download_path
                )
                return {
                    'title': article['title'],
                    'url': article['url'],
                    'filepath': filepath,
                    'success': filepath is not None
                }
        
        # 创建下载任务
        tasks = [download_with_semaphore(article) for article in articles]
        
        # 执行下载
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Download task failed: {result}")
                final_results.append({
                    'title': 'Unknown',
                    'url': 'Unknown',
                    'filepath': None,
                    'success': False,
                    'error': str(result)
                })
            else:
                final_results.append(result)
        
        return final_results