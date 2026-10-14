# 两篇多靶点药物设计论文 — 数据集与使用指南

## 论文概览

| 项目 | 论文 1: MM-MT | 论文 2: DualDiff |
|------|--------------|-----------------|
| **标题** | Geometric Pocket-Centric Protein Encoding for Polypharmacology-Guided Multi-Target Drug Design | Reprogramming Pretrained Target-Specific Diffusion Models for Dual-Target Drug Design |
| **会议** | ICML 2026 | NeurIPS 2024 |
| **一作** | Liu, Haoran | Zhou, Xiangxin |
| **GitHub** | https://github.com/HaoranLiu1998/MM-MT | https://github.com/zhouxiangxin1998/DualDiff |
| **arXiv** | 无公开预印本 | 2410.20688 |
| **OpenReview** | https://openreview.net/forum?id=DuaA7vJGF6 | — |
| **核心方法** | Pocket-centric 蛋白拓扑编码 + 多模态融合生成 | 将单靶点扩散模型零样本迁移到双靶点设计 |

---

## 论文 1: MM-MT (Geometric Pocket-Centric)

### 1.1 仓库结构

```
MM-MT/
├── model/
│   └── 2MM-MT-surf-drugdesignv10.py   # 主模型代码
├── data/                               # 数据目录
└── results/                            # 实验结果
    ├── 生成的候选分子
    ├── 对接和结合亲和力结果
    ├── 分子性质评估
    ├── 多靶点筛选结果
    └── 可视化分析
```

### 1.2 数据集详解（从仓库验证）

口径说明：论文报告最终训练集为 75,921 行、1,305 个蛋白；公开 CSV 实测为 79,514 行、1,328 个蛋白。发布 zip 另含 1,970 个 1024 维 embedding 和 1,961 个结构图；1,961 个 ID 两种模态重叠，另有 9 个仅有 embedding。公开 CSV 的 1,328 个蛋白均有两种表示。

#### A. 预训练数据 — ZINC15

预训练数据从 ZINC15 筛选，仓库提供了筛选脚本：

```
data/1screenpretraindatafromZINC15.py   # 从 ZINC15 筛选预训练数据
data/2pretrainedsmiles_properties.py    # 预训练 SMILES 及分子性质处理
```

