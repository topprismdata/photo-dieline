# WP-GSO-PN 协议冻结 v1.0 (R22 §5.1 批准; R23-B 执行)

日期: 2026-11-28 | 独立实验: 通过率不并入 WP1-Pilot-100 | 编译器版本: GOV-IR-01 补丁后 (FG-004 契约修复在位)

## 抽取隔离纪律 (R22 §5.2 白名单)

允许从 GSO 提取: ① 三轴总体尺寸 (size_x/y/z_cm, 目录字段) ② 结构家族判定 ③ 编译契约必需参数 (按家族映射公式派生)。**禁止**: 结果锁定前用网格表面细节做针对性拟合 (本轮不下载网格, 元数据优先)。

## 确定性选择规则 (无随机过程, census of first-N)

分类 (排序 dims desc [L,M,S], 基于 size_cm):
- cylinder: |x−y|/max(x,y) ≤ 0.08 且 S/L ≥ 0.15
- bottle_shaped: 瓶类子家族 (supplement_bottle/care_bottle/beverage_pkg/bottle_jug_tube) 且非 cylinder 且 S/L ≥ 0.18
- flat_container: S/L < 0.18
- box_rect: 其余且 S/L ≥ 0.18
- complex: 剩余
每类按 object_id 字典序取前 4 (不足则全取并登记缺口)。

## 家族映射 (FG-004 契约在位)

- box_rect / flat_container → rsc_css {W=L, D=M, H=S} (GSO 无官方轴向语义, 排序赋值为冻结约定)
- cylinder → prism_dust_n12 {n:12, side=Ø·tan(π/12), h=L, tuck_depth=Ø/2} (Ø=D_face 对边距语义, R23-A 收口)
- bottle_shaped → prism_dust_n12 近似 {Ø=(x+y)/2, tuck=Ø/2} 已声明 approx
- complex → rsc_css 近似尝试; 失败登记 coverage_miss

## 评价指标 (独立)

① 家族覆盖: native / approx / miss (coverage 是被测对象) ② 编译 QA 门禁 ③ NVSDK 结构 ④ DIM-01 vs 扫描派生输入 (契约忠实度, tol=max(1mm,1%))
**不可评**: 独立实物尺寸精度 (无真值) / 质量惯性 (无参考) / 77 家族泛化 (样本外)
