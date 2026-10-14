import modal

app = modal.App("drug-design-verify-counts")
volume = modal.Volume.from_name("drug-design-data")
image = modal.Image.debian_slim(python_version="3.11")


@app.function(image=image, volumes={"/data": volume}, timeout=300)
def verify():
    import pickle, os
    from collections import Counter

    dd = "/data/repos/DualDiff/data/processed"

    # 1. Check synergy list
    with open(f"{dd}/drug_synergy/synergy_idx_list.pkl", "rb") as f:
        synergy = pickle.load(f)
    print(f"synergy_idx_list.pkl: {len(synergy)} pairs")

    # Check directed duplicates and direction symmetry separately
    directed_counts = Counter(tuple(pair) for pair in synergy)
    repeated_directed = {pair: count for pair, count in directed_counts.items() if count > 1}
    print(f"Unique directed records: {len(directed_counts)}")
    print(f"Repeated directed keys: {len(repeated_directed)}")
    print(f"Extra rows from exact directed duplicates: {sum(c - 1 for c in repeated_directed.values())}")

    unique_pairs = set()
    for pair in synergy:
        unique_pairs.add(tuple(sorted(pair)))
    print(f"Unique unordered pairs: {len(unique_pairs)}")
    print(f"Rows beyond unordered-key count: {len(synergy) - len(unique_pairs)}")

    # Check if there are reverse duplicates
    fwd = set(directed_counts)
    rev = set((b, a) for a, b in synergy)
    both_directions = fwd & rev
    print(f"Pairs present in both directions (a,b) and (b,a): {len(both_directions)}")
    missing_reverse = sorted(pair for pair in fwd if (pair[1], pair[0]) not in fwd)
    self_pairs = sorted(pair for pair in fwd if pair[0] == pair[1])
    print(f"Directed keys without a reverse key: {len(missing_reverse)}")
    print(f"Self-pairs: {len(self_pairs)}")
    if missing_reverse:
        print(f"Examples without reverse: {missing_reverse[:10]}")

    # 2. Check index_dict
    with open(f"{dd}/dock/index_dict.pkl", "rb") as f:
        idx = pickle.load(f)

    if isinstance(idx, dict) and "smiles_to_idx" in idx:
        s2i = idx["smiles_to_idx"]
        i2s = idx["idx_to_smiles"]
        print(f"\nindex_dict: {len(s2i)} drugs (smiles_to_idx)")
        print(f"index_dict: {len(i2s)} drugs (idx_to_smiles)")
        max_idx = max(i2s.keys()) if i2s else -1
        min_idx = min(i2s.keys()) if i2s else -1
        print(f"Index range: {min_idx} to {max_idx}")
    else:
        print(f"\nindex_dict keys: {list(idx.keys())[:10]}")
        print(f"index_dict length: {len(idx)}")

    # 3. Count actual directories
    dataset_dir = f"{dd}/dock/ligand_protein_dataset_v2"
    if os.path.isdir(dataset_dir):
        drugs = [d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]
        print(f"\nActual drug directories: {len(drugs)}")

        total_complexes = 0
        for drug in drugs:
            dp = os.path.join(dataset_dir, drug)
            targets = [t for t in os.listdir(dp) if os.path.isdir(os.path.join(dp, t))]
            total_complexes += len(targets)
        print(f"Total drug-target complexes: {total_complexes}")

    # 4. Check all indices in synergy list are valid
    all_indices = set()
    for a, b in synergy:
        all_indices.add(a)
        all_indices.add(b)
    print(f"\nUnique drug indices in synergy list: {len(all_indices)}")
    print(f"Index range in synergy: {min(all_indices)} to {max(all_indices)}")

    if isinstance(idx, dict) and "idx_to_smiles" in idx:
        missing = all_indices - set(i2s.keys())
        if missing:
            print(f"WARNING: {len(missing)} indices in synergy not in index_dict: {sorted(missing)[:10]}")
        else:
            print("All synergy indices are valid in index_dict")

    # 5. Report the unresolved 12,917 vs 12,972 discrepancy
    print(f"\n=== ANALYSIS ===")
    print(f"Paper claims: 12,917 positive drug combinations")
    print(f"synergy_idx_list.pkl has: {len(synergy)} entries")
    print(f"Difference: {len(synergy) - 12917}")
    print(f"If we merge direction: {len(unique_pairs)} unique unordered pairs")
    print("12,917 is NOT the unordered-pair count; the released files do not explain the 55-entry gap.")


@app.local_entrypoint()
def main():
    verify.remote()
