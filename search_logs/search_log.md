# 多靶点+单配体数据集搜索日志

> 目标：找到或构建 1 ligand + N targets (N=2,3,4) 的训练/评估数据集

## Round 1 — 2026-10-14

**搜索关键词**：
1. `multi-target drug design dataset polypharmacology ligand binding multiple proteins ChEMBL training data`
2. `polypharmacology benchmark dataset one ligand multiple targets protein-ligand binding affinity`
3. `ChEMBL multi-target ligand dataset drug repurposing polypharmacology selectivity panel screening`
4. `MTLD Multiple Target Ligand Database`
5. `FuseDiff dual-target dataset`
6. `POLYGON multi-target compound generation`

**工具**：paper-search skill (Tavily) + WebSearch

**发现**：

| # | 来源 | 数据量 | 是否直接可用 | 优先级 |
|---|------|--------|-------------|--------|
| 1 | **MTLD** (PDB 来源, 1,732 多靶点配体) | 中 | ✅ 有 3D 结构 | ⭐⭐⭐ |
| 2 | **BindingDB** (2.88M 测量, 1.24M 化合物) | 大 | 需分组构建 | ⭐⭐⭐ |
| 3 | **PPB3** (2.5M interactions, 1.19M 分子) | 大 | 需确认下载方式 | ⭐⭐⭐ |
| 4 | **ChEMBL 34** (20M+ 活性数据) | 最大 | 需 SQL 查询构建 | ⭐⭐ |
| 5 | **POLYGON** (Nature Comms 2024) | 100K+ | 待确认开源 | ⭐⭐ |
| 6 | **FuseDiff** (arXiv 2026) | 扩展 DualDiff | 待确认 | ⭐ |
| 7 | **eMOSAIC** (bioRxiv 2024) | 待确认 | 有选择性图谱 | ⭐ |

**结论**：没有现成的"开箱即用"的 N≥3 靶点训练集，需要从 BindingDB/ChEMBL 构建。MTLD 最接近需求但规模小（1,732 条）。

**下一步**：下载 BindingDB TSV → 按化合物分组 → 筛选 2/3/4 靶点配体 → 统计数据量
