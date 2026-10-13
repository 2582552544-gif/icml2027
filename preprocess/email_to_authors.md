# 给 MM-MT 作者的邮件

**收件人**: linxiaoli@wust.edu.cn, zouyu@wust.edu.cn, xiaolong.zhang@wust.edu.cn

**主题**: Request for Preprocessing Scripts and Raw Data — "Geometric Pocket-Centric Protein Encoding" (ICML 2026)

---

Dear Prof. Lin, Prof. Zou, and Prof. Zhang,

I hope this message finds you well. I am writing regarding your ICML 2026 paper *"Geometric Pocket-Centric Protein Encoding for Polypharmacology-Guided Multi-Target Drug Design"*, which I found very inspiring.

I am currently working on reproducing and extending your multi-target drug design framework. I have cloned the GitHub repository (https://github.com/HaoranLiu1998/MM-MT) and downloaded the `multidata.zip` via Git LFS. However, I noticed that the released data package only contains the intermediate CSV (`filtered_dual_target_data2.csv`, 79,514 rows), protein embeddings, and structure graphs.

According to Appendix C, the final training dataset should contain **75,921** samples after applying SMILES standardization, target filtering (AA > 1,000 / nucleotide > 6,400), and homology filtering (> 40% sequence identity with test proteins). I have been unable to reproduce this exact number because the following files referenced in the preprocessing scripts are not included in the release:

1. **`smi_prot.xlsx`** — the original (SMILES, Target1, Target2) triplets from ChEMBL (referenced in `4screenmultimodaldata.py`)
2. **`ID2Refseq.xlsx`** — UniProt-to-RefSeq ID mapping
3. **`gene_seq_data/mRNA_ID.txt` and `mRNA_Seq.txt`** — nucleotide sequences from NCBI
4. **`vocab.pkl`** and **`smiles.txt`** — SMILES vocabulary (referenced in the model script)
5. **`filtered_dual_mol_8properties.txt`** — the 8-dimensional pharmacological property file

Would it be possible to share any of the following?

- The missing raw data files listed above, so I can run the full preprocessing pipeline
- The exact preprocessing script that produces the final 75,921-sample dataset from the released CSV
- Or alternatively, the final filtered CSV (75,921 rows) and its corresponding property file

I would greatly appreciate your help. Thank you for your excellent work and for open-sourcing the code.

Best regards,
[你的名字]
[你的机构]
[你的邮箱]
