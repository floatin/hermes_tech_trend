"""Quick fix: recompute 2-way fusion with correct K handling"""
import os
os.environ.setdefault('http_proxy', 'http://127.0.0.1:7890')
os.environ.setdefault('https_proxy', 'http://127.0.0.1:7890')
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

import json
import numpy as np
from pathlib import Path
from PIL import Image
import torch
import time

IMAGE_DIR = os.path.expanduser("~/workspace/clip-exp/real_images")
MAPPING_FILE = os.path.expanduser("~/workspace/clip-exp/results/goods_image_mapping.json")
EVAL_DATA_FILE = os.path.expanduser("~/workspace/clip-exp/results/real_evaluation_data.json")
ONNX_MODEL_PATH = os.path.expanduser("~/.cache/modelscope/jinaai/jina-clip-v2/onnx/model.onnx")
RESULTS_FILE = os.path.expanduser("~/workspace/clip-exp/results/real_b2b_extended_benchmark.json")
EMBED_DIR = os.path.expanduser("~/workspace/clip-exp/results/embeds")

def load_data():
    with open(MAPPING_FILE) as f:
        data = json.load(f)
    goods_to_img = data['goods_to_img']
    img_to_goods = data['img_to_goods']
    with open(EVAL_DATA_FILE) as f:
        eval_data = json.load(f)
    return goods_to_img, img_to_goods, eval_data

def build_gallery_and_queries(goods_to_img, img_to_goods, eval_data):
    all_images = sorted(set(
        img for gno, img in goods_to_img.items()
        if os.path.exists(os.path.join(IMAGE_DIR, img))
    ))
    gallery_goods, gallery_paths = [], []
    for img in all_images:
        gno = img_to_goods.get(img)
        if gno:
            gallery_goods.append(gno)
            gallery_paths.append(os.path.join(IMAGE_DIR, img))

    query_goods, query_img_files, ground_truth = [], [], {}
    for e in eval_data:
        qgno = e['query_goods_no']
        qimg = e['query_img']
        if not os.path.exists(os.path.join(IMAGE_DIR, qimg)):
            continue
        similar_nos = set()
        for model_name, model_data in e['models'].items():
            similar_nos.update(model_data['similar_goods_nos'])
        if similar_nos:
            query_goods.append(qgno)
            query_img_files.append(qimg)
            ground_truth[qgno] = similar_nos

    query_paths = [os.path.join(IMAGE_DIR, f) for f in query_img_files]
    return gallery_goods, gallery_paths, query_goods, query_paths, ground_truth

def eval_fusion_fixed(sim1, sim2, query_goods, gallery_goods, ground_truth, alphas, Ks=[5, 10]):
    """Fixed 2-way fusion: handle multiple Ks without overwriting"""
    def norm_sim(s):
        return (s - s.min(axis=1, keepdims=True)) / (s.max(axis=1, keepdims=True) - s.min(axis=1, keepdims=True) + 1e-8)

    sim1_n = norm_sim(sim1)
    sim2_n = norm_sim(sim2)

    fusion_results = {}
    for alpha in alphas:
        fused = alpha * sim1_n + (1 - alpha) * sim2_n
        key = f'alpha={alpha:.1f}'
        entry = {'alpha': alpha}

        for K in Ks:
            recalls, precisions, ndcgs = [], [], []
            for qi, qgno in enumerate(query_goods):
                top_indices = np.argsort(fused[qi])[::-1][:K + 1]
                retrieved = []
                for idx in top_indices:
                    gno = gallery_goods[idx]
                    if gno == qgno:
                        continue
                    retrieved.append(gno)
                    if len(retrieved) >= K:
                        break
                gt = ground_truth.get(qgno, set())
                if not gt:
                    continue
                hits = sum(1 for g in retrieved[:K] if g in gt)
                recalls.append(hits / min(len(gt), K))
                precisions.append(hits / K)
                dcg = sum(1.0 / np.log2(i + 2) for i, g in enumerate(retrieved[:K]) if g in gt)
                idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(gt), K)))
                ndcgs.append(dcg / idcg if idcg > 0 else 0)

            entry[f'Recall@{K}'] = float(np.mean(recalls)) if recalls else 0
            entry[f'P@{K}'] = float(np.mean(precisions)) if precisions else 0
            entry[f'NDCG@{K}'] = float(np.mean(ndcgs)) if ndcgs else 0

        fusion_results[key] = entry
    return fusion_results

