"""Download TargetDiff pretrained checkpoint from Zenodo + HuggingFace."""
import modal

app = modal.App("download-targetdiff-ckpt")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "huggingface_hub", "requests"
).apt_install("wget")

MOUNT_PATH = "/data"


@app.function(image=image, volumes={MOUNT_PATH: volume}, timeout=1800)
def download():
    import subprocess
    import os

    ckpt_dir = f"{MOUNT_PATH}/repos/targetdiff/pretrained_models"
    os.makedirs(ckpt_dir, exist_ok=True)

    existing = [f for f in os.listdir(ckpt_dir)
                if not f.startswith(".") and os.path.getsize(os.path.join(ckpt_dir, f)) > 1000]
    if existing:
        print(f"[skip] Already have: {existing}")
        for f in existing:
            print(f"  {f}: {os.path.getsize(os.path.join(ckpt_dir, f))/1024/1024:.1f} MB")
        volume.commit()
        return

    # Method 1: Zenodo (DOI: 10.5281/zenodo.14041881)
    print("[1/2] Downloading from Zenodo (targetdiff_pretrained_models.tar.gz, ~57 MB)...")
    zenodo_url = "https://zenodo.org/records/14041881/files/targetdiff_pretrained_models.tar.gz"
    tar_path = f"{ckpt_dir}/targetdiff_pretrained_models.tar.gz"

    result = subprocess.run(
        ["wget", "-q", "--show-progress", "-O", tar_path, zenodo_url],
        capture_output=True, text=True, timeout=300,
    )
    print(f"  wget exit: {result.returncode}")

    if os.path.exists(tar_path) and os.path.getsize(tar_path) > 10000:
        print(f"  Downloaded: {os.path.getsize(tar_path)/1024/1024:.1f} MB")
        subprocess.run(["tar", "-xzf", tar_path, "-C", ckpt_dir, "--strip-components=1"],
                       check=False)
        os.remove(tar_path)
        print("  Extracted and cleaned up tar.gz")
    else:
        print("  Zenodo download failed, trying HuggingFace...")

    # Check if we got files
    files = [f for f in os.listdir(ckpt_dir) if not f.startswith(".") and os.path.getsize(os.path.join(ckpt_dir, f)) > 1000]
    if not files:
        # Method 2: HuggingFace (OneScience-Group/TargetDiff)
        print("\n[2/2] Downloading from HuggingFace (OneScience-Group/TargetDiff)...")
        from huggingface_hub import snapshot_download
        try:
            local_dir = snapshot_download(
                repo_id="OneScience-Group/TargetDiff",
                local_dir=f"{ckpt_dir}/_hf_tmp",
                allow_patterns=["*.pt", "*.pth", "weights/*"],
            )
            print(f"  Downloaded to: {local_dir}")
            # Move weight files to ckpt_dir
            for root, dirs, fnames in os.walk(local_dir):
                for fname in fnames:
                    if fname.endswith((".pt", ".pth")):
                        src = os.path.join(root, fname)
                        dst = os.path.join(ckpt_dir, fname)
                        os.rename(src, dst)
                        print(f"  Moved: {fname}")
        except Exception as e:
            print(f"  HuggingFace failed: {e}")

    # Final verification
    print("\n=== pretrained_models/ ===")
    total = 0
    for f in sorted(os.listdir(ckpt_dir)):
        fp = os.path.join(ckpt_dir, f)
        if os.path.isfile(fp) and not f.startswith("."):
            sz = os.path.getsize(fp)
            print(f"  ✅ {f}: {sz/1024/1024:.1f} MB")
            total += sz
        elif os.path.isdir(fp):
            for sf in sorted(os.listdir(fp)):
                sfp = os.path.join(fp, sf)
                if os.path.isfile(sfp):
                    sz = os.path.getsize(sfp)
                    print(f"  ✅ {f}/{sf}: {sz/1024/1024:.1f} MB")
                    total += sz

    if total > 1_000_000:
        print(f"\n✅ 总共 {total/1024/1024:.1f} MB 模型权重已下载")
    else:
        print("\n❌ 下载失败")

    volume.commit()


@app.local_entrypoint()
def main():
    download.remote()
