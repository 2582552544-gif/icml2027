# Multi-Target Drug Design — Datasets & Tools

两篇多靶点药物设计论文的数据集收集、验证和使用指南。

## 目标论文（2 篇）

| # | 论文 | 会议 | 方法 | GitHub |
|---|------|------|------|--------|
| 1 | **Geometric Pocket-Centric Protein Encoding for Polypharmacology-Guided Multi-Target Drug Design** | ICML 2026 | Pocket-centric 蛋白拓扑编码 + 多模态融合 | [HaoranLiu1998/MM-MT](https://github.com/HaoranLiu1998/MM-MT) |
| 2 | **Reprogramming Pretrained Target-Specific Diffusion Models for Dual-Target Drug Design** | NeurIPS 2024 | 单靶点扩散模型零样本迁移到双靶点 | [zhouxiangxin1998/DualDiff](https://github.com/zhouxiangxin1998/DualDiff) |

> **注意**：Modal volume 中还包含 [TargetDiff](https://github.com/guanjq/targetdiff)（ICLR 2023），它**不是目标论文**，仅作为 DualDiff 的预训练基础模型依赖。DualDiff 的代码和模型权重都依赖于它。

## 数据概览

### DualDiff (556 MB)

- **438** 个药物，**12,972** 条协同靶点对（6,486 个唯一无序对）
- 每个药物-靶点复合物包含：`ligand.sdf` + `pocket_10A.pdb` + `protein.pdb`
- 数据来源：DrugCombDB → DrugBank/TTD → PDBBind/PDB/AlphaFold DB
- 下载：[HuggingFace](https://huggingface.co/datasets/zhouxiangxin/DualDiff)

### MM-MT (451.6 MB)

- **79,514** 行双靶点数据（CSV），**1,057** 个唯一蛋白靶点
- 蛋白嵌入：1,970 个 `.npy` 文件（1024 维向量）
- 蛋白图：1,961 个 `.pt` 文件（PyG Data）
- 预训练数据源：ZINC15

> `.npy` 和 `.pt` 文件的 UniProt ID 完全不重叠，代表两组不同蛋白的不同模态表示。

## 文件说明

| 文件 | 说明 |
|------|------|
| [数据使用指南.md](数据使用指南.md) | **核心文档** — 数据格式详解 + Few-shot 代码示例 |
| [datasets-guide.md](datasets-guide.md) | 论文概览、数据来源、下载链接汇总 |
| `images/` | 3 张 AI 生成的数据格式解释图 |
| `download_to_modal.py` | 下载三个 GitHub 仓库到 Modal volume |
| `download_hf_data.py` | 下载 HuggingFace 数据 + Git LFS 拉取到 Modal |
| `share_data.py` | Modal web endpoint，提供数据浏览页面 |
| `verify_*.py` | 数据验证脚本（论文 vs 实际数据交叉核对） |

## 数据格式图

### DualDiff 数据构建流程
![DualDiff Pipeline](images/dualdiff_data_pipeline.png)

### MM-MT 多模态数据结构
![MM-MT Structure](images/mmmt_data_structure.png)

### 两篇论文数据格式对比
![Comparison](images/comparison_data_formats.png)

## 快速开始

### 方式 1：Modal（数据已就绪）

```python
import modal

volume = modal.Volume.from_name("drug-design-data")

@app.function(volumes={"/data": volume}, gpu="A10G")
def run():
    # DualDiff 数据在 /data/repos/DualDiff/data/processed/
    # MM-MT 数据在 /data/repos/MM-MT/data/multidata.zip
    pass
```

### 方式 2：在线浏览

访问 https://iabtcun--drug-design-share-list.us-east.modal.run 查看所有文件。

### 方式 3：拉到本地/服务器

```bash
# 拉取全部
modal volume get drug-design-data repos/ ./drug-design-data/

# 只拉取某个仓库
modal volume get drug-design-data repos/DualDiff/ ./DualDiff/
```

### 方式 4：直接 clone

```bash
# 目标论文 1: MM-MT (ICML 2026)
git clone https://github.com/HaoranLiu1998/MM-MT.git

# 目标论文 2: DualDiff (NeurIPS 2024)
git clone https://github.com/zhouxiangxin1998/DualDiff.git

# ⚠️ 以下不是目标论文，是 DualDiff 的预训练依赖
git clone https://github.com/guanjq/targetdiff.git
```

## 已验证的数据差异

| 项目 | 论文声称 | 实际数据 |
|------|---------|---------|
| DualDiff 靶点对 | 12,917 | pkl 含 12,972 条双向对，6,486 唯一无序对 |
| MM-MT 嵌入维度 | — | 1024（非 528） |
| MM-MT npy/pt 关系 | — | 两组完全不重叠的 UniProt ID |
