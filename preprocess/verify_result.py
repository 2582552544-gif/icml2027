"""验证预处理结果是否与论文报告一致。"""

import modal

app = modal.App("mmmt-verify-preprocess")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11").pip_install("pandas")

MOUNT = "/data"
OUTPUT = f"{MOUNT}/repos/MM-MT/preprocess_output"


@app.function(image=image, volumes={MOUNT: volume}, timeout=120)
def verify():
    import os

    import pandas as pd

    print("=" * 60)
    print("验证预处理结果")
    print("=" * 60)

    # 检查输出文件
    for fname in ["filtered_final.csv", "filtered_final_mol_8properties.txt",
                   "homologous_proteins.txt", "preprocess_log.txt",
                   "uniprot_sequences.txt"]:
        path = f"{OUTPUT}/{fname}"
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"  {'✅' if exists else '❌'} {fname} ({size:,} bytes)")

    # 读取最终 CSV
    csv_path = f"{OUTPUT}/filtered_final.csv"
    if not os.path.exists(csv_path):
        print("\n❌ filtered_final.csv 不存在，请先运行 preprocess_mmmt.py")
        return

    df = pd.read_csv(csv_path)
    targets = set(df["Target1_Uniprot"].unique()) | set(df["Target2_Uniprot"].unique())

    print(f"\n--- 结果对比 ---")
    print(f"  {'指标':<20} {'实际':>10} {'论文':>10} {'差异':>10}")
    print(f"  {'-' * 50}")
    print(f"  {'样本数':<18} {len(df):>10,} {'75,921':>10} {len(df) - 75921:>+10,}")
    print(f"  {'蛋白数':<18} {len(targets):>10,} {'1,305':>10} {len(targets) - 1305:>+10,}")
    print(f"  {'唯一 SMILES':<14} {df['SMILES_std'].nunique():>10,}")

    # 检查测试蛋白不在数据中
    test_ids = {"P15056", "P62942", "P0DTD1", "P0DTC4", "P04899", "P28335"}
    leaked = targets & test_ids
    if leaked:
        print(f"\n  ⚠️  测试蛋白泄露: {leaked}")
    else:
        print(f"\n  ✅ 无测试蛋白泄露")

    # 读取属性文件
    props_path = f"{OUTPUT}/filtered_final_mol_8properties.txt"
    if os.path.exists(props_path):
        props = pd.read_csv(props_path, sep="\t")
        print(f"\n--- 属性统计 (归一化前) ---")
        for col in ["MW", "HBD", "HBA", "RotB", "LogP", "NumR", "MaxR", "NumA"]:
            if col in props.columns:
                print(f"  {col:<6} mean={props[col].mean():.2f}  "
                      f"min={props[col].min():.1f}  max={props[col].max():.1f}")

    # 读取 log
    log_path = f"{OUTPUT}/preprocess_log.txt"
    if os.path.exists(log_path):
        print(f"\n--- 过滤日志 ---")
        with open(log_path) as f:
            print(f.read())


@app.local_entrypoint()
def main():
    verify.remote()
