# ECO-CPG-01 实物侦察报告：Neurolabs CPGDet-129 数据集与合成感知路线

- 日期：2026-11-27
- 授权：R09-13 "ECO-CPG-01 P0 AUTHORIZED, IMMEDIATE PARALLEL EXECUTION"
- 资源上限：2 小时主动工作 / 5 GB 下载（实际使用：约 1 MB——见 EVIDENCE_UNAVAILABLE）

## 一、执行摘要

**CPGDet-129 数据集本体不可得（EVIDENCE_UNAVAILABLE）**：官方 README 下载链接 `bit.ly/3n3jowR` → `dl.orangedox.com/SampleRetailSyntheticDataset` 返回 **HTTP 404 "File Not Found"**（Orangedox 平台，疑似限时/下架）。仓库本体仅含 README + postprocess.py + 2 张 4K 样例图。数据集无法核验 → E2 实物核验不可达，按 R09-06 规则记录 `EVIDENCE_UNAVAILABLE`，不据此判定竞品能力。

## 二、已获实物（E2 最小可达物）

| 实物 | 规格 | 来源 |
|---|---|---|
| 样例合成渲染 ×2（jpeg+png 同景） | 3840×2160 4K | raw.githubusercontent samples/ |
| postprocess.py | 5,498 bytes | 仓库（标注三重过滤脚本）|
| README + LICENSE.MD (BSD-3) | — | 仓库 |

**样例质量观察**（evidence/eco_cpg01/1_KMXdMBez.jpeg，4K 全图目验）：
- 合成风格明显：光照完全均匀、货架结构简化（白板+价签）、商品摆放规律（等距行排）、地面纯灰
- 但达**商业可用级**：商品纹理/遮挡/堆叠真实（可乐/奶制品/意面酱等可辨品牌形态）、标注框密度高
- 与我方对比：我方 Cycles+AgX 棚拍渲染（hfpackage 出货板）在光照真实感上**同级或更优**；其优势在**大规模标注管线**（129 SKU 全标注 COCO 格式 + 三重过滤方法论），非单图质量

## 三、postprocess.py 方法论核验（E1→E3 部分）

三重过滤参数（README 实证）：可见度 ≥60%、类内 bbox 分布 ±1.5σ、绝对面积 ≥150px——**"合成标注→人工一致性"的后处理范式**可复用于我方未来感知管线（WP5 场景）。脚本存在 `filter -c` CLI，与 COCO json 兼容 → 我方 shelf SDG 输出可直接适配该范式。

## 四、对 RWI 的含义（按 R09-12 §三 修正后框架）

1. **路线先例成立（商业级）**：Neurolabs 以合成 CV 为核心建成 ReShelf 商业产品（Auchan 案例厂商报告）——"合成渲染→零售感知"路线的商业可行性由存续公司背书。
2. **数据集本体不可复现**：宣称 129 SKU 公开数据集实际不可下载——**"公开合成数据集"生态的可持续性风险实证**（限时托管/链接腐坏）。我方资产库若走公开数据路线，需**自有长期托管**（HuggingFace/HF dataset 永久 DOI）。
3. **我方差异化位置确认**：Neurolabs 卖"感知结果"，资产不公开；我方卖"资产+编译器"，感知是下游验证场景——**互补而非竞争**（R09-12 台账归类维持）。
4. **对 WP1 的影响**：CPGDet-129 的 COCO 格式 + 过滤参数可作为 WP1-v0.4 盲测标注格式的**外部参照**（非直接使用——其 129 SKU 与我方 77 家族不同域）。

## 五、证据分级与遗留

| 项 | 等级 | 说明 |
|---|---|---|
| Neurolabs 公司/ReShelf 产品存续 | E1→E2 部分（样例实物+官网存续）| 维持"下游商业参照"归类 |
| CPGDet-129 数据集本体 | **EVIDENCE_UNAVAILABLE** | 链接 404；medium 帖 403 |
| postprocess.py 方法论 | E1（文档核验，未执行）| 可 ADAPT 至我方 SDG 管线 |
| 样例合成渲染 4K×2 | E2 实物（已入库 evidence/eco_cpg01/）| 质量观察依据 |

遗留：若后续需要 E2 完整核验，可联系 Neurolabs 索取数据集（business development 渠道）或从 medium 帖的存档版本（web.archive.org）找替代链接——按 R09-12 资源配比（ECO 10%）暂不追加。

## 六、请求裁决

1. EVIDENCE_UNAVAILABLE 记录是否接受，ECO-CPG-01 是否可按"路线佐证成立、数据集本体不可得"关闭本侦察包。
2. "自有长期托管（HF 永久 DOI）作为我方公开数据集基础设施"是否纳入 RWI 架构原则（回应链接腐坏风险）。
3. 指派下一步（WP1-v0.4.1 的 13 例补齐与验证器专项 3 字段补证仍排队）。