"""
Real B2B Product Image Evaluation: FashionSigLIP vs FashionCLIP
Uses real product images from 相似商品汇总_50个.docx

Evaluation method:
- 50 query products, each with ground-truth similar products (from multiple models' results)
- Image-to-Image retrieval using pure image embeddings
- Metrics: Recall@K, Precision@K, NDCG@K
"""
import os
import sys

# Ensure proxy and HF mirror for model downloads
os.environ.setdefault('http_proxy', 'http://127.0.0.1:7890')
os.environ.setdefault('https_proxy', 'http://127.0.0.1:7890')
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

import json
import time
import numpy as np
from pathlib import Path
from PIL import Image
import torch
from collections import defaultdict

# ─── Config ───
IMAGE_DIR = os.path.expanduser("~/workspace/clip-exp/real_images")
MAPPING_FILE = os.path.expanduser("~/workspace/clip-exp/results/goods_image_mapping.json")
EVAL_DATA_FILE = os.path.expanduser("~/workspace/clip-exp/results/real_evaluation_data.json")
OUTPUT_DIR = os.path.expanduser("~/workspace/clip-exp/results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_mapping():
    with open(MAPPING_FILE) as f:
        data = json.load(f)
    return data['goods_to_img'], data['img_to_goods']


def load_eval_data():
    with open(EVAL_DATA_FILE) as f:
        return json.load(f)


def get_all_unique_images(goods_to_img):
    """Get all unique image files needed for the gallery."""
    images = set()
    for gno, img in goods_to_img.items():
        path = os.path.join(IMAGE_DIR, img)
        if os.path.exists(path):
            images.add(img)
    return sorted(images)


def load_fashion_siglip():
    """Load Marqo-FashionSigLIP via open_clip"""
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms('hf-hub:Marqo/marqo-fashionSigLIP')
    tokenizer = open_clip.get_tokenizer('hf-hub:Marqo/marqo-fashionSigLIP')
    model.eval()
    return model, preprocess, tokenizer, "FashionSigLIP"


def load_fashion_clip():
    """Load FashionCLIP via transformers"""
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
    processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
    model.eval()
    return model, processor, None, "FashionCLIP"


def encode_images_siglip(model, preprocess, image_paths, batch_size=16):
    """Encode images using FashionSigLIP"""
    all_embeds = []
    total = len(image_paths)
    
    for i in range(0, total, batch_size):
        batch_paths = image_paths[i:i+batch_size]
        images = []
        for p in batch_paths:
            try:
                img = preprocess(Image.open(p).convert('RGB'))
                images.append(img)
            except Exception as e:
                print(f"  Error loading {p}: {e}")
                images.append(preprocess(Image.new('RGB', (224, 224))))
        
        batch = torch.stack(images)
        with torch.no_grad():
            features = model.encode_image(batch, normalize=True)
        all_embeds.append(features.cpu().numpy())
        
        if (i + batch_size) % 100 < batch_size:
            print(f"  SigLIP: {min(i+batch_size, total)}/{total}")
    
    return np.vstack(all_embeds)


def encode_images_fclip(model, processor, image_paths, batch_size=16):
    """Encode images using FashionCLIP"""
    all_embeds = []
    total = len(image_paths)
    
    for i in range(0, total, batch_size):
        batch_paths = image_paths[i:i+batch_size]
        images = []
        for p in batch_paths:
            try:
                images.append(Image.open(p).convert('RGB'))
            except Exception as e:
                print(f"  Error loading {p}: {e}")
                images.append(Image.new('RGB', (224, 224)))
        
        inputs = processor(images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            features = model.get_image_features(inputs['pixel_values'])
            # transformers 5.x returns BaseModelOutputWithPooling
            if hasattr(features, 'pooler_output'):
                features = features.pooler_output
            features = features / features.norm(dim=-1, keepdim=True)
        all_embeds.append(features.cpu().numpy())
        
        if (i + batch_size) % 100 < batch_size:
            print(f"  FCLIP: {min(i+batch_size, total)}/{total}")
    
    return np.vstack(all_embeds)


def evaluate_retrieval(query_embeds, gallery_embeds, query_goods, gallery_goods, 
                       ground_truth, Ks=[1, 5, 10, 20]):
    """
    Evaluate image-to-image retrieval.
    
    Args:
        query_embeds: (N_q, D) normalized query embeddings
        gallery_embeds: (N_g, D) normalized gallery embeddings
        query_goods: list of query goods_no
        gallery_goods: list of gallery goods_no
        ground_truth: dict {query_goods_no: set(similar_goods_nos)}
        Ks: list of K values for Recall@K
    """
    # Compute similarity matrix
    sim_matrix = query_embeds @ gallery_embeds.T  # (N_q, N_g)
    
    results = {}
    for K in Ks:
        recalls = []
        precisions = []
        ndcgs = []
        
        for qi, qgno in enumerate(query_goods):
            sims = sim_matrix[qi].copy()
            
            # Get top-K (exclude self if query is in gallery)
            top_indices = np.argsort(sims)[::-1][:K + 1]  # +1 in case self is included
            
            retrieved_goods = []
            for idx in top_indices:
                gno = gallery_goods[idx]
                if gno == qgno:  # skip self
                    continue
                retrieved_goods.append(gno)
                if len(retrieved_goods) >= K:
                    break
            
            # Ground truth
            gt = ground_truth.get(qgno, set())
            if not gt:
                continue
            
            # Recall@K
            hits = sum(1 for g in retrieved_goods[:K] if g in gt)
            recall = hits / min(len(gt), K)
            recalls.append(recall)
            
            # Precision@K
            precision = hits / K
            precisions.append(precision)
            
            # NDCG@K
            dcg = sum(1.0 / np.log2(i + 2) for i, g in enumerate(retrieved_goods[:K]) if g in gt)
            idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(gt), K)))
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcgs.append(ndcg)
        
        results[f'Recall@{K}'] = np.mean(recalls) if recalls else 0
        results[f'P@{K}'] = np.mean(precisions) if precisions else 0
        results[f'NDCG@{K}'] = np.mean(ndcgs) if ndcgs else 0
    
    return results


