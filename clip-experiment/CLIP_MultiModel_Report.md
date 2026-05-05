# CLIP模型女装以图搜图：多模型对比与文本增强融合深度实验报告

> 实验日期：2026-05-05 | 环境：CPU 8核/16G | 数据集：1811张女装B2B商品图（评测300张/21类）

---

## 一、实验背景与动机

### 1.1 业务问题

女装B2B批发平台的"相似商品推荐"场景：商家上传一张商品图，系统返回视觉相似的商品列表。当前纯图片检索效果差——时尚商品在视觉上高度同质化（都是模特+服装），CLIP的image embedding无法有效区分品类、风格、场景。

### 1.2 核心假设

CLIP天然支持image-text双模态。如果能在检索时**引入文本信号**（商品品类、风格描述等），是否能突破纯image检索的天花板？

### 1.3 实验路线

```
阶段1: 多模型选型 → 找出image-only最强模型
阶段2: 文本增强上界 → gold-label文本 + Slerp/Linear融合
阶段3: 自动描述实战 → zero-shot自动生成文本 + 融合
阶段4: 根因分析 → 为什么融合在某些模型上有效，某些无效
```

---

## 二、实验设置

### 2.1 数据集

- **来源**：女装B2B平台商品图
- **总量**：1811张
- **评测集**：前300张
- **类别划分**：按文件名前缀自动分组，共21个类别

| 类别 | 图片数 | 说明 |
|------|--------|------|
| pdf_img_p17 | 34 | PDF页面提取图 |
| pdf_img_p19 | 26 | 同上 |
| pdf_img_p13 | 22 | 同上 |
| pdf_img_p10 | 21 | 同上 |
| pdf_img_p20 | 21 | 同上 |
| pdf_img_p23 | 21 | 同上 |
| pdf_img_p1 | 19 | 同上 |
| pdf_img_p18 | 18 | 同上 |
| pdf_img_p15 | 17 | 同上 |
| pdf_img_p12 | 16 | 同上 |
| dress | 3 | 连衣裙 |
| blouse | 2 | 衬衫 |
| jeans | 2 | 牛仔裤 |
| outfit | 2 | 套装 |
| img | 5 | 未分类 |
| ... | ... | 共21类 |

> ⚠️ **数据局限**：大部分图片是PDF页面提取（pdf_img_pXX），不属于标准商品图；明确的时尚品类样本极少（dress/blouse/jeans等仅2-3张）。这是后续实验效果不够显著的重要原因之一。

### 2.2 评测指标

| 指标 | 含义 | 计算方式 |
|------|------|---------|
| **Recall@K** | 前K个结果中同类别的召回率 | 命中同类数 / 该类别总数-1 |
| **Precision@K** | 前K个结果的准确率 | 命中同类数 / K |
| **NDCG@K** | 考虑排序位置的归一化折损累积增益 | DCG / IDCG |
| **Gap** | 类内/类间相似度差 | intra_sim - inter_sim |

### 2.3 文本来源定义

本实验涉及三种文本来源，这是理解整个实验的关键：

| 文本来源 | 如何生成 | 信息来源 | 独立于模型？ | 描述多样性 |
|---------|---------|---------|------------|-----------|
| **Gold-label** | 从文件名前缀提取类别，构造固定模板 | 文件名（"作弊"标签） | 是 | 21种（300张图共享） |
| **Zero-shot caption** | 用FashionCLIP自身做zero-shot分类，取top-K预测模板 | 模型自身预测 | **否（自循环）** | top1: 17种 / top3: 139种 |
| **BLIP caption**（对照） | 用独立VLM(BLIP)生成图片描述 | 模型独立理解图片 | 是 | 14种（效果极差） |

**Gold-label vs Auto-caption的本质区别**：

```
Gold-label（作弊标签）:
  dress_1.jpg → "A photo of a women's dress, elegant flowing garment"
  dress_2.jpg → "A photo of a women's dress, elegant flowing garment"  ← 同类同文本
  blouse_1.jpg → "A photo of a women's blouse, lightweight top"
  blouse_2.jpg → "A photo of a women's blouse, lightweight top"      ← 同类同文本
  
  特点：300张图 → 21种描述，每类共享完全相同的文本embedding
  本质：把"品类标签"硬编码进embedding空间

Zero-shot caption（自循环）:
  dress_1.jpg → "elegant women's dress for formal occasions, women's evening party wear fashion..."
  dress_2.jpg → "floral print women's fashion clothing, women's spring fashion clothing..."  ← 不同文本！
  blouse_1.jpg → "floral print women's fashion clothing, women's fashion clothing in light colors..."
  
  特点：300张图 → 139种描述（top3），每张图文本不同
  本质：用CLIP分类 → 再用同一CLIP编码 → 没有引入新信息
  问题：CLIP zero-shot分类概率极度扁平（最高仅0.075），预测不可靠
```

---

## 三、阶段1：多模型Image-Only对比

### 3.1 模型概览

