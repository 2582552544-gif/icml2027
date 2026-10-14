import modal

app = modal.App("drug-design-verify-mmmt")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11").pip_install("numpy")


@app.function(image=image, volumes={"/data": volume}, timeout=300)
def verify():
    import csv, io, os, zipfile, numpy as np

    mm = "/data/repos/MM-MT"

    # 1. Check multidata.zip contents in detail
    mz = f"{mm}/data/multidata.zip"
    print(f"multidata.zip size: {os.path.getsize(mz) / 1024 / 1024:.1f} MB")

    with zipfile.ZipFile(mz) as z:
        names = z.namelist()

        # Count by type
        npy_files = [n for n in names if n.endswith(".npy")]
        pt_files = [n for n in names if n.endswith(".pt")]
        csv_files = [n for n in names if n.endswith(".csv")]

        print(f"\nTotal files: {len(names)}")
        print(f"  .npy (protein embeddings): {len(npy_files)}")
        print(f"  .pt  (protein graphs): {len(pt_files)}")
        print(f"  .csv: {len(csv_files)}")

        # Check npy file names (UniProt IDs)
        npy_ids = set(os.path.basename(n).replace(".npy", "") for n in npy_files)
        pt_ids = {
            os.path.basename(n).removeprefix("alphafold_").removesuffix("_surf.pt")
            for n in pt_files
        }
        print(f"\nUnique UniProt IDs in .npy: {len(npy_ids)}")
        print(f"Unique UniProt IDs in .pt: {len(pt_ids)}")
        print(f"IDs in npy but not pt: {len(npy_ids - pt_ids)}")
        print(f"IDs in pt but not npy: {len(pt_ids - npy_ids)}")
        common = npy_ids & pt_ids
        print(f"Common IDs: {len(common)}")

        # Sample npy file
        sample_npy = npy_files[0]
        with z.open(sample_npy) as f:
            arr = np.load(f)
        print(f"\nSample .npy ({os.path.basename(sample_npy)}):")
        print(f"  shape: {arr.shape}")
        print(f"  dtype: {arr.dtype}")
        print(f"  min: {arr.min():.4f}, max: {arr.max():.4f}, mean: {arr.mean():.4f}")

        # Check a few more npy files to confirm consistent shape
        shapes = set()
        for npy in npy_files[:20]:
            with z.open(npy) as f:
                a = np.load(f)
            shapes.add(a.shape)
        print(f"  All shapes in first 20: {shapes}")

        # Read CSV header and count rows
        csv_file = csv_files[0]
        print(f"\nCSV file: {csv_file}")
        with z.open(csv_file) as f:
            header = f.readline().decode("utf-8").strip()
            print(f"  Header: {header}")
            row_count = 0
            first_rows = []
            for line in f:
                row_count += 1
                if row_count <= 3:
                    decoded = line.decode("utf-8", "replace").strip()
                    first_rows.append(decoded[:200])
            print(f"  Total rows: {row_count}")
            print(f"  Columns: {header.split(',')}")
            for i, r in enumerate(first_rows):
                print(f"  Row {i+1}: {r}")

        # Check UniProt IDs in CSV vs embedding files
        print(f"\n=== Cross-check ===")
        with z.open(csv_file) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
            csv_targets = set()
            for row in reader:
                csv_targets.add(row["Target1_Uniprot"].strip())
                csv_targets.add(row["Target2_Uniprot"].strip())
        print(f"Unique UniProt IDs in CSV: {len(csv_targets)}")
        csv_in_npy = csv_targets & npy_ids
        csv_not_in_npy = csv_targets - npy_ids
        print(f"CSV targets with .npy embedding: {len(csv_in_npy)}")
        print(f"CSV targets WITHOUT .npy embedding: {len(csv_not_in_npy)}")
        if csv_not_in_npy:
            print(f"  Missing examples: {list(csv_not_in_npy)[:5]}")

    # 2. Check model scripts
    print(f"\n=== Model scripts ===")
    for f in ["model/1pretrainedmodelv1-MutiMolGPT.py", "model/2MM-MT-surf-drugdesignv10.py"]:
        fp = os.path.join(mm, f)
        if os.path.exists(fp):
            with open(fp) as fh:
                content = fh.read()
            print(f"\n{f}: {len(content)} chars")
            # Find key constants/dimensions
            for line in content.split("\n"):
                stripped = line.strip()
                if any(kw in stripped.lower() for kw in ["embed_dim", "hidden_dim", "n_head", "vocab_size", "max_len", "528", "256", "512", "1024"]):
                    print(f"  {stripped}")

    # 3. Check result PDBs
    print(f"\n=== Result PDBs ===")
    result_dir = f"{mm}/result"
    for target in sorted(os.listdir(result_dir)):
        tpath = os.path.join(result_dir, target)
        if os.path.isdir(tpath):
            files = os.listdir(tpath)
            print(f"  {target}/: {len(files)} PDB files")


@app.local_entrypoint()
def main():
    verify.remote()
