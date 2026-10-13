import modal

app = modal.App("drug-design-hf-download")

volume = modal.Volume.from_name("drug-design-data")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "git-lfs")
    .run_commands("git lfs install")
    .pip_install("huggingface_hub")
)

MOUNT_PATH = "/data"


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
    timeout=3600,
)
def download_hf_data():
    import subprocess
    import os

    # 1. Download DualDiff dataset from HuggingFace
    print("=" * 60)
    print("下载 DualDiff 数据集 (HuggingFace)")
    print("=" * 60)

    dd_path = f"{MOUNT_PATH}/repos/DualDiff"
    data_path = os.path.join(dd_path, "data")

    if os.path.isdir(data_path) and len(os.listdir(data_path)) > 2:
        print(f"[skip] data/ already exists with {len(os.listdir(data_path))} items")
    else:
        os.chdir(dd_path)
        print("[download] Fetching data.tar.gz from HuggingFace...")
        from huggingface_hub import hf_hub_download
        local_file = hf_hub_download(
            repo_id="zhouxiangxin/DualDiff",
            filename="data.tar.gz",
            repo_type="dataset",
            local_dir=dd_path,
        )
        print(f"[downloaded] {local_file}")

        # Check size
        size = os.path.getsize(local_file)
        print(f"[size] data.tar.gz = {size / 1024 / 1024:.1f} MB")

        # Extract
        print("[extract] tar -xzf data.tar.gz ...")
        subprocess.run(["tar", "-xzf", "data.tar.gz"], cwd=dd_path, check=True)
        print("[done] extracted")

        # Remove tar to save space
        os.remove(local_file)
        print("[cleanup] removed data.tar.gz")

    # 2. Download MM-MT multidata.zip (check if it's LFS pointer)
    print("\n" + "=" * 60)
    print("检查 MM-MT multidata.zip")
    print("=" * 60)

    mm_mt_path = f"{MOUNT_PATH}/repos/MM-MT"
    multidata = os.path.join(mm_mt_path, "data", "multidata.zip")
    if os.path.exists(multidata):
        size = os.path.getsize(multidata)
        print(f"[check] multidata.zip = {size} bytes")
        if size < 1000:
            with open(multidata, "r") as f:
                content = f.read()
            print(f"[warning] Likely a Git LFS pointer:\n{content}")
            # Try to pull LFS
            print("[lfs] Attempting git lfs pull...")
            result = subprocess.run(
                ["git", "lfs", "pull"],
                cwd=mm_mt_path,
                capture_output=True, text=True
            )
            print(f"  stdout: {result.stdout}")
            print(f"  stderr: {result.stderr}")
            new_size = os.path.getsize(multidata)
            print(f"[result] multidata.zip = {new_size} bytes after LFS pull")

    # 3. Verify everything
    print("\n" + "=" * 60)
    print("验证数据完整性")
    print("=" * 60)

    # DualDiff data
    dd_data = os.path.join(dd_path, "data")
    if os.path.isdir(dd_data):
        result = subprocess.run(["du", "-sh", dd_data], capture_output=True, text=True)
        print(f"\nDualDiff data/: {result.stdout.strip()}")

        processed = os.path.join(dd_data, "processed")
        if os.path.isdir(processed):
            for item in sorted(os.listdir(processed)):
                full = os.path.join(processed, item)
                if os.path.isdir(full):
                    sub = os.listdir(full)
                    print(f"  📁 processed/{item}/ ({len(sub)} items)")
                    for s in sorted(sub)[:5]:
                        sf = os.path.join(full, s)
                        if os.path.isdir(sf):
                            print(f"    📁 {s}/ ({len(os.listdir(sf))} items)")
                        else:
                            print(f"    📄 {s} ({os.path.getsize(sf):,} bytes)")
                else:
                    print(f"  📄 {item} ({os.path.getsize(full):,} bytes)")

        # Check key files
        for pkl in ["processed/dock/index_dict.pkl", "processed/drug_synergy/synergy_idx_list.pkl"]:
            fp = os.path.join(dd_data, pkl)
            if os.path.exists(fp):
                print(f"  ✅ {pkl} ({os.path.getsize(fp):,} bytes)")
            else:
                print(f"  ❌ {pkl} NOT FOUND")

        # Count drug-target complexes
        dataset_dir = os.path.join(dd_data, "processed", "dock", "ligand_protein_dataset_v2")
        if os.path.isdir(dataset_dir):
            drugs = os.listdir(dataset_dir)
            total_targets = 0
            for drug in drugs:
                dp = os.path.join(dataset_dir, drug)
                if os.path.isdir(dp):
                    total_targets += len(os.listdir(dp))
            print(f"\n  📊 药物数: {len(drugs)}")
            print(f"  📊 药物-靶点复合物数: {total_targets}")

    volume.commit()
    print("\n✅ 全部完成，volume 已 commit")


@app.local_entrypoint()
def main():
    download_hf_data.remote()