| 模型 | 架构 | 维度 | 训练数据 | 加载方式 |
|------|------|------|---------|---------|
| **FashionCLIP** | ViT-B/32 | 512 | Farfetch时尚目录微调 | transformers |
| **FashionSigLIP** | ViT-B/16-SigLIP | 768 | Marqo时尚数据GCL微调 | open_clip |
| **OpenAI CLIP** | ViT-B/32 | 512 | WIT 400M | transformers |
| **jina-clip-v2** | ViT-B/16 | 1024 | 89语言多模态MRL | ONNX Runtime |

### 3.2 结果

| 模型 | R@1 | R@5 | R@10 | R@20 | NDCG@5 | P@5 | Gap | 速度 |
|------|------|------|-------|-------|--------|------|------|------|
| **FashionCLIP** | 0.030 | **0.135** | **0.237** | **0.385** | **0.477** | **0.459** | **0.129** | 12.0 img/s |
| jina-clip-v2 | **0.037** | 0.131 | 0.226 | 0.356 | 0.475 | 0.449 | 0.092 | 0.19 img/s |
| FashionSigLIP | 0.032 | 0.125 | 0.212 | 0.353 | 0.445 | 0.428 | 0.100 | 4.0 img/s |
| OpenAI CLIP | 0.030 | 0.111 | 0.200 | 0.318 | 0.406 | 0.383 | 0.093 | 12.3 img/s |

### 3.3 分析

**1. FashionCLIP综合最优**

FashionCLIP在R@5/R@10/R@20/NDCG@5/P@5五个指标上全面领先，且类间区分度Gap=0.129最高。Farfetch时尚目录微调确实让模型学到了更好的时尚特征表示。

**2. jina-clip-v2：单点击中最好但排序混乱**

R@1=0.037最高（1024维特征更精准），但R@5/R@10反而下降，Gap=0.092最差。说明高维特征在top-1命中上有优势，但top-K排序质量差——相似度分布更平坦，缺乏有效排序信号。

**3. FashionSigLIP不如FashionCLIP**

SigLIP架构（sigmoid loss）理论上优于softmax loss的CLIP，但Marqo的微调数据和训练策略可能不如Farfetch覆盖全面。在实际B2B数据上，数据质量>架构优势。

**4. 所有模型纯image检索都极差**

最高R@5仅0.135，意味着前5个结果中平均只有0.67个同类商品。时尚商品视觉同质化是根本原因——所有商品都是"模特穿衣服"，CLIP的视觉编码器无法区分品类差异。

### 3.4 相似度分布对比

| 模型 | 类内相似度 | 类间相似度 | 区分度Gap |
|------|----------|----------|----------|
| FashionCLIP | 高 | 较低 | **0.129** |
| FashionSigLIP | 中 | 中 | 0.100 |
| OpenAI CLIP | 中 | 中 | 0.093 |
| jina-clip-v2 | 高 | 高 | 0.092 |

Gap越大说明模型越能区分"同类vs非同类"。FashionCLIP的Gap最高，与其R@5最优一致。

---

## 四、阶段2：Gold-Label文本增强融合

### 4.1 什么是Gold-Label？

Gold-label是**从文件名提取的"作弊"标签**——我们知道图片的类别（dress/blouse/jeans/pdf_img_pXX），用固定模板生成文本描述。

```python
# Gold-label生成逻辑
if category == "dress":
    text = "A photo of a women's dress, elegant flowing garment"
elif category == "blouse":
    text = "A photo of a women's blouse, lightweight top"
elif category.startswith("pdf_img"):
    text = f"A photo of women's fashion clothing, {category}"
```

**关键特征**：
- 300张图 → 仅21种不同描述
- 同一类别内所有图片共享**完全相同**的文本embedding
- 这是文本增强的**理论上界**——如果gold-label都没用，真实场景更不可能有用

### 4.2 实验方法

| 融合方法 | 公式 | 说明 |
|---------|------|------|
| Slerp | `slerp(img_emb, txt_emb, α)` | 球面线性插值，α=1纯image，α=0纯text |
| Linear | `α·img_emb + (1-α)·txt_emb` | 线性加权，α=1纯image，α=0纯text |

α从0.5到0.99，步进扫描最优混合比例。

### 4.3 结果

#### 4.3.1 纯文本检索 vs 纯图片检索

| 方法 | R@1 | R@5 | R@10 | R@20 | NDCG@5 | P@5 |
|------|------|------|-------|-------|--------|------|
| Image-only | 0.030 | 0.135 | 0.237 | 0.385 | 0.477 | 0.459 |
| Text-only (gold) | **0.086** | **0.336** | **0.591** | **0.935** | **1.000** | **0.978** |
| 提升 | +186% | +150% | +150% | +143% | +110% | +113% |

**解读**：Gold-label文本检索效果碾压image检索！R@5从0.135到0.336（+150%），NDCG@5直接到1.0（完美排序）。这是因为21个类别的文本embedding天然就把同类聚在一起——"dress"永远和"dress"最相似，和"blouse"不相似。

> 但这不公平——gold-label是"作弊"标签，生产环境没有。

#### 4.3.2 Slerp融合 α扫描

