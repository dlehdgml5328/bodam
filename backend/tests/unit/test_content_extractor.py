"""Content Extractor 단위 테스트"""

import pytest
from bs4 import BeautifulSoup

from src.services.crawler.content_extractor import ContentExtractor


class TestContentExtractor:
    """콘텐츠 추출기 테스트 케이스"""

    @pytest.fixture
    def extractor(self):
        """ContentExtractor 인스턴스 생성"""
        return ContentExtractor()

    def test_extract_basic_structure(self, extractor):
        """기본 HTML 구조 추출 테스트"""
        html = """
        <html>
            <head><title>테스트 제목</title></head>
            <body>
                <h1>메인 제목</h1>
                <p>본문 내용</p>
            </body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert result["title"] == "테스트 제목"
        assert "메인 제목" in result["content"]
        assert "본문 내용" in result["content"]

    def test_extract_news_article(self, extractor):
        """뉴스 기사 추출 테스트"""
        html = """
        <html>
            <body>
                <article>
                    <h1 class="article-title">강남구 화재 발생</h1>
                    <div class="article-meta">
                        <span class="author">기자 홍길동</span>
                        <time datetime="2025-10-15">2025년 10월 15일</time>
                    </div>
                    <div class="article-body">
                        <p>오늘 오후 강남구에서 화재가 발생했습니다.</p>
                        <p>소방당국이 진화 작업을 진행중입니다.</p>
                    </div>
                </article>
            </body>
        </html>
        """
        
        result = extractor.extract_news_article(html)
        
        assert result["title"] == "강남구 화재 발생"
        assert result["author"] == "기자 홍길동"
        assert "화재가 발생했습니다" in result["content"]

    def test_extract_with_javascript_content(self, extractor):
        """JavaScript로 생성된 콘텐츠 추출 테스트"""
        html = """
        <html>
            <body>
                <div id="dynamic-content">
                    <p>동적으로 로드된 내용</p>
                </div>
            </body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert "동적으로 로드된 내용" in result["content"]

    def test_extract_removes_scripts_and_styles(self, extractor):
        """스크립트와 스타일 태그가 제거되는지 확인"""
        html = """
        <html>
            <head>
                <style>body { color: red; }</style>
            </head>
            <body>
                <p>실제 내용</p>
                <script>alert('test');</script>
            </body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert "실제 내용" in result["content"]
        assert "alert" not in result["content"]
        assert "color: red" not in result["content"]

    def test_extract_metadata(self, extractor):
        """메타데이터 추출 테스트"""
        html = """
        <html>
            <head>
                <meta property="og:title" content="OG 제목">
                <meta property="og:description" content="OG 설명">
                <meta name="keywords" content="뉴스,화재,긴급">
            </head>
            <body><p>내용</p></body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert result["metadata"]["og_title"] == "OG 제목"
        assert result["metadata"]["og_description"] == "OG 설명"
        assert "뉴스" in result["metadata"]["keywords"]

    def test_extract_links(self, extractor):
        """링크 추출 테스트"""
        html = """
        <html>
            <body>
                <a href="https://example.com/page1">링크 1</a>
                <a href="/relative/path">링크 2</a>
                <a href="#anchor">앵커</a>
            </body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert len(result["links"]) >= 2
        assert "https://example.com/page1" in result["links"]

    def test_extract_images(self, extractor):
        """이미지 URL 추출 테스트"""
        html = """
        <html>
            <body>
                <img src="https://example.com/image1.jpg" alt="이미지 1">
                <img src="/images/image2.png" alt="이미지 2">
            </body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert len(result["images"]) >= 1
        assert "https://example.com/image1.jpg" in result["images"]

    def test_extract_empty_html(self, extractor):
        """빈 HTML 처리 테스트"""
        html = "<html><body></body></html>"
        
        result = extractor.extract(html, url="https://example.com")
        
        assert result["content"] == ""
        assert result["title"] == ""

    def test_extract_malformed_html(self, extractor):
        """잘못된 HTML 처리 테스트"""
        html = "<html><body><p>닫히지 않은 태그</body></html>"
        
        # 예외 발생하지 않고 처리되어야 함
        result = extractor.extract(html, url="https://example.com")
        
        assert "닫히지 않은 태그" in result["content"]

    def test_extract_korean_text(self, extractor):
        """한글 텍스트 처리 테스트"""
        html = """
        <html>
            <body>
                <h1>한글 제목입니다</h1>
                <p>본문에는 한글과 숫자 123, 영문 ABC가 섞여있습니다.</p>
            </body>
        </html>
        """
        
        result = extractor.extract(html, url="https://example.com")
        
        assert "한글 제목입니다" in result["content"]
        assert "123" in result["content"]
        assert "ABC" in result["content"]

    def test_extract_publish_date(self, extractor):
        """발행일 추출 테스트"""
        html = """
        <html>
            <body>
                <article>
                    <time datetime="2025-10-15T10:30:00Z">2025년 10월 15일</time>
                    <p>기사 본문</p>
                </article>
            </body>
        </html>
        """
        
        result = extractor.extract_news_article(html)
        
        assert result["publish_date"] == "2025-10-15T10:30:00Z"

    def test_extract_with_custom_selectors(self, extractor):
        """커스텀 셀렉터를 사용한 추출 테스트"""
        html = """
        <html>
            <body>
                <div class="custom-content">
                    <h2>커스텀 제목</h2>
                    <div class="text">커스텀 본문</div>
                </div>
            </body>
        </html>
        """
        
        result = extractor.extract(
            html,
            url="https://example.com",
            selectors={"title": ".custom-content h2", "content": ".custom-content .text"}
        )
        
        assert "커스텀 제목" in result["title"]
        assert "커스텀 본문" in result["content"]
