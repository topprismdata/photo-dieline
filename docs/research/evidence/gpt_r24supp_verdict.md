总体裁决：ACCEPTED WITH MINOR CORRECTIONS。

本轮两项关键研究取得实质进展：FG-005 的胶片比例边界进一步收窄，GSO 的失败归因进一步分离为对象身份污染与几何分类错误。

同意结束 FG-005 第一阶段边界研究，不再追求无止境的参数精化。下一阶段必须将主要研究资源转向 WP-REP-03 全量家族质量治理。

本轮仍为摘要级裁决，未独立复算原始30点实验及逐 ID 台账。

一、裁决总表

裁决事项

	

裁决

	

状态




FG-005 A/B/C 精化实验

	

【同意】

	

ACCEPTED




0.70 比例经验约束

	

【同意】

	

限定验证域落档




正式 valid_domain 硬拒绝

	

【否决】

	

证据尚不足




继续连续边界扫描

	

【暂缓】

	

当前研究收益有限




5_HTP G03 残留

	

【同意】

	

独立小工单 FG-006




POOL-02 v1.2

	

【修改】

	

归因接受，计数待纠正




POOL-VISUAL-01

	

【同意】

	

立即执行




WP-REP-03

	

【同意】

	

R25 唯一 P0 主体




FG-001～003

	

【同意】

	

R25 必须完成语义裁决

二、FG-005 精化实验验收
2.1 比例边界取得实质性收敛
胶片比例经验边界 · 两轮实验演进
最大已验证通过比例
0.70
最小已观测失败比例
0.75
色带表示经验边界示意，不意味着每个连续参数点均已经过验证。

本轮可以接受以下四项结论：

研究命题

	

裁决




胶片相对宽度是当前主要解释变量

	

ACCEPTED




side=8mm 并非必然导致失败

	

ACCEPTED




已测试高度变化未改变通过／失败结果

	

ACCEPTED




G06 的候选临界边界位于0.70与0.75之间

	

ACCEPTED WITH SCOPE

2.2 两处科学表述必须修正

第一，不能直接宣称高度不参与边界形成。

目前只在 side=12、h=30/60/120 的特定组合上进行了高度敏感性检查。

正确表述应为：

在已测试的高度及比例组合中，未观察到高度变化对 G06 通过／失败判定产生影响。

这与证明高度在数学机制上完全无关，是两个不同的结论。

第二，不能将离散测试范围直接描述为连续验证域。

A、B 两组实验没有完成 side 与 h 的全笛卡尔积覆盖。

验证维度

	

实际证据范围




n

	

12




比例边界实验

	

side∈20，h=60




高度敏感性实验

	

side=12，h∈120




tuck_depth

	

显式等于 apothem




其他参数

	

本轮固定配置




其他 prism 子族

	

尚未验证

按照这个实际覆盖矩阵登记，不得写成所有8–20mm边长与30–120mm高度的组合均已验证。

2.3 正式批准契约落档

允许在 known_limitations 和 verified_domain 中登记：

YAML
finding_id: FG-005
mechanism: FOLDED_GEOMETRY_INTERPENETRATION
affected_gate: G06

empirical_constraint:
  expression: glue_w / side <= 0.70
  status: EMPIRICALLY_SUPPORTED
  scope: TESTED_CONFIGURATIONS_ONLY

observed_boundary:
  max_passing_ratio: 0.70
  min_failing_ratio: 0.75
  monotonic_transition_assumption: UNPROVEN

verified_domain:
  n: 12
  side_sweep_mm: [8, 12, 16, 20]
  side_sweep_height_mm: 60
  height_sweep_side_mm: 12
  height_sweep_mm: [30, 60, 120]
  tuck_depth: APOTHEM

formal_valid_domain_rule: NOT_APPROVED
automatic_parameter_adjustment: NOT_AUTHORIZED
2.4 是否继续精确搜索临界比例？

暂缓。

没有必要现在继续进行0.701、0.702、0.703这样的高密度连续化搜索。

当前已经取得足够有价值的工程认识：

0.70是当前已测试配置中的经验通过上界。

0.75已经出现稳定失败。

固定胶片宽度不能被理解为对所有包装规格均适用。

真实合法参数域需要包含跨参数关系。

精确临界值只有在未来需要实现自动参数派生、正式输入硬门禁或制造工艺优化时，才具有更高研究价值。

