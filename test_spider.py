#!/usr/bin/env python3
"""
Test script to verify the improved spider performance
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append('backend')

from services.original_spider import OriginalScholarSpider

async def test_spider():
    """Test the spider with a simple query"""
    print("🧪 Testing improved spider...")
    
    async with OriginalScholarSpider() as spider:
        # Test with the same query as shown in the comparison
        articles = await spider.search(
            keyword="point cloud",
            num_results=20,  # Start with smaller number for testing
            start_year=None,
            end_year=None
        )
    
    print(f"\n📊 Test Results:")
    print(f"   - Total articles found: {len(articles)}")
    print(f"   - Articles with valid titles: {sum(1 for a in articles if a.title and a.title != 'Unknown Title')}")
    print(f"   - Articles with citations: {sum(1 for a in articles if a.citations > 0)}")
    print(f"   - Articles with years: {sum(1 for a in articles if a.year)}")
    
    print(f"\n📝 Sample articles:")
    for i, article in enumerate(articles[:5]):
        print(f"   {i+1}. {article.title[:80]}...")
        print(f"      Citations: {article.citations}, Year: {article.year or 'N/A'}")
        print(f"      Authors: {article.authors[:50]}..." if article.authors else "      Authors: N/A")
        print()

if __name__ == "__main__":
    asyncio.run(test_spider())