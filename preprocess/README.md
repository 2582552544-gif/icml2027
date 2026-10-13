# MM-MT 数据预处理（对齐论文 Appendix C）

将 GitHub 仓库中的原始数据 (79,514 行) 处理为论文报告的最终数据 (75,921 行)。

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
filtered_final.csv (目标: 75,921 行, 1,305 蛋白)
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

# 运行预处理（约 20-30 分钟，主要耗时在 UniProt 序列获取和同源性计算）
modal run preprocess_mmmt.py

# 验证结果
modal run verify_result.py
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `filtered_final.csv` | 最终过滤后的数据集 |
| `filtered_final_mol_8properties.txt` | 8 维属性（原始值 + 归一化值） |
| `homologous_proteins.txt` | 被排除的同源蛋白列表 |
| `uniprot_sequences.txt` | UniProt 序列缓存（避免重复请求） |
| `preprocess_log.txt` | 各步骤删除行数记录 |

所有输出位于 Modal Volume `drug-design-data` 的 `/data/repos/MM-MT/preprocess_output/`。

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
