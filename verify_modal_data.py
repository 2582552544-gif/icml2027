import modal

app = modal.App("drug-design-verify")

volume = modal.Volume.from_name("drug-design-data")

image = modal.Image.debian_slim(python_version="3.11").apt_install("git", "tree")

MOUNT_PATH = "/data"


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
    timeout=600,
)
def verify():
    import subprocess
    import os

    print("=" * 60)
    print("验证 Modal Volume: drug-design-data")
    print("=" * 60)

    # 1. 总览
    result = subprocess.run(
        ["du", "-sh", f"{MOUNT_PATH}/repos/MM-MT",
         f"{MOUNT_PATH}/repos/DualDiff",
         f"{MOUNT_PATH}/repos/targetdiff"],
        capture_output=True, text=True
    )
    print("\n📦 仓库大小:")
    print(result.stdout)

    # 2. MM-MT 验证
    print("=" * 60)
    print("论文1: MM-MT (Geometric Pocket-Centric)")
    print("=" * 60)
    mm_mt = f"{MOUNT_PATH}/repos/MM-MT"

    # 检查关键目录
    for d in ["model", "data", "result", "Figure"]:
        path = os.path.join(mm_mt, d)
        if os.path.isdir(path):
            items = os.listdir(path)
            print(f"\n  📁 {d}/ ({len(items)} items)")
            for item in sorted(items)[:20]:
                full = os.path.join(path, item)
                if os.path.isdir(full):
                    sub_items = os.listdir(full)
                    print(f"    📁 {item}/ ({len(sub_items)} items)")
                else:
                    size = os.path.getsize(full)
                    print(f"    📄 {item} ({size:,} bytes)")

    # 检查 environment.yml
    env_file = os.path.join(mm_mt, "environment.yml")
    if os.path.exists(env_file):
        print(f"\n  📄 environment.yml:")
        with open(env_file) as f:
            print("    " + f.read()[:500].replace("\n", "\n    "))

    # README
    readme = os.path.join(mm_mt, "README.md")
    if os.path.exists(readme):
        with open(readme) as f:
            content = f.read()
        print(f"\n  📄 README.md ({len(content):,} chars)")
        print("    " + content[:2000].replace("\n", "\n    "))

    # 3. DualDiff 验证
    print("\n" + "=" * 60)
    print("论文2: DualDiff")
    print("=" * 60)
    dd = f"{MOUNT_PATH}/repos/DualDiff"

    for d in ["datasets", "dual_scripts", "models", "configs", "scripts", "outputs"]:
        path = os.path.join(dd, d)
        if os.path.isdir(path):
            items = os.listdir(path)
            print(f"\n  📁 {d}/ ({len(items)} items)")
            for item in sorted(items)[:15]:
                full = os.path.join(path, item)
                if os.path.isdir(full):
                    sub_items = os.listdir(full)
                    print(f"    📁 {item}/ ({len(sub_items)} items)")
                    for sub in sorted(sub_items)[:5]:
                        sub_full = os.path.join(full, sub)
                        if os.path.isdir(sub_full):
                            print(f"      📁 {sub}/ ({len(os.listdir(sub_full))} items)")
                        else:
                            print(f"      📄 {sub} ({os.path.getsize(sub_full):,} bytes)")
                else:
                    size = os.path.getsize(full)
                    print(f"    📄 {item} ({size:,} bytes)")

    # README
    readme = os.path.join(dd, "README.md")
    if os.path.exists(readme):
        with open(readme) as f:
            content = f.read()
        print(f"\n  📄 README.md ({len(content):,} chars)")
        print("    " + content[:3000].replace("\n", "\n    "))

    # 4. TargetDiff 验证
    print("\n" + "=" * 60)
    print("依赖: TargetDiff")
    print("=" * 60)
    td = f"{MOUNT_PATH}/repos/targetdiff"

    for d in ["data", "pretrained_models", "configs", "datasets", "scripts"]:
        path = os.path.join(td, d)
        if os.path.isdir(path):
            items = os.listdir(path)
            print(f"\n  📁 {d}/ ({len(items)} items)")
            for item in sorted(items)[:10]:
                full = os.path.join(path, item)
                if os.path.isdir(full):
                    sub_items = os.listdir(full)
                    print(f"    📁 {item}/ ({len(sub_items)} items)")
                else:
                    size = os.path.getsize(full)
                    print(f"    📄 {item} ({size:,} bytes)")

    # README
    readme = os.path.join(td, "README.md")
    if os.path.exists(readme):
        with open(readme) as f:
            content = f.read()
        print(f"\n  📄 README.md ({len(content):,} chars)")
        print("    " + content[:2000].replace("\n", "\n    "))

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)


@app.local_entrypoint()
def main():
    verify.remote()
