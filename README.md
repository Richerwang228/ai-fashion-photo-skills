# AI Fashion Photo Skills

一套给 AI 编程助手（Claude Code、Codex 等）用的服装商品图 skills：从几张平铺或挂拍的衣服照片出发，生成 AI 模特图、生活场景图、细节特写，以及一整套手机端商品详情长图。

这套流程最初是给一家男装店做的，实际产出了几百张用在朋友圈和客户沟通里的模特图。

[English](#english)

## 包含什么

| Skill | 作用 | 作者 |
| --- | --- | --- |
| `generate-clothing-detail-set` | 总流程：确认卖法 → 整理衣服事实 → 规划 6–10 屏详情页 → 逐张出图 → 质检 → 拼成长图打包 | Richer Wang |
| `model-catalog` | 模特图流程：复用同一个 AI 模特、先出一张中性全身底片、审核通过后再做 10–20 张变体 | Richer Wang |
| `openai-compatible-image-provider` | 出图通道：异步提交、轮询任务、本地校验图片；付费请求不自动重试，中断后只续查原任务 | Richer Wang |
| `product-analysis-styling` | 分析衣服的品类、面料、颜色和细节 | ShopOS（Apache-2.0） |
| `product-tryon-visualization` | 把衣服穿到模特身上 | ShopOS（Apache-2.0） |
| `fashion-model-photography` | 棚拍、目录、型录方向 | ShopOS（Apache-2.0） |
| `garment-lifestyle-photography` | 街拍、生活场景 | ShopOS（Apache-2.0） |
| `macro-product-photography` | 面料、走线、五金特写 | ShopOS（Apache-2.0） |
| `product-background-generation` | 棚拍和场景背景 | ShopOS（Apache-2.0） |

## 几条核心规矩

- **衣服要对**：版型、颜色、口袋、扣子都以实拍为准，好看但不对的图不收。
- **先底片后变体**：一套衣服先出一张中性全身图，确认没问题再做创意变体。
- **花钱要确认**：每次付费出图前先确认张数；已经提交的任务只续查，不重复提交。
- **事实分级**：尺码、面料成分等没有证据的信息不写进详情页文案。

## 用法

1. 把 `.agents/` 整个复制到你的项目根目录。
2. 在项目根目录的 `.env` 里填出图接口的 key（不要提交到 git）：

   ```dotenv
   RIGHT_CODES_API_KEY=你的 key
   # 可选：换成其他兼容同一异步协议的接口
   RIGHT_CODES_BASE_URL=https://www.rightapi.ai/draw
   RIGHT_CODES_MODEL=gpt-image-2
   ```

3. 对 AI 助手说「用 generate-clothing-detail-set 给这件衣服做一套详情图」，并给它衣服照片所在的文件夹。

先跑免费的连通检查：

```bash
python3 .agents/scripts/right_codes_image_generator.py --check-auth --credential-name RIGHT_CODES_API_KEY
```

## 测试

```bash
cd .agents/scripts && python3 -m pytest -q
cd .agents/skills/generate-clothing-detail-set/scripts && python3 -m pytest -q tests
```

## 许可

Apache License 2.0。ShopOS 的六个 skill 原样保留作者信息，见 `NOTICE`。

---

## English

Skills for AI coding agents that turn a few flat-lay garment photos into AI model shots, lifestyle scenes, macro details and a full mobile product-detail page. Built for a real menswear shop. Copy `.agents/` into your project, put your image API key in `.env`, and ask your agent to run `generate-clothing-detail-set`. Licensed under Apache-2.0; six skills by ShopOS are redistributed unmodified (see `NOTICE`).
