# web-scraper — 经验教训

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

---

_Last updated: 2026-02-26_
