# 多靶点 + 单配体 数据集来源清单

> 目标：1 个 ligand 同时结合 2/3/4 个蛋白靶点的训练/评估数据集
>
> 更新时间：2026-10-14

## 一、现成可用的多靶点数据集

### 1. MTLD — Multiple Target Ligand Database ⭐⭐⭐

| 项目 | 值 |
|------|-----|
| **数据量** | 1,732 个多靶点配体，绑定 14,996 个结合位点 |
| **来源** | 从 12,759 个 PDB 结构中提取 |
| **特点** | 有 3D 结构，直接可用于 SBDD |
| **论文** | [J Cheminform, 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4403778/) |
| **更新版** | [MTLD v2, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6151691/) |
| **下载** | 网站免费下载 |
| **适用性** | ✅ 直接有「1 ligand → N targets」结构，是最接近需求的 |

### 2. BindingDB 批量导出 ⭐⭐⭐

| 项目 | 值 |
|------|-----|
| **数据量** | 2,882,970 测量，1,243,034 化合物，9,311 靶点 |
| **下载** | https://www.bindingdb.org/rwd/bind/chemsearch/marvin/Download.jsp |
| **特点** | SDF 文件包含同一化合物对多个靶点的活性数据 |
| **构建方法** | 按化合物分组，保留有 ≥2 个靶点活性数据的化合物 |
| **适用性** | ✅ 最大规模来源，需自己分组构建 |

### 3. ChEMBL 34 ⭐⭐

| 项目 | 值 |
|------|-----|
| **数据量** | 20M+ 活性数据，2.4M 化合物，15K 靶点 |
| **下载** | https://www.ebi.ac.uk/chembl/ (PostgreSQL dump) |
| **构建方法** | 查 compound_structures + activities + assays，按 molregno 分组 |
| **适用性** | ✅ 数据最全，但需要较多预处理 |

### 4. PPB3 — Polypharmacology Browser 3 ⭐⭐⭐

| 项目 | 值 |
|------|-----|
| **数据量** | 2,496,555 interactions，1,187,089 分子，7,546 靶点 |
| **来源** | ChEMBL 34，IC50/EC50/Ki/Kd ≤ 10 μM |
| **论文** | 2026 年发表 |
| **网站** | https://gdb.unibe.ch/polypharmacology-browser-ppb3 |
| **适用性** | ✅ 最新的多靶点标注数据，有现成的 target prediction |

### 5. POLYGON (Nature Communications 2024) ⭐⭐

| 项目 | 值 |
|------|-----|
| **论文** | [De novo generation of multi-target compounds](https://www.nature.com/articles/s41467-024-47120-y) |
| **数据量** | 评估了 >100,000 化合物的双靶点结合 |
| **方法** | 强化学习生成双靶点抑制剂 |
| **适用性** | ⚠️ 需确认训练数据是否开源 |

### 6. FuseDiff (arXiv 2603.05567, 2026) ⭐⭐

| 项目 | 值 |
|------|-----|
| **论文** | Symmetry-Preserving Joint Diffusion for Dual-Target SBDD |
| **数据** | 使用 DualDiff 的 benchmark + 自建评估集 |
| **适用性** | ⚠️ 扩展了 DualDiff 的双靶点方法，数据待确认 |

### 7. eMOSAIC (bioRxiv 2024) ⭐

| 项目 | 值 |
|------|-----|
| **论文** | [Multi-modal Uncertainty Quantification for Drug Discovery](https://www.biorxiv.org/content/10.1101/2024.01.05.574359v2) |
| **数据** | 从 ChEMBL 提取多靶点活性数据 |
| **特点** | 有 selectivity profile（选择性图谱） |
| **适用性** | ⚠️ 需确认数据规模 |

---

## 二、构建自己的多靶点数据集（推荐方案）

### 最佳方案：从 BindingDB 构建

```python
"""
从 BindingDB 构建多靶点数据集
1 ligand → N targets (N=2,3,4)
"""

# Step 1: 下载 BindingDB TSV
# wget https://www.bindingdb.org/bind/downloads/BindingDB_All_2024m4.tsv.zip

# Step 2: 按化合物分组，找多靶点配体
import pandas as pd

df = pd.read_csv("BindingDB_All.tsv", sep="\t", low_memory=False)

# 筛选有活性数据的（Ki 或 IC50 ≤ 10 μM）
df_active = df[df["Ki (nM)"].notna() | df["IC50 (nM)"].notna()]

# 按 SMILES 分组，统计每个化合物命中的靶点数
target_counts = df_active.groupby("Ligand SMILES")["UniProt (SwissProt) Primary ID of Target Chain"].nunique()

# 筛选多靶点配体
dual_target = target_counts[target_counts == 2]     # 2 靶点
triple_target = target_counts[target_counts == 3]   # 3 靶点
quad_target = target_counts[target_counts >= 4]     # 4+ 靶点

print(f"2 靶点配体: {len(dual_target)}")
print(f"3 靶点配体: {len(triple_target)}")
print(f"4+ 靶点配体: {len(quad_target)}")
```

### 预估数据量

根据 PPB3 的统计（ChEMBL 34, ≤10μM 阈值）：
- 已批准药物平均命中 ~10 个靶点
- pChEMBL ≥ 6 时：1,914 个药物，16,256 个药物-靶点对
- 超过 1,000 个化合物命中 ≥10 个不同类别的靶点

因此预计：
- **2 靶点**：数万~数十万条
- **3 靶点**：数千~数万条
- **4 靶点**：数百~数千条

---

## 三、已有数据对比（icml2027 现有）

| 数据集 | 格式 | 靶点数 | 是否有 3D 结构 |
|--------|------|--------|---------------|
| MM-MT CSV | 1 SMILES + 2 UniProt | 固定 2 | ❌ 只有嵌入和图 |
| DualDiff | 2 个单靶点复合物配对 | 固定 2 | ✅ PDB + SDF |
| MTLD (待下载) | 1 ligand + N 结合位点 | 可变 N | ✅ 来自 PDB |
| BindingDB (待构建) | 1 SMILES + N 活性靶点 | 可变 N | ⚠️ 需对接获取 3D |

---

## 四、下一步行动

- [ ] 下载 MTLD 数据库，统计 2/3/4 靶点配体分布
- [ ] 下载 BindingDB 批量 TSV，构建多靶点分组
- [ ] 检查 POLYGON 论文代码是否开源数据
- [ ] 检查 PPB3 数据是否可下载
- [ ] 从 ChEMBL 34 提取 pChEMBL ≥ 6 的多靶点配体
- [ ] 用 Modal 跑构建脚本，上传到 volume
