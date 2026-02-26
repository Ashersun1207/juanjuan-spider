"""
站点适配器基类 + 默认通用适配器。

每个适配器定义：选择器、等待策略、登录需求、输出转换。
新增站点适配器只需继承 DefaultAdapter，覆盖需要的方法。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from spider.core.engine import FetchConfig
from spider.core.result import CrawlResult


@dataclass
class DefaultAdapter:
    """
    通用默认适配器。

    子类覆盖属性和方法即可定制特定站点的爬取行为。

    示例（知乎适配器）:
        @dataclass
        class ZhihuAdapter(DefaultAdapter):
            name: str = "zhihu"
            domains: list[str] = field(default_factory=lambda: ["zhihu.com"])
            needs_login: bool = True
            wait_for: str = ".RichContent"
            scroll: bool = True
    """

    name: str = "default"
    domains: list[str] = field(default_factory=list)
    needs_login: bool = False
    wait_for: str | None = None  # CSS 选择器，等待此元素出现
    css_selector: str | None = None  # 只提取匹配内容
    js_code: str | None = None  # 页面加载后执行的 JS
    scroll: bool = False  # 是否自动滚动
    extra_wait: float = 0  # 额外等待秒数

    def customize_config(self, config: FetchConfig) -> FetchConfig:
        """
        根据适配器配置修改 FetchConfig。

        子类可覆盖此方法做更复杂的配置调整。
        """
        if self.css_selector:
            config.selector = self.css_selector
        if self.js_code:
            config.js_code = self.js_code
        if self.scroll:
            config.scroll = True
        if self.extra_wait > 0:
            config.wait = max(config.wait, self.extra_wait)
        return config

    def transform(self, result: CrawlResult) -> CrawlResult:
        """
        对爬取结果做站点专用的清洗/转换。

        默认原样返回。子类覆盖此方法做定制处理。
        """
        return result
