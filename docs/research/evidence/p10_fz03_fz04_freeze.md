# P10-FZ03/FZ04 输入规格与参考隔离冻结 (WP1-P10-YCB)

日期: 2026-11-28 | 依据: R21 §3.2/§4.3 | 状态: FROZEN

## P10-FZ03 输入规格、单位、质量语义冻结

| 字段 | 冻结值 |
|---|---|
| 规格来源 | YCB 官方物品清单 PDF (2015-09, ycbbenchmarks.com) 十件表格 |
| 单位 | mm (规格) / g (质量) |
| 轴向语义 | 规格三值按官方 PDF 原始顺序登记; 对照时按排序轴比较 (sorted-desc ×3), 不假设轴名 |
| 圆柱语义 | 官方两值 = [Ø, H]; 实测 Ø=AABB 双近等轴均值, H=独异轴 |
| 质量语义 | **官方 PDF 质量按"含内容物实物总质量(gross)"登记** — 原始文档未注明测量状态, 如实登记为语义未明项; 禁止将其当空包装净质量使用 |
| 十件规格 | 见 p10_mesh_reference_study.json items[].official_mm + source PDF |

## P10-FZ04 参考资产与编译输入隔离 (双通道证据架构)

**通道 A (主实验, 规格驱动)**:
- 编译输入 = 官方 PDF 规格 (mm/g) + 结构家族标签 (box/cylinder/bottle)
- 评价真值 = 同一官方 PDF 规格 (DIM-01 内部契约验证)
- 扫描网格 **禁止** 用于提取编译输入参数

**通道 B (独立实验, 扫描辅助 — WP-CMP-01)**:
- 输入 = 扫描网格 OBB/AABB 提取参数, 明确标记 "scan-assisted parametric reconstruction"
- 对照真值 = 扫描网格本身 (声明: 扫描模型非绝对几何真值, R21 §5.2)
- 通道 A/B 结论 **不得混合**; 两通道资产命名/目录隔离

## 参考研究实测结论 (p10_mesh_reference_study.json, 扫描侧)

| 类别 | 实测 vs 官方 PDF |
|---|---|
| 圆柱 ×4 (chips/masterchef/soup/tuna) | Ø 0.4-4.7%, H 0.9-1.8% — **高吻合** |
| 盒 ×4 (cracker/sugar/pudding/gelatin) | 长轴 0.6-25%, **厚度轴 +11%~-+45% 系统性膨胀** (AABB) |
| 瓶 ×1 (mustard) | 9.3/14.4/33.2% (瓶肩+瓶盖不规则形) |
| Spam 盒 | 5.2/1.9/20.2% (厚度轴 +20%) |

**机理假设 (登记待验证)**: 官方 PDF = 包装规格尺寸(空盒/印刷态); 扫描网格 = 装填态实物。同一产品线, 不同测量状态 → 两态不可互换; 规格(通道A)与扫描(通道B)各自自洽。008 pudding 偏差最大 (google_16k 扫描质量存疑), 通道 B 单独标注。

## P10-FZ01 资产获取状态

- 20 文件 (10 物件 × google_16k + berkeley_meshes): 19 有效 gzip + 1 失败 (001_chips_can google_16k=404, berkeley_meshes 补位) — 全量 sha256 见 p10_asset_hash_ledger.json
- YCB 官方许可原文已归档: licenses/ycb_site_license.html (**数据 CC BY 4.0 / 代码 MIT** — 与 R21 更正一致)
- KITchen 许可原文: licenses/kitchen_readme.md (数据 CC BY-SA 4.0 / 代码 GPL-3.0)
