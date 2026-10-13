"""检查 Modal Volume 上 MM-MT 的完整文件列表，确认哪些原始数据可用。"""
import modal

app = modal.App("mmmt-check-files")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11")


@app.function(image=image, volumes={"/data": volume}, timeout=120)
def check():
    import os

    repo = "/data/repos/MM-MT"
    multidata = f"{repo}/multidata"

    print("=" * 60)
    print("MM-MT 文件清单")
    print("=" * 60)

    for root, dirs, files in os.walk(repo):
        depth = root.replace(repo, "").count(os.sep)
        indent = " " * 2 * depth
        dirname = os.path.basename(root)

        # 不递归进入大目录的子目录
        file_count = len(files)
        if file_count > 20:
            total_size = sum(os.path.getsize(os.path.join(root, f)) for f in files)
            print(f"{indent}📁 {dirname}/ ({file_count} files, {total_size/1024/1024:.1f} MB)")
            # 只列出几个示例
            for f in sorted(files)[:5]:
                fp = os.path.join(root, f)
                print(f"{indent}  {f} ({os.path.getsize(fp):,} bytes)")
            if file_count > 5:
                print(f"{indent}  ... and {file_count - 5} more")
        else:
            print(f"{indent}📁 {dirname}/")
            for f in sorted(files):
                fp = os.path.join(root, f)
                print(f"{indent}  {f} ({os.path.getsize(fp):,} bytes)")

    # 特别检查关键文件
    print(f"\n{'=' * 60}")
    print("关键文件检查")
    print("=" * 60)
    key_files = [
        "multidata/smi_prot.xlsx",
        "multidata/ID2Refseq.xlsx",
        "multidata/gene_seq_data/mRNA_ID.txt",
        "multidata/gene_seq_data/mRNA_Seq.txt",
        "multidata/filtered_dual_target_data2.csv",
        "multidata/filtered_dual_mol_8properties.txt",
        "data/vocab.pkl",
        "data/multidata.zip",
        "data/smiles.txt",
    ]
    for kf in key_files:
        fp = f"{repo}/{kf}"
        if os.path.exists(fp):
            size = os.path.getsize(fp)
            print(f"  ✅ {kf} ({size:,} bytes)")
        else:
            print(f"  ❌ {kf}")


@app.local_entrypoint()
def main():
    check.remote()
