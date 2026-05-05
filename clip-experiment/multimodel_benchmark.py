#!/usr/bin/env python3
"""
多模型同口径对比评测
==================
4个CLIP模型在相同数据集上跑相同指标，输出统一对比表。

模型加载方式：
- FashionSigLIP: open_clip (768d)
- OpenAI CLIP ViT-B/32: transformers (512d)
- FashionCLIP: transformers (512d)
- jina-clip-v2: ONNX Runtime (1024d)

数据集：~/workspace/fashion_images/ (1811张)
评测采样：前300张
类别：按文件名前缀分组

指标：Recall@K, Precision@K, NDCG@K (K=1,5,10,20)
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

# Force flush all output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Set proxy for any model downloads
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# ========== CONFIG ==========
IMAGE_DIR = Path("/home/floating/workspace/jina-clip-v2/test_images")
NUM_SAMPLES = 300
RESULTS_DIR = Path("/home/floating/workspace/clip-exp/results")
RESULTS_DIR.mkdir(exist_ok=True)

# ========== DATASET ==========
def load_dataset():
    """Load images and assign categories by filename prefix."""
    images = sorted([f for f in os.listdir(IMAGE_DIR) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    images = images[:NUM_SAMPLES]
    
    # Category by filename prefix (before last _N)
    categories = {}
    for fname in images:
        # e.g. "pdf_img_p10_12.jpeg" -> "pdf_img_p10"
        # e.g. "dress_1.jpg" -> "dress"
        name = os.path.splitext(fname)[0]
        # Split by _ and remove trailing numbers
        parts = name.rsplit('_', 1)
        if len(parts) > 1 and parts[1].isdigit():
            cat = parts[0]
        else:
            cat = name
        categories[fname] = cat
    
    print(f"Dataset: {len(images)} images, {len(set(categories.values()))} categories")
    cat_counts = defaultdict(int)
    for c in categories.values():
        cat_counts[c] += 1
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {cnt}")
    if len(cat_counts) > 10:
        print(f"  ... and {len(cat_counts)-10} more categories")
    
    return images, categories

# ========== METRICS ==========
def compute_metrics(sim_matrix, categories, image_list, ks=[1, 5, 10, 20]):
    """Compute Recall@K, Precision@K, NDCG@K for image-to-image retrieval."""
    n = len(image_list)
    # Build category index
    cat_to_indices = defaultdict(list)
    for i, fname in enumerate(image_list):
        cat_to_indices[categories[fname]].append(i)
    
    metrics = {}
    for k in ks:
        recalls = []
        precisions = []
        ndcgs = []
        
        for i in range(n):
            query_cat = categories[image_list[i]]
            # Get top-K most similar (excluding self)
            sims = sim_matrix[i].copy()
            sims[i] = -float('inf')  # exclude self
            topk_indices = np.argsort(sims)[::-1][:k]
            
            # Relevance: 1 if same category, 0 otherwise
            relevances = np.array([1.0 if categories[image_list[j]] == query_cat else 0.0 
                                   for j in topk_indices])
            
            # Total relevant items (excluding self)
            total_relevant = len(cat_to_indices[query_cat]) - 1
            if total_relevant == 0:
                continue
            
            # Recall@K
            recalls.append(np.sum(relevances) / total_relevant)
            
            # Precision@K
            precisions.append(np.mean(relevances))
            
            # NDCG@K
            dcg = np.sum(relevances / np.log2(np.arange(2, k + 2)))
            ideal_relevances = np.sort(relevances)[::-1]  # already sorted by construction
            # Actually, ideal is all 1s for min(total_relevant, k) positions
            ideal = np.zeros(k)
            ideal[:min(total_relevant, k)] = 1.0
            idcg = np.sum(ideal / np.log2(np.arange(2, k + 2)))
            ndcgs.append(dcg / idcg if idcg > 0 else 0.0)
        
        metrics[f'Recall@{k}'] = float(np.mean(recalls))
        metrics[f'P@{k}'] = float(np.mean(precisions))
        metrics[f'NDCG@{k}'] = float(np.mean(ndcgs))
    
    return metrics

# ========== MODEL LOADERS ==========

class FashionSigLIPModel:
    """Load via open_clip."""
    def __init__(self):
        import open_clip
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'hf-hub:Marqo/marqo-fashionSigLIP'
        )
        self.model.eval()
        self.dim = 768
        self.name = "FashionSigLIP"
    
    def encode_images(self, image_paths):
        embeddings = []
        for i, path in enumerate(image_paths):
            img = Image.open(path).convert('RGB')
            img_tensor = self.preprocess(img).unsqueeze(0)
            with torch.no_grad():
                features = self.model.encode_image(img_tensor)
                if isinstance(features, tuple):
                    features = features[0]
                features = F.normalize(features.float(), dim=-1)
            embeddings.append(features.cpu().numpy().flatten())
            if (i+1) % 50 == 0:
                print(f"    {self.name}: {i+1}/{len(image_paths)} encoded", flush=True)
        return np.array(embeddings)


class OpenAICLIPModel:
    """Load via transformers."""
    def __init__(self):
        from transformers import CLIPModel, CLIPProcessor
        self.model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
        self.processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
        self.model.eval()
        self.dim = 512
        self.name = "OpenAI-CLIP-ViT-B32"
    
    def encode_images(self, image_paths):
        embeddings = []
        for i, path in enumerate(image_paths):
            img = Image.open(path).convert('RGB')
            inputs = self.processor(images=img, return_tensors="pt")
            with torch.no_grad():
                out = self.model.get_image_features(**inputs)
                # transformers 5.x returns BaseModelOutputWithPooling
                # projected features are in pooler_output
                if isinstance(out, torch.Tensor):
                    features = out
                elif hasattr(out, 'pooler_output'):
                    features = out.pooler_output
                elif hasattr(out, 'last_hidden_state'):
                    features = out.last_hidden_state[:, 0, :]
                else:
                    features = out[0]
                features = F.normalize(features.float(), dim=-1)
            embeddings.append(features.cpu().numpy().flatten())
            if (i+1) % 50 == 0:
                print(f"    {self.name}: {i+1}/{len(image_paths)} encoded", flush=True)
        return np.array(embeddings)


class FashionCLIPModel:
    """Load via transformers."""
    def __init__(self):
        from transformers import CLIPModel, CLIPProcessor
        self.model = CLIPModel.from_pretrained('patrickjohncyh/fashion-clip', local_files_only=True)
        self.processor = CLIPProcessor.from_pretrained('patrickjohncyh/fashion-clip', local_files_only=True)
        self.model.eval()
        self.dim = 512
        self.name = "FashionCLIP"
    
    def encode_images(self, image_paths):
        embeddings = []
        for i, path in enumerate(image_paths):
            img = Image.open(path).convert('RGB')
            inputs = self.processor(images=img, return_tensors="pt")
            with torch.no_grad():
                out = self.model.get_image_features(**inputs)
                if isinstance(out, torch.Tensor):
                    features = out
                elif hasattr(out, 'pooler_output'):
                    features = out.pooler_output
                elif hasattr(out, 'last_hidden_state'):
                    features = out.last_hidden_state[:, 0, :]
                else:
                    features = out[0]
                features = F.normalize(features.float(), dim=-1)
            embeddings.append(features.cpu().numpy().flatten())
            if (i+1) % 50 == 0:
                print(f"    {self.name}: {i+1}/{len(image_paths)} encoded", flush=True)
        return np.array(embeddings)


class JinaCLIPV2Model:
    """Load via ONNX Runtime (avoids transformers 5.x incompatibility)."""
    def __init__(self):
        import onnxruntime as ort
        model_path = "/home/floating/.cache/modelscope/jinaai/jina-clip-v2/onnx/model_quantized.onnx"
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 4
        self.session = ort.InferenceSession(model_path, opts)
        self.dim = 1024
        self.name = "jina-clip-v2"
    
    def encode_images(self, image_paths):
        mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32).reshape(3, 1, 1)
        std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32).reshape(3, 1, 1)
        embeddings = []
        for i, path in enumerate(image_paths):
            img = Image.open(path).convert('RGB').resize((512, 512), Image.LANCZOS)
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = img_array.transpose(2, 0, 1)
            img_array = (img_array - mean) / std
            img_array = img_array[np.newaxis, :, :, :].astype(np.float32)
            input_ids = np.zeros((1, 1), dtype=np.int64)
            outputs = self.session.run(
                ['l2norm_image_embeddings'],
                {'pixel_values': img_array, 'input_ids': input_ids}
            )
            embeddings.append(outputs[0].flatten())
            if (i+1) % 50 == 0:
                print(f"    {self.name}: {i+1}/{len(image_paths)} encoded", flush=True)
        return np.array(embeddings)


# ========== MAIN ==========
def run_benchmark():
    print("=" * 70)
    print("CLIP Model Benchmark: Multi-Model Comparison")
    print("=" * 70)
    
    # Load dataset
    images, categories = load_dataset()
    image_paths = [str(IMAGE_DIR / fname) for fname in images]
    
    # Models to test
    model_classes = [
        FashionSigLIPModel,
        OpenAICLIPModel,
        FashionCLIPModel,
        JinaCLIPV2Model,
    ]
    
    all_results = {}
    
    for model_cls in model_classes:
        print(f"\n{'='*60}")
        print(f"Loading {model_cls.__name__}...")
        start = time.time()
        try:
            model = model_cls()
            load_time = time.time() - start
            print(f"  Loaded in {load_time:.1f}s (dim={model.dim})")
        except Exception as e:
            print(f"  FAILED to load: {e}")
            continue
        
        # Encode all images
        print(f"  Encoding {len(image_paths)} images...")
        encode_start = time.time()
        try:
            embeddings = model.encode_images(image_paths)
            encode_time = time.time() - encode_start
            print(f"  Encoded in {encode_time:.1f}s ({len(image_paths)/encode_time:.2f} img/s)")
            print(f"  Embedding shape: {embeddings.shape}")
        except Exception as e:
            print(f"  FAILED to encode: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # Compute similarity matrix
        sim_matrix = embeddings @ embeddings.T  # already L2-normalized
        
        # Compute metrics
        metrics = compute_metrics(sim_matrix, categories, images)
        metrics['encode_time'] = encode_time
        metrics['load_time'] = load_time
        metrics['dim'] = model.dim
        metrics['throughput'] = len(image_paths) / encode_time
        
        # Category-level analysis
        cat_to_indices = defaultdict(list)
        for i, fname in enumerate(images):
            cat_to_indices[categories[fname]].append(i)
        
        cat_metrics = {}
        for cat, indices in cat_to_indices.items():
            if len(indices) < 2:
                continue
            # Compute intra-category similarity
            cat_embs = embeddings[indices]
            cat_sim = cat_embs @ cat_embs.T
            # Exclude self-similarity
            mask = ~np.eye(len(indices), dtype=bool)
            intra_sim = cat_sim[mask].mean()
            cat_metrics[cat] = {'count': len(indices), 'intra_sim': float(intra_sim)}
        
        # Inter-category similarity (sample-based)
        all_cats = list(cat_to_indices.keys())
        inter_sims = []
        for i in range(min(20, len(all_cats))):
            for j in range(i+1, min(20, len(all_cats))):
                ci, cj = all_cats[i], all_cats[j]
                ii, ij = cat_to_indices[ci], cat_to_indices[cj]
                # Sample max 10 from each
                si = ii[:10]
                sj = ij[:10]
                sim_block = embeddings[si] @ embeddings[sj].T
                inter_sims.append(float(sim_block.mean()))
        
        metrics['intra_sim_mean'] = float(np.mean([c['intra_sim'] for c in cat_metrics.values()]))
        metrics['inter_sim_mean'] = float(np.mean(inter_sims)) if inter_sims else 0
        metrics['sim_gap'] = metrics['intra_sim_mean'] - metrics['inter_sim_mean']
        
        all_results[model.name] = metrics
        
        print(f"\n  Results for {model.name}:")
        for k in [1, 5, 10, 20]:
            print(f"    R@{k}: {metrics[f'Recall@{k}']:.4f}  P@{k}: {metrics[f'P@{k}']:.4f}  NDCG@{k}: {metrics[f'NDCG@{k}']:.4f}")
        print(f"    Intra-sim: {metrics['intra_sim_mean']:.4f}  Inter-sim: {metrics['inter_sim_mean']:.4f}  Gap: {metrics['sim_gap']:.4f}")
        print(f"    Throughput: {metrics['throughput']:.2f} img/s")
        
        # Save embeddings
        emb_path = RESULTS_DIR / f"{model.name}_embeddings.npy"
        np.save(emb_path, embeddings)
        print(f"  Saved embeddings to {emb_path}")
        
        # Free memory
        del model, embeddings, sim_matrix
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # Save all results
    results_path = RESULTS_DIR / "multimodel_benchmark.json"
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {results_path}")
    
    # Print comparison table
    print("\n" + "=" * 90)
    print("📊 COMPARISON TABLE")
    print("=" * 90)
    header = f"{'Model':<25} {'Dim':>4} {'R@1':>7} {'R@5':>7} {'R@10':>7} {'R@20':>7} {'NDCG@5':>7} {'P@5':>7} {'Gap':>7} {'img/s':>7}"
    print(header)
    print("-" * 90)
    for name, m in all_results.items():
        row = f"{name:<25} {m['dim']:>4} {m['Recall@1']:>7.4f} {m['Recall@5']:>7.4f} {m['Recall@10']:>7.4f} {m['Recall@20']:>7.4f} {m['NDCG@5']:>7.4f} {m['P@5']:>7.4f} {m['sim_gap']:>7.4f} {m['throughput']:>7.2f}"
        print(row)
    
    return all_results


if __name__ == "__main__":
    results = run_benchmark()
