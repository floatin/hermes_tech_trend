"""
Real B2B Extended Benchmark:
1. Three-model comparison: FashionSigLIP vs FashionCLIP vs jina-clip-v2
2. Per-section exploratory analysis (docx labels are REFERENCE ONLY)
3. Result-level fusion: alpha-weighted img_sim from multiple models
"""
import os
import sys

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
ONNX_MODEL_PATH = os.path.expanduser("~/.cache/modelscope/jinaai/jina-clip-v2/onnx/model.onnx")
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
    images = set()
    for gno, img in goods_to_img.items():
        path = os.path.join(IMAGE_DIR, img)
        if os.path.exists(path):
            images.add(img)
    return sorted(images)


# ─── Section mapping from docx (REFERENCE ONLY) ───
def parse_docx_sections():
    """Parse section labels from docx. These are subjective human judgments, NOT ground truth."""
    from lxml import etree
    from zipfile import ZipFile

    docx_path = '/home/floating/.hermes/cache/documents/doc_cb1d18aea1cb_相似商品汇总_50个.docx'
    with ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml')

    root = etree.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs = root.findall('.//w:p', ns)

    current_section = None
    section_map = {}  # sequential query index -> section name
    query_idx = 0

    for p in paragraphs:
        texts = p.findall('.//w:t', ns)
        text = ''.join(t.text for t in texts if t.text).strip()

        if '一、效果更好' in text:
            current_section = '效果更好'
            query_idx = 0
            continue
        elif '二、效果相近' in text:
            current_section = '效果相近'
            query_idx = 0
            continue
        elif '三、效果欠缺' in text:
            current_section = '效果欠缺'
            query_idx = 0
            continue

        if current_section and '比较表' in text:
            section_map[query_idx] = current_section
            query_idx += 1

    return section_map


# ─── Model Loaders ───
def load_fashion_siglip():
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms('hf-hub:Marqo/marqo-fashionSigLIP')
    model.eval()
    return model, preprocess, "FashionSigLIP"


def load_fashion_clip():
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
    processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
    model.eval()
    return (model, processor), None, "FashionCLIP"


def load_jina_clip_v2():
    """Load jina-clip-v2 via ONNX runtime (unified model)"""
    import onnxruntime as ort

    session = ort.InferenceSession(ONNX_MODEL_PATH, providers=['CPUExecutionProvider'])

    # jina-clip-v2: pixel_values is 512x512, CLIP normalization
    from torchvision import transforms
    preprocess = transforms.Compose([
        transforms.Resize((512, 512), interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.48145466, 0.4578275, 0.40821073],
                           std=[0.26862954, 0.26130258, 0.27577711]),
    ])

    return session, preprocess, "jina-clip-v2"


# ─── Encoding Functions ───
def encode_images_siglip(model, preprocess, image_paths, batch_size=16):
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
                images.append(preprocess(Image.new('RGB', (224, 224))))
        batch = torch.stack(images)
        with torch.no_grad():
            features = model.encode_image(batch, normalize=True)
        all_embeds.append(features.cpu().numpy())
        if (i + batch_size) % 100 < batch_size:
            print(f"  SigLIP: {min(i+batch_size, total)}/{total}")
    return np.vstack(all_embeds)


