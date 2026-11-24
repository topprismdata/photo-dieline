# Pack10K Coverage Matrix v0.1 (WP1; R1 P0-03 整改)

> 原则: 类别数四种含义分开数 (结构/工艺/商品语义/独立拓扑); 分母 = 真实零售包装需求
> (超市实拍盘点 + 冷柜对账台账品类), 不是我们自己造的清单。
> 状态列: ✅ 已覆盖(族ID) / 🔶 部分覆盖 / ❌ 未覆盖(故意的标"不做+理由")。

## A. 结构类别 × 现有 16 族

| 结构类别 (拓扑) | 覆盖 | 族/类 |
|---|---|---|
| 屋顶包 (gable top) | ✅ | gable_top/finless/fin_gap_wide/rect_base/window_front/screw_cap |
| 无菌砖 (aseptic brick) | ✅ | aseptic_brick / brick_250ml |
| 插舌封盒 (CLV) | ✅ | clv_* 7 类 |
| 锥台/锥筒 | ✅ | cone_wrap (+n12/n20) / pyramid_frustum_n* |
| RSC 快锁箱 | ✅ | rsc_* |
| 托盘 (open tray) | ✅ | tray_family |
| 天地盖 | ✅ | box_essentials |
| 抽屉套筒 | ✅ | box_essentials |
| 锁底盒 (lock bottom) | ✅ | lockbottom_* |
| 花边/异形链 | ✅ | odd_family / fan_net_ext |
| crashlock 底 | ✅ | crashlock_* |
| 信封/冲切异形 | ✅ | envelope_* / special_shapes |
| 提手盒 | ✅ | handle_box |
| 挂钩盒 | ✅ | hanger_box |
| 六角翻盖 | ✅ | hexagonal_flip |
| 展示台/分格 | ✅ | display_counter / divided_tray / food_bento |

## B. 未覆盖结构 (真实需求在, 模板缺 — 候选新族)

| 结构 | 需求证据 | 状态 |
|---|---|---|
| 八边封咖啡袋 (gusset) | 货架盘点高频 | ❌ 候选 |
| 自立袋 (doypouch) | 零食/宠物粮高频 | ❌ 候选 |
| 枕式袋 (pillow bag) | 膨化食品高频 | ❌ 候选 |
| 饮料瓶 (PET 曲面) | 曲面族 (非折纸拓扑) | ❌ 故意不做 (折叠引擎域外, 声明) |
| 罐/杯 (成型硬质) | 同上曲面域 | ❌ 故意不做 (酸奶杯走 USD 直建线, 另册) |
| 瓶盖/喷嘴等关节件 | R1 建议后续增加可动件 | ❌ 候选 (WP2 后) |

## C. 工艺类别 (与结构正交)

| 工艺 | 覆盖 |
|---|---|
| 插舌封口 | ✅ clv |
| 胶水封口 | ✅ glue 参数/胶条面板 |
| 锁底/自锁 | ✅ lockbottom/crashlock |
| 螺旋盖/旋入 | ✅ gable_screw_cap |
| 撕拉线 | 🔶 (glue_seal 有, 撕拉缺口未参数化) |
| 开窗 (透明窗) | ✅ gable_window_front |

## D. 多样性度量计划 (答"8 模板跑一万次"质疑)

1. **独立拓扑签名**: 由 IR 图 (面板+边图) 哈希计数 — 签名数 ≪ 资产数是事实, 公开声明;
2. **形态距离**: 归一化形状距离分布 (尺寸/长宽比谱);
3. **工艺/封口组合数**: 结构×工艺 笛卡尔覆盖;
4. **视觉外观**: 印刷色场/版面参数谱 (WP2 后);
5. **物理行为**: 质量/重心分布 (克重推导后)。