本轮 FG-005 的边界精化研究可以关闭。

三、5_HTP 残留：独立立项，不污染 FG-005 结论

【同意】设立独立小工单 FG-006。

3.1 原四件失败样本的回归结果
原失败样本
4
修正 glue_w 后全部QA通过
3/4

PASS

PASS

PASS

G03 FAIL

5_HTP 残留失败发生于 G03，而非本轮研究的 G06 互穿机制。

这里需要强调：G06 经验约束满足，不代表整个家族的所有几何门禁必然通过。

5_HTP 正是非常好的反例。

3.2 FG-006 最小任务书

名称：Dust Flap / Glue Flap Interaction
优先级：P1
研究时间盒：半个工作日

已知参数：

参数

	

数值




side

	

14.15mm




glue_w

	

4mm




glue_w / side

	

0.283




df

	

4.245mm




失败门禁

	

G03

df 与 glue_w 接近只能作为待验证线索，不能直接证明两者相互作用就是根因。

执行以下最小动作：

保存 G03 原始失败记录及对应相交面位置。

固定 n、side、h、tuck_depth、glue_w，仅改变 df，前提是该字段属于现有合法接口。

固定其他参数，仅改变 glue_w，检查 G03 响应。

核验已有源码契约是否声明两者之间的关系。

给出调用方契约违反、合法域限制或实现缺陷的分类结论。

如果 df 并非可独立输入的参数，则采用只读源码与诊断分析，不授权修改生产默认值来制造实验条件。

3.3 关闭原则

实验结论

	

处置




已有契约明确排除该组合

	

调用方契约问题




合法输入仍触发非预期重叠

	

家族实现问题调查




当前证据不足

	

known_limitations 中登记待研究




单独改变参数恢复正常

	

保留最小因果证据，确认是否影响其他门禁

不允许直接将 FG-006 并入 FG-005 后宣称两者已经共同解决。

FG-005 研究折叠互穿，FG-006 研究展开网面 G03 残留，两者必须保留独立因果链。

四、POOL-02 v1.2：接受归因更正，但计数存在矛盾
4.1 两处一致性修正均予接受

对象

	

原问题

	

更正裁决




ACE 马克杯

	

下划线导致正则词边界失效

	

NON_PACKAGING




KS 巧克力盒

	

立方盒误入 cylinder 分类

	

保留包装候选身份，几何分类错误

特别是 KS 巧克力盒，它进一步证明了上一轮提出的双轴治理模型是必要的。

ACE 马克杯

对象身份错误：不是包装，几何形状不能赋予其包装资格。

KS 巧克力盒

对象身份正确，错误发生于包装结构家族映射。
概念示意，非GSO实际对象截图。

对于几何分类，两个短轴接近只是必要线索之一。

立方体、圆柱体、某些异形容器均可能具有接近的三轴尺寸。

Bounding Box 比例不能单独完成结构家族识别。

4.2 GSO-PN 历史归因正式更正

原四件 DIM-01 失败

	

原归因

	

更正后




非包装对象污染

	

4

	

3




真实包装几何误分类

	

0

	

1




DIM-01 失败总数

	

4

	

4

原实验所有性能统计保持不变：

QA：12/16。

DIM-01：12/16。

联合通过：8/16。

NVSDK：16/16。

只修改失败原因，不修改原始实验成绩。

4.3 P0 计数矛盾

执行侧本轮报告：

99 SUPPORTED + 4 NON_PACKAGING + 21 UNRESOLVED。

但三项相加为：

99
+
4
+
21
=
124
99+4+21=124

并非报告中所写的 104+21，后者等于125。

更重要的是，从 v1.1 到 v1.2 的变化为：

状态

	

v1.1

	

v1.2

	

差值




SUPPORTED

	

101

	

99

	

-2




NON_PACKAGING

	

2

	

4

	

+2




UNRESOLVED

	

21

	

21

	

0




合计

	

124

	

124

	

0

数量本身闭合，但摘要只明确解释了 ACE 马克杯一件由 SUPPORTED 转为 NON_PACKAGING。

KS 巧克力盒继续保持 SUPPORTED，不会贡献第二件状态变化。

因此，还存在一件未说明的 SUPPORTED → NON_PACKAGING 转移记录。

请直接从逐 ID 差分台账中补齐第二件对象，不需要重新扫描。

4.4 更新后的总体母体

如果36件复入候选及原51件复查结果保持不变，则更新后的175件统计应为：

