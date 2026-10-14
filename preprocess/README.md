# MM-MT 数据预处理审计（尝试对齐论文 Appendix C）

目标是检查公开 CSV（79,514 行、1,328 蛋白）与论文最终训练集（75,921 行、1,305 蛋白）之间的差异。这里的脚本是复现性审计工具，不是作者原始预处理实现，也不能保证生成论文同一数据集。

已验证的离线结果：仅执行 RDKit 标准化和 SMILES token 长度 `[34, 74]` 过滤后，得到 78,550 行、1,319 蛋白，仍比论文多 2,629 行、14 蛋白。

## 预处理流水线

```
filtered_dual_target_data2.csv (79,514 行)
    │
    ├── Step 1: SMILES 标准化 + token 长度过滤 [34, 74]
    ├── Step 2: 靶点过滤 (AA ≤ 1000 残基, 核苷酸 ≤ 6400 碱基)
    ├── Step 3: 8 维药理性质提取 + min-max 归一化
    └── Step 4: 同源性过滤 (与测试蛋白 sequence identity > 40% 排除)
    │
    ▼
filtered_final.csv (审计输出；论文参照值: 75,921 行, 1,305 蛋白)
```

### 测试蛋白 (Appendix D, Table 4)

| 疾病 | 靶点1 | UniProt | 靶点2 | UniProt |
|------|-------|---------|-------|---------|
| 肿瘤 | MEK1 | P15056 | mTOR | P62942 |
| COVID-19 | Mpro | P0DTD1 | Epro | P0DTC4 |
| 精神分裂症 | TAAR1 | P04899 | 5HT2C | P28335 |

## 运行

```bash
cd 论文/icml2027/preprocess

# 运行审计性预处理（会访问当前 UniProt；结果不等同于作者当年的版本化数据）
modal run preprocess_mmmt.py

# 验证结果
modal run verify_result.py
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `filtered_final.csv` | 本脚本规则下的过滤结果，不应标记为论文最终训练集 |
| `filtered_final_mol_8properties.txt` | 8 维属性（原始值 + 归一化值） |
| `homologous_proteins.txt` | 被排除的同源蛋白列表 |
| `uniprot_sequences.txt` | UniProt 序列缓存（避免重复请求） |
| `preprocess_log.txt` | 各步骤删除行数记录 |

所有输出位于 Modal Volume `drug-design-data` 的 `/data/repos/MM-MT/preprocess_output/`。

## 已知限制

- 发布包没有原始氨基酸序列、作者使用的 UniProt/NCBI 版本或最终过滤清单。
- 当前 UniProt 返回失败或 accession 变化会导致样本被错误保留/删除。
- `preprocess_mmmt.py` 中的同源性实现是近似审计实现，不是论文明确指定的比对工具和参数。
- 已有一次审计输出仅得到 31,909 行、712 蛋白，且仍出现测试蛋白，说明该输出无效，不能用于论文复现。

## 8 维药理性质 (Appendix A, Table 3)

| 属性 | 全名 | 缩放范围 |
|------|------|----------|
| MW | Molecular Weight | [0, 500] → [0, 1] |
| HBD | H-Bond Donors | [0, 5] → [0, 1] |
| HBA | H-Bond Acceptors | [0, 5] → [0, 1] |
| RotB | Rotatable Bonds | [0, 8] → [0, 1] |
| LogP | Octanol-water partition | [-2, 4] → [0, 1] |
| NumR | Number of rings | [0, 4] → [0, 1] |
| MaxR | Max size of rings | [3, 8] → [0, 1] |
| NumA | Number of amino groups | [0, 3] → [0, 1] |