def main():
    print("Loading data...")
    goods_to_img, img_to_goods, eval_data = load_data()
    gallery_goods, gallery_paths, query_goods, query_paths, ground_truth = \
        build_gallery_and_queries(goods_to_img, img_to_goods, eval_data)
    print(f"Gallery: {len(gallery_goods)}, Queries: {len(query_goods)}")

    # Check if cached embeds exist
    os.makedirs(EMBED_DIR, exist_ok=True)
    need_encode = not all(
        os.path.exists(os.path.join(EMBED_DIR, f))
        for f in ['gallery_siglip.npy', 'query_siglip.npy',
                   'gallery_fclip.npy', 'query_fclip.npy',
                   'gallery_jina.npy', 'query_jina.npy']
    )

    if need_encode:
        print("Encoding all 3 models (saving cache)...")
        # SigLIP
        import open_clip
        print("[1/3] FashionSigLIP...")
        t0 = time.time()
        model, _, preprocess = open_clip.create_model_and_transforms('hf-hub:Marqo/marqo-fashionSigLIP')
        model.eval()

        def enc_siglip(paths, batch_size=16):
            all_e = []
            for i in range(0, len(paths), batch_size):
                batch = [preprocess(Image.open(p).convert('RGB')) for p in paths[i:i+batch_size]]
                with torch.no_grad():
                    f = model.encode_image(torch.stack(batch), normalize=True)
                all_e.append(f.cpu().numpy())
                if (i + batch_size) % 100 < batch_size:
                    print(f"  SigLIP: {min(i+batch_size, len(paths))}/{len(paths)}")
            return np.vstack(all_e)

        gallery_siglip = enc_siglip(gallery_paths)
        query_siglip = enc_siglip(query_paths)
        np.save(os.path.join(EMBED_DIR, 'gallery_siglip.npy'), gallery_siglip)
        np.save(os.path.join(EMBED_DIR, 'query_siglip.npy'), query_siglip)
        print(f"  SigLIP done: {time.time()-t0:.1f}s")
        del model

        # FCLIP
        from transformers import CLIPModel, CLIPProcessor
        print("[2/3] FashionCLIP...")
        t0 = time.time()
        fmodel = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
        fproc = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
        fmodel.eval()

        def enc_fclip(paths, batch_size=16):
            all_e = []
            for i in range(0, len(paths), batch_size):
                imgs = [Image.open(p).convert('RGB') for p in paths[i:i+batch_size]]
                inputs = fproc(images=imgs, return_tensors="pt", padding=True)
                with torch.no_grad():
                    f = fmodel.get_image_features(inputs['pixel_values'])
                    if hasattr(f, 'pooler_output'):
                        f = f.pooler_output
                    f = f / f.norm(dim=-1, keepdim=True)
                all_e.append(f.cpu().numpy())
                if (i + batch_size) % 100 < batch_size:
                    print(f"  FCLIP: {min(i+batch_size, len(paths))}/{len(paths)}")
            return np.vstack(all_e)

        gallery_fclip = enc_fclip(gallery_paths)
        query_fclip = enc_fclip(query_paths)
        np.save(os.path.join(EMBED_DIR, 'gallery_fclip.npy'), gallery_fclip)
        np.save(os.path.join(EMBED_DIR, 'query_fclip.npy'), query_fclip)
        print(f"  FCLIP done: {time.time()-t0:.1f}s")
        del fmodel, fproc

        # jina-clip-v2 ONNX
        import onnxruntime as ort
        from torchvision import transforms
        print("[3/3] jina-clip-v2 ONNX...")
        t0 = time.time()
        session = ort.InferenceSession(ONNX_MODEL_PATH, providers=['CPUExecutionProvider'])
        jina_preprocess = transforms.Compose([
            transforms.Resize((512, 512), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.48145466, 0.4578275, 0.40821073],
                               std=[0.26862954, 0.26130258, 0.27577711]),
        ])

        def enc_jina(paths, batch_size=4):
            all_e = []
            dummy_ids = np.array([[0]], dtype=np.int64)
            for i in range(0, len(paths), batch_size):
                batch = []
                for p in paths[i:i+batch_size]:
                    try:
                        batch.append(jina_preprocess(Image.open(p).convert('RGB')).numpy())
                    except:
                        batch.append(jina_preprocess(Image.new('RGB', (512, 512))).numpy())
                pv = np.stack(batch).astype(np.float32)
                ids = np.repeat(dummy_ids, len(batch), axis=0)
                out = session.run(['l2norm_image_embeddings'], {'pixel_values': pv, 'input_ids': ids})
                all_e.append(out[0])
                if (i + batch_size) % 50 < batch_size:
                    print(f"  jina: {min(i+batch_size, len(paths))}/{len(paths)}")
            return np.vstack(all_e)

        gallery_jina = enc_jina(gallery_paths)
        query_jina = enc_jina(query_paths)
        np.save(os.path.join(EMBED_DIR, 'gallery_jina.npy'), gallery_jina)
        np.save(os.path.join(EMBED_DIR, 'query_jina.npy'), query_jina)
        print(f"  jina done: {time.time()-t0:.1f}s")
        del session
    else:
        print("Loading cached embeds...")
        gallery_siglip = np.load(os.path.join(EMBED_DIR, 'gallery_siglip.npy'))
        query_siglip = np.load(os.path.join(EMBED_DIR, 'query_siglip.npy'))
        gallery_fclip = np.load(os.path.join(EMBED_DIR, 'gallery_fclip.npy'))
        query_fclip = np.load(os.path.join(EMBED_DIR, 'query_fclip.npy'))
        gallery_jina = np.load(os.path.join(EMBED_DIR, 'gallery_jina.npy'))
        query_jina = np.load(os.path.join(EMBED_DIR, 'query_jina.npy'))
        print("All embeds loaded from cache")

    # Compute similarity matrices
    sim_siglip = query_siglip @ gallery_siglip.T
    sim_fclip = query_fclip @ gallery_fclip.T
    sim_jina = query_jina @ gallery_jina.T

    alphas = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    print("\n=== 2-way Fusion (FIXED) ===")
    all_fusion = {}

    print("\n--- SigLIP + FCLIP ---")
    f1 = eval_fusion_fixed(sim_siglip, sim_fclip, query_goods, gallery_goods, ground_truth, alphas)
    all_fusion['SigLIP+FCLIP'] = f1
    print(f"  {'Alpha':<8} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for key in sorted(f1.keys(), key=lambda x: f1[x]['alpha']):
        r = f1[key]
        print(f"  {r['alpha']:<8.1f} {r['Recall@5']:>8.4f} {r['Recall@10']:>8.4f} {r['NDCG@5']:>8.4f} {r['NDCG@10']:>8.4f}")

    print("\n--- SigLIP + jina-v2 ---")
    f2 = eval_fusion_fixed(sim_siglip, sim_jina, query_goods, gallery_goods, ground_truth, alphas)
    all_fusion['SigLIP+jina-v2'] = f2
    print(f"  {'Alpha':<8} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for key in sorted(f2.keys(), key=lambda x: f2[x]['alpha']):
        r = f2[key]
        print(f"  {r['alpha']:<8.1f} {r['Recall@5']:>8.4f} {r['Recall@10']:>8.4f} {r['NDCG@5']:>8.4f} {r['NDCG@10']:>8.4f}")

    print("\n--- FCLIP + jina-v2 ---")
    f3 = eval_fusion_fixed(sim_fclip, sim_jina, query_goods, gallery_goods, ground_truth, alphas)
    all_fusion['FCLIP+jina-v2'] = f3
    print(f"  {'Alpha':<8} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for key in sorted(f3.keys(), key=lambda x: f3[x]['alpha']):
        r = f3[key]
        print(f"  {r['alpha']:<8.1f} {r['Recall@5']:>8.4f} {r['Recall@10']:>8.4f} {r['NDCG@5']:>8.4f} {r['NDCG@10']:>8.4f}")

    # Update the JSON file with fixed fusion results
    with open(RESULTS_FILE) as f:
        full_results = json.load(f)

    full_results['fusion_results'] = all_fusion

    with open(RESULTS_FILE, 'w') as f:
        json.dump(full_results, f, indent=2, default=str)
    print(f"\nUpdated {RESULTS_FILE}")

    # Best fusion summary
    print("\n=== Best Fusion Summary ===")
    for name, data in all_fusion.items():
        best = max(data.values(), key=lambda x: x.get('NDCG@5', 0))
        print(f"  {name}: Best alpha={best['alpha']:.1f}, R@5={best['Recall@5']:.4f}, NDCG@5={best['NDCG@5']:.4f}")

if __name__ == '__main__':
    main()