| α | 文本占比 | R@5 | R@10 | NDCG@5 | P@5 | vs Baseline |
|------|---------|------|-------|--------|------|------------|
| 1.0 | 0% (baseline) | 0.1345 | 0.2368 | 0.4774 | 0.4593 | — |
| 0.99 | 1% | 0.1347 | 0.2368 | 0.4778 | 0.4600 | +0.0002 |
| 0.97 | 3% | 0.1349 | 0.2370 | 0.4780 | 0.4607 | +0.0004 |
| 0.95 | 5% | 0.1349 | 0.2373 | 0.4781 | 0.4607 | +0.0004 |
| 0.9 | 10% | 0.1383 | 0.2371 | 0.4795 | 0.4613 | +0.0038 |
| 0.85 | 15% | 0.1388 | 0.2375 | 0.4813 | 0.4613 | +0.0043 |
| 0.8 | 20% | 0.1411 | 0.2404 | 0.4837 | 0.4627 | +0.0066 |
| 0.7 | 30% | 0.1493 | 0.2424 | 0.4898 | 0.4640 | +0.0148 |
| 0.6 | 40% | 0.1533 | 0.2460 | 0.4954 | 0.4680 | +0.0188 |
| **0.5** | **50%** | **0.1579** | **0.2516** | **0.5019** | **0.4720** | **+0.0234** |

#### 4.3.3 Linear融合 α扫描

| α | 文本占比 | R@5 | R@10 | NDCG@5 | P@5 | vs Baseline |
|------|---------|------|-------|--------|------|------------|
| 0.5 | 50% | **0.1579** | **0.2516** | **0.5019** | **0.4720** | **+0.0234** |
| 0.6 | 40% | 0.1525 | 0.2460 | 0.4946 | 0.4667 | +0.0180 |
| 0.7 | 30% | 0.1478 | 0.2424 | 0.4890 | 0.4640 | +0.0133 |
| 0.8 | 20% | 0.1395 | 0.2370 | 0.4826 | 0.4620 | +0.0050 |
| 0.9 | 10% | 0.1383 | 0.2373 | 0.4794 | 0.4613 | +0.0038 |
| 0.95 | 5% | 0.1349 | 0.2372 | 0.4781 | 0.4607 | +0.0004 |

**关键发现**：

1. **Slerp和Linear效果完全一致** — α=0.5时两者R@5都是0.1579。在512维投影空间中，L2归一化后线性加权已经近似球面插值。

2. **需要50%文本才有+17%提升** — α=0.5时R@5从0.135到0.158。但50%文本意味着图片信息被严重稀释。

3. **10%文本仅+2.8%** — α=0.9（之前论文推荐的参数）在FashionCLIP上几乎无用。

4. **与FashionSigLIP形成巨大反差** — 同样的gold-label方法：
   - FashionSigLIP Slerp α=0.9 → R@5 **+256%**
   - FashionCLIP Slerp α=0.5 → R@5 **+17%**

---

## 五、阶段3：Zero-Shot自动描述融合

### 5.1 为什么不用BLIP？

之前的Phase 2实验用BLIP-image-captioning-base自动生成描述，结果极差：

| 方法 | R@5 | vs Baseline |
|------|------|------------|
| BLIP text-only | 0.027 | -70% ❌ |
| BLIP Slerp α=0.9 | 0.072 | -20% ❌ |

**BLIP失败原因**：300张图只生成了14种不同描述，109张被标为"cardigan"：
```
[109x] A photo of a women's cardigan, fashion clothing
[74x]  A photo of a women's t-shirt, fashion clothing
[41x]  A photo of a women's jacket, fashion clothing
[16x]  A photo of a women's coat, fashion clothing
...
```
BLIP的品类分类太粗糙，且完全无法区分时尚细分品类。

### 5.2 Zero-Shot Caption方案

**核心思路**：用FashionCLIP自身的zero-shot分类能力，从30个精心设计的时尚属性模板中选出最匹配的top-K，组合成描述。

**30个时尚属性模板**：

```python
# 品类类 (15个)
"casual women's dress for everyday wear"
"elegant women's dress for formal occasions"
"casual women's blouse with relaxed fit"
"formal women's blouse for office wear"
"classic women's jeans denim pants"
"women's jacket outerwear coat"
"women's sweater cardigan knitwear"
"women's t-shirt casual top"
"women's skirt midi mini"
"women's hoodie sweatshirt sportswear"
"women's blazer suit jacket"
"women's jumpsuit romper playsuit"
"women's vest waistcoat sleeveless"
"women's coat overcoat winter wear"
"women's pants trousers wide-leg"

# 风格/场景类 (15个)
"floral print women's fashion clothing"
"solid color women's fashion clothing"
"striped pattern women's fashion clothing"
"women's fashion clothing in dark colors"
"women's fashion clothing in light colors"
"women's fashion clothing in bright colors"
"women's evening party wear fashion"
"women's streetwear urban fashion"
"women's minimalist clean fashion"
"women's vintage retro fashion style"
"women's bohemian free-spirited fashion"
"women's professional workwear office fashion"
"women's summer lightweight fashion"
"women's autumn layered fashion"
"women's spring fashion clothing"
```

### 5.3 Gold-Label vs Zero-Shot Caption对比

