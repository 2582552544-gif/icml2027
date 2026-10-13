import modal

app = modal.App("drug-design-inspect")

volume = modal.Volume.from_name("drug-design-data")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("rdkit-pypi", "numpy")
)

MOUNT_PATH = "/data"


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
    timeout=300,
)
def inspect():
    import pickle
    import os
    import zipfile

    # ========== DualDiff ==========
    print("=" * 70)
    print("DualDiff 数据格式详解")
    print("=" * 70)

    dd = f"{MOUNT_PATH}/repos/DualDiff/data/processed"

    # 1. index_dict.pkl
    print("\n--- index_dict.pkl ---")
    with open(f"{dd}/dock/index_dict.pkl", "rb") as f:
        index_dict = pickle.load(f)
    print(f"类型: {type(index_dict)}")
    print(f"条目数: {len(index_dict)}")
    print(f"key 类型: {type(list(index_dict.keys())[0])}")
    print(f"value 类型: {type(list(index_dict.values())[0])}")
    print(f"\n前 5 条:")
    for i, (k, v) in enumerate(index_dict.items()):
        if i >= 5:
            break
        print(f"  [{k}] → {v}")
    print(f"\n最后 3 条:")
    items = list(index_dict.items())
    for k, v in items[-3:]:
        print(f"  [{k}] → {v}")

    # 2. synergy_idx_list.pkl
    print("\n--- synergy_idx_list.pkl ---")
    with open(f"{dd}/drug_synergy/synergy_idx_list.pkl", "rb") as f:
        synergy_list = pickle.load(f)
    print(f"类型: {type(synergy_list)}")
    print(f"条目数: {len(synergy_list)}")
    print(f"元素类型: {type(synergy_list[0])}")
    print(f"\n前 10 条:")
    for i, pair in enumerate(synergy_list[:10]):
        idx1, idx2 = pair
        smiles1 = index_dict.get(idx1, "?")
        smiles2 = index_dict.get(idx2, "?")
        print(f"  [{idx1}, {idx2}] → Drug1: {smiles1[:50]}... | Drug2: {smiles2[:50]}...")

    # 3. 一个复合物目录的结构
    print("\n--- 复合物目录示例 ---")
    dataset_dir = f"{dd}/dock/ligand_protein_dataset_v2"
    drugs = sorted(os.listdir(dataset_dir))[:3]
    for drug in drugs:
        drug_path = os.path.join(dataset_dir, drug)
        if not os.path.isdir(drug_path):
            continue
        targets = os.listdir(drug_path)
        print(f"\n  药物 SMILES: {drug[:60]}{'...' if len(drug) > 60 else ''}")
        print(f"  靶点数: {len(targets)}")
        for t in targets[:2]:
            t_path = os.path.join(drug_path, t)
            files = os.listdir(t_path)
            print(f"    靶点 UniProt: {t}")
            for f in sorted(files):
                fp = os.path.join(t_path, f)
                size = os.path.getsize(fp)
                print(f"      {f} ({size:,} bytes)")
                # Show first few lines of PDB
                if f.endswith(".pdb") and "pocket" in f:
                    with open(fp) as fh:
                        lines = fh.readlines()
                    print(f"        行数: {len(lines)}")
                    print(f"        前3行: {lines[0].strip()}")
                    print(f"                {lines[1].strip()}")
                    print(f"                {lines[2].strip()}")
                    atom_lines = [l for l in lines if l.startswith("ATOM")]
                    print(f"        ATOM 行数: {len(atom_lines)}")
                # Show SDF info
                if f.endswith(".sdf"):
                    from rdkit import Chem
                    mol = Chem.MolFromMolFile(fp)
                    if mol:
                        print(f"        原子数: {mol.GetNumAtoms()}")
                        print(f"        键数: {mol.GetNumBonds()}")
                        print(f"        SMILES: {Chem.MolToSmiles(mol)}")

    # ========== MM-MT ==========
    print("\n\n" + "=" * 70)
    print("MM-MT 数据格式详解")
    print("=" * 70)

    mm = f"{MOUNT_PATH}/repos/MM-MT"

    # Check multidata.zip contents
    multidata = f"{mm}/data/multidata.zip"
    if os.path.exists(multidata) and os.path.getsize(multidata) > 1000:
        print(f"\n--- multidata.zip ({os.path.getsize(multidata) / 1024 / 1024:.1f} MB) ---")
        with zipfile.ZipFile(multidata, "r") as z:
            names = z.namelist()
            print(f"文件数: {len(names)}")
            # Show directory structure
            dirs = set()
            exts = {}
            for n in names:
                parts = n.split("/")
                if len(parts) > 1:
                    dirs.add(parts[0])
                ext = n.rsplit(".", 1)[-1] if "." in n else "dir"
                exts[ext] = exts.get(ext, 0) + 1
            print(f"顶层目录: {sorted(dirs)[:10]}")
            print(f"文件类型分布: {exts}")
            print(f"\n前 20 个文件:")
            for n in names[:20]:
                info = z.getinfo(n)
                print(f"  {n} ({info.file_size:,} bytes)")

            # Read a sample file
            for n in names[:50]:
                if n.endswith(".csv") or n.endswith(".txt") or n.endswith(".smi"):
                    print(f"\n  示例文件内容 ({n}):")
                    with z.open(n) as f:
                        content = f.read().decode("utf-8", errors="replace")
                    lines = content.split("\n")
                    for line in lines[:5]:
                        print(f"    {line}")
                    print(f"    ... (共 {len(lines)} 行)")
                    break

    # Check result directory
    print("\n--- result/ 目录 ---")
    result_dir = f"{mm}/result"
    for target in sorted(os.listdir(result_dir)):
        t_path = os.path.join(result_dir, target)
        if os.path.isdir(t_path):
            files = os.listdir(t_path)
            print(f"\n  📁 {target}/ ({len(files)} files)")
            for f in sorted(files):
                fp = os.path.join(t_path, f)
                size = os.path.getsize(fp)
                print(f"    📄 {f} ({size:,} bytes)")

    # Read the scripts to understand data pipeline
    print("\n--- data/ 脚本分析 ---")
    for script in ["1screenpretraindatafromZINC15.py", "2pretrainedsmiles_properties.py",
                    "3PDB2graph.py", "4screenmultimodaldata.py"]:
        fp = os.path.join(mm, "data", script)
        if os.path.exists(fp):
            with open(fp) as f:
                content = f.read()
            print(f"\n  📄 {script} ({len(content)} chars)")
            # Extract imports and key comments
            lines = content.split("\n")
            for line in lines[:30]:
                if line.strip() and (line.startswith("import") or line.startswith("from") or line.startswith("#") or "=" in line):
                    print(f"    {line.strip()}")


@app.local_entrypoint()
def main():
    inspect.remote()