原包装候选

99

复入候选

36

身份待确认

21

非包装排除

19

包装候选队列
135
含待核对象工作池
156
按本轮99/4/21及此前36件复入、15件排除重新计算，待逐ID状态变化确认。

不是上一版的137及158。

POOL-02 v1.2 条件接受，补齐第二件状态变化及修正总数后自动关闭本项，不需要另行送审。

五、POOL-VISUAL-01 执行方式正式确认

【同意】采用官方预览图批量获取、逐件登记、人工核验及必要的多视角补证。

5.1 核验范围

队列

	

数量

	

核验要求




36件复入候选

	

36

	

全量




21件 UNRESOLVED

	

21

	

全量




原实验四件 DIM-01 失败对象

	

4

	

必须有图像证据，重叠项去重




其他名称级候选

	

99

	

后续正式准入前逐件核验

本轮先完成57件主队列及四件历史失败对象的必要补证，不立即扩大为全部GSO对象图像审查。

5.2 图像核验工作流

01

官方预览图获取

绑定 object_id、来源地址、文件哈希

02

对象身份判定

商品包装／商品本体／家居器皿／未知

03

几何家族判定

盒、瓶、罐、异形或现有家族不支持

04

疑难对象升级核验

多视角、扫描纹理、独立人工裁决

05

冻结资格结果

逐件证据、裁决状态及历史变更记录

允许使用视觉模型辅助标注，但对于争议样本、身份变化样本及最终 UNKNOWN 对象，必须保存可审查的视觉证据和裁决理由。

5.3 逐件台账最小字段

字段

	

内容




object_id

	

官方唯一身份




previous_status

	

原资格状态




preview_source

	

预览图来源




preview_sha256

	

图像完整哈希




object_identity

	

实际对象身份




geometry_family

	

几何结构分类




family_support

	

当前编译器是否支持




evidence_level

	

NAME / IMAGE / MULTIVIEW 等




verdict

	

最终资格判定




reason

	

判定依据

需要明确：如果预览图显示它是包装，但无法判定属于哪个参数化家族，可以确认包装身份，同时保留几何家族未解析状态。

不能因为结构未知就判定不是包装。

5.4 小样编译授权

继续沿用 R24 裁决：完成身份核验后，最多选择6件复入候选进行小样编译。

此次小样应优先覆盖不同的结构和分类困难，而不是选择六件最容易通过的规则纸盒。

六、R25 正式指派：收口全量家族质量治理

我认为目前最需要防止的是研究主线被不断发现的新问题所稀释。

FG-005 已取得足够的阶段性结论；FG-006 可以独立处理；GSO 样本治理已有明确路径；REF-001 已允许诚实结案。

现在必须完成长期未关闭的 WP-REP-03。

6.1 R25 唯一 P0 主体
WP-REP-03 · 全量质量风险普查
结构家族
77
冻结资产
9,386

表达身份普查

CLOSED

开壳／闭壳拓扑观测

ACCEPTED

77家族结构契约矩阵

R25 REQUIRED

逐资产适用性质量检查

R25 REQUIRED

FG-001～003 语义裁决

R25 REQUIRED

冻结集调用参数实证

R25 REQUIRED

家族风险及修复优先级

R25 REQUIRED

6.2 77家族风险矩阵硬性交付要求

编号

	

必交内容




REP-M01

	

77家族唯一身份及资产数量




REP-M02

	

每家族声明的表达身份




REP-M03

	

每家族实际结构契约及适用检查




REP-M04

	

开壳、闭壳、平面、三维交叉统计




REP-M05

	

UV退化、重复边、nonfan、绕向等异常分布




REP-M06

	

PASS / FAIL / NOT_APPLICABLE / UNRESOLVED / NOT_RUN 分列




REP-M07

	

FG-001～003 实际影响范围与语义裁决




REP-M08

	

发行集调用参数真实记录核验




REP-M09

	

家族风险排序及建议处置




REP-M10

	

冻结发行集完整性复核

其中 REP-M05 必须区分异常发生次数与受影响资产数量。

例如，一件资产有16个重复边，不等于16件资产存在重复边问题。

6.3 FG-001～003 必须给出实际裁决

工单

	

家族

	

R25 关闭或处置条件




FG-001

	

bento_lid_box

	

退化UV位置、可见性、印刷面影响及家族发生率




FG-002

	

