"""适配器测试。"""

from spider.adapters.default import DefaultAdapter
from spider.core.engine import FetchConfig
from spider.core.result import CrawlResult


def test_default_adapter_passthrough():
    """默认适配器不修改结果。"""
    adapter = DefaultAdapter()
    result = CrawlResult(url="https://example.com", markdown="# Test")
    transformed = adapter.transform(result)
    assert transformed.markdown == "# Test"


def test_adapter_customizes_config():
    """适配器可以修改 FetchConfig。"""
    adapter = DefaultAdapter(
        name="test",
        css_selector=".content",
        scroll=True,
        extra_wait=2.0,
    )
    fc = FetchConfig()
    fc = adapter.customize_config(fc)

    assert fc.selector == ".content"
    assert fc.scroll is True
    assert fc.wait == 2.0


def test_adapter_keeps_existing_wait():
    """适配器不会缩短已有的 wait。"""
    adapter = DefaultAdapter(extra_wait=1.0)
    fc = FetchConfig(wait=3.0)
    fc = adapter.customize_config(fc)
    assert fc.wait == 3.0  # 保持原来更长的 wait


def test_custom_adapter():
    """自定义适配器继承。"""
    class ZhihuAdapter(DefaultAdapter):
        name: str = "zhihu"

        def transform(self, result: CrawlResult) -> CrawlResult:
            # 知乎专用清洗：去掉 "登录" 相关内容
            cleaned = result.markdown.replace("登录查看更多", "")
            return result.model_copy(update={"markdown": cleaned})

    adapter = ZhihuAdapter()
    result = CrawlResult(
        url="https://zhihu.com/q/1",
        markdown="正文内容\n登录查看更多\n更多回答",
    )
    transformed = adapter.transform(result)
    assert "登录查看更多" not in transformed.markdown
    assert "正文内容" in transformed.markdown
