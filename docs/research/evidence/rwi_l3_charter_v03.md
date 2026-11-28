# RWI-L3 章程 v0.3 (R48 修订版, 依 R48 终裁)

日期: 2026-11-28 | 依据: R48 终裁 (路线 D, 文档证据轨道) | 状态: v0.3

## 一、战略命题 (不变)

数字资产与真实商品之间可信对应关系的建立 (L1 生产 -> L2 消费验证 -> L3 真实世界绑定)。

## 二、核心假设 (分层验收)

| 假设 | 一件样本是否足够 |
|---|---|
| H1 绑定契约可执行 | 文档证据轨道: 可以 |
| H2 时间维度有效性维护 | 跨时间重取证据比对 |

## 三、双轨道结构 (R48 重构)

| 轨道 | 状态 | 预算 |
|---|---|---|
| WP-L3-01-PHYSICAL (实物轨道) | BLOCKED_BY_PHYSICAL_REFERENCE (硬约束; resume 条件 = NEW_EXPLICIT_USER_AUTHORIZATION; 不设预计恢复日期, 不安排采购调查, 不重复申请预算) | 0 |
| WP-L3-01-DOC (文档轨道) | AUTHORIZED (R49 启动) | 0 |

实物轨道封锁范围: 独立尺寸实测 / 空·满质量实测 / 独立商品摄影 / 摩擦实测 / 真实行为验证。
blocks_documented_track: false — 文档轨道不受实物封锁影响。

## 四、证据来源层级 (七级, 非线性可信度)

| 来源类型 | 代码 | 可支持的证据 |
|---|---|---|
| 独立实物测量 | REAL_MEASURED | 原始物理测量 |
| 厂商官方规格/技术资料 | DOCUMENTED_MANUFACTURER | 厂商声明的商品属性 |
| 官方标准化商品目录 | DOCUMENTED_REGISTRY | 商品身份及已登记属性 |
| 可追溯零售商品页面 | DOCUMENTED_RETAILER | 零售渠道所声明的商品属性 |
| 商品图片及包装文字观察 | DOCUMENTED_VISUAL | 可直接观察的包装信息 |
| 内部业务登记 | BUSINESS_CLAIMED | 业务系统中的声明 |
| 工程假设 | ENGINEERING_ASSUMPTION | 条件计算与机制实验 |

非绝对线性排名 (厂商规格可优于一次粗糙实测, 但不能替代制造偏差测量)。

## 五、DOCUMENTED 字段允许表

允许: 品牌 / 商品名称 / GTIN (区分公开登记与实物扫码) / 标称净含量 / 包装形式。
条件允许 (须满足限制): 包装版本 (须版本识别依据) / 外部尺寸 (须明确单件外尺寸非整箱) / 印刷内容 (仅可见区域) / 空包装质量 (须对象状态及来源) / 满装总质量 (不得以净含量直接替代) / 材料类别 (不从照片强行推断) / 摩擦系数 (须对应接触条件) / 惯量质心 (不得将估算标为厂商实测)。
禁止: 实物测量原始值 (保持 NULL) / 真实动态行为 (规格不足, 保持未验证)。

## 六、文档证据记录格式 (七字段追溯)

evidence_id / subject_id / attribute / value / unit / source_level / source_uri / source_locator / retrieved_at / source_snapshot_sha256 / assertion_type: DECLARED_SPECIFICATION / package_version_ref / verification_status: UNVERIFIED。

每份证据回答: 谁声明 / 原文在哪 / 针对哪个商品及包装版本 / 何时取得 / 是否与他源冲突。
禁止: 详情页单件尺寸·销售组合尺寸·物流包装尺寸混用; 公开渠道只有净含量时外部尺寸保持 NULL; 从资产自身尺寸反向补写真实商品规格再用它证明资产匹配。

## 七、非目标

不新增家族 / 不全量重编译 / 不重启 WP-L2-02 / 不建物理参数数据库 / L3-02..04 不自动启动 / 不换商品掩盖证据获取失败。

## 八、时间盒

WP-L3-01-DOC: 一个工作日, 采购预算 0。停止条件: 无法取得可信单件外尺寸或包装版本证据 -> EVIDENCE_INSUFFICIENT 结项。
