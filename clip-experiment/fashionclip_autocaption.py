#!/usr/bin/env python3
"""
FashionCLIP Auto-Caption Fusion Experiment
===========================================
用FashionCLIP自身的zero-shot分类生成per-image文本描述，
替代BLIP captioning，避免下载大模型。

策略：30个fashion属性模板 → top-3预测 → 组合描述 → Slerp融合
"""

import os, sys, json, time
import numpy as np
from pathlib import Path
from collections import defaultdict
from PIL import Image
import torch
import torch.nn.functional as F

sys.stdout.reconfigure(line_buffering=True)
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

IMAGE_DIR = Path("/home/floating/workspace/jina-clip-v2/test_images")
NUM_SAMPLES = 300
RESULTS_DIR = Path("/home/floating/workspace/clip-exp/results")
RESULTS_DIR.mkdir(exist_ok=True)

# Fashion attribute templates for zero-shot classification
TEMPLATES = [
    "casual women's dress for everyday wear",
    "elegant women's dress for formal occasions",
    "casual women's blouse with relaxed fit",
    "formal women's blouse for office wear",
    "classic women's jeans denim pants",
    "women's jacket outerwear coat",
    "women's sweater cardigan knitwear",
    "women's t-shirt casual top",
    "women's skirt midi mini",
    "women's hoodie sweatshirt sportswear",
    "women's blazer suit jacket",
    "women's jumpsuit romper playsuit",
    "women's vest waistcoat sleeveless",
    "women's coat overcoat winter wear",
    "women's pants trousers wide-leg",
    "floral print women's fashion clothing",
    "solid color women's fashion clothing",
    "striped pattern women's fashion clothing",
    "women's fashion clothing in dark colors",
    "women's fashion clothing in light colors",
    "women's fashion clothing in bright colors",
    "women's evening party wear fashion",
    "women's streetwear urban fashion",
    "women's minimalist clean fashion",
    "women's vintage retro fashion style",
    "women's bohemian free-spirited fashion",
    "women's professional workwear office fashion",
    "women's summer lightweight fashion",
    "women's autumn layered fashion",
    "women's spring fashion clothing",
]