def encode_images_fclip(model_processor, _, image_paths, batch_size=16):
    model, processor = model_processor
    all_embeds = []
    total = len(image_paths)
    for i in range(0, total, batch_size):
        batch_paths = image_paths[i:i+batch_size]
        images = []
        for p in batch_paths:
            try:
                images.append(Image.open(p).convert('RGB'))
            except Exception as e:
                images.append(Image.new('RGB', (224, 224)))
        inputs = processor(images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            features = model.get_image_features(inputs['pixel_values'])
            if hasattr(features, 'pooler_output'):
                features = features.pooler_output
            features = features / features.norm(dim=-1, keepdim=True)
        all_embeds.append(features.cpu().numpy())
        if (i + batch_size) % 100 < batch_size:
            print(f"  FCLIP: {min(i+batch_size, total)}/{total}")
    return np.vstack(all_embeds)


def encode_images_jina(session, preprocess, image_paths, batch_size=4):
    """Encode images using jina-clip-v2 ONNX unified model.
    Input: pixel_values (B,3,512,512), Output: l2norm_image_embeddings (B,1024)
    Also needs dummy input_ids for text (just pass a padding token).
    """
    all_embeds = []
    total = len(image_paths)
    # Create dummy text input (1 token, pad)
    dummy_input_ids = np.array([[0]], dtype=np.int64)

    for i in range(0, total, batch_size):
        batch_paths = image_paths[i:i+batch_size]
        batch_tensors = []
        for p in batch_paths:
            try:
                img = preprocess(Image.open(p).convert('RGB'))
                batch_tensors.append(img.numpy())
            except Exception as e:
                batch_tensors.append(preprocess(Image.new('RGB', (512, 512))).numpy())

        pixel_values = np.stack(batch_tensors).astype(np.float32)
        # Expand dummy input_ids to batch size
        input_ids = np.repeat(dummy_input_ids, len(batch_tensors), axis=0)

        outputs = session.run(
            ['l2norm_image_embeddings'],
            {'pixel_values': pixel_values, 'input_ids': input_ids}
        )

        embeds = outputs[0]  # Already L2-normalized
        all_embeds.append(embeds)

        if (i + batch_size) % 50 < batch_size:
            print(f"  jina-clip-v2: {min(i+batch_size, total)}/{total}")
    return np.vstack(all_embeds)


# ─── Evaluation ───
def evaluate_retrieval(query_embeds, gallery_embeds, query_goods, gallery_goods,
                       ground_truth, Ks=[1, 5, 10, 20], return_per_query=False):
    sim_matrix = query_embeds @ gallery_embeds.T

    results = {}
    per_query_results = {} if return_per_query else None

    for K in Ks:
        recalls, precisions, ndcgs = [], [], []

        for qi, qgno in enumerate(query_goods):
            sims = sim_matrix[qi].copy()
            top_indices = np.argsort(sims)[::-1][:K + 1]

            retrieved_goods = []
            for idx in top_indices:
                gno = gallery_goods[idx]
                if gno == qgno:
                    continue
                retrieved_goods.append(gno)
                if len(retrieved_goods) >= K:
                    break

            gt = ground_truth.get(qgno, set())
            if not gt:
                continue

            hits = sum(1 for g in retrieved_goods[:K] if g in gt)
            recall = hits / min(len(gt), K)
            precision = hits / K
            dcg = sum(1.0 / np.log2(i + 2) for i, g in enumerate(retrieved_goods[:K]) if g in gt)
            idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(gt), K)))
            ndcg = dcg / idcg if idcg > 0 else 0

            recalls.append(recall)
            precisions.append(precision)
            ndcgs.append(ndcg)

            if return_per_query:
                per_query_results[(qgno, K)] = {
                    'recall': recall, 'precision': precision, 'ndcg': ndcg
                }

        results[f'Recall@{K}'] = np.mean(recalls) if recalls else 0
        results[f'P@{K}'] = np.mean(precisions) if precisions else 0
        results[f'NDCG@{K}'] = np.mean(ndcgs) if ndcgs else 0

    if return_per_query:
        return results, per_query_results
    return results


