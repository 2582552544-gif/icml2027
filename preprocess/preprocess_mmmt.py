"""
MM-MT 数据预处理 Pipeline（对齐论文 Appendix C）

论文: Geometric Pocket-Centric Protein Encoding for Polypharmacology-Guided Multi-Target Drug Design (ICML 2026)

输入: filtered_dual_target_data2.csv (79,514 行)
输出: filtered_final.csv (论文报告 75,921 行)

预处理步骤 (Appendix C):
  1. SMILES 标准化 + token 长度过滤 [34, 74]
  2. 靶点过滤: AA 序列 > 1000 残基 或 核苷酸序列 > 6400 碱基
  3. 药理性质提取: 8 维属性向量 + min-max 归一化
  4. 同源性过滤: 与 6 个测试蛋白序列同一性 > 40% 的训练样本排除

测试蛋白 (Appendix D, Table 4):
  Tumour:        MEK1 (P15056),  mTOR (P62942)
  COVID-19:      Mpro (P0DTD1),  Epro (P0DTC4)
  Schizophrenia: TAAR1 (P04899), 5HT2C (P28335)
"""

import modal

app = modal.App("mmmt-preprocess")
volume = modal.Volume.from_name("drug-design-data")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "pandas",
        "rdkit-pypi",
        "numpy",
        "biopython",
        "requests",
        "tqdm",
    )
)

MOUNT = "/data"
REPO = f"{MOUNT}/repos/MM-MT"
OUTPUT = f"{REPO}/preprocess_output"

TEST_PROTEINS = {
    "P15056": "MEK1",
    "P62942": "mTOR",
    "P0DTD1": "Mpro",
    "P0DTC4": "Epro",
    "P04899": "TAAR1",
    "P28335": "5HT2C",
}

PROPERTY_RANGES = {
    "MW":   (0, 500),
    "HBD":  (0, 5),
    "HBA":  (0, 5),
    "RotB": (0, 8),
    "LogP": (-2, 4),
    "NumR": (0, 4),
    "MaxR": (3, 8),
    "NumA": (0, 3),
}

NUM_WORKERS = 8


# ── 顶层函数供 multiprocessing 序列化 ──────────────────────────

def _standardize_and_filter(smi):
    """SMILES 标准化 + token 长度过滤 [34, 74]（与仓库 1screenpretraindatafromZINC15.py 一致）"""
    import re
    from rdkit import Chem
    _tok_re = re.compile(
        r"(\[[^\]]+]|<|Br?|Cl?|N|O|S|P|F|I|b|c|n|o|s|p"
        r"|\(|\)|\.|=|#|-|\+|\\\\|\/|:|~|@|\?|>|\*|\$|\%[0-9]{2}|[0-9])"
    )
    try:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None
        mol = Chem.RemoveHs(mol)
        std = Chem.MolToSmiles(mol, isomericSmiles=False, canonical=True)
        tlen = len(_tok_re.findall(std))
        if 34 <= tlen <= 74:
            return std
    except Exception:
        pass
    return None


