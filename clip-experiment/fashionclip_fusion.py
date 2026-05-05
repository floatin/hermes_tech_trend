#!/usr/bin/env python3
"""
FashionCLIP Text-Augmented Fusion Experiment
============================================
最优模型(FashionCLIP)的文本增强融合实验。

实验矩阵：
1. Baseline: image-only
2. Gold-label text-only (上界参考)
3. Gold-label Slerp fusion (α sweep: 0.5~0.95)
4. Gold-label Linear fusion (α sweep)
"""

import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from collections import defaultdict
from PIL import Image
import torch
import torch.nn.functional as F

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# ========== CONFIG ==========
IMAGE_DIR = Path("/home/floating/workspace/jina-clip-v2/test_images")
NUM_SAMPLES = 300
RESULTS_DIR = Path("/home/floating/workspace/clip-exp/results")
RESULTS_DIR.mkdir(exist_ok=True)

# ========== HELPERS ==========
def load_dataset():
    images = sorted([f for f in os.listdir(IMAGE_DIR) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    images = images[:NUM_SAMPLES]
    categories = {}
    for fname in images:
        name = os.path.splitext(fname)[0]
        parts = name.rsplit('_', 1)
        if len(parts) > 1 and parts[1].isdigit():
            cat = parts[0]
        else:
            cat = name
        categories[fname] = cat
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
            if total_relevant == 0:
                continue
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
    """Spherical linear interpolation. alpha=1 means all v1 (image)."""
    v1_norm = F.normalize(v1, dim=-1)
    v2_norm = F.normalize(v2, dim=-1)
    omega = torch.acos(torch.clamp((v1_norm * v2_norm).sum(dim=-1, keepdim=True), -0.999, 0.999))
    sin_omega = torch.sin(omega)
    # Avoid division by zero
    mask = (sin_omega.abs() > 1e-7).float()
    coef1 = torch.sin((1 - alpha) * omega) / (sin_omega + 1e-10) * mask + (1 - alpha) * (1 - mask)
    coef2 = torch.sin(alpha * omega) / (sin_omega + 1e-10) * mask + alpha * (1 - mask)
    return coef1 * v2 + coef2 * v1

# ========== GOLD-LABEL TEXT ==========
# Map filename categories to fashion descriptions
CATEGORY_TEXT = {
    'dress': "A photo of a women's dress, elegant flowing garment",
    'blouse': "A photo of a women's blouse, lightweight top",
    'jeans': "A photo of women's jeans, denim pants",
    'outfit': "A photo of a women's outfit set, coordinated look",
    'img': "A photo of women's fashion clothing",
}

def get_gold_label_text(fname, category):
    """Generate text description from filename category."""
    if category in CATEGORY_TEXT:
        return CATEGORY_TEXT[category]
    # For pdf_img_pXX categories, use generic fashion description
    return f"A photo of women's fashion clothing, {category}"

# ========== MAIN EXPERIMENT ==========
def run_experiment():
    print("=" * 70)
    print("FashionCLIP Text-Augmented Fusion Experiment")
    print("=" * 70)
    
    images, categories = load_dataset()
    image_paths = [str(IMAGE_DIR / fname) for fname in images]
    print(f"Dataset: {len(images)} images, {len(set(categories.values()))} categories", flush=True)
    
    # ========== 1. Load FashionCLIP ==========
    print("\n[1/4] Loading FashionCLIP...", flush=True)
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained('patrickjohncyh/fashion-clip', local_files_only=True)
    processor = CLIPProcessor.from_pretrained('patrickjohncyh/fashion-clip', local_files_only=True)
    model.eval()
    
    # ========== 2. Encode all images ==========
    print("[2/4] Encoding images...", flush=True)
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
            print(f"  {i+1}/{len(image_paths)} images encoded ({time.time()-t0:.1f}s)", flush=True)
    img_embeddings = np.array(img_embeddings)
    print(f"  Image embeddings: {img_embeddings.shape} ({time.time()-t0:.1f}s)", flush=True)
    
    # ========== 3. Encode gold-label text ==========
    print("[3/4] Encoding gold-label text...", flush=True)
    t0 = time.time()
    text_descriptions = [get_gold_label_text(fname, categories[fname]) for fname in images]
    text_embeddings = []
    # Batch encode for speed
    batch_size = 32
    for i in range(0, len(text_descriptions), batch_size):
        batch = text_descriptions[i:i+batch_size]
        inputs = processor(text=batch, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            out = model.get_text_features(**inputs)
            features = out.pooler_output if hasattr(out, 'pooler_output') else out
            features = F.normalize(features.float(), dim=-1)
        text_embeddings.append(features.cpu().numpy())
    text_embeddings = np.vstack(text_embeddings)
    print(f"  Text embeddings: {text_embeddings.shape} ({time.time()-t0:.1f}s)", flush=True)
    
    # Show text diversity
    unique_texts = set(text_descriptions)
    print(f"  Unique descriptions: {len(unique_texts)}", flush=True)
    
    # ========== 4. Run all experiments ==========
    print("\n[4/4] Running experiments...", flush=True)
    results = {}
    
    # --- 4a. Baseline: image-only ---
    sim_img = img_embeddings @ img_embeddings.T
    results['baseline_image'] = compute_metrics(sim_img, categories, images)
    print(f"  baseline_image: R@5={results['baseline_image']['Recall@5']:.4f}", flush=True)
    
    # --- 4b. Text-only ---
    sim_text = text_embeddings @ text_embeddings.T
    results['text_only'] = compute_metrics(sim_text, categories, images)
    print(f"  text_only:      R@5={results['text_only']['Recall@5']:.4f}", flush=True)
    
    # --- 4c. Slerp fusion (α sweep) ---
    img_t = torch.from_numpy(img_embeddings).float()
    txt_t = torch.from_numpy(text_embeddings).float()
    
    best_slerp_r5 = 0
    best_slerp_alpha = None
    for alpha in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99]:
        fused = slerp(img_t, txt_t, alpha)
        fused_np = F.normalize(fused, dim=-1).numpy()
        sim_fused = fused_np @ fused_np.T
        key = f'slerp_a{alpha}'
        results[key] = compute_metrics(sim_fused, categories, images)
        r5 = results[key]['Recall@5']
        print(f"  slerp α={alpha}: R@5={r5:.4f}", flush=True)
        if r5 > best_slerp_r5:
            best_slerp_r5 = r5
            best_slerp_alpha = alpha
    
    # --- 4d. Linear fusion (α sweep) ---
    best_linear_r5 = 0
    best_linear_alpha = None
    for alpha in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99]:
        fused = alpha * img_t + (1 - alpha) * txt_t
        fused_np = F.normalize(fused, dim=-1).numpy()
        sim_fused = fused_np @ fused_np.T
        key = f'linear_a{alpha}'
        results[key] = compute_metrics(sim_fused, categories, images)
        r5 = results[key]['Recall@5']
        print(f"  linear α={alpha}: R@5={r5:.4f}", flush=True)
        if r5 > best_linear_r5:
            best_linear_r5 = r5
            best_linear_alpha = alpha
    
    # Save results
    results_path = RESULTS_DIR / "fashionclip_fusion_experiment.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}", flush=True)
    
    # ========== SUMMARY TABLE ==========
    print("\n" + "=" * 100)
    print("📊 FashionCLIP Text-Augmented Fusion Results")
    print("=" * 100)
    print(f"{'Method':<30} {'R@1':>7} {'R@5':>7} {'R@10':>7} {'R@20':>7} {'NDCG@5':>7} {'P@5':>7} {'vs Base':>8}")
    print("-" * 100)
    
    base_r5 = results['baseline_image']['Recall@5']
    
    # Print in order
    order = ['baseline_image', 'text_only']
    # Add slerp sorted by alpha
    slerp_keys = sorted([k for k in results if k.startswith('slerp_')],
                        key=lambda k: float(k.split('_a')[1]))
    # Add linear sorted by alpha
    linear_keys = sorted([k for k in results if k.startswith('linear_')],
                         key=lambda k: float(k.split('_a')[1]))
    order += slerp_keys + linear_keys
    
    for key in order:
        m = results[key]
        vs_base = m['Recall@5'] - base_r5
        arrow = "✅" if vs_base > 0.01 else ("❌" if vs_base < -0.01 else "➡️")
        # Shorten method name for display
        display = key.replace('slerp_', 'Slerp α=').replace('linear_', 'Linear α=').replace('baseline_image', 'Image-only (baseline)').replace('text_only', 'Text-only (gold)')
        print(f"{display:<30} {m['Recall@1']:>7.4f} {m['Recall@5']:>7.4f} {m['Recall@10']:>7.4f} {m['Recall@20']:>7.4f} {m['NDCG@5']:>7.4f} {m['P@5']:>7.4f} {vs_base:>+7.4f} {arrow}")
    
    print(f"\n🏆 Best Slerp: α={best_slerp_alpha}, R@5={best_slerp_r5:.4f} (+{(best_slerp_r5-base_r5)/base_r5*100:.1f}%)")
    print(f"🏆 Best Linear: α={best_linear_alpha}, R@5={best_linear_r5:.4f} (+{(best_linear_r5-base_r5)/base_r5*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    run_experiment()