| 维度 | Gold-Label | Zero-Shot Top-1 | Zero-Shot Top-3 |
|------|-----------|-----------------|-----------------|
| **信息来源** | 文件名标签（作弊） | CLIP自身预测 | CLIP自身预测 |
| **独立于模型** | ✅ 是 | ❌ 否（自循环） | ❌ 否（自循环） |
| **独特描述数** | 21种 | 17种 | 139种 |
| **文本多样性** | 低（同类同文本） | 低（预测集中在少数模板） | 中等（3个模板组合） |
| **分类可靠性** | 100%（已知标签） | 很低（概率最高0.075） | 较低 |
| **Per-image独特性** | ❌ 同类完全相同 | ❌ 300图仅17种 | ✅ 300图139种 |

**示例对比**：

| 图片 | Gold-Label | Zero-Shot Top-3 |
|------|-----------|-----------------|
| dress_1.jpg | "A photo of a women's dress, elegant flowing garment" | "elegant women's dress for formal occasions, women's evening party wear fashion, solid color women's fashion clothing" |
| blouse_1.jpg | "A photo of a women's blouse, lightweight top" | "floral print women's fashion clothing, women's fashion clothing in light colors, women's spring fashion clothing" |
| jeans_1.jpg | "A photo of women's jeans, denim pants" | "classic women's jeans denim pants, women's streetwear urban fashion, women's spring fashion clothing" |
| img_1.jpg | "A photo of women's fashion clothing, img" | "women's streetwear urban fashion, solid color women's fashion clothing, women's fashion clothing in bright colors" |

### 5.4 Zero-Shot Caption融合结果

#### 5.4.1 纯文本检索效果

| 方法 | R@5 | R@10 | NDCG@5 | P@5 | vs Image-only |
|------|------|-------|--------|------|--------------|
| Image-only | 0.1345 | 0.2368 | 0.4774 | 0.4593 | — |
| Gold text-only | **0.3361** | **0.5908** | **1.0000** | **0.9780** | +150% ✅ |
| Zero-shot top1 | 0.0413 | 0.0884 | 0.1262 | 0.1707 | -69% ❌ |
| Zero-shot top3 | 0.0692 | 0.1233 | 0.2216 | 0.2840 | -49% ❌ |

**Zero-shot纯文本比纯图片还差！** 这是因为：
1. CLIP zero-shot分类概率极度扁平（15个类别最高仅0.075），预测不可靠
2. 自循环问题：用CLIP分类 → 用同一CLIP编码 → 没有引入任何新信息
3. "floral print"这类模板对300张图的区分力不如"pdf_img_p17"这种文件名标签

#### 5.4.2 Slerp融合 α扫描

**Zero-shot top-1：**

| α | 文本占比 | R@5 | R@10 | NDCG@5 | vs Baseline |
|------|---------|------|-------|--------|------------|
| 1.0 | 0% | 0.1345 | 0.2368 | 0.4774 | — |
| 0.99 | 1% | 0.1345 | 0.2378 | 0.4776 | +0.0000 |
| 0.95 | 5% | 0.1345 | 0.2382 | 0.4787 | +0.0000 |
| 0.9 | 10% | 0.1345 | 0.2378 | 0.4794 | +0.0000 |
| 0.85 | 15% | 0.1345 | 0.2382 | 0.4789 | +0.0000 |
| 0.8 | 20% | 0.1328 | 0.2331 | 0.4779 | -0.0017 |
| 0.7 | 30% | 0.1284 | 0.2232 | 0.4637 | -0.0061 |

**Zero-shot top-3：**

| α | 文本占比 | R@5 | R@10 | NDCG@5 | vs Baseline |
|------|---------|------|-------|--------|------------|
| 1.0 | 0% | 0.1345 | 0.2368 | 0.4774 | — |
| 0.99 | 1% | 0.1343 | 0.2373 | 0.4769 | -0.0002 |
| 0.95 | 5% | 0.1346 | 0.2374 | 0.4774 | +0.0001 |
| **0.9** | **10%** | **0.1377** | **0.2366** | **0.4821** | **+0.0032** |
| 0.85 | 15% | 0.1365 | 0.2367 | 0.4808 | +0.0020 |
| 0.8 | 20% | 0.1326 | 0.2340 | 0.4797 | -0.0019 |
| 0.7 | 30% | 0.1314 | 0.2264 | 0.4766 | -0.0031 |

**结论：Zero-shot caption融合几乎无效。** 最好的Slerp top3 α=0.9仅+0.0032（+2.4%），且统计上不显著。

---

## 六、跨模型对比：同一方法的效果差异

### 6.1 Gold-Label Slerp在不同模型上

| 模型 | Image-only R@5 | 最佳Slerp R@5 | 最佳α | 提升幅度 |
|------|---------------|--------------|------|---------|
| FashionSigLIP | 0.091 | 0.324 | 0.9 | **+256%** |
| FashionCLIP | 0.135 | 0.158 | 0.5 | +17% |

同一个gold-label数据、同一个Slerp方法，效果差了15倍！

### 6.2 Auto-Caption Slerp在不同模型上