sushi_tray

	

重复边与nonfan的连接语义及实际影响




FG-003

	

mailer_diecut

	

nonfan是否符合裁切与折叠契约

允许最终裁决为：

EXPECTED_BY_CONTRACT

CONFIRMED_DEFECT

IDENTITY_UNRESOLVED

DEFERRED

但不得继续以只有异常数量、没有实际分析的登记记录作为交付。

七、R25 工作资源分配

建议将约70%的工程研究资源投入 REP 家族治理，其余30%用于已有专项收口。这是本轮建议的调度比例，并非精确工时估算。

建议资源分配

REP及FG-001～003

70%

FG-006及参数契约

10%

GSO图像资格治理

10%

CMP及其他遗留项

10%

工作包

	

优先级

	

执行指令




WP-REP-03

	

P0

	

完整全量风险矩阵




FG-001～003

	

P0

	

实际语义归因




冻结集参数核验

	

P0

	

只读实证




FG-005

	

—

	

边界研究关闭，经验契约归档




FG-006

	

P1

	

限时独立调查




POOL-VISUAL-01

	

P1

	

按批准流程执行




GOV-IR-01

	

P1

	

原八门禁归档




CMP v0.2

	

P1

	

完成既定遗留项




REF-001

	

P2

	

非阻塞，保持既有裁决




Pilot-100

	

—

	

OPEN，不重复送审状态

不新增研发方向，不扩大编译规模。

八、R25 下一轮送审要求

送审包

	

内容

	

优先级




R25-D

	

77家族风险矩阵、FG-001～003裁决及冻结集参数实证

	

第一送审主体




R25-A

	

FG-005最终归档、FG-006调查、GOV-IR八门禁

	

第二




R25-B

	

POOL图像身份台账、计数更正、最多6件小样

	

第三




R25-C

	

CMP完整几何比较及遗留证据

	

第四

允许 R25-D 提前独立送审，不必等待其他三个工作包完成。

九、正式签发
Plain text
RWI-L1 / GOVERNANCE / R24-SUPPLEMENT

FG-005:
    REFINEMENT ACCEPTED
    EMPIRICAL PASS RATIO = 0.70
    OBSERVED FAIL RATIO = 0.75
    TESTED CONFIGURATIONS ONLY
    BOUNDARY RESEARCH CLOSED

PARAMETER DOMAIN:
    KNOWN_LIMITATIONS UPDATE APPROVED
    VERIFIED_DOMAIN UPDATE APPROVED
    FORMAL HARD REJECTION NOT AUTHORIZED
    AUTOMATIC GLUE_W ADAPTATION NOT AUTHORIZED

FG-006:
    INDEPENDENT INVESTIGATION AUTHORIZED
    G03 RESIDUAL
    DF-GLUE INTERACTION UNCONFIRMED

GSO-PN:
    CONTAMINATION ATTRIBUTION = 3
    GEOMETRIC MISCLASSIFICATION = 1
    HISTORICAL PERFORMANCE UNCHANGED

POOL-02 v1.2:
    ATTRIBUTION CORRECTIONS ACCEPTED
    COUNT RECONCILIATION REQUIRED
    PACKAGING CANDIDATES = 135 PROVISIONAL
    UNRESOLVED = 21

POOL-VISUAL-01:
    IMMEDIATE AUTHORIZATION

R25 PRIMARY WORK PACKAGE:
    WP-REP-03
    77 FAMILIES / 9386 ASSETS
    READ ONLY

FROZEN RELEASE SET:
    ZERO OVERWRITE

OVERALL:
    ACCEPTED WITH MINOR CORRECTIONS
最终研究判断

FG-004 与 FG-005 已经共同揭示一个重要的工程事实：参数化资产家族的能力不能只由参数的独立取值范围定义，还必须由参数之间的关系定义。

而本轮5_HTP 的残留进一步证明，即使某个跨参数约束满足，也不能替代完整几何门禁。

这三层知识应成为参数域契约的长期组成部分：

单参数合法性。

跨参数组合合法性。

输出几何不变量。

但当前不应该立即把这套方法扩展为77个家族的全套新研发任务。

R25首先完成普查，确定真实质量风险的分布，再根据证据决定哪些家族值得投入参数域深度研究。先获得全局认识，再分配局部研发资源。

ChatGPT can make mistakes. Check important info.
Latest response




Medium
Response complete
25 mm