"""列出 Modal Volume 上 multidata.zip 的完整文件列表。"""
import modal

app = modal.App("mmmt-list-zip")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11")


@app.function(image=image, volumes={"/data": volume}, timeout=120)
def list_zip():
    import zipfile
    import os

    zip_path = "/data/repos/MM-MT/data/multidata.zip"
    print(f"ZIP: {zip_path} ({os.path.getsize(zip_path)/1024/1024:.1f} MB)")

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        print(f"\n文件总数: {len(names)}")

        dirs = {}
        for n in names:
            parts = n.split("/")
            top = parts[0] if len(parts) > 1 else "(root)"
            sub = "/".join(parts[:2]) if len(parts) > 2 else top
            if sub not in dirs:
                dirs[sub] = {"count": 0, "size": 0, "examples": []}
            info = z.getinfo(n)
            dirs[sub]["count"] += 1
            dirs[sub]["size"] += info.file_size
            if len(dirs[sub]["examples"]) < 3:
                dirs[sub]["examples"].append(f"{n} ({info.file_size:,} bytes)")

        print(f"\n{'='*60}")
        print("目录结构:")
        print(f"{'='*60}")
        for d, info in sorted(dirs.items()):
            print(f"\n📁 {d}/ — {info['count']} files, {info['size']/1024/1024:.1f} MB")
            for ex in info["examples"]:
                print(f"   {ex}")

        # 特别找关键文件
        print(f"\n{'='*60}")
        print("关键文件搜索:")
        print(f"{'='*60}")
        keywords = ["smi_prot", "ID2Refseq", "mRNA", "vocab", "smiles",
                     "gene_seq", "properties", "filtered"]
        for kw in keywords:
            matches = [n for n in names if kw.lower() in n.lower()]
            if matches:
                for m in matches[:5]:
                    info = z.getinfo(m)
                    print(f"  ✅ {m} ({info.file_size:,} bytes)")
            else:
                print(f"  ❌ '{kw}' — 未找到")


@app.local_entrypoint()
def main():
    list_zip.remote()
