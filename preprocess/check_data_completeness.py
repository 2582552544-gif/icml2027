"""
复刻脚本4的逻辑：检查 CSV 中每行的蛋白是否有对应的 .npy 和 .pt 文件。
同时检查 SMILES token 长度 [34, 74]（脚本1）。
目标：找出从 79,514 → 75,921 的差异来源。
"""
import modal

app = modal.App("mmmt-completeness")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11").pip_install("pandas", "rdkit-pypi")

MOUNT = "/data"
REPO = f"{MOUNT}/repos/MM-MT"


@app.function(image=image, volumes={MOUNT: volume}, timeout=300, cpu=2)
def check():
    import os
    import re

    import pandas as pd

    multidata = f"{REPO}/multidata"
    csv_path = f"{multidata}/filtered_dual_target_data2.csv"
    emb_dir = f"{multidata}/prot_emb_data"
    stru_dir = f"{multidata}/stru_data"

    df = pd.read_csv(csv_path)
    print(f"原始 CSV: {len(df)} 行")

    # 列出实际存在的文件
    emb_files = {f.replace(".npy", "") for f in os.listdir(emb_dir) if f.endswith(".npy")}
    stru_files = set()
    for f in os.listdir(stru_dir):
        if f.endswith(".pt"):
            # alphafold_P00533_surf.pt → P00533
            uid = f.replace("alphafold_", "").replace("_surf.pt", "")
            stru_files.add(uid)

    print(f"蛋白嵌入 .npy: {len(emb_files)} 个")
    print(f"结构图 .pt:    {len(stru_files)} 个")

    # CSV 中所有蛋白
    all_targets = set(df["Target1_Uniprot"].unique()) | set(df["Target2_Uniprot"].unique())
    print(f"CSV 唯一蛋白:  {len(all_targets)} 个")

    # 检查缺失
    missing_emb = all_targets - emb_files
    missing_stru = all_targets - stru_files
    print(f"\n缺 .npy: {len(missing_emb)} 个 → {sorted(missing_emb)[:20]}")
    print(f"缺 .pt:  {len(missing_stru)} 个 → {sorted(missing_stru)[:20]}")

    # ── 过滤1：蛋白数据完整性（脚本4逻辑）──
    has_emb1 = df["Target1_Uniprot"].isin(emb_files)
    has_emb2 = df["Target2_Uniprot"].isin(emb_files)
    has_stru1 = df["Target1_Uniprot"].isin(stru_files)
    has_stru2 = df["Target2_Uniprot"].isin(stru_files)
    complete = has_emb1 & has_emb2 & has_stru1 & has_stru2

    removed_data = (~complete).sum()
    print(f"\n[过滤1] 蛋白数据完整性: 删除 {removed_data} 行 → {complete.sum()} 行")

    df_filtered = df[complete].reset_index(drop=True)

    # ── 过滤2：SMILES token 长度 [34, 74]（脚本1逻辑）──
    tok_re = re.compile(
        r"(\[[^\]]+]|<|Br?|Cl?|N|O|S|P|F|I|b|c|n|o|s|p"
        r"|\(|\)|\.|=|#|-|\+|\\\\|\/|:|~|@|\?|>|\*|\$|\%[0-9]{2}|[0-9])"
    )

    def token_len(smi):
        return len(tok_re.findall(str(smi)))

    tlen = df_filtered["SMILES"].apply(token_len)
    in_range = (tlen >= 34) & (tlen <= 74)
    removed_smiles = (~in_range).sum()
    print(f"[过滤2] SMILES token [34,74]: 删除 {removed_smiles} 行 → {in_range.sum()} 行")

    df_final = df_filtered[in_range].reset_index(drop=True)

    # ── 汇总 ──
    final_targets = set(df_final["Target1_Uniprot"].unique()) | set(df_final["Target2_Uniprot"].unique())
    print(f"\n{'='*50}")
    print(f"最终: {len(df_final)} 行, {len(final_targets)} 蛋白")
    print(f"论文: 75,921 行, 1,305 蛋白")
    print(f"差异: {len(df_final) - 75921:+,} 行, {len(final_targets) - 1305:+,} 蛋白")
    print(f"{'='*50}")

    # token 长度分布
    print(f"\nSMILES token 长度分布（过滤前）:")
    full_tlen = df["SMILES"].apply(token_len)
    print(f"  min={full_tlen.min()}, max={full_tlen.max()}, mean={full_tlen.mean():.1f}")
    print(f"  <34: {(full_tlen < 34).sum()}")
    print(f"  34-74: {((full_tlen >= 34) & (full_tlen <= 74)).sum()}")
    print(f"  >74: {(full_tlen > 74).sum()}")


@app.local_entrypoint()
def main():
    check.remote()