def main():
    print("=" * 70)
    print("Real B2B Product Image Evaluation: FashionSigLIP vs FashionCLIP")
    print("=" * 70)
    
    # Load mappings
    goods_to_img, img_to_goods = load_mapping()
    eval_data = load_eval_data()
    
    # Build gallery: all unique images with goods_no
    all_images = get_all_unique_images(goods_to_img)
    print(f"\nGallery size: {len(all_images)} images")
    
    # Build gallery goods_no list (same order as all_images)
    gallery_goods = []
    gallery_paths = []
    for img in all_images:
        gno = img_to_goods.get(img)
        if gno:
            gallery_goods.append(gno)
            gallery_paths.append(os.path.join(IMAGE_DIR, img))
    
    print(f"Gallery with goods_no: {len(gallery_goods)}")
    
    # Build query list and ground truth
    query_goods = []
    query_img_files = []
    ground_truth = {}
    
    for e in eval_data:
        qgno = e['query_goods_no']
        qimg = e['query_img']
        qpath = os.path.join(IMAGE_DIR, qimg)
        
        if not os.path.exists(qpath):
            continue
        
        # Ground truth: union of all models' similar results
        similar_nos = set()
        for model_name, model_data in e['models'].items():
            similar_nos.update(model_data['similar_goods_nos'])
        
        if similar_nos:
            query_goods.append(qgno)
            query_img_files.append(qimg)
            ground_truth[qgno] = similar_nos
    
    print(f"Queries: {len(query_goods)}")
    print(f"Avg ground truth size: {np.mean([len(v) for v in ground_truth.values()]):.1f}")
    
    # ─── Encode with FashionSigLIP ───
    print("\n" + "=" * 50)
    print("Encoding with FashionSigLIP...")
    print("=" * 50)
    
    t0 = time.time()
    siglip_model, siglip_preprocess, _, _ = load_fashion_siglip()
    
    # Encode gallery
    print("Encoding gallery...")
    gallery_siglip = encode_images_siglip(siglip_model, siglip_preprocess, gallery_paths)
    
    # Encode queries
    print("Encoding queries...")
    query_paths = [os.path.join(IMAGE_DIR, f) for f in query_img_files]
    query_siglip = encode_images_siglip(siglip_model, siglip_preprocess, query_paths)
    
    siglip_time = time.time() - t0
    print(f"SigLIP total time: {siglip_time:.1f}s")
    
    # ─── Encode with FashionCLIP ───
    print("\n" + "=" * 50)
    print("Encoding with FashionCLIP...")
    print("=" * 50)
    
    t0 = time.time()
    fclip_model, fclip_processor, _, _ = load_fashion_clip()
    
    # Encode gallery
    print("Encoding gallery...")
    gallery_fclip = encode_images_fclip(fclip_model, fclip_processor, gallery_paths)
    
    # Encode queries
    print("Encoding queries...")
    query_fclip = encode_images_fclip(fclip_model, fclip_processor, query_paths)
    
    fclip_time = time.time() - t0
    print(f"FCLIP total time: {fclip_time:.1f}s")
    
    # ─── Evaluate ───
    print("\n" + "=" * 50)
    print("Evaluating...")
    print("=" * 50)
    
    siglip_results = evaluate_retrieval(
        query_siglip, gallery_siglip, query_goods, gallery_goods, ground_truth
    )
    siglip_results['total_time'] = siglip_time
    siglip_results['query_count'] = len(query_goods)
    siglip_results['gallery_size'] = len(gallery_goods)
    
    fclip_results = evaluate_retrieval(
        query_fclip, gallery_fclip, query_goods, gallery_goods, ground_truth
    )
    fclip_results['total_time'] = fclip_time
    
    # ─── Print Results ───
    print("\n" + "=" * 70)
    print("RESULTS: FashionSigLIP vs FashionCLIP on Real B2B Product Images")
    print("=" * 70)
    print(f"{'Metric':<15} {'SigLIP':>10} {'FCLIP':>10} {'Diff':>10} {'Winner':>10}")
    print("-" * 55)
    
    for metric in ['Recall@1', 'Recall@5', 'Recall@10', 'Recall@20',
                    'P@1', 'P@5', 'P@10', 'NDCG@5', 'NDCG@10']:
        sv = siglip_results.get(metric, 0)
        fv = fclip_results.get(metric, 0)
        diff = sv - fv
        winner = "SigLIP" if diff > 0 else "FCLIP" if diff < 0 else "Tie"
        print(f"{metric:<15} {sv:>10.4f} {fv:>10.4f} {diff:>+10.4f} {winner:>10}")
    
    print(f"{'Time(s)':<15} {siglip_time:>10.1f} {fclip_time:>10.1f} {siglip_time-fclip_time:>+10.1f}")
    
    # Save results
    output = {
        'FashionSigLIP': siglip_results,
        'FashionCLIP': fclip_results,
        'meta': {
            'query_count': len(query_goods),
            'gallery_size': len(gallery_goods),
            'ground_truth_avg_size': np.mean([len(v) for v in ground_truth.values()]),
        }
    }
    
    with open(os.path.join(OUTPUT_DIR, 'real_b2b_benchmark.json'), 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {OUTPUT_DIR}/real_b2b_benchmark.json")
    
    # Also compute per-group results for deeper analysis
    print("\n" + "=" * 50)
    print("Per-section analysis...")
    print("=" * 50)
    
    # Re-parse sections from eval_data
    sections = defaultdict(list)
    for e in eval_data:
        qgno = e['query_goods_no']
        section = e.get('section', 'unknown')
        if qgno in query_goods:
            qi = query_goods.index(qgno)
            sections[section].append(qi)
    
    for section, indices in sections.items():
        if not indices:
            continue
        # Filter query embeds and goods for this section
        sec_q_goods = [query_goods[i] for i in indices]
        sec_q_siglip = query_siglip[indices]
        sec_q_fclip = query_fclip[indices]
        sec_gt = {qgno: ground_truth[qgno] for qgno in sec_q_goods}
        
        sec_siglip = evaluate_retrieval(sec_q_siglip, gallery_siglip, sec_q_goods, gallery_goods, sec_gt)
        sec_fclip = evaluate_retrieval(sec_q_fclip, gallery_fclip, sec_q_goods, gallery_goods, sec_gt)
        
        print(f"\n{section} ({len(indices)} queries):")
        print(f"  {'Metric':<12} {'SigLIP':>8} {'FCLIP':>8} {'Winner':>8}")
        for metric in ['Recall@5', 'Recall@10', 'P@5', 'NDCG@5']:
            sv = sec_siglip.get(metric, 0)
            fv = sec_fclip.get(metric, 0)
            winner = "SigLIP" if sv > fv else "FCLIP" if fv > sv else "Tie"
            print(f"  {metric:<12} {sv:>8.4f} {fv:>8.4f} {winner:>8}")


if __name__ == '__main__':
    main()
