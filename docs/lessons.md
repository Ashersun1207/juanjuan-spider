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

---

_Last updated: 2026-02-26_
