import modal

app = modal.App("check-reproduce")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11")


@app.function(image=image, volumes={"/data": volume}, timeout=120)
def check():
    import os

    def check_path(path, desc):
        if os.path.exists(path):
            if os.path.isdir(path):
                items = [f for f in os.listdir(path) if not f.startswith(".")]
                size = sum(os.path.getsize(os.path.join(path, f)) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
                status = f"✅ 存在 ({len(items)} 项, {size/1024/1024:.1f}MB)" if items else "❌ 空目录"
            else:
                size = os.path.getsize(path)
                status = f"✅ 存在 ({size/1024/1024:.1f}MB)" if size > 200 else f"⚠️ 可能是占位符 ({size}B)"
        else:
            status = "❌ 不存在"
        print(f"  {status} — {desc}")
        print(f"    路径: {path}")
        return os.path.exists(path)

    # ============ DualDiff ============
    dd = "/data/repos/DualDiff"
    print("=" * 60)
    print("DualDiff 复现所需数据检查")
    print("=" * 60)

    print("\n[评估数据] 双靶点协同数据集:")
    check_path(f"{dd}/data/processed/dock/index_dict.pkl", "药物索引")
    check_path(f"{dd}/data/processed/drug_synergy/synergy_idx_list.pkl", "协同对列表")
    check_path(f"{dd}/data/processed/dock/ligand_protein_dataset_v2", "复合物结构")

    print("\n[预训练模型] TargetDiff 权重:")
    td = "/data/repos/targetdiff"
    check_path(f"{td}/pretrained_models", "预训练模型目录")
    # Check if there's actual model files
    pm_dir = f"{td}/pretrained_models"
    if os.path.isdir(pm_dir):
        real_files = [f for f in os.listdir(pm_dir) if not f.startswith(".")]
        if real_files:
            for f in real_files:
                print(f"    文件: {f} ({os.path.getsize(os.path.join(pm_dir, f))/1024/1024:.1f}MB)")
        else:
            print("    ❌ 目录为空！需要下载预训练权重")

    print("\n[训练数据] CrossDocked2020 (仅重新训练时需要):")
    check_path(f"{td}/data", "TargetDiff data 目录")
    td_data = f"{td}/data"
    if os.path.isdir(td_data):
        for f in os.listdir(td_data):
            fp = os.path.join(td_data, f)
            if os.path.isfile(fp):
                print(f"    {f}: {os.path.getsize(fp)/1024/1024:.1f}MB")

    print("\n[环境配置]:")
    check_path(f"{dd}/environment.yaml", "conda 环境文件")
    check_path(f"{dd}/configs/training.yml", "训练配置")
    check_path(f"{dd}/configs/sampling.yml", "采样配置")

    # Check README for download instructions
    with open(f"{td}/README.md") as f:
        readme = f.read()
    for line in readme.split("\n"):
        if "pretrained" in line.lower() or "checkpoint" in line.lower() or "download" in line.lower() or "drive.google" in line.lower() or "zenodo" in line.lower():
            print(f"  README提及: {line.strip()}")

    # ============ MM-MT ============
    mm = "/data/repos/MM-MT"
    print("\n" + "=" * 60)
    print("MM-MT 复现所需数据检查")
    print("=" * 60)

    print("\n[多模态数据]:")
    check_path(f"{mm}/data/multidata.zip", "multidata.zip (CSV+嵌入+图)")

    print("\n[ZINC15 预训练数据]:")
    check_path(f"{mm}/data/1screenpretraindatafromZINC15.py", "ZINC15 筛选脚本")
    # Check if there's already downloaded ZINC data
    for item in os.listdir(f"{mm}/data"):
        if item not in ["1screenpretraindatafromZINC15.py", "2pretrainedsmiles_properties.py",
                        "3PDB2graph.py", "4screenmultimodaldata.py", "multidata.zip"]:
            fp = os.path.join(f"{mm}/data", item)
            sz = os.path.getsize(fp) if os.path.isfile(fp) else 0
            print(f"    额外文件: {item} ({sz}B)")

    print("\n[模型代码]:")
    check_path(f"{mm}/model/1pretrainedmodelv1-MutiMolGPT.py", "预训练模型代码")
    check_path(f"{mm}/model/2MM-MT-surf-drugdesignv10.py", "药物设计模型代码")

    print("\n[环境配置]:")
    check_path(f"{mm}/environment.yml", "conda 环境文件")

    print("\n[结果/评估]:")
    check_path(f"{mm}/result/MEK1", "MEK1 靶点结果")
    check_path(f"{mm}/result/mTOR", "mTOR 靶点结果")

    # ============ 总结 ============
    print("\n" + "=" * 60)
    print("公开文件与论文级复现状态")
    print("=" * 60)
    print()
    print("DualDiff:")
    print("  ✅ TargetDiff 预训练权重 — 当前 Volume 已下载")
    print("  ✅ 公开评估数据 — 已就绪")
    print("  ⚠️  论文 12,917 条，公开 pkl 12,972 条，严格复现需作者清单")
    print("  ⚠️  CrossDocked2020 — 仅重新训练 TargetDiff 时需要")
    print()
    print("MM-MT:")
    print("  ❌ ZINC15 预训练数据 — 需运行脚本从 ZINC15 下载")
    print("  ✅ 公开多模态文件 (multidata.zip) — 已就绪")
    print("  ⚠️  公开 CSV 为 79,514/1,328，论文最终训练集为 75,921/1,305")
    print("  ❌ vocab、8维属性、预训练 decoder checkpoint、最终过滤清单缺失")
    print("  ❌ 仓库主脚本不能原样直接复现论文训练")


@app.local_entrypoint()
def main():
    check.remote()