def load_dataset():
    images = sorted([f for f in os.listdir(IMAGE_DIR) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    images = images[:NUM_SAMPLES]
    categories = {}
    for fname in images:
        name = os.path.splitext(fname)[0]
        parts = name.rsplit('_', 1)
        categories[fname] = parts[0] if len(parts) > 1 and parts[1].isdigit() else name
    return images, categories

def compute_metrics(sim_matrix, categories, image_list, ks=[1, 5, 10, 20]):
    n = len(image_list)
    cat_to_indices = defaultdict(list)
    for i, fname in enumerate(image_list):
        cat_to_indices[categories[fname]].append(i)
    metrics = {}
    for k in ks:
        recalls, precisions, ndcgs = [], [], []
        for i in range(n):
            query_cat = categories[image_list[i]]
            sims = sim_matrix[i].copy()
            sims[i] = -float('inf')
            topk_indices = np.argsort(sims)[::-1][:k]
            relevances = np.array([1.0 if categories[image_list[j]] == query_cat else 0.0 
                                   for j in topk_indices])
            total_relevant = len(cat_to_indices[query_cat]) - 1
            if total_relevant == 0: continue
            recalls.append(np.sum(relevances) / total_relevant)
            precisions.append(np.mean(relevances))
            dcg = np.sum(relevances / np.log2(np.arange(2, k + 2)))
            ideal = np.zeros(k)
            ideal[:min(total_relevant, k)] = 1.0
            idcg = np.sum(ideal / np.log2(np.arange(2, k + 2)))
            ndcgs.append(dcg / idcg if idcg > 0 else 0.0)
        metrics[f'Recall@{k}'] = float(np.mean(recalls))
        metrics[f'P@{k}'] = float(np.mean(precisions))
        metrics[f'NDCG@{k}'] = float(np.mean(ndcgs))
    return metrics

def slerp(v1, v2, alpha):
    v1_n = F.normalize(v1, dim=-1)
    v2_n = F.normalize(v2, dim=-1)
    omega = torch.acos(torch.clamp((v1_n * v2_n).sum(dim=-1, keepdim=True), -0.999, 0.999))
    sin_omega = torch.sin(omega)
    mask = (sin_omega.abs() > 1e-7).float()
    c1 = torch.sin((1 - alpha) * omega) / (sin_omega + 1e-10) * mask + (1 - alpha) * (1 - mask)
    c2 = torch.sin(alpha * omega) / (sin_omega + 1e-10) * mask + alpha * (1 - mask)
    return c1 * v2 + c2 * v1

# ========== Caption strategies ==========
def generate_captions_zeroshot(model, processor, image_paths, top_k=3):
    """Use FashionCLIP zero-shot to generate per-image descriptions."""
    # Pre-encode all templates
    txt_inputs = processor(text=TEMPLATES, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        out_txt = model.get_text_features(**txt_inputs)
        txt_feat = out_txt.pooler_output if hasattr(out_txt, 'pooler_output') else out_txt
        txt_feat = F.normalize(txt_feat.float(), dim=-1)
    
    captions = []
    for i, path in enumerate(image_paths):
        img = Image.open(path).convert('RGB')
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            out_img = model.get_image_features(**inputs)
            img_feat = out_img.pooler_output if hasattr(out_img, 'pooler_output') else out_img
            img_feat = F.normalize(img_feat.float(), dim=-1)
        
        sims = (img_feat @ txt_feat.T).squeeze()
        topk_idx = sims.topk(top_k).indices
        caption = ", ".join([TEMPLATES[idx] for idx in topk_idx])
        captions.append(caption)
        
        if (i+1) % 50 == 0:
            print(f"  Captioned {i+1}/{len(image_paths)}", flush=True)
    
    return captions

def run():
    print("=" * 70)
    print("FashionCLIP Auto-Caption Fusion Experiment")
    print("=" * 70, flush=True)
    
    images, categories = load_dataset()
    image_paths = [str(IMAGE_DIR / fname) for fname in images]
    print(f"Dataset: {len(images)} images", flush=True)
    
    # Load model
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained('patrickjohncyh/fashion-clip', local_files_only=True)
    processor = CLIPProcessor.from_pretrained('patrickjohncyh/fashion-clip', local_files_only=True)
    model.eval()
    
    # Encode images
    print("\n[1] Encoding images...", flush=True)
    t0 = time.time()
    img_embeddings = []
    for i, path in enumerate(image_paths):
        img = Image.open(path).convert('RGB')
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            out = model.get_image_features(**inputs)
            features = out.pooler_output if hasattr(out, 'pooler_output') else out
            features = F.normalize(features.float(), dim=-1)
        img_embeddings.append(features.cpu().numpy().flatten())
        if (i+1) % 50 == 0:
            print(f"  {i+1}/300 ({time.time()-t0:.1f}s)", flush=True)
    img_embeddings = np.array(img_embeddings)
    print(f"  Done: {img_embeddings.shape} ({time.time()-t0:.1f}s)", flush=True)
    
    # Baseline
    sim_img = img_embeddings @ img_embeddings.T
    baseline = compute_metrics(sim_img, categories, images)
    print(f"\n  Baseline R@5: {baseline['Recall@5']:.4f}", flush=True)
    
    # ========== Caption Strategy 1: Zero-shot top-1 ==========
    print("\n[2] Generating zero-shot captions (top-1)...", flush=True)
    captions_top1 = generate_captions_zeroshot(model, processor, image_paths, top_k=1)
    unique_top1 = len(set(captions_top1))
    print(f"  Unique captions: {unique_top1}", flush=True)
    
    # Encode top-1 text
    txt_inputs_1 = processor(text=captions_top1, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        out = model.get_text_features(**txt_inputs_1)
        txt_emb_1 = out.pooler_output if hasattr(out, 'pooler_output') else out
        txt_emb_1 = F.normalize(txt_emb_1.float(), dim=-1).cpu().numpy()
    
    # ========== Caption Strategy 2: Zero-shot top-3 combined ==========
    print("\n[3] Generating zero-shot captions (top-3)...", flush=True)
    captions_top3 = generate_captions_zeroshot(model, processor, image_paths, top_k=3)
    unique_top3 = len(set(captions_top3))
    print(f"  Unique captions: {unique_top3}", flush=True)
    
    txt_inputs_3 = processor(text=captions_top3, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        out = model.get_text_features(**txt_inputs_3)
        txt_emb_3 = out.pooler_output if hasattr(out, 'pooler_output') else out
        txt_emb_3 = F.normalize(txt_emb_3.float(), dim=-1).cpu().numpy()
    
    # ========== Fusion experiments ==========
    print("\n[4] Running fusion experiments...", flush=True)
    results = {'baseline_image': baseline}
    
    img_t = torch.from_numpy(img_embeddings).float()
    
    # Text-only baselines
    sim_txt1 = txt_emb_1 @ txt_emb_1.T
    results['text_only_top1'] = compute_metrics(sim_txt1, categories, images)
    print(f"  text_only_top1: R@5={results['text_only_top1']['Recall@5']:.4f}", flush=True)
    
    sim_txt3 = txt_emb_3 @ txt_emb_3.T
    results['text_only_top3'] = compute_metrics(sim_txt3, categories, images)
    print(f"  text_only_top3: R@5={results['text_only_top3']['Recall@5']:.4f}", flush=True)
    
    # Slerp fusion with different caption strategies and alpha values
    for cap_name, txt_emb in [('top1', txt_emb_1), ('top3', txt_emb_3)]:
        txt_t = torch.from_numpy(txt_emb).float()
        for alpha in [0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99]:
            fused = slerp(img_t, txt_t, alpha)
            fused_np = F.normalize(fused, dim=-1).numpy()
            sim = fused_np @ fused_np.T
            key = f'slerp_{cap_name}_a{alpha}'
            results[key] = compute_metrics(sim, categories, images)
            r5 = results[key]['Recall@5']
            vs = r5 - baseline['Recall@5']
            print(f"  slerp_{cap_name} α={alpha}: R@5={r5:.4f} ({vs:+.4f})", flush=True)
    
    # Save
    with open(RESULTS_DIR / "fashionclip_autocaption_fusion.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save captions for inspection
    with open(RESULTS_DIR / "zeroshot_captions.json", 'w') as f:
        json.dump({'top1': captions_top1, 'top3': captions_top3, 
                   'unique_top1': unique_top1, 'unique_top3': unique_top3}, f, indent=2)
    
    # Summary table
    print("\n" + "=" * 100)
    print("📊 FashionCLIP Auto-Caption Fusion Results")
    print("=" * 100)
    base_r5 = baseline['Recall@5']
    print(f"{'Method':<35} {'R@5':>7} {'R@10':>7} {'NDCG@5':>7} {'vs Base':>8}")
    print("-" * 70)
    
    order = ['baseline_image', 'text_only_top1', 'text_only_top3']
    for cap in ['top1', 'top3']:
        for alpha in [0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99]:
            order.append(f'slerp_{cap}_a{alpha}')
    
    for key in order:
        if key not in results: continue
        m = results[key]
        vs = m['Recall@5'] - base_r5
        arrow = "✅" if vs > 0.01 else ("❌" if vs < -0.01 else "➡️")
        display = key.replace('baseline_image', 'Image-only').replace('text_only_top1', 'Text-only (top1)').replace('text_only_top3', 'Text-only (top3)').replace('slerp_', 'Slerp ').replace('_a', ' α=')
        print(f"{display:<35} {m['Recall@5']:>7.4f} {m['Recall@10']:>7.4f} {m['NDCG@5']:>7.4f} {vs:>+7.4f} {arrow}")

if __name__ == "__main__":
    run()