- **数据源**: [ZINC15](https://zinc15.docking.org/) — 免费商用化合物数据库
- **下载**: 需运行 `1screenpretraindatafromZINC15.py` 从 ZINC15 下载并筛选

#### B. 多模态数据 — PDB 蛋白结构 + 图表示

```
data/3PDB2graph.py                      # PDB 蛋白结构转图表示
data/4screenmultimodaldata.py           # 筛选多模态数据
data/multidata.zip                      # Git LFS 文件；拉取后 451.6 MB
```

- **数据源**: [PDB](https://www.rcsb.org/) — Protein Data Bank
- **处理**: PDB 结构 → 图表示（残基为节点，空间邻近关系为边）

#### C. 评估结果（已包含在仓库中）

```
result/
├── MEK1/    # MEK1 靶点的实验结果（4 files）
└── mTOR/    # mTOR 靶点的实验结果（4 files）
```

包含：生成的候选分子、对接分数、结合亲和力结果、分子性质评估

#### D. 模型代码

| 文件 | 说明 |
|------|------|
| `model/1pretrainedmodelv1-MutiMolGPT.py` | 预训练模型（MutiMolGPT，15K bytes） |
| `model/2MM-MT-surf-drugdesignv10.py` | 主模型：多靶点药物设计（41K bytes） |

### 1.3 环境配置

```bash
# GPU: CUDA 12.6
conda create -n polypharma python=3.11.9
conda activate polypharma
conda install -c rdkit rdkit
pip install torch torchvision torchaudio
conda env create -f environment.yml
```

### 1.4 运行方式

以下是仓库 README 给出的入口，不代表当前发布包可原样执行。实际还缺 `vocab.pkl`、8 维属性文件、预训练 decoder checkpoint，以及复现论文最终 75,921 行训练集的过滤清单。

```bash
# 1. 预训练
python ./model/1pretrainedmodelv1-MutiMolGPT.py

# 2. 多靶点药物设计
python ./model/2MM-MT-surf-drugdesignv10.py
```

### 1.5 评估靶点

COVID-19、精神分裂症 (Schizophrenia)、肿瘤 (Tumor)

### 1.6 引用

```bibtex
@inproceedings{liu2026geometric,
  title={Geometric Pocket-Centric Protein Encoding for Polypharmacology-Guided Multi-Target Drug Design},
  author={Liu, Haoran and others},
  booktitle={Proceedings of the International Conference on Machine Learning},
  year={2026}
}
```

---

## 论文 2: DualDiff

### 2.1 仓库结构

```
DualDiff/
├── dual_scripts/
│   ├── align/
│   │   └── align_protein_ligand_score.py   # 口袋对齐脚本
│   ├── example/
│   │   ├── sample_targetdiff.sh            # 单靶点采样
│   │   └── sample_compdiff.sh              # 双靶点采样
│   └── evaluate/                           # 评估脚本
├── outputs/
│   └── composition_score/8/104/            # 示例对齐结果
├── data/                                   # 数据目录 (从 data.tar.gz 解压)
└── ...                                     # 继承自 TargetDiff 的代码
```

### 2.2 数据集详解

DualDiff 涉及 **两类数据**：

#### A. 训练数据 — CrossDocked2020（继承自 TargetDiff）

DualDiff **不需要自己训练**（零样本迁移），直接使用 TargetDiff 的预训练权重。TargetDiff 训练在 CrossDocked2020 上：

| 属性 | 值 |
|------|-----|
| **数据源** | CrossDocked2020 |
| **总复合物数** | ~22.5M 蛋白-配体对 |
| **过滤后** | ~180K 高质量数据点（RMSD ≤ 1 Å） |
| **独立蛋白数** | 2,922 |
| **独立配体数** | 13,780 |
| **训练/测试划分** | 30% 序列相似度聚类 |
| **下载** | 参考 TargetDiff 仓库: https://github.com/guanjq/targetdiff |

**CrossDocked2020 下载步骤** (来自 TargetDiff):
```bash
# 参考 TargetDiff README 中的数据准备说明
# CrossDocked2020 原始数据:
# https://bits.csb.pitt.edu/files/crossdock2020/
```

#### B. 评估数据 — 双靶点协同药物组合数据集（DualDiff 自建）

这是论文的核心贡献之一。构建流程：

```
DrugCombDB (448,555 组合, 2,887 药物, 124 癌细胞系)
    ↓ 筛选协同性 (ZIP + Bliss + Loewe + HSA 全正)
DrugBank + TTD (收集 SMILES, 靶点, 同义词)
    ↓ 排除无 SMILES/靶点的药物
PDBBind / PDB / AlphaFold DB (获取蛋白结构)
    ↓ pLDDT ≥ 70 过滤 (AlphaFold 结构)
P2Rank (预测配体结合口袋)
    ↓
AutoDock Vina (获取蛋白-配体复合物结构 + 选择最佳靶点)
    ↓
最终数据集: 12,917 阳性药物组合对, 438 个独立药物
```

| 属性 | 值 |
|------|-----|
| **药物组合记录** | 论文 12,917；实际 pkl 12,972 行、12,960 个唯一有方向键、6,486 个唯一无序组合 |
| **独立药物数** | 438 |
| **数据来源** | DrugCombDB, DrugBank, TTD, PDBBind, PDB, AlphaFold DB |
| **协同性判定** | ZIP、Bliss、Loewe、HSA 四项得分均为正 |
| **结构来源** | PDBBind（已有复合物）→ PDB → AlphaFold DB（pLDDT ≥ 70） |
| **口袋预测** | P2Rank |
| **对接工具** | AutoDock Vina |
| **用途** | 评估双靶点药物设计方法的能力 |

#### 一条组合记录如何映射到结构：
- `synergy_idx_list.pkl` 中每条记录是两个参考药物索引，不是两个蛋白 ID
- 每个参考药物目录关联一个 UniProt 靶标及其参考配体/蛋白结构
- 将两个药物索引展开后，得到用于双靶点评估的两个药物—靶标复合物

### 2.3 数据下载与使用

```bash
# 1. 克隆仓库
git clone https://github.com/zhouxiangxin1998/DualDiff.git
cd DualDiff

# 2. 安装环境 (基于 TargetDiff)
# 先按 TargetDiff 官方仓库安装依赖: https://github.com/guanjq/targetdiff
# 然后安装额外依赖:
python -m pip install numpy==1.23.1
python -m pip install meeko==0.3.0

# 3. 下载数据 (从 HuggingFace)
# 下载地址: https://huggingface.co/datasets/zhouxiangxin/DualDiff
# 下载 data.tar.gz，解压到项目根目录:
tar -xzf data.tar.gz

# 4. 下载预训练模型
# 从 TargetDiff 仓库获取预训练权重
```

### 2.4 数据目录结构（解压后）

```
data/processed/
├── dock/
│   ├── index_dict.pkl              # 索引 → 参考配体 SMILES 的映射 (0-437)
│   └── ligand_protein_dataset_v2/  # 按 SMILES/UniProt ID 组织
│       ├── {SMILES}/
│       │   └── {UniProt_ID}/
│       │       ├── ligand.sdf          # 参考配体 SDF 文件
│       │       ├── pocket_10A.pdb      # 口袋（配体 10Å 范围内残基）
│       │       ├── protein.pdb         # 完整蛋白
│       │       └── protein_clean.pdb   # 清洗后蛋白
└── drug_synergy/
    └── synergy_idx_list.pkl        # 有方向的协同药物组合索引 [(idx1, idx2), ...]
```

**关键文件说明**:
- `index_dict.pkl`: dict，key=整数索引(0~437)，value=参考配体 SMILES
- `synergy_idx_list.pkl`: list of tuples，每个 tuple 是一对协同参考药物的索引；公开文件 12,972 行、12,960 个唯一有方向键，归并顺序后 6,486 个唯一无序组合
- 每个 `{SMILES}/{UniProt_ID}/` 目录 = 一个药物-靶点复合物

### 2.4 实验流程

```bash
# Step 1: 口袋对齐
python dual_scripts/align/align_protein_ligand_score.py

# Step 2: 单靶点采样 (baseline)
bash dual_scripts/example/sample_targetdiff.sh

# Step 3: 双靶点采样 (CompDiff/DualDiff)
bash dual_scripts/example/sample_compdiff.sh

# Step 4: 评估
# 使用 dual_scripts/evaluate/ 下的脚本
```

### 2.5 评估指标

| 指标 | 说明 | 方向 |
|------|------|------|
| P-1 Vina Dock | 对靶点1的 Vina 对接分数 | ↓ 越低越好 |
| P-2 Vina Dock | 对靶点2的 Vina 对接分数 | ↓ 越低越好 |
| Max Vina Dock | 两个靶点中较大的 Vina 分数 | ↓ 越低越好 |
| Dual High Affinity | 同时超过两个靶点参考分子亲和力的比例 | ↑ 越高越好 |
| QED | 类药性 (Drug-likeness) | ↑ 越高越好 |
| SA | 合成可及性 (Synthesizability) | ↑ 越高越好 |
| Diversity | 生成分子的多样性 | ↑ 越高越好 |

论文称对 12,917 条组合进行评估；公开 pkl 有 12,972 条记录。若严格复现论文，必须先获得作者当时使用的 12,917 条清单；若使用公开 pkl，应明确报告 12,972 的实际口径。

### 2.6 主要实验结果

| 方法 | P-1 Vina (Avg) | P-2 Vina (Avg) | Dual High Aff. (Avg) | QED (Avg) |
|------|----------------|----------------|----------------------|-----------|
| Reference | -7.60 | -6.02 | — | 0.53 |
| TargetDiff | -8.62 | -6.89 | 29.0% | 0.50 |
| CompDiff | -8.32 | -8.37 | 35.9% | 0.55 |
| **DualDiff** | **-8.41** | **-8.48** | **36.3%** | **0.56** |

### 2.7 引用

```bibtex
@inproceedings{zhou2024reprogramming,
  title={Reprogramming Pretrained Target-Specific Diffusion Models for Dual-Target Drug Design},
  author={Zhou, Xiangxin and Guan, Jiaqi and Zhang, Yijia and Peng, Xingang and Wang, Liang and Ma, Jianzhu},
  booktitle={Advances in Neural Information Processing Systems},
  year={2024}
}
```

---

## 数据下载链接汇总

### 可直接下载（不需要代码）

| 数据 | 链接 | 说明 |
|------|------|------|
| DualDiff 代码 | https://github.com/zhouxiangxin1998/DualDiff | 仓库代码 |
| DualDiff 数据 (data.tar.gz) | https://huggingface.co/datasets/zhouxiangxin/DualDiff | 公开 pkl 12,972 条药物组合记录 + 438 药物复合物；论文报告 12,917 |
| MM-MT 代码+数据 | https://github.com/HaoranLiu1998/MM-MT | 含 data/ 和 results/ 目录 |
| TargetDiff（DualDiff 依赖） | https://github.com/guanjq/targetdiff | 预训练模型 + CrossDocked2020 数据 |
| CrossDocked2020 原始数据 | https://bits.csb.pitt.edu/files/crossdock2020/ | ~22.5M 蛋白-配体对 |
| DrugCombDB | http://drugcombdb.denglab.org/main | 药物组合协同性数据库 |
| DrugBank | https://go.drugbank.com/ | 药物信息（SMILES、靶点） |
| TTD | https://idrblab.net/ttd/ | Therapeutic Target Database |
| PDBBind | http://www.pdbbind.org.cn/ | 蛋白-配体结合结构 |
| PDB | https://www.rcsb.org/ | Protein Data Bank |
| AlphaFold DB | https://alphafold.ebi.ac.uk/ | AlphaFold 预测结构 |

### 清华服务器上建议的下载顺序

1. **优先**: `git clone` 两个 GitHub 仓库（MM-MT 和 DualDiff）
2. **其次**: 下载 `data.tar.gz`（公开 pkl 实含 12,972 条药物组合记录；论文报告 12,917）
3. **其次**: `git clone` TargetDiff 仓库 + 下载预训练权重
4. **可选**: 如需重建数据集，再下载 CrossDocked2020、DrugCombDB 等原始数据

---

## 两篇论文的数据关系对比

```
                    ┌─────────────────────────────┐
                    │      CrossDocked2020         │
                    │  (22.5M 蛋白-配体对)          │
                    └──────────┬──────────────────┘
                               │ 训练
                    ┌──────────▼──────────────────┐
                    │        TargetDiff            │
                    │   (单靶点扩散模型预训练)        │
                    └──────────┬──────────────────┘
                               │ 零样本迁移
        ┌──────────────────────▼──────────────────────┐
        │              DualDiff (论文2)                 │
        │  论文: 12,917 条组合；公开 pkl: 12,972 条       │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │              MM-MT (论文1)                    │
        │  Pocket-centric 编码 + 多模态融合              │
        │  评估: COVID-19 / 精神分裂症 / 肿瘤靶点        │
        │  论文: 75,921/1,305；公开 CSV: 79,514/1,328    │
        └─────────────────────────────────────────────┘
```

---

## 快速开始脚本

以下脚本可在清华服务器上批量下载所有数据：

```bash
#!/bin/bash
# download_all_data.sh

# 创建工作目录
mkdir -p ~/multi-target-drug-design && cd ~/multi-target-drug-design

# 1. 克隆 MM-MT
git clone https://github.com/HaoranLiu1998/MM-MT.git
echo "✓ MM-MT 仓库已克隆"

# 2. 克隆 DualDiff
git clone https://github.com/zhouxiangxin1998/DualDiff.git
echo "✓ DualDiff 仓库已克隆"

# 3. 克隆 TargetDiff (DualDiff 的基础)
git clone https://github.com/guanjq/targetdiff.git
echo "✓ TargetDiff 仓库已克隆"

# 4. 提示手动步骤
echo ""
echo "=== 手动步骤 ==="
echo "1. 进入 DualDiff 目录，按 README 下载 data.tar.gz 并解压"
echo "2. 进入 TargetDiff 目录，按 README 下载预训练模型和 CrossDocked2020 数据"
echo "3. 安装 Python 环境依赖（参考各仓库 README）"
```
