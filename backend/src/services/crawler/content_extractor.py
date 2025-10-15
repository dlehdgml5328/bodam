"""Content extractor

Extracts structured data from rendered HTML.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Content extractor for crawled pages

    Extracts structured data from HTML based on page type.
    """

    def extract(self, html: str, url: str, page_type: str = "news") -> Dict[str, Any]:
        """
        Extract structured data from HTML

        Args:
            html: Rendered HTML content
            url: Source URL
            page_type: Type of page (news, emergency_alert, etc.)

        Returns:
            Extracted structured data
        """
        if page_type == "news":
            return self.extract_news_article(html, url)
        else:
            return self.extract_generic(html, url)

    def extract_news_article(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract news article data

        Args:
            html: HTML content
            url: Source URL

        Returns:
            dict with title, content, publish_date, author, etc.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title (try multiple selectors)
        title = self._extract_title(soup)

        # Extract content
        content = self._extract_content(soup)

        # Extract publish date
        publish_date = self._extract_publish_date(soup)

        # Extract author
        author = self._extract_author(soup)

        return {
            "title": title,
            "content": content,
            "publish_date": publish_date,
            "author": author,
            "url": url,
            "extracted_at": datetime.utcnow().isoformat(),
        }

    def extract_generic(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract generic data from any page

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Basic page metadata
        """
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string if soup.title else None
        meta_description = self._extract_meta_tag(soup, "description")

        return {
            "title": title,
            "meta_description": meta_description,
            "url": url,
            "extracted_at": datetime.utcnow().isoformat(),
        }

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        # Try common title selectors
        selectors = [
            "h1",
            ".article-title",
            "#article-title",
            "[itemprop='headline']",
            "article h1",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content"""
        selectors = [
            "article",
            ".article-content",
            ".post-content",
            "[itemprop='articleBody']",
            "#article-body",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date"""
        # Try meta tags
        date_meta = self._extract_meta_tag(soup, "article:published_time")
        if date_meta:
            return date_meta

        # Try time element
        time_element = soup.select_one("time")
        if time_element and time_element.get("datetime"):
            return time_element.get("datetime")

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author name"""
        # Try meta tag
        author_meta = self._extract_meta_tag(soup, "author")
        if author_meta:
            return author_meta

        # Try rel=author link
        author_link = soup.select_one("[rel='author']")
        if author_link:
            return author_link.get_text(strip=True)

        return None

    def _extract_meta_tag(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Extract meta tag content"""
        # Try name attribute
        meta = soup.find("meta", attrs={"name": name})
        if meta:
            return meta.get("content")

        # Try property attribute (for OpenGraph)
        meta = soup.find("meta", attrs={"property": name})
        if meta:
            return meta.get("content")

        return None