def _compute_properties(smi):
    """计算 8 维药理性质（与仓库 2pretrainedsmiles_properties.py 一致）"""
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    _amino = Chem.MolFromSmarts("[NX3;H2]")
    try:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None
        mw = Descriptors.MolWt(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        rotb = rdMolDescriptors.CalcNumRotatableBonds(mol)
        logp = Descriptors.MolLogP(mol)
        ri = mol.GetRingInfo()
        num_rings = ri.NumRings()
        max_ring = max((len(r) for r in ri.AtomRings()), default=0)
        num_amino = len(mol.GetSubstructMatches(_amino))
        return [mw, hbd, hba, rotb, logp, num_rings, max_ring, num_amino]
    except Exception:
        return None


def _check_homology_one(args):
    """检查单个训练蛋白是否与任一测试蛋白同源 >40%（BioPython globalxx）"""
    from Bio import pairwise2
    uid, train_seq, test_seqs_items = args
    if not train_seq:
        return None
    s1 = train_seq[:500]
    for _test_uid, test_seq in test_seqs_items:
        if not test_seq:
            continue
        s2 = test_seq[:500]
        score = pairwise2.align.globalxx(s1, s2, score_only=True)
        identity = score / max(len(s1), len(s2))
        if identity > 0.40:
            return uid
    return None


def _fetch_one_seq(uid):
    """从 UniProt 获取单个蛋白的氨基酸序列"""
    import requests
    url = f"https://rest.uniprot.org/uniprotkb/{uid}.fasta"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            return uid, "".join(lines[1:])
    except Exception:
        pass
    return uid, None


# ── 主函数 ─────────────────────────────────────────────────────

@app.function(image=image, volumes={MOUNT: volume}, timeout=1800, cpu=NUM_WORKERS)
def preprocess():
    import ast
    import os
    import time
    import zipfile
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

    import numpy as np
    import pandas as pd
    from tqdm import tqdm

    t0 = time.time()
    os.makedirs(OUTPUT, exist_ok=True)

    # ================================================================
    # Step 0: 解压 multidata.zip
    # ================================================================
    multidata_dir = f"{REPO}/multidata"
    if not os.path.isdir(multidata_dir):
        zip_path = f"{REPO}/data/multidata.zip"
        print(f"[Step 0] 解压 {zip_path} ...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(REPO)
        print(f"  → {multidata_dir}")
    else:
        print(f"[Step 0] multidata/ 已存在，跳过")

    csv_path = f"{multidata_dir}/filtered_dual_target_data2.csv"
    df = pd.read_csv(csv_path)
    n_orig = len(df)
    print(f"\n[原始数据] {n_orig} 行, 列: {df.columns.tolist()}")

    # ================================================================
    # Step 1: SMILES 标准化 + token 长度过滤 [34, 74]  ── 单进程（rdkit 不兼容 fork）
    # ================================================================
    print(f"\n[Step 1] SMILES 标准化 + token 过滤 [34, 74] ...")
    t1 = time.time()

    results = [_standardize_and_filter(s) for s in tqdm(df["SMILES"], desc="  SMILES")]

    df["SMILES_std"] = results
    n_before = len(df)
    df = df[df["SMILES_std"].notna()].reset_index(drop=True)
    removed_s1 = n_before - len(df)
    print(f"  → {len(df)} 行 (删除 {removed_s1}) [{time.time()-t1:.1f}s]")

    # ================================================================
    # Step 2: 靶点过滤 — 核苷酸 > 6400
    # CSV 名为 "filtered_dual_target_data2" — 靶点长度过滤大部分已做过
    # 这里仅复查核苷酸序列 ≤ 6400 (模型 max_len)
    # AA > 1000 在 Step 4 用真实 UniProt 序列长度过滤（nuc//3 会严重高估）
    # ================================================================
    print("\n[Step 2] 靶点过滤: 核苷酸 ≤ 6400 ...")
    t2 = time.time()

    def _count_tokens_fast(s):
        if not isinstance(s, str) or len(s) < 3:
            return 0
        return s.count(",") + 1

    nuc1 = df["Target1_Encoded_Gene_Seq"].apply(_count_tokens_fast)
    nuc2 = df["Target2_Encoded_Gene_Seq"].apply(_count_tokens_fast)
    keep = (nuc1 <= 6400) & (nuc2 <= 6400)

    n_before = len(df)
    df = df[keep].reset_index(drop=True)
    removed_s2 = n_before - len(df)
    print(f"  → {len(df)} 行 (删除 {removed_s2}) [{time.time()-t2:.1f}s]")

    # ================================================================
    # Step 3: 8 维药理性质  ── 单进程（rdkit 不兼容 fork）
    # ================================================================
    print(f"\n[Step 3] 计算 8 维药理性质 ...")
    t3 = time.time()

    props_list = [_compute_properties(s) for s in tqdm(df["SMILES_std"], desc="  属性")]

    prop_cols = ["MW", "HBD", "HBA", "RotB", "LogP", "NumR", "MaxR", "NumA"]
    props_arr = [p if p else [-1]*8 for p in props_list]
    props_df = pd.DataFrame(props_arr, columns=prop_cols)
    df = pd.concat([df.reset_index(drop=True), props_df], axis=1)

    n_before = len(df)
    df = df[df["MW"] >= 0].reset_index(drop=True)
    removed_s3 = n_before - len(df)

    for col, (lo, hi) in PROPERTY_RANGES.items():
        df[f"{col}_norm"] = df[col].clip(lo, hi).sub(lo).div(hi - lo)

    print(f"  → {len(df)} 行 (删除 {removed_s3}) [{time.time()-t3:.1f}s]")

    # ================================================================
    # Step 4: 同源性过滤 — sequence identity > 40%
    # ================================================================
    print("\n[Step 4] 同源性过滤 (>40% seq identity vs test proteins) ...")
    t4 = time.time()

    all_targets = set(df["Target1_Uniprot"].unique()) | set(df["Target2_Uniprot"].unique())
    training_targets = sorted(all_targets - set(TEST_PROTEINS.keys()))
    print(f"  训练蛋白: {len(training_targets)}, 测试蛋白: {len(TEST_PROTEINS)}")

    # 4a. UniProt 序列获取 ── 多线程并发
    targets_to_fetch = all_targets | set(TEST_PROTEINS.keys())
    seq_cache_path = f"{OUTPUT}/uniprot_sequences.txt"
    seq_map = {}

    if os.path.exists(seq_cache_path):
        with open(seq_cache_path) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    seq_map[parts[0]] = parts[1]
        print(f"  缓存命中: {len(seq_map)} 条")

    missing = sorted(targets_to_fetch - set(seq_map.keys()))
    if missing:
        print(f"  并发获取 {len(missing)} 条 UniProt 序列 (32 threads) ...")
        with ThreadPoolExecutor(max_workers=32) as pool:
            for uid, seq in tqdm(pool.map(_fetch_one_seq, missing),
                                 total=len(missing), desc="  UniProt"):
                if seq:
                    seq_map[uid] = seq
        with open(seq_cache_path, "w") as f:
            for uid, seq in sorted(seq_map.items()):
                f.write(f"{uid}\t{seq}\n")
        print(f"  缓存更新: {len(seq_map)} 条")

    # 4b. AA > 1000 过滤（用真实 UniProt 序列长度）
    long_aa_proteins = {uid for uid, seq in seq_map.items() if len(seq) > 1000}
    if long_aa_proteins:
        n_before = len(df)
        mask_aa = ~(df["Target1_Uniprot"].isin(long_aa_proteins)
                    | df["Target2_Uniprot"].isin(long_aa_proteins))
        df = df[mask_aa].reset_index(drop=True)
        removed_aa = n_before - len(df)
        all_targets = set(df["Target1_Uniprot"].unique()) | set(df["Target2_Uniprot"].unique())
        training_targets = sorted(all_targets - set(TEST_PROTEINS.keys()))
        print(f"  AA > 1000 过滤: 删除 {removed_aa} 行 ({len(long_aa_proteins)} 个长蛋白)")
    else:
        removed_aa = 0

    # 4c. 同源性检测 ── 多进程并行
    test_seqs_items = [(uid, seq_map.get(uid, "")) for uid in TEST_PROTEINS]
    tasks = [(uid, seq_map.get(uid, ""), test_seqs_items) for uid in training_targets]

    print(f"  并行同源性比对 ({NUM_WORKERS} workers, {len(tasks)} 蛋白 × 6 测试蛋白) ...")
    homologous_proteins = set()
    import multiprocessing
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=NUM_WORKERS, mp_context=ctx) as pool:
        for result in tqdm(pool.map(_check_homology_one, tasks, chunksize=16),
                           total=len(tasks), desc="  同源性"):
            if result is not None:
                homologous_proteins.add(result)

    print(f"  同源蛋白 (>40%): {len(homologous_proteins)} 个")

    # 4c. 过滤
    n_before = len(df)
    mask = ~(df["Target1_Uniprot"].isin(homologous_proteins)
             | df["Target2_Uniprot"].isin(homologous_proteins))
    df = df[mask].reset_index(drop=True)
    removed_s4 = n_before - len(df)
    print(f"  → {len(df)} 行 (删除 {removed_s4}) [{time.time()-t4:.1f}s]")

    # ================================================================
    # 输出
    # ================================================================
    remaining_targets = set(df["Target1_Uniprot"].unique()) | set(df["Target2_Uniprot"].unique())
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"预处理完成  [{elapsed:.0f}s]")
    print(f"{'=' * 60}")
    print(f"  最终样本数: {len(df):,} (论文: 75,921)")
    print(f"  最终蛋白数: {len(remaining_targets):,} (论文: 1,305)")
    print(f"  差异: 样本 {len(df)-75921:+,}, 蛋白 {len(remaining_targets)-1305:+,}")

    # 保存
    out_cols = ["SMILES_std", "Target1_Uniprot", "Target1_Encoded_Gene_Seq",
                "Target2_Uniprot", "Target2_Encoded_Gene_Seq"]
    df[out_cols].to_csv(f"{OUTPUT}/filtered_final.csv", index=False)

    norm_cols = [f"{c}_norm" for c in prop_cols]
    df[prop_cols + norm_cols].to_csv(f"{OUTPUT}/filtered_final_mol_8properties.txt",
                                     sep="\t", index=False)

    with open(f"{OUTPUT}/homologous_proteins.txt", "w") as f:
        for uid in sorted(homologous_proteins):
            f.write(f"{uid}\t{TEST_PROTEINS.get(uid, '')}\n")

    with open(f"{OUTPUT}/preprocess_log.txt", "w") as f:
        f.write(f"MM-MT Preprocessing Log (Appendix C)\n{'='*50}\n")
        f.write(f"原始: {n_orig}\n")
        f.write(f"Step 1 (SMILES token [34,74]): -{removed_s1}\n")
        f.write(f"Step 2 (AA≤1000, nuc≤6400):   -{removed_s2}\n")
        f.write(f"Step 3 (无效属性):              -{removed_s3}\n")
        f.write(f"Step 4a (AA>1000):               -{removed_aa} ({len(long_aa_proteins)} 蛋白)\n")
        f.write(f"Step 4b (同源性>40%):            -{removed_s4} ({len(homologous_proteins)} 蛋白)\n")
        f.write(f"最终: {len(df)} 行, {len(remaining_targets)} 蛋白\n")
        f.write(f"论文: 75,921 行, 1,305 蛋白\n")
        f.write(f"耗时: {elapsed:.0f}s\n")

    volume.commit()
    print(f"\n  已保存至 {OUTPUT}/ ✅")


@app.local_entrypoint()
def main():
    preprocess.remote()