# ─── Result-level Fusion ───
def evaluate_fusion(query_embeds_dict, gallery_embeds_dict, query_goods, gallery_goods,
                    ground_truth, alphas, Ks=[5, 10]):
    """
    Result-level fusion: weighted sum of similarity scores from multiple models.
    alpha: weight for first model (1-alpha for second model)
    """
    fusion_results = {}

    model_names = list(query_embeds_dict.keys())
    if len(model_names) < 2:
        return fusion_results

    for alpha in alphas:
        # Compute similarity matrices
        sim1 = query_embeds_dict[model_names[0]] @ gallery_embeds_dict[model_names[0]].T
        sim2 = query_embeds_dict[model_names[1]] @ gallery_embeds_dict[model_names[1]].T

        # Normalize each model's similarities to [0, 1] per query
        sim1_norm = (sim1 - sim1.min(axis=1, keepdims=True)) / (sim1.max(axis=1, keepdims=True) - sim1.min(axis=1, keepdims=True) + 1e-8)
        sim2_norm = (sim2 - sim2.min(axis=1, keepdims=True)) / (sim2.max(axis=1, keepdims=True) - sim2.min(axis=1, keepdims=True) + 1e-8)

        # Weighted fusion
        fused_sim = alpha * sim1_norm + (1 - alpha) * sim2_norm

        for K in Ks:
            recalls, precisions, ndcgs = [], [], []
            for qi, qgno in enumerate(query_goods):
                top_indices = np.argsort(fused_sim[qi])[::-1][:K + 1]
                retrieved_goods = []
                for idx in top_indices:
                    gno = gallery_goods[idx]
                    if gno == qgno:
                        continue
                    retrieved_goods.append(gno)
                    if len(retrieved_goods) >= K:
                        break

                gt = ground_truth.get(qgno, set())
                if not gt:
                    continue

                hits = sum(1 for g in retrieved_goods[:K] if g in gt)
                recall = hits / min(len(gt), K)
                precision = hits / K
                dcg = sum(1.0 / np.log2(i + 2) for i, g in enumerate(retrieved_goods[:K]) if g in gt)
                idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(gt), K)))
                ndcg = dcg / idcg if idcg > 0 else 0

                recalls.append(recall)
                precisions.append(precision)
                ndcgs.append(ndcg)

            key = f'alpha={alpha:.1f}'
            fusion_results[key] = {
                'alpha': alpha,
                f'Recall@{K}': np.mean(recalls) if recalls else 0,
                f'P@{K}': np.mean(precisions) if precisions else 0,
                f'NDCG@{K}': np.mean(ndcgs) if ndcgs else 0,
            }

    return fusion_results


