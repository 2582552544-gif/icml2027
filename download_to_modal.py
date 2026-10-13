import modal

app = modal.App("drug-design-data-download")

volume = modal.Volume.from_name("drug-design-data", create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").apt_install("git")

MOUNT_PATH = "/data"


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
    timeout=3600,
)
def download_repos():
    import subprocess
    import os

    os.makedirs(f"{MOUNT_PATH}/repos", exist_ok=True)
    os.chdir(f"{MOUNT_PATH}/repos")

    repos = [
        ("MM-MT", "https://github.com/HaoranLiu1998/MM-MT.git"),
        ("DualDiff", "https://github.com/zhouxiangxin1998/DualDiff.git"),
        ("targetdiff", "https://github.com/guanjq/targetdiff.git"),
    ]

    for name, url in repos:
        target = f"{MOUNT_PATH}/repos/{name}"
        if os.path.exists(target):
            print(f"[skip] {name} already exists")
        else:
            print(f"[clone] {name} ...")
            subprocess.run(["git", "clone", url, target], check=True)
            print(f"[done] {name}")

    volume.commit()

    for name, _ in repos:
        target = f"{MOUNT_PATH}/repos/{name}"
        if os.path.isdir(target):
            result = subprocess.run(
                ["du", "-sh", target], capture_output=True, text=True
            )
            print(f"  {name}: {result.stdout.strip()}")

    print("\n=== listing repos/ ===")
    for item in sorted(os.listdir(f"{MOUNT_PATH}/repos")):
        print(f"  {item}/")

    print("\n=== MM-MT contents ===")
    mm_mt = f"{MOUNT_PATH}/repos/MM-MT"
    if os.path.isdir(mm_mt):
        for item in sorted(os.listdir(mm_mt)):
            print(f"  {item}")

    print("\n=== DualDiff contents ===")
    dd = f"{MOUNT_PATH}/repos/DualDiff"
    if os.path.isdir(dd):
        for item in sorted(os.listdir(dd)):
            print(f"  {item}")

    print("\n=== TargetDiff contents ===")
    td = f"{MOUNT_PATH}/repos/targetdiff"
    if os.path.isdir(td):
        for item in sorted(os.listdir(td)):
            print(f"  {item}")


@app.local_entrypoint()
def main():
    download_repos.remote()
    print("\nAll repos downloaded to Modal volume 'drug-design-data' at /data/repos/")
