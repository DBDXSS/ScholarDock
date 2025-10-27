from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from core.config import settings
from core.database import init_db, get_db
from models.article import SearchRequest, SearchResponse, SearchDB, ArticleDB, SearchSchema, ArticleSchema
from services.original_spider import OriginalScholarSpider
from services.export import ExportService
from services.pdf_downloader import PDFDownloader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}


@app.post("/api/search", response_model=SearchResponse)
async def search_articles(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Starting search for keyword: '{request.keyword}', num_results: {request.num_results}")
    
    search_record = SearchDB(
        keyword=request.keyword,
        start_year=request.start_year,
        end_year=request.end_year
    )
    db.add(search_record)
    await db.commit()
    await db.refresh(search_record)
    
    try:
        async with OriginalScholarSpider() as spider:
            articles = await spider.search(
                keyword=request.keyword,
                num_results=request.num_results,
                start_year=request.start_year,
                end_year=request.end_year,
                sort_by=request.sort_by
            )
        
        logger.info(f"📊 Spider returned {len(articles)} articles")
        
        # Return empty results if nothing found
        if not articles:
            logger.warning(f"No results found for '{request.keyword}' - may be blocked by Google Scholar")
        
        # Keep original Google Scholar order - sorting will be done on frontend
        logger.info(f"📈 Maintaining original Google Scholar order for {len(articles)} articles")
        
        # Store articles in database
        stored_count = 0
        for article in articles:
            try:
                article_db = ArticleDB(
                    title=article.title,
                    authors=article.authors,
                    venue=article.venue,
                    publisher=article.publisher,
                    year=article.year,
                    citations=article.citations,
                    citations_per_year=article.citations_per_year,
                    description=article.description,
                    url=article.url,
                    pdf_url=article.pdf_url,
                    search_id=search_record.id
                )
                db.add(article_db)
                stored_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to store article '{article.title[:50]}...': {e}")
        
        search_record.total_results = len(articles)
        await db.commit()
        
        logger.info(f"✅ Search completed: {len(articles)} articles found, {stored_count} stored in database")
        
        return SearchResponse(
            search_id=search_record.id,
            keyword=request.keyword,
            total_results=len(articles),
            articles=articles,
            message=f"Search completed successfully. Found {len(articles)} articles."
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Search failed for '{request.keyword}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/searches", response_model=List[SearchSchema])
async def get_search_history(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SearchDB)
        .options(selectinload(SearchDB.articles))
        .order_by(SearchDB.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    searches = result.scalars().all()
    return searches


@app.get("/api/search/{search_id}", response_model=SearchSchema)
async def get_search_details(
    search_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SearchDB)
        .options(selectinload(SearchDB.articles))
        .where(SearchDB.id == search_id)
    )
    search = result.scalar_one_or_none()
    
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    return search


@app.get("/api/export/{search_id}")
async def export_search_results(
    search_id: int,
    format: str = "csv",
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SearchDB)
        .options(selectinload(SearchDB.articles))
        .where(SearchDB.id == search_id)
    )
    search = result.scalar_one_or_none()
    
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    articles = [ArticleSchema.model_validate(article) for article in search.articles]
    
    if format == "csv":
        content = ExportService.to_csv(articles)
        media_type = "text/csv"
        filename = f"scholar_results_{search.keyword}.csv"
    elif format == "json":
        content = ExportService.to_json(articles)
        media_type = "application/json"
        filename = f"scholar_results_{search.keyword}.json"
    elif format == "excel":
        content = ExportService.to_excel(articles)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"scholar_results_{search.keyword}.xlsx"
    elif format == "bibtex":
        content = ExportService.to_bibtex(articles)
        media_type = "text/plain"
        filename = f"scholar_results_{search.keyword}.bib"
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.delete("/api/search/{search_id}")
async def delete_search(
    search_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SearchDB)
        .options(selectinload(SearchDB.articles))
        .where(SearchDB.id == search_id)
    )
    search = result.scalar_one_or_none()
    
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    await db.delete(search)
    await db.commit()
    
    return {"message": "Search deleted successfully"}

# PDF下载相关的请求和响应模型
from pydantic import BaseModel

class PDFDownloadRequest(BaseModel):
    articles: List[dict]  # 包含title和url的文章列表
    download_path: Optional[str] = None

class PDFDownloadResponse(BaseModel):
    success: bool
    message: str
    results: List[dict]


@app.post("/api/download-pdf", response_model=PDFDownloadResponse)
async def download_pdfs(
    request: PDFDownloadRequest,
    background_tasks: BackgroundTasks
):
    """批量下载PDF文件"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📥 Starting PDF download for {len(request.articles)} articles")
    
    try:
        async with PDFDownloader() as downloader:
            results = await downloader.download_multiple_pdfs(
                articles=request.articles,
                download_path=request.download_path,
                max_concurrent=3
            )
        
        success_count = len(results['successful'])
        total_count = results['total']
        logger.info(f"✅ PDF download completed: {success_count}/{total_count} successful")
        
        # 转换结果格式以匹配响应模型
        formatted_results = []
        for item in results['successful']:
            formatted_results.append({
                'success': True,
                'title': item['title'],
                'filepath': item['filepath']
            })
        for item in results['failed']:
            formatted_results.append({
                'success': False,
                'title': item['title'],
                'url': item['url']
            })
        
        return PDFDownloadResponse(
            success=True,
            message=f"Download completed: {success_count}/{total_count} files downloaded successfully",
            results=formatted_results
        )
        
    except Exception as e:
        logger.error(f"❌ PDF download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF download failed: {str(e)}")


@app.post("/api/download-single-pdf")
async def download_single_pdf(
    title: str,
    url: str,
    download_path: Optional[str] = None
):
    """下载单个PDF文件"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📥 Starting single PDF download for: {title}")
    
    try:
        async with PDFDownloader() as downloader:
            filepath = await downloader.download_article_pdf(
                article_title=title,
                article_url=url,
                download_path=download_path
            )
        
        if filepath:
            logger.info(f"✅ PDF downloaded successfully: {filepath}")
            return {
                "success": True,
                "message": "PDF downloaded successfully",
                "filepath": filepath
            }
        else:
            logger.warning(f"⚠️ PDF download failed for: {title}")
            return {
                "success": False,
                "message": "Failed to download PDF - file may not be available",
                "filepath": None
            }
        
    except Exception as e:
        logger.error(f"❌ Single PDF download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF download failed: {str(e)}")