def main():
    print("=" * 70)
    print("Real B2B Extended Benchmark: 3 Models + Fusion")
    print("=" * 70)

    # Load data
    goods_to_img, img_to_goods = load_mapping()
    eval_data = load_eval_data()
    all_images = get_all_unique_images(goods_to_img)
    print(f"\nGallery size: {len(all_images)} images")

    # Build gallery
    gallery_goods = []
    gallery_paths = []
    for img in all_images:
        gno = img_to_goods.get(img)
        if gno:
            gallery_goods.append(gno)
            gallery_paths.append(os.path.join(IMAGE_DIR, img))
    print(f"Gallery with goods_no: {len(gallery_goods)}")

    # Build queries and ground truth
    query_goods = []
    query_img_files = []
    ground_truth = {}

    for e in eval_data:
        qgno = e['query_goods_no']
        qimg = e['query_img']
        qpath = os.path.join(IMAGE_DIR, qimg)
        if not os.path.exists(qpath):
            continue
        similar_nos = set()
        for model_name, model_data in e['models'].items():
            similar_nos.update(model_data['similar_goods_nos'])
        if similar_nos:
            query_goods.append(qgno)
            query_img_files.append(qimg)
            ground_truth[qgno] = similar_nos

    print(f"Queries: {len(query_goods)}")
    print(f"Avg ground truth size: {np.mean([len(v) for v in ground_truth.values()]):.1f}")

    # Parse section labels (REFERENCE ONLY)
    try:
        section_map = parse_docx_sections()
        print(f"Section labels parsed: {len(section_map)} queries (REFERENCE ONLY, not ground truth)")
    except Exception as e:
        print(f"Warning: could not parse docx sections: {e}")
        section_map = {}

    query_paths = [os.path.join(IMAGE_DIR, f) for f in query_img_files]

    # ─── Model 1: FashionSigLIP ───
    print("\n" + "=" * 50)
    print("[1/3] Encoding with FashionSigLIP...")
    print("=" * 50)
    t0 = time.time()
    siglip_model, siglip_preprocess, _ = load_fashion_siglip()
    gallery_siglip = encode_images_siglip(siglip_model, siglip_preprocess, gallery_paths)
    query_siglip = encode_images_siglip(siglip_model, siglip_preprocess, query_paths)
    siglip_time = time.time() - t0
    print(f"SigLIP total time: {siglip_time:.1f}s")
    del siglip_model  # free memory

    # ─── Model 2: FashionCLIP ───
    print("\n" + "=" * 50)
    print("[2/3] Encoding with FashionCLIP...")
    print("=" * 50)
    t0 = time.time()
    fclip_model_processor, _, _ = load_fashion_clip()
    gallery_fclip = encode_images_fclip(fclip_model_processor, None, gallery_paths)
    query_fclip = encode_images_fclip(fclip_model_processor, None, query_paths)
    fclip_time = time.time() - t0
    print(f"FCLIP total time: {fclip_time:.1f}s")
    del fclip_model_processor

    # ─── Model 3: jina-clip-v2 ───
    print("\n" + "=" * 50)
    print("[3/3] Encoding with jina-clip-v2 (ONNX)...")
    print("=" * 50)
    t0 = time.time()
    jina_session, jina_preprocess, _ = load_jina_clip_v2()
    gallery_jina = encode_images_jina(jina_session, jina_preprocess, gallery_paths)
    query_jina = encode_images_jina(jina_session, jina_preprocess, query_paths)
    jina_time = time.time() - t0
    print(f"jina-clip-v2 total time: {jina_time:.1f}s")
    del jina_session

    # ─── Evaluate all 3 models ───
    print("\n" + "=" * 50)
    print("Evaluating 3 models...")
    print("=" * 50)

    siglip_results, siglip_per_q = evaluate_retrieval(
        query_siglip, gallery_siglip, query_goods, gallery_goods, ground_truth,
        return_per_query=True
    )
    siglip_results['total_time'] = siglip_time

    fclip_results, fclip_per_q = evaluate_retrieval(
        query_fclip, gallery_fclip, query_goods, gallery_goods, ground_truth,
        return_per_query=True
    )
    fclip_results['total_time'] = fclip_time

    jina_results, jina_per_q = evaluate_retrieval(
        query_jina, gallery_jina, query_goods, gallery_goods, ground_truth,
        return_per_query=True
    )
    jina_results['total_time'] = jina_time

    # ─── Print comparison table ───
    print("\n" + "=" * 70)
    print("RESULTS: 3-Model Comparison on Real B2B Product Images")
    print("=" * 70)
    print(f"{'Metric':<15} {'SigLIP':>10} {'FCLIP':>10} {'jina-v2':>10} {'Best':>10}")
    print("-" * 55)

    for metric in ['Recall@1', 'Recall@5', 'Recall@10', 'Recall@20',
                    'P@1', 'P@5', 'P@10', 'NDCG@5', 'NDCG@10']:
        sv = siglip_results.get(metric, 0)
        fv = fclip_results.get(metric, 0)
        jv = jina_results.get(metric, 0)
        vals = {'SigLIP': sv, 'FCLIP': fv, 'jina-v2': jv}
        best = max(vals, key=vals.get)
        print(f"{metric:<15} {sv:>10.4f} {fv:>10.4f} {jv:>10.4f} {best:>10}")

    print(f"{'Time(s)':<15} {siglip_time:>10.1f} {fclip_time:>10.1f} {jina_time:>10.1f}")

    # ─── Per-section analysis (REFERENCE ONLY) ───
    print("\n" + "=" * 50)
    print("Per-section analysis (docx labels - REFERENCE ONLY)")
    print("=" * 50)

    # Map query indices to sections
    query_section = {}
    for qi, qgno in enumerate(query_goods):
        if qi in section_map:
            query_section[qi] = section_map[qi]

    section_results = defaultdict(lambda: defaultdict(dict))
    for section_name in ['效果更好', '效果相近', '效果欠缺']:
        indices = [qi for qi, sec in query_section.items() if sec == section_name]
        if not indices:
            continue

        sec_q_goods = [query_goods[i] for i in indices]
        sec_gt = {qgno: ground_truth[qgno] for qgno in sec_q_goods}

        sec_siglip = evaluate_retrieval(
            query_siglip[indices], gallery_siglip, sec_q_goods, gallery_goods, sec_gt,
            Ks=[1, 5, 10]
        )
        sec_fclip = evaluate_retrieval(
            query_fclip[indices], gallery_fclip, sec_q_goods, gallery_goods, sec_gt,
            Ks=[1, 5, 10]
        )
        sec_jina = evaluate_retrieval(
            query_jina[indices], gallery_jina, sec_q_goods, gallery_goods, sec_gt,
            Ks=[1, 5, 10]
        )

        section_results[section_name]['FashionSigLIP'] = sec_siglip
        section_results[section_name]['FashionCLIP'] = sec_fclip
        section_results[section_name]['jina-clip-v2'] = sec_jina

        print(f"\n{section_name} ({len(indices)} queries):")
        print(f"  {'Metric':<12} {'SigLIP':>8} {'FCLIP':>8} {'jina-v2':>8} {'Best':>8}")
        for metric in ['Recall@1', 'Recall@5', 'Recall@10', 'NDCG@5']:
            sv = sec_siglip.get(metric, 0)
            fv = sec_fclip.get(metric, 0)
            jv = sec_jina.get(metric, 0)
            vals = {'SigLIP': sv, 'FCLIP': fv, 'jina-v2': jv}
            best = max(vals, key=vals.get)
            print(f"  {metric:<12} {sv:>8.4f} {fv:>8.4f} {jv:>8.4f} {best:>8}")

    # ─── Result-level Fusion ───
    print("\n" + "=" * 50)
    print("Result-level Fusion")
    print("=" * 50)

    all_fusion_results = {}

    # Fusion 1: SigLIP + FCLIP
    print("\n--- SigLIP + FCLIP Fusion ---")
    embeds_pair_1 = {
        'FashionSigLIP': (query_siglip, gallery_siglip),
        'FashionCLIP': (query_fclip, gallery_fclip),
    }
    fusion_1 = evaluate_fusion(
        {k: v[0] for k, v in embeds_pair_1.items()},
        {k: v[1] for k, v in embeds_pair_1.items()},
        query_goods, gallery_goods, ground_truth,
        alphas=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        Ks=[5, 10]
    )
    all_fusion_results['SigLIP+FCLIP'] = fusion_1
    print(f"  {'Alpha':<8} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for key in sorted(fusion_1.keys(), key=lambda x: fusion_1[x]['alpha']):
        r = fusion_1[key]
        print(f"  {r['alpha']:<8.1f} {r.get('Recall@5', 0):>8.4f} {r.get('Recall@10', 0):>8.4f} "
              f"{r.get('NDCG@5', 0):>8.4f} {r.get('NDCG@10', 0):>8.4f}")

    # Fusion 2: SigLIP + jina-clip-v2
    print("\n--- SigLIP + jina-clip-v2 Fusion ---")
    embeds_pair_2 = {
        'FashionSigLIP': (query_siglip, gallery_siglip),
        'jina-clip-v2': (query_jina, gallery_jina),
    }
    fusion_2 = evaluate_fusion(
        {k: v[0] for k, v in embeds_pair_2.items()},
        {k: v[1] for k, v in embeds_pair_2.items()},
        query_goods, gallery_goods, ground_truth,
        alphas=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        Ks=[5, 10]
    )
    all_fusion_results['SigLIP+jina-v2'] = fusion_2
    print(f"  {'Alpha':<8} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for key in sorted(fusion_2.keys(), key=lambda x: fusion_2[x]['alpha']):
        r = fusion_2[key]
        print(f"  {r['alpha']:<8.1f} {r.get('Recall@5', 0):>8.4f} {r.get('Recall@10', 0):>8.4f} "
              f"{r.get('NDCG@5', 0):>8.4f} {r.get('NDCG@10', 0):>8.4f}")

    # Fusion 3: FCLIP + jina-clip-v2
    print("\n--- FCLIP + jina-clip-v2 Fusion ---")
    embeds_pair_3 = {
        'FashionCLIP': (query_fclip, gallery_fclip),
        'jina-clip-v2': (query_jina, gallery_jina),
    }
    fusion_3 = evaluate_fusion(
        {k: v[0] for k, v in embeds_pair_3.items()},
        {k: v[1] for k, v in embeds_pair_3.items()},
        query_goods, gallery_goods, ground_truth,
        alphas=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        Ks=[5, 10]
    )
    all_fusion_results['FCLIP+jina-v2'] = fusion_3
    print(f"  {'Alpha':<8} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for key in sorted(fusion_3.keys(), key=lambda x: fusion_3[x]['alpha']):
        r = fusion_3[key]
        print(f"  {r['alpha']:<8.1f} {r.get('Recall@5', 0):>8.4f} {r.get('Recall@10', 0):>8.4f} "
              f"{r.get('NDCG@5', 0):>8.4f} {r.get('NDCG@10', 0):>8.4f}")

    # ─── Three-way fusion ───
    print("\n--- 3-way Fusion: SigLIP + FCLIP + jina-v2 ---")
    three_way_results = {}
    # Weight combinations for 3 models: w1 + w2 + w3 = 1.0
    weight_combos = [
        (0.5, 0.3, 0.2), (0.6, 0.2, 0.2), (0.4, 0.4, 0.2),
        (0.5, 0.2, 0.3), (0.4, 0.3, 0.3), (0.6, 0.3, 0.1),
        (0.7, 0.2, 0.1), (0.3, 0.3, 0.4), (0.8, 0.1, 0.1),
    ]

    sim_siglip = query_siglip @ gallery_siglip.T
    sim_fclip = query_fclip @ gallery_fclip.T
    sim_jina = query_jina @ gallery_jina.T

    # Normalize
    def norm_sim(s):
        return (s - s.min(axis=1, keepdims=True)) / (s.max(axis=1, keepdims=True) - s.min(axis=1, keepdims=True) + 1e-8)

    sim_siglip_n = norm_sim(sim_siglip)
    sim_fclip_n = norm_sim(sim_fclip)
    sim_jina_n = norm_sim(sim_jina)

    print(f"  {'Weights':<20} {'R@5':>8} {'R@10':>8} {'NDCG@5':>8} {'NDCG@10':>8}")
    for w1, w2, w3 in weight_combos:
        fused_sim = w1 * sim_siglip_n + w2 * sim_fclip_n + w3 * sim_jina_n
        for K in [5, 10]:
            recalls, ndcgs = [], []
            for qi, qgno in enumerate(query_goods):
                top_indices = np.argsort(fused_sim[qi])[::-1][:K + 1]
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
                dcg = sum(1.0 / np.log2(i + 2) for i, g in enumerate(retrieved[:K]) if g in gt)
                idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(gt), K)))
                ndcgs.append(dcg / idcg if idcg > 0 else 0)

            key = f'{w1:.1f}/{w2:.1f}/{w3:.1f}'
            if key not in three_way_results:
                three_way_results[key] = {'weights': (w1, w2, w3)}
            three_way_results[key][f'Recall@{K}'] = np.mean(recalls) if recalls else 0
            three_way_results[key][f'NDCG@{K}'] = np.mean(ndcgs) if ndcgs else 0

    for key in sorted(three_way_results.keys()):
        r = three_way_results[key]
        print(f"  {r['weights'][0]:.1f}/{r['weights'][1]:.1f}/{r['weights'][2]:.1f}"
              f"{'':>8} {r.get('Recall@5', 0):>8.4f} {r.get('Recall@10', 0):>8.4f} "
              f"{r.get('NDCG@5', 0):>8.4f} {r.get('NDCG@10', 0):>8.4f}")

    # ─── Save all results ───
    output = {
        'FashionSigLIP': siglip_results,
        'FashionCLIP': fclip_results,
        'jina-clip-v2': jina_results,
        'section_analysis': {k: dict(v) for k, v in section_results.items()},
        'fusion_results': all_fusion_results,
        'three_way_fusion': three_way_results,
        'meta': {
            'query_count': len(query_goods),
            'gallery_size': len(gallery_goods),
            'ground_truth_avg_size': float(np.mean([len(v) for v in ground_truth.values()])),
            'section_note': 'docx labels are REFERENCE ONLY, not evaluation criteria',
        }
    }

    output_path = os.path.join(OUTPUT_DIR, 'real_b2b_extended_benchmark.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved to {output_path}")

    # ─── Summary ───
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Single model best:")
    for metric in ['Recall@5', 'NDCG@5']:
        sv = siglip_results.get(metric, 0)
        fv = fclip_results.get(metric, 0)
        jv = jina_results.get(metric, 0)
        print(f"  {metric}: SigLIP={sv:.4f}  FCLIP={fv:.4f}  jina-v2={jv:.4f}")

    print("\nBest 2-way fusion:")
    for fusion_name, fusion_data in all_fusion_results.items():
        best_r5 = max(fusion_data.values(), key=lambda x: x.get('Recall@5', 0))
        print(f"  {fusion_name}: R@5={best_r5.get('Recall@5', 0):.4f} @ alpha={best_r5['alpha']:.1f}")

    print("\nBest 3-way fusion:")
    best_3way = max(three_way_results.values(), key=lambda x: x.get('Recall@5', 0))
    print(f"  Weights={best_3way['weights']}: R@5={best_3way.get('Recall@5', 0):.4f}")


if __name__ == '__main__':
    main()
