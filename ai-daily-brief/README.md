# AI Daily Brief · 每日科技早报归档

每天 8:30 (Asia/Shanghai) 自动生成的科技早报存档目录。

## 目录结构

    ai-daily-brief/
    ├── README.md                   本文件
    ├── YYYY-MM-DD.md               当日图文早报(纯文本+链接,可直接转发)
    └── audio/
        └── YYYY-MM-DD.mp3          当日 TTS 早报语音(推微信时作为附件)

## 内容范围

- 主题:AI/算法(LLM/多模态/RLHF/Agent/AI Infra/HBM/算力/对齐/世界模型)
- 来源:国内外各 10 条,优先近 30 天内的报道(STRONG_KW 严格过滤)
- 语种:中文
- 形式:`### N. <标题>` 标题 + 来源 + 链接 + 2-3 句摘要

## 每日归档

| 日期 | 条数 | 链接 |
|------|------|------|
| 2026-06-21 | 国内 10 + 国外 10 | [查看](./2026-06-21.md) |
| 2026-06-20 | 国内 10 + 国外 10 | [查看](./2026-06-20.md) |

## 推送渠道

- 主渠道:Weixin 微信(`o9cq807Jx1dCpxkGpv4Z5mVkfab4@im.wechat`)
  - 走 iLink API(企业微信 iLink 通道)
- 失败降级:本地留档永远存在,微信推送失败不影响存档

## 常见问题

**Q: 微信没收到早报?**
A: 打开 ~/.hermes/logs/cron.log 找当天 8:30 的 job_id,看 deliver 状态;如果 rate limited,本目录已有完整存档

**Q: 想换主题/语种?**
A: 修改 cron job 的 prompt(用 `hermes cron edit <job_id>`)
