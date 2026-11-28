# RWI Asset Quality Baseline v1.0 (质量基线冻结件)

冻结日期: 2026-11-28 | 治理授权: R28 (FINAL QUALITY BASELINE FREEZE) | 治理原则: **零隐瞒、零口径混用、零无证据质量声明**

## 一、资产分类学 (GOV-TAX-01 已验收)

| 层 | 数量 | 说明 |
|---|---|---|
| Builder Group | 27 | build.json 构建分组 |
| Registered Class | 101 | 权威注册表 cls_id |
| Released Class | **77** | 集合差分证明: 101−24 未发行 = 77 (历史口径得证) |
| Released Asset | 9,386 | 冻结发行集 |

未发行 24 类登记在案 (family_taxonomy_crosswalk.json), 状态"注册未发行"。

## 二、质量证据分层 (四层并立, 不互相替代)

| 层 | 证据 | 结果 |
|---|---|---|
| L1 历史构建门禁 | build.json G02-G10 逐 SKU | 9,386/9,386 PASS (27/27 组全净) |
| L2 尺寸和解 | conformance.json 逐轴 | 9,386/9,386 ok, 最差 0.001mm |
| L3 独立输出审计 (REP-M05) | 9,386 最终网格全扫 | UV/3D 退化 **0** · 非流形边 **0** · dup 顶点对 455 (UV 接缝疑似) · 闭壳 1,484 + 开壳 7,902 (设计语义) |
| L4 外部审计发现 | G2 对照 + Pilot-10 | FG-001/002/003 OPEN (审计层, build 盲区实证) |

**关键事实**: L1 门禁全过 ≠ L3 独立审计全净 — 两层并立是治理基础 (G2 三对照家族实证)。

## 三、家族发现台账 (FG Ledger)

| ID | 状态 | 结论 |
|---|---|---|
| FG-001 bento | OPEN (语义裁决待) | solid-with-open-boundary + UV 退化 5 面 (UV primvar 层; 3D 层 0) |
| FG-002 sushi | OPEN (语义裁决待) | dup16+nonfan2 (刀版粘合双顶点 vs 真拓扑, 待逐件核对) |
| FG-003 mailer | OPEN (语义裁决待) | nonmanifold 顶点 3 (刀版多面交汇; REP-M05 边级 0 → 顶点级判定待复算) |
| FG-004 prism_n12 | **CLOSED RETRACTED** | 调用方契约违反 (R23-A); 家族缺陷归因撤销 |
| FG-005 小尺寸 glue | **CLOSED** | 跨参数组合约束: glue_w/side ≤0.70 实测安全 / 0.75 失败 (实测构型), 高度不敏感; 非正式硬拒绝 |
| FG-006 5_HTP | **CLOSED_WITH_KNOWN_LIMITATION** | 单点量化切达 (side≈14.1485); 冻结集 152 prism 实扫 0 命中 |

## 四、参数域契约 (三层知识, prism_dust 试点)

1. **单参数合法性**: n/side/h/tuck_depth/glue_w schema
2. **跨参数组合合法性**: tuck_depth = apothem(n, side) (G04 如实 FAIL 语义) + glue_w/side ≤ 0.70 实测安全
3. **输出几何不变量**: closure_checks 五判据 ≤0.2mm + G03 切达豁免缺失 (FG-006 known limitation)

## 五、外部样本池 (GSO) 终态

- 工作池 150 = 116 SUPPORTED + 34 PACKAGING_CANDIDATE; 9 NON_PACKAGING + 1 SOURCE_BINDING_UNRESOLVED (上游 webp 错绑, GLB 已验正确)
- GSO-PN RUN-01: QA 12/16 · NVSDK 16/16 · DIM01 12/16 · 联合 8/16 (历史保留, 不可变)
- 正式准入仍待逐件审计 (扫描派生尺寸非物理真值; 质量字段缺失)

## 六、YCB Pilot-10 终态 (固定群组, 已关闭)

RUN-01 5/10 → RUN-03 (契约一致) **10/10** 编译+NVSDK; DIM-01 严格 9/10 + 006 近似声明。对外限定语: "初始调用 50%, 根因=调用参数违反既有几何契约, 修正后 100% 通过编译 QA 与 NVSDK" — **不得表述为 100% 真实未见泛化能力**。十件永久退出未见测试。

## 七、已声明的已知限制 (零隐瞒)

1. 质量语义 = MEASURED_MASS_STATE_UNKNOWN (官方文档未注明测量状态)
2. GSO 尺寸 = 扫描 BBox 派生 (非物理实测, 五源表第 4 类); GSO 质量字段缺失
3. 瓶体无原生家族 (棱柱近似, Ø=横截面均值, 已声明)
4. #31 上游 webp 错绑 (GLB 已验正确); HF 上游 issue 非阻塞反馈授权
5. 008 参考-规格冲突 CONFLICT_UNRESOLVED (官方规格不被推翻; 补真值=实物采购/GS1)
6. 物理/视觉保真/消费端适用性: **未验证, 不声明**
7. 独立资产质量审计覆盖: REP-M05 几何层全量; UV-primvar 层/顶点级非流形仅对照三件, 未全量

## 八、红线 (质量声明禁令)

- 9,386 全量重编译 PROHIBITED; 冻结发行集零覆盖
- UV 正确性 / 商品尺寸正确性 NOT CONFIRMED 不得宣称
- 不以红灯消失/边界归零为成功标准
- Pilot-10 十件永久退出未见测试
- 禁止合并不同层通过率为单一"端到端成功率"