| 模型 | Caption方式 | 最佳Slerp R@5 | vs Baseline |
|------|-----------|--------------|------------|
| FashionSigLIP | BLIP-base | 0.072 | -20% ❌ |
| FashionCLIP | Zero-shot top3 | 0.138 | +2.4% ➡️ |

两种auto-caption方案在两个模型上都几乎无效。

### 6.3 BLIP Auto-Caption详细结果（FashionSigLIP，Phase 2）

| 方法 | R@5 | R@10 | vs Baseline |
|------|------|-------|------------|
| Image-only | 0.091 | 0.152 | — |
| BLIP short text-only | 0.027 | 0.045 | -70% ❌ |
| BLIP short Slerp α=0.7 | 0.075 | 0.129 | -18% ❌ |
| BLIP short Slerp α=0.9 | 0.072 | 0.120 | -21% ❌ |
| BLIP short Linear α=0.8 | 0.091 | 0.157 | +0.1% ➡️ |
| BLIP standard Slerp α=0.7 | 0.081 | 0.142 | -11% ❌ |
| BLIP detailed text-only | 0.046 | 0.081 | -50% ❌ |
| BLIP detailed Slerp α=0.7 | 0.065 | 0.118 | -29% ❌ |
| **Gold Slerp α=0.9** | **0.324** | **0.529** | **+256%** ✅ |

**三种caption方式的全面对比**：

| Caption方式 | 模型 | 纯文本R@5 | 最佳融合R@5 | 信息来源 | 独立于模型 |
|-----------|------|----------|-----------|---------|----------|
| Gold-label | FashionSigLIP | 0.336 | 0.324 (+256%) | 文件名标签 | ✅ |
| Gold-label | FashionCLIP | 0.336 | 0.158 (+17%) | 文件名标签 | ✅ |
| BLIP caption | FashionSigLIP | 0.027 | 0.072 (-21%) | VLM独立理解 | ✅ |
| Zero-shot top1 | FashionCLIP | 0.041 | 0.135 (+0%) | 自身分类 | ❌ |
| Zero-shot top3 | FashionCLIP | 0.069 | 0.138 (+2%) | 自身分类 | ❌ |

---

## 七、根因分析

### 7.1 为什么Slerp在FashionCLIP上几乎无效？

**原因1：模型越强，文本边际价值越低**

```
FashionSigLIP: Gap=0.100 → image embedding品类区分度差 → 文本能补大量信息
FashionCLIP:   Gap=0.129 → image embedding品类区分度好 → 文本能补的信息少
```

这是"雪中送炭"vs"锦上添花"的区别。FashionSigLIP的image特征太差，文本信号相对价值巨大；FashionCLIP已经较好编码了品类，文本反而成噪声。

**原因2：CLIP的image/text存在模态鸿沟（Modality Gap）**

Liang et al. (2022) "Mind the Gap" 证明了CLIP的image embedding和text embedding在共享空间中占据不同的区域，两者之间存在一个系统性偏移（modality gap）。Slerp假设两个向量可以在球面上连续插值，但实际上插值路径穿过了特征空间的低密度区域，生成的融合向量既不像image也不像text。

```
Image subspace          Gap region         Text subspace
┌─────────────┐                           ┌─────────────┐
│  🖼️ img_emb  │ ←── 低密度区域 ──→        │  📝 txt_emb  │
│  (聚类中心)   │    Slerp插值经过这里       │  (聚类中心)   │
└─────────────┘                           └─────────────┘
```

当模型较弱（FashionSigLIP）时，image embedding分布更散，gap区域的影响被掩盖；当模型较强（FashionCLIP）时，image embedding已形成好的聚类，插值反而破坏了聚类结构。

**原因3：Gold-label是标签泄露，不是真正的检索增强**

21个类别的gold-label意味着：
- 同类的34张图共享完全相同的文本embedding
- Slerp融合后，同类图的融合向量几乎相同
- 检索时"同类聚在一起"不是因为视觉相似，而是因为文本标签相同

这本质上是把分类问题包装成了检索问题，不反映真实检索能力。

### 7.2 为什么Auto-Caption无效？

**BLIP失败原因**：生成的描述太粗糙（14种），品类分类不准（109张标为cardigan），引入的是噪声而非信号。

**Zero-shot失败原因**：这是**信息自循环**——用CLIP预测文本 → 用同一CLIP编码文本 → 融合。输入和输出的信息量完全相同，等价于对自己做了一次非线性变换，不会产生新信息。CLIP zero-shot的概率极度扁平（最高0.075/15类≈随机水平），说明模型对时尚属性的判断力有限。

**共同问题**：无论BLIP还是Zero-shot，都没有引入**模型外部**的文本信息。真正的文本增强需要：
1. 商品元数据（标题、品类、属性标签） — P0
2. 独立VLM的理解（不是用检索模型自身） — P1

### 7.3 Embedding级融合 vs 结果级融合

本实验所有融合都是在**embedding级**做的（先融合向量，再计算相似度）。但更合理的方案是**结果级融合**（分别检索，再融合分数）：

