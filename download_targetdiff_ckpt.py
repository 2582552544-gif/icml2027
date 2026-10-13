"""Download TargetDiff pretrained checkpoint from Google Drive."""
import modal

app = modal.App("download-targetdiff-ckpt")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11").run_commands(
    "pip install gdown==5.2.0",
    "apt-get update && apt-get install -y wget curl",
)

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
        volume.commit()
        return

    # The Google Drive folder has these known files.
    # Folder: https://drive.google.com/drive/folders/1-ftaIrTXjWFhw3-0Twkrs5m0yX6CNarz
    # We use gdown with the folder URL as a positional argument (gdown v5 syntax).
    print("[download] Attempting gdown folder download...")
    result = subprocess.run(
        ["gdown",
         "https://drive.google.com/drive/folders/1-ftaIrTXjWFhw3-0Twkrs5m0yX6CNarz",
         "-O", ckpt_dir,
         "--folder", "--remaining-ok"],
        capture_output=True, text=True, timeout=600,
    )
    print(f"stdout: {result.stdout[-500:]}")
    print(f"stderr: {result.stderr[-500:]}")

    files = [f for f in os.listdir(ckpt_dir) if not f.startswith(".") and os.path.getsize(os.path.join(ckpt_dir, f)) > 100]
    if files:
        print(f"[success] gdown got {len(files)} files")
    else:
        # Fallback: use wget with cookies trick
        print("\n[fallback] Trying wget cookie method...")
        # For public shared folders, we can sometimes use the export link
        # First try the data folder which has lmdb + test set
        data_folder_id = "1j21cc7-97TedKh_El5E34yI8o5ckI7eK"
        subprocess.run(
            ["gdown",
             f"https://drive.google.com/drive/folders/{data_folder_id}",
             "-O", f"{MOUNT_PATH}/repos/targetdiff/data",
             "--folder", "--remaining-ok"],
            capture_output=True, text=True, timeout=600,
        )

    # Final check
    print("\n=== pretrained_models/ ===")
    all_ok = True
    for f in sorted(os.listdir(ckpt_dir)):
        fp = os.path.join(ckpt_dir, f)
        if os.path.isfile(fp) and not f.startswith("."):
            sz = os.path.getsize(fp)
            print(f"  {f}: {sz/1024/1024:.1f} MB")
            if sz < 1000:
                all_ok = False
                print(f"    ⚠️ Too small, likely failed")

    if not all_ok or not files:
        print("\n❌ 自动下载失败。Google Drive 限制了自动化访问。")
        print("需要手动下载：")
        print("  1. 浏览器打开 https://drive.google.com/drive/folders/1-ftaIrTXjWFhw3-0Twkrs5m0yX6CNarz")
        print("  2. 下载全部文件")
        print("  3. 上传到 Modal: modal volume put drug-design-data <local-file> repos/targetdiff/pretrained_models/")

    volume.commit()
    print("\n✅ Done")


@app.local_entrypoint()
def main():
    download.remote()
