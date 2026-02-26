# juanjuan-spider — 经验教训

---

## L1: MQL5 SSL 被封不是工具问题（2026-02-25）

**现象**：MQL5 抓取 SSL 错误
**原因**：代理出口 IP 被 MQL5 封了，换代理或直连可解
**教训**：抓取失败先排查网络层（代理/IP/DNS），再查工具

## L2: networkidle 不可靠（2026-02-25）

**现象**：部分站点 networkidle 超时
**原因**：长轮询、WebSocket、analytics 持续请求导致永远不 idle
**教训**：networkidle 作为首选但必须有 domcontentloaded 降级兜底

## L3: clean_markdown 启发式有误判（2026-02-25）

**现象**：过滤 CSS/JS 残留时偶尔误删正文内容
**原因**：关键词匹配太宽泛（如 `var ` 可能出现在正文）
**教训**：启发式规则要持续调优，遇到新站点验证输出质量

## L4: GitHub 不是静态页（2026-02-26）

**现象**：HTTP 引擎抓 GitHub 输出 69K 字符全是 JSON/CSS 垃圾
**原因**：GitHub 是 SPA，markdownify 拿到的是未渲染的模板
**教训**：SPA 站点必须走浏览器引擎，STATIC_SAFE 列表要保守

## L5: CSS 选择器适配器不能太激进（2026-02-26）

**现象**：CNBC 适配器加了 `css_selector` 后返回 0 字符
**原因**：选择器在 Crawl4AI 层面直接过滤了所有内容（页面结构和预期不符）
**教训**：不用 CSS 选择器强匹配，改用 transform() 后处理去噪更安全

## L6: 去噪应该分两层（2026-02-26）

**现象**：每个站点都有大量导航噪音
**方案**：引擎级（excluded_tags/selector 通用规则）+ 适配器（站点专用 transform）
**效果**：BBC -56%、CNBC -53%
**教训**：通用规则先干掉大部分噪音，适配器只处理站点特异的垃圾

## L7: adapter 不应覆盖 fit_markdown（2026-02-26）

**现象**：所有 adapter 把 fit_markdown 设成清洗后的全文，Crawl4AI Readability 结果被丢弃
**原因**：v0.4 写 adapter 时没想清楚 fit_markdown 的语义
**教训**：fit_markdown = 正文提取结果（引擎或 Extractor 产生），adapter 只负责清洗 raw markdown

## L8: 用成熟提取库替代手写 regex（2026-02-26）

**现象**：24 个域名写了 adapter，但都是 regex 删几行，信噪比仍然低
**方案**：集成 trafilatura（F-Score 0.914），作为通用提取层
**效果**：BBC 文章页 raw 3.6K → fit 2.8K 纯正文；PG Essay 67K 近乎全保留
**教训**：正文提取是已解决问题，不要自己造轮子。regex adapter 适合做精调，不适合做主力提取

---

_Last updated: 2026-02-26_
