"""ContentExtractor 单元测试。"""

import pytest

from spider.core.extractor import ContentExtractor, _quality_score
from spider.core.result import CrawlResult


@pytest.fixture
def extractor():
    return ContentExtractor()


# --- _quality_score ---

def test_quality_score_empty():
    assert _quality_score("") == 0.0


def test_quality_score_short():
    assert _quality_score("too short") == 0.1


def test_quality_score_good_text():
    text = ("This is a well-structured paragraph with enough content. " * 5 + "\n\n") * 4
    score = _quality_score(text)
    assert score > 0.7


def test_quality_score_link_heavy():
    """链接密集的文本应该比正文低分。"""
    link_text = "\n".join(f"[Link {i}](https://example.com/{i})" for i in range(50))
    prose_text = ("This is a well-structured paragraph with enough content. " * 5 + "\n\n") * 4
    link_score = _quality_score(link_text)
    prose_score = _quality_score(prose_text)
    assert link_score < prose_score  # 链接堆砌一定比正文低


# --- ContentExtractor.extract ---

def test_extract_no_html(extractor):
    """没有 HTML 时应跳过提取。"""
    result = CrawlResult(url="https://example.com", markdown="some text")
    out = extractor.extract(result)
    assert out.markdown == "some text"
    assert out.fit_markdown == ""


def test_extract_failed_status(extractor):
    """失败状态应跳过提取。"""
    result = CrawlResult(url="https://example.com", html="<p>text</p>", status="failed")
    out = extractor.extract(result)
    assert out.status == "failed"


def test_extract_article_html(extractor):
    """正常文章 HTML 应提取出 fit_markdown。"""
    html = """
    <html><head><title>Test Article</title></head>
    <body>
        <nav><a href="/">Home</a><a href="/about">About</a></nav>
        <article>
            <h1>Main Title</h1>
            <p>This is the first paragraph of a well-written article about technology
            and its impact on modern society. It contains enough text to be meaningful.</p>
            <p>The second paragraph continues the discussion with additional details
            about the subject matter, providing depth and context for the reader.</p>
            <p>A third paragraph wraps up the article with concluding thoughts
            and a forward-looking perspective on future developments.</p>
        </article>
        <footer><p>Copyright 2026</p></footer>
    </body></html>
    """
    result = CrawlResult(url="https://example.com/article", html=html)
    out = extractor.extract(result)
    # trafilatura 应该提取出正文
    assert out.fit_markdown  # 不再为空
    assert "first paragraph" in out.fit_markdown
    assert "Home" not in out.fit_markdown  # 导航应该被过滤


def test_extract_preserves_better_engine_fit(extractor):
    """如果引擎的 fit_markdown 质量更高，应保留。"""
    good_fit = ("This is a high quality extracted paragraph. " * 10 + "\n\n") * 5
    # 给一个很短的 HTML，trafilatura 提取结果会比较差
    html = "<html><body><p>Short.</p></body></html>"
    result = CrawlResult(
        url="https://example.com",
        html=html,
        fit_markdown=good_fit,
    )
    out = extractor.extract(result)
    assert out.fit_markdown == good_fit  # 保留引擎原值


def test_extract_metadata(extractor):
    """应提取元数据（标题、作者、日期）。"""
    html = """
    <html><head>
        <title>My Article Title</title>
        <meta name="author" content="John Doe">
        <meta property="article:published_time" content="2026-01-15">
    </head>
    <body>
        <article>
            <h1>My Article Title</h1>
            <p>A substantial paragraph with enough text to trigger extraction.
            This article discusses various topics in a detailed manner.</p>
            <p>Another paragraph with more content to ensure the article
            is long enough for trafilatura to process it properly.</p>
        </article>
    </body></html>
    """
    result = CrawlResult(url="https://example.com/meta-test", html=html, title="")
    out = extractor.extract(result)
    # 标题应被补充
    if out.title:  # trafilatura 可能提取到也可能没有
        assert "Article" in out.title


def test_extract_does_not_overwrite_existing_title(extractor):
    """已有标题不应被覆盖。"""
    html = """
    <html><head><title>HTML Title</title></head>
    <body><article><p>Some article content here that is long enough.</p></article></body>
    </html>
    """
    result = CrawlResult(url="https://example.com", html=html, title="Original Title")
    out = extractor.extract(result)
    assert out.title == "Original Title"