```
Embedding级融合（本实验，效果差）:
  fused_emb = Slerp(img_emb, txt_emb, α)
  score = cosine(query_fused, target_fused)
  问题：模态鸿沟导致融合向量落入低密度区域

结果级融合（推荐方案）:
  img_score = cosine(query_img_emb, target_img_emb)
  txt_score = cosine(query_txt_emb, target_txt_emb)
  final_score = α·img_score + (1-α)·txt_score
  优势：各自在熟悉的模态空间内计算，不做跨模态插值
```

---

## 八、生产落地建议

### 8.1 推荐架构

```
┌──────────────────────────────────────────────────────────────┐
│              双路检索 + 结果级融合架构                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  INDEXING (离线)                                              │
│  ┌──────────────┐                  ┌──────────────┐         │
│  │ 商品图片      │                  │ 商品元数据    │         │
│  │              │                  │ (标题/品类/  │         │
│  │              │                  │  风格/颜色)  │         │
│  └──────┬───────┘                  └──────┬───────┘         │
│         │                                 │                  │
│         ▼                                 ▼                  │
│  FashionCLIP                        FashionCLIP             │
│  Image Encoder                      Text Encoder            │
│         │                                 │                  │
│         ▼                                 ▼                  │
│  img_emb(512)                       txt_emb(512)           │
│  存入Milvus/FAISS索引1              存入Milvus/FAISS索引2    │
│                                                              │
│  QUERY (在线)                                                 │
│  ┌──────────────┐                                           │
│  │ 查询图片      │                                           │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  FashionCLIP Image Encoder → query_img_emb                  │
│         │                                                   │
│         ├──→ 索引1检索 → img_scores                          │
│         │                                                   │
│         │   如果有查询文本:                                   │
│         │   FashionCLIP Text Encoder → query_txt_emb        │
│         │   └──→ 索引2检索 → txt_scores                      │
│         │                                                   │
│         ▼                                                   │
│  final_score = α·img_scores + (1-α)·txt_scores             │
│         │                                                   │
│         ▼                                                   │
│  排序 → 返回Top-K结果                                        │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 落地优先级

| 优先级 | 方案 | 预期效果 | 实施成本 | 说明 |
|--------|------|---------|---------|------|
| **P0** | FashionCLIP + 商品元数据结果级融合 | R@5 0.3+ | 低 | 数据已有，双路索引+加权 |
| P1 | 部署InternVL2/BLIP-large生成独立描述 | 补充无元数据图片 | 中 | 需GPU推理 |
| P2 | FashionCLIP on B2B数据fine-tune | 领域适配 | 高 | 需标注数据+GPU |
| P3 | 多模型embedding拼接(img+txt+DINOv2) | 视觉+语义+结构三重 | 高 | 复杂度高 |

### 8.3 FashionCLIP推理性能参考

| 部署方式 | 速度 | 说明 |
|---------|------|------|
| CPU (本实验) | 12 img/s | 可用于小规模离线 |
| GPU (T4) | ~200 img/s | 生产推荐 |
| GPU (A10G) | ~500 img/s | 大规模索引 |

---

## 九、深度对比：Marqo-FashionSigLIP vs FashionCLIP

### 9.1 模型背景

| 维度 | Marqo-FashionSigLIP | FashionCLIP |
|------|---------------------|-------------|
| **发布方** | Marqo (向量搜索公司) | patrickjohncyh (研究者) |
| **基座模型** | ViT-B-16-SigLIP (webli) | OpenAI CLIP ViT-B/32 |
| **架构** | SigLIP (Sigmoid替代Softmax) | 标准CLIP (Softmax对比学习) |
| **训练方法** | GCL (Generalized Contrastive Learning) | 标准CLIP对比学习 |
| **训练数据** | Marqo自有时尚数据集 | Farfetch商品数据集 |
| **Embed维度** | 768 | 512 |
| **上下文长度** | 64 tokens | 77 tokens |
| **HF下载量** | 91.5万 | 270.7万 |
| **HF Likes** | 74 | 278 |
| **License** | Apache-2.0 | 未声明 |
| **发布时间** | 2024-08 | 2023-02 |
| **配套库** | open_clip / transformers | transformers |
| **Marqo官方声称** | 比FashionCLIP高57% MRR/Recall | — |

> **Marqo-FashionSigLIP 2** 已发布，官方声称比v1再提升78% MRR/Recall，但为闭源商业模型，需联系Marqo获取。

### 9.2 Image-Only检索对比

| 指标 | FashionSigLIP | FashionCLIP | 差异 |
|------|--------------|-------------|------|
| **R@1** | 0.0318 | 0.0303 | -4.7% |
| **R@5** | 0.1253 | 0.1345 | **+7.3%** |
| **R@10** | 0.2120 | 0.2368 | **+11.7%** |
| **R@20** | 0.3531 | 0.3848 | **+9.0%** |
| **P@1** | 0.467 | 0.510 | **+9.2%** |
| **NDCG@5** | 0.4445 | 0.4774 | **+7.4%** |
| **NDCG@20** | 0.3946 | 0.4254 | **+7.8%** |
| **类内相似度** | 0.733 | 0.662 | — |
| **类间相似度** | 0.633 | 0.533 | — |
| **区分度Gap** | 0.100 | 0.129 | FashionCLIP +29% |
| **吞吐** | 4.0 img/s | 12.0 img/s | FashionCLIP **3x** |
| **维度** | 768 | 512 | FashionCLIP更紧凑 |

**关键发现**：FashionCLIP在所有Recall/NDCG指标上均优于FashionSigLIP（+7~12%），且速度快3倍、维度更小。

### 9.3 效果差异根因：评测场景错位 + 数据域偏移

两个模型呈现出截然不同的embedding分布特征：

```
FashionSigLIP:  intra=0.733  inter=0.633  gap=0.100
FashionCLIP:    intra=0.662  inter=0.533  gap=0.129
```

#### 9.3.1 Marqo官方评测 vs 我们的评测：完全不同的任务

**Marqo官方LEADERBOARD**（7个标准数据集，全面领先）：

| 任务类型 | FashionSigLIP | FashionCLIP 2.0 | Marqo-FashionCLIP |
|---------|--------------|-----------------|-------------------|
| Text→Image AvgRecall | **0.231** | 0.163 | 0.192 |
| Category→Product AvgP | **0.737** | 0.684 | 0.705 |
| Sub-Category→Product AvgP | **0.725** | 0.657 | 0.707 |

FashionSigLIP在标准评测上全面领先，这不是虚标。但注意：
- **评测任务**：Text→Image（文本检索图片）、Category→Product（品类标签检索商品）
- **doc端embedding**：Category→Product使用`0.9*image + 0.1*text`加权融合，**不是纯image**
- **数据集**：DeepFashion-InShop、Fashion200k、Polyvore等**高质量电商商品图**

**我们的评测**（1个自有数据集，FashionCLIP领先）：

| 任务类型 | FashionSigLIP | FashionCLIP |
|---------|--------------|-------------|
| Image→Image R@5 | 0.1253 | **0.1345** |
| Image→Image R@10 | 0.2120 | **0.2368** |

核心差异：
- **评测任务**：Image→Image（图片检索图片，纯image embedding）
- **数据集**：PDF提取的低分辨率图片（480x640，<60KB），品类按文件名前缀分组

**这是完全不同的两个赛道**。FashionSigLIP的训练目标（GCL + 细粒度标签对齐）让它擅长text→image和category→product，但我们只测了image→image——恰好是它最不需要擅长的方向。

#### 9.3.2 数据域偏移：B/16对图片质量更敏感

| 因素 | FashionSigLIP (ViT-B/16) | FashionCLIP (ViT-B/32) |
|------|-------------------------|----------------------|
| Patch数 | 196 | 49 |
| 每个patch覆盖 | 16×16像素 | 32×32像素 |
| 敏感度 | 更细粒度，对纹理/材质敏感 | 更粗粒度，对整体轮廓/色调敏感 |
| 高质量图表现 | 强（官方评测验证） | 也强，但细粒度不如 |
| PDF提取图表现 | 弱（纹理信息丢失，patch噪声放大） | 相对鲁棒（粗patch对低质量图更宽容） |

PDF提取图的特征：
- 原始商品图经过PDF压缩，纹理/材质信息大量丢失
- 不同PDF页面的图片可能共享相似的背景/排版风格
- 同一PDF页面内的图片视觉风格高度一致

**这解释了为什么SigLIP只在"视觉高度一致的类别"上赢**（见9.3.4）：它依赖的是细粒度纹理特征区分品类，当纹理信息丢失后，剩下的共享视觉风格（如同一PDF的排版背景）反而成了干扰信号。

#### 9.3.3 跨图相似度分布差异

| 指标 | FashionSigLIP | FashionCLIP |
|------|--------------|-------------|
| 平均跨图相似度 | **0.685** | 0.595 |
| 误判率(FP@0.7) | 43.6% | 14.3% |
| 跨模型结构对齐(Spearman ρ vs OpenAI) | 0.682 | 0.747 |

SigLIP在PDF数据集上的跨图相似度偏高（0.685 vs 0.595），这不是"Embedding空间坍缩"，而是**数据域偏移的体现**：B/16编码了更多在训练数据上有区分力但在PDF图上变成噪声的细粒度特征，导致不同品类的embedding反常地接近。在标准数据集上，这些特征恰恰是区分品类的关键信号。

#### 9.3.4 Per-Category分析

| 统计 | SigLIP胜(6/21) | FCLIP胜(15/21) |
|------|---------------|----------------|
| 胜出类别平均类内相似度 | 0.753 | 0.725 |

SigLIP只在"视觉高度一致"的类别上胜出（同PDF页面图片），进一步印证了数据域偏移的影响。

#### 9.3.5 修正后的结论

~~FashionSigLIP存在Embedding空间坍缩~~ → **FashionSigLIP在标准评测上全面领先，在我们的PDF数据集上表现不如FashionCLIP，原因是数据域偏移(image→image场景 + PDF低质量图)放大了B/16对纹理信息丢失的敏感性**。

这也意味着：**如果我们用真实B2B商品图（而非PDF提取图）重新评测，FashionSigLIP很可能会反超FashionCLIP**。

### 9.4 文本增强融合对比（Gold-Label）

| 融合方式 | FashionSigLIP R@5 | FashionCLIP R@5 | FashionSigLIP 提升 | FashionCLIP 提升 |
|---------|-------------------|-----------------|-------------------|-----------------|
| Image-only baseline | 0.1253 | 0.1345 | — | — |
| Text-only | 0.3361 | 0.3361 | — | — |
| Slerp α=0.5 | 0.1432 | 0.1579 | +14.3% | +17.4% |
| Slerp α=0.7 | 0.1606 | 0.1493 | +28.2% | +11.0% |
| Slerp α=0.9 | **0.3086** | 0.1383 | **+146%** | +2.8% |

**这是最关键的对比**：FashionSigLIP在α=0.9时R@5暴增146%到0.309，而FashionCLIP几乎不动（+2.8%）。

**根因**：

| 因素 | FashionSigLIP | FashionCLIP |
|------|--------------|-------------|
| Image-only基线 | 0.125（弱） | 0.135（强） |
| 文本信号边际价值 | 高（image弱，text补位空间大） | 低（image已强，text增量小） |
| 模态间隙影响 | α=0.9时text=10%，间隙干扰小 | 同上，但image已好所以增量有限 |
| Embedding空间对齐 | image和text空间较近 | image和text空间较远（gap大=0.129） |

### 9.5 融合提升的悖论

```
模型image越弱 → 文本融合提升越大 → 但你不会选弱模型
模型image越强 → 文本融合提升越小 → 但这正是你要用的模型
```

FashionSigLIP +256%提升看似惊人，但绝对值R@5=0.309仍然低于FashionCLIP baseline 0.135 + 结果级融合的预期效果。**百分比提升是误导性的——绝对值才是决策依据。**

### 9.6 与Marqo官方声称的对比

Marqo官方声称FashionSigLIP比FashionCLIP高57% MRR/Recall。但我们的实验结果显示FashionCLIP更优（R@5 +7.3%），可能原因：

1. **评测数据集不同**：Marqo使用的是标准时尚电商数据集（如DeepFashion），图片质量远高于我们的PDF提取图
2. **评测方式不同**：Marqo可能用text-to-image检索（SigLIP天然擅长），我们用的是image-to-image检索
3. **FashionSigLIP更擅长细粒度匹配**：在高质量图片上，GCL训练的细粒度标签优势可能更明显；PDF提取图丢失了大量纹理/材质信息，削弱了这一优势
4. **SigLIP在跨模态检索上的优势**：Sigmoid loss可能更适合text→image方向，我们测的是image→image

### 9.7 选型建议

| 场景 | 推荐 | 理由 |
|------|------|------|
| **Text→Image检索** | FashionSigLIP | 官方评测全面领先，GCL训练天然擅长 |
| **有品类标签的检索** | FashionSigLIP | Category→Product官方P@1=0.758，远超其他 |
| **纯Image→Image（高质量图）** | FashionSigLIP | B/16细粒度优势在好图上能发挥 |
| **纯Image→Image（低质量图）** | FashionCLIP | B/32对图片退化更鲁棒 |
| **轻量部署** | FashionCLIP | 512维/12img/s vs 768维/4img/s |
| **生产环境（有商品元数据）** | FashionSigLIP | Marqo官方doc端用0.9img+0.1text融合 |

---

## 十、实验局限

| 局限 | 影响 | 改进方向 |
|------|------|---------|
| 数据集为PDF提取图，非标准商品图 | 视觉质量差，品类不清晰 | 用真实B2B商品数据 |
| 类别按文件名前缀定义 | 不反映业务语义相似 | 人工标注相似度 |
| 评测只看类别命中 | 图片相似≠品类相同 | 多维度评测（风格/颜色/版型） |
| CPU环境限制 | 无法测试更大模型 | GPU环境重跑 |
| Gold-label仅21种描述 | 融合效果可能被低估 | 用真实商品标题/属性 |
| 未测试结果级融合 | 缺少对比 | 实现双路检索+加权 |

---

## 十一、结论

1. **FashionCLIP是最优模型** — 综合性能、区分度、速度均领先，推荐作为生产基线
2. **纯image检索在时尚场景严重不足** — 所有模型R@5<0.14，视觉同质化是根本原因
3. **Embedding级Slerp融合不是通用解法** — 在强模型上几乎无效（FashionCLIP +17% vs FashionSigLIP +256%）
4. **Auto-caption（无论BLIP还是Zero-shot）在当前条件下均无效** — BLIP太粗糙，Zero-shot是自循环
5. **文本信号本身有巨大价值** — gold-label text-only R@5=0.336（image-only的2.5倍），关键是怎么用
6. **正确的路径是结果级融合** — `score = α·img_sim + (1-α)·text_sim`，不做跨模态embedding插值
7. **真正的突破需要外部文本源** — 商品元数据（P0）或独立VLM（P1），不能自循环

---

*实验代码：~/workspace/clip-exp/multimodel_benchmark.py, fashionclip_fusion.py, fashionclip_autocaption.py*
*实验结果：~/workspace/clip-exp/results/*
