# Multi-Target Drug Design — Datasets & Tools

两篇多靶点药物设计论文的数据集收集、验证和使用指南。

## 目标论文（2 篇）

| # | 论文 | 会议 | 方法 | GitHub |
|---|------|------|------|--------|
| 1 | **Geometric Pocket-Centric Protein Encoding for Polypharmacology-Guided Multi-Target Drug Design** | ICML 2026 | Pocket-centric 蛋白拓扑编码 + 多模态融合 | [HaoranLiu1998/MM-MT](https://github.com/HaoranLiu1998/MM-MT) |
| 2 | **Reprogramming Pretrained Target-Specific Diffusion Models for Dual-Target Drug Design** | NeurIPS 2024 | 单靶点扩散模型零样本迁移到双靶点 | [zhouxiangxin1998/DualDiff](https://github.com/zhouxiangxin1998/DualDiff) |

> **注意**：Modal volume 中还包含 [TargetDiff](https://github.com/guanjq/targetdiff)（ICLR 2023），它**不是目标论文**，仅作为 DualDiff 的预训练基础模型依赖。DualDiff 的代码和模型权重都依赖于它。

## 数据概览

> 口径约定：本文将“论文报告值”“公开文件实测值”“可离线复现值”分开陈述。文件存在不等于论文实验可完整复现。

### DualDiff (556 MB)

- **438** 个参考药物，公开 pkl 含 **12,972** 行：12,960 个唯一有方向键，其中 12 个自组合键各重复 1 次；归并方向后为 6,486 个唯一无序组合。论文报告 12,917 条
- 每个药物-靶点复合物包含：`ligand.sdf` + `pocket_10A.pdb` + `protein.pdb`
- 数据来源：DrugCombDB → DrugBank/TTD → PDBBind/PDB/AlphaFold DB
- 下载：[HuggingFace](https://huggingface.co/datasets/zhouxiangxin/DualDiff)

### MM-MT (451.6 MB)

- **79,514** 行双靶点数据（CSV），**1,328** 个唯一蛋白靶点
- 蛋白嵌入：1,970 个 `.npy` 文件（1024 维向量）
- 蛋白图：1,961 个 `.pt` 文件（PyG Data）
- 预训练数据源：ZINC15

> 正确规范化结构图文件名后，1,961 个 `.pt` ID 全部存在同名 `.npy`；另有 9 个仅存在 `.npy`。CSV 使用的 1,328 个靶点均同时具备两种表示。

## 文件说明

| 文件 | 说明 |
|------|------|
| [数据使用指南.md](数据使用指南.md) | **核心文档** — 数据格式详解 + Few-shot 代码示例 |
| [datasets-guide.md](datasets-guide.md) | 论文概览、数据来源、下载链接汇总 |
| `images/` | 旧版 AI 信息图及生成元数据；存在历史错误，当前文档不再引用 |
| `download_to_modal.py` | 下载三个 GitHub 仓库到 Modal volume |
| `download_hf_data.py` | 下载 HuggingFace 数据 + Git LFS 拉取到 Modal |
| `share_data.py` | Modal web endpoint，提供数据浏览页面 |
| `verify_*.py` | 数据验证脚本（论文 vs 实际数据交叉核对） |

## 数据关系速览

- DualDiff：药物组合索引 → 两个参考药物 → 各自对应的 UniProt 靶标和蛋白—配体复合物。
- MM-MT：每条 CSV 记录包含一个 SMILES、两个 UniProt ID、两条编码核苷酸序列；每个靶点再关联一个 1024 维 ProtTrans embedding 和一个结构图。
- `images/` 中旧信息图基于早期错误统计生成，已停止在文档中引用；应以本文数字和验证脚本输出为准。

## 快速开始

### 方式 1：Modal（公开文件已就绪）

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
| DualDiff 协同药物组合 | 12,917 条 | pkl 含 12,972 行、12,960 个唯一有方向键；归并顺序后为 6,486 个唯一无序组合 |
| MM-MT 最终训练集 | 75,921 行、1,305 蛋白 | 公开 CSV 为 79,514 行、1,328 蛋白；缺最终过滤清单，不能等同 |
| MM-MT 嵌入维度 | `Femb ∈ R^1024` | `.npy` shape 为 `(1, 1024)`，一致 |
| MM-MT npy/pt 关系 | 每个样本需两种表示 | 1,961 个 ID 重叠；9 个仅有 `.npy`；CSV 的 1,328 个 ID 均完整 |
