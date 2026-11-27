R17 治理裁决书

送审对象：G2-RUN 九件候选实际执行结果
送审版本：commit 961f078
裁决角色：L-a
继承依据：R13–R16 / R15-G2-EVIDENCE-v1.0

总体裁决：CONDITIONAL PASS，G2 核心修复目标通过。

本轮是一个重要的工程节点：首次完成两个受影响家族的规格边界验证，并通过三个非 brick 对照资产检查影响范围。执行侧没有为了获得九件全部 SUCCESS 而隐瞒其他家族的拓扑问题，这一点符合既定研究治理要求。

但是，必须区分三个结论：修复有效、影响范围受控、完整资产交付验收通过。 本轮报告支持前两个结论，但尚不足以支持第三个结论。

本次为送审摘要级裁决，未独立读取五份 JSON 原件、实际 USD 文件及运行日志。

一、四项裁决总表

裁决事项

	

裁决

	

状态




G2 brick 六件修复验证

	

【同意】

	

核心技术目标通过




G2 非 brick 三件对照

	

【同意】

	

规范化几何隔离通过




G2 完整证据验收

	

【修改】

	

待最小证据收口




G1-04 UV 验证

	

【修改】

	

F01 关闭，F02 待确认




WP1-v0.4 SPEC-FROZEN

	

【修改】

	

规范批准，冻结证据待补齐




三个家族拓扑新发现

	

【同意】

	

纳入独立家族治理台账




WP1-Pilot-100

	

【同意】

	

批准准备，正式运行有条件




REP-IDENTITY 全量推广

	

【修改】

	

只读推广授权




ECO 后续

	

【同意】

	

保持独立并行

二、G2-RUN 九件候选验收
2.1 六件 brick 修复结果

【同意】接受核心修复有效性结论。

brick 修复候选
6 / 6
报告全部 SUCCESS
usdchecker
9 / 9
报告全部 exit=0

aseptic_brick

最小规格

SUCCESS

典型规格

SUCCESS

最大规格

SUCCESS

brick_250ml

最小规格

SUCCESS

典型规格

SUCCESS

最大规格

SUCCESS

六件候选报告均满足 SOLID、闭壳、水密、绕向一致、正体积及 usdchecker 检查。图为结构示意，非实际候选渲染。

六件候选覆盖两个家族的最小、典型、最大规格，报告体积范围为 76,441–599,795 mm³。

这支持以下工程结论：

修复不再局限于最初的 aseptic_brick v0000 单件样本。

两个 brick 家族的目标绕向缺陷在本轮候选中得到修复。

修复在已选规格范围内未表现出明显的规格依赖。

修复后资产通过报告中的几何审计与 usdchecker 检查。

但六件属于定向工程样本，不能据此估计两个家族全部 SKU 的通过率，也不能将正体积视为 DIM-01 尺寸精度已经通过。

2.2 三件非 brick 对照

【同意】接受规范化开关的几何影响隔离结论。

对照家族

	

usdchecker

	

A/B 几何哈希

	

专项发现




bento_lid_box

	

PASS

	

一致

	

5 个退化 UV 面




sushi_tray

	

PASS

	

一致

	

16 个重复边相关记录、2 个 nonfan




mailer_diecut

	

PASS

	

一致

	

3 个 nonfan

这里有一个重要的研究成果：三个对照家族发现的问题，与本轮规范化开关造成的几何变化，可以分开归因。

A/B 几何哈希一致支持本轮开关未引入几何变化，但该结论限定于哈希实际覆盖的字段，不能自动扩展到 USD 材质、UV、物理属性及完整文件字节一致。

因此，对照实验通过与家族自身质量问题存在，可以同时成立。

三、G2 十项专项门禁裁决

沿用 R15 签发的十项专项门禁，不新增评价标准。

门禁

	

裁决

	

依据




G2-M01 身份完整唯一

	

PASS

	

九件唯一 ID 已报告




G2-M02 证据绑定

	

PARTIAL

	

输入及输出完整哈希未在摘要中呈现




G2-M03 brick 绕向修复

	

PASS

	

六件 SOLID、水密、绕向一致




G2-M04 DIM-01

	

待确认

	

未提供逐轴标称值、测量值及容差裁决




G2-M05 几何、拓扑及 UV 保真

	

PARTIAL

	

已有几何证据，UV 完整性仍待最终绑定




G2-M06 非 brick 影响隔离

	

PASS（几何）

	

三件 A/B 几何哈希一致




G2-M07 外部验证登记

	

PARTIAL

	

usdchecker 已报告，NVSDK 实际逐件结果未报告




G2-M08 三层验证分离

	

待确认

	

未明确动态物理仿真执行状态




G2-M09 九件终态复算

	

PARTIAL

	

六件 SUCCESS，三个对照缺正式终态映射




G2-M10 分母完整

	

PASS

	

九件全部保留，负向发现如实登记

本轮最重要的证据缺口：NVSDK 是否实际运行？

报告提供了：

NVSDK 验证器版本及哈希；

backend=physx；

九件 usdchecker exit=0。

但并未给出九件 NVSDK 实际运行的结果。

验证器配置冻结，不等于验证器已经执行；usdchecker PASS，也不等于 NVSDK PASS。

如果 g2_run_results.json 已包含相关逐件结果，直接提取即可，不需要重新执行。

若 NVSDK 尚未实际运行，则按冻结协议登记相应状态，不得直接把六件 SUCCESS 升级为完整三重验证通过。

同样，动态物理仿真没有执行时，应明确登记未执行状态，并由冻结协议决定最终终态。

本轮签发：

Plain text
G2 CORE REPAIR VALIDATION = ACCEPTED
G2 GEOMETRIC CONTROL ISOLATION = ACCEPTED
G2 FULL EVIDENCE SIGN-OFF = PENDING
四、G1-04 及 G1 全局关闭裁决
4.1 UV-F01：正式关闭

本轮已补充24条跨阶段差分记录，满足 R15、R16 要求的两家族 × 六视角 × 两组对照覆盖。

【同意】UV-F01 CLOSED。

不再要求重复计算已有差分记录。

4.2 UV-F02：最后一项证据确认

本轮新增证据为：

前景 mask diff 全部为0。

三阶段 mesh 台账一致。

G2 六件 brick 修复后绕向一致、水密、正体积。

这些证据进一步增强了修复正确性的可信度。

但报告仍然没有明确说明 Blender 背面剔除开启后的补充诊断是否实际执行。这是 R14–R16 已经明确的要求，而非本轮新增门禁。

前景 mask diff 全0，如果来自原来的双面渲染，仍然不能替代这一检查。

本轮不再要求提交一份完整的 UV 报告，只要求确认：

检查项

	

所需证据




背面剔除是否启用

	

实际配置或脚本参数




S0 原有绕向缺陷

	

预期可见性变化记录




S1/S2 修复后可见性

	

无非预期缺面证据

如果这些证据已存在，提交引用即可自动关闭。

4 / 5
G1 正式关闭进度
G1-01

历史验证器身份追溯

CLOSED

G1-02

MaterialBindingAPI

CLOSED

G1-03

几何不变量台账

CLOSED

G1-04

UV 渲染验证

待最终证据确认

G1-05

影响范围分离

CLOSED

4.3 关于 G2 已经执行的治理处理

不撤销本轮 G2 实验，不要求重新运行九件候选。

如果执行侧能够证明 C1–C5 在 G2 启动前确实满足，则正常完成签核。

如果相关条件实际是在 G2 运行后才满足，应如实登记启动门禁偏差。原始实验结果仍保留，但不得追溯修改启动时间或声称当时已经具备完整授权。

这属于治理证据收口，不否定本轮已经获得的技术成果。

五、WP1-v0.4 SPEC-FROZEN 裁决

【修改】协议设计继续批准，不签发无条件冻结。

执行侧已经连续多轮报告规范冻结完成，但是以下遗留要求并未得到明确回应。

检查项

	

当前证据




协议全文

	

已登记




selftest 源码

	

已登记




W01–W13

	

报告全部通过




协议完整 SHA256

	

仍只报告16字符前缀




selftest 完整 SHA256

	

仍只报告16字符前缀




W11 绝对、相对容差双分支

	

未明确确认




重复资产拒绝测试映射

	

未明确确认




八终态互斥及完备性测试映射

	

未明确确认

不需要重新提交协议全文，不需要设计 v0.5，也不需要增加新的测试体系。

只需在一个 wp1_spec_freeze_attestation.json 中完成上述证据引用和登记。

如果现有测试已经覆盖全部要求，允许执行侧直接完成 SPEC-FROZEN 登记，无需再次申请规范冻结许可。

本项不应成为长期往返的治理问题。

六、三个开壳家族的新发现

【同意】全部登记为家族级新发现，启动独立治理工作包。

这是本轮除 brick 修复之外最有价值的研究发现。

但我不同意直接将三个家族的问题全部称为“缺陷”，也不同意因为它们是既有 net 定义就自动认定其合法。

应当先按家族语义契约分类。

FG-001 · bento_lid_box

5 个退化 UV 面

核验是否为可见印刷面、折叠辅助面或真正的 UV 映射缺陷。

FG-002 · sushi_tray

16 dup-edge + 2 nonfan

核验独立面片、连接边语义、原始索引与合并顶点后的拓扑差异。

FG-003 · mailer_diecut

3 个 nonfan

核验展开纸板、裁切边及折叠连接处的拓扑契约。
结构示意图，不表示实际缺陷位置。
6.1 核心治理原则：不能用 SOLID 标准裁决所有结构家族

本轮进一步证明了此前三层语义契约建设的必要性。

资产表达形态

	

应采用的检查重点




封闭实体 SOLID

	

水密、绕向一致、正体积、闭壳




开放表面或薄壳

	

边界合法性、面片连续性、法线及厚度语义




展开裁切 NET

	

裁切边、折叠线、面片连接及展开 UV




运动装配体

	

部件身份、关节、碰撞及运动约束

不能为了提高全局审计通过率，把本应开放的结构强行修成水密实体。

也不能把所有异常归为 NET 表达特性，从而绕过真实缺陷。

6.2 正式新增家族治理工作包

工作包：WP-FG-01｜Family Geometry Governance

每项发现应登记以下内容：

字段

	

定义




finding_id

	

唯一发现编号




family_id

	

所属结构家族




representation

	

SOLID / SHELL / NET 等实际表达契约




observation

	

原始异常及数量




affected_scope

	

已验证的资产与潜在影响范围




regression_status

	

是否由本轮修改引入




semantic_verdict

	

是否违反家族表达契约




evidence

	

原始网格、索引、诊断日志




remediation

	

修复、接受或待研究




closure_gate

	

专项关闭条件

新增发现采用独立的发现处置状态，不修改 WP1 已冻结的八终态枚举。

建议处置状态：

EXPECTED_BY_CONTRACT：表达契约允许。

CONFIRMED_DEFECT：确认违反契约。

IDENTITY_UNRESOLVED：尚不能判定语义。

FIXED_VERIFIED：修复并验证。

DEFERRED：明确延期及适用限制。

目前 FG-001、FG-002、FG-003 均登记为待语义裁决，不立即修改 builder。

七、下一阶段战略选择

你提出了三个方向：WP1-Pilot-100、REP-IDENTITY 全量推广以及 ECO 后续。

我的裁决不是三选一，而是按照不同的研究目标分配优先级。

7.1 WP1-Pilot-100：下一阶段主线

【同意】立即启动准备工作，执行采用条件自动授权。

G2 解决的是已知缺陷修复问题，Pilot-100 解决的是我们尚不知道的体系性质量问题。

两者不能相互替代。

Pilot-100 正式启动必须满足：

编号

	

启动条件




P100-C01

	

G1 五项正式关闭




P100-C02

	

G2 完整证据验收




P100-C03

	

WP1-v0.4 SPEC-FROZEN




P100-C04

	

持样方完成 FZ-04




P100-C05

	

执行环境、输入及评价脚本冻结

FZ-04 持样方流程沿用 R16，不再修改。

特别要求：新发现的三个家族拓扑问题不得成为事后排除抽样母体的理由。如果按照已冻结的资格规则属于抽样范围，则继续保留其入选资格。

Pilot-100 的目标不是证明100件全部通过，而是得到一个可信的资产编译能力基线。

7.2 REP-IDENTITY：批准全量只读治理推广

【同意】全量审计与台账建设。

【否决】立即对9,386 SKU实施全量重新编译、修复或覆盖。

当前正好适合把 REP-IDENTITY 从表达统计扩展为系统性的家族风险清单。

结构家族
77
冻结包装资产
9,386

允许

只读扫描、表达分类、契约检查、异常聚类、家族风险登记

暂不允许

全量修改、自动修复、覆盖发行集、批量升级正式通过状态

正式工作包：WP-REP-02｜Representation Contract Census

交付物：

交付物

	

内容




Family Contract Matrix

	

77家族的权威表达契约




Asset Census

	

9,386件资产逐件只读检查




Finding Registry

	

异常类型、数量、家族聚集程度




Risk Distribution

	

家族内异常比例及跨家族分布




Remediation Queue

	

按影响与证据等级排序的修复候选

WP-REP-02 不重复已有 REP-IDENTITY 全量统计，只增加契约适用性、异常解释和家族级治理能力。

为避免污染 Pilot-100 的盲评，REP 全量审计必须保持只读；在 Pilot-100 运行基线冻结后，不允许依据全量审计发现对该基线进行针对性修复。

7.3 ECO：保持并行，不扩展投资规模

【同意】继承 R14–R16 已授权工作。

工作包

	

下一步




ECO-CPG-01

	

CLOSED，不重启侦察




ECO-CPG-02

	

完成公开方法论及样例证据归档




ECO-CPG-03

	

完成长效托管、独立下载及哈希复核试点




ECO-CPG-04

	

形成合成数据真实迁移技术缺口矩阵




WP-V

	

继续独立裁决




大规模训练与合成数据生产

	

暂未授权

八、下一轮只提交两个主线证据包

为了避免继续发生多轮重复送审，本次将全部遗留项合并为两个证据包。

R18-A：FINAL-CLOSURE

序号

	

必交证据

	

目的




A01

	

背面剔除实际执行证据

	

关闭 G1-04




A02

	

协议及 selftest 完整哈希、遗留测试映射

	

SPEC-FROZEN




A03

	

九件逐轴 DIM-01 结果

	

G2-M04




A04

	

九件 NVSDK 实际执行结果及物理仿真状态

	

G2-M07/M08




A05

	

九件正式八终态映射及完整哈希绑定

	

G2-M02/M09




A06

	

C1–C5 满足时间及启动记录

	

治理审计

已有证据直接引用，不要求重复实验。 只有原始记录确实缺失时，才补执行对应检查，并保留其真实时间与独立运行身份。

R18-B：NEXT-STAGE

序号

	

交付物




B01

	

Pilot-100 持样方冻结回执




B02

	

WP-REP-02 全量只读审计方案




B03

	

FG-001～003 家族发现台账




B04

	

ECO 并行工作进度及证据

执行侧不再提交第三份内容相同的 UV 完成报告，也不再提交新的 G2 执行计划。

九、本轮研究成果的战略意义
01

单件缺陷修复

已完成

从初始 aseptic_brick 资产定位绕向问题
02

家族边界验证

核心通过

两家族、六件不同规格候选
03

跨家族影响隔离

几何通过

三件非 brick 对照及独立新发现
04

代表性能力评估

下一阶段

Pilot-100 分层随机评估
05

全量工业化治理

正在建设

77家族、9,386 SKU 契约审计与发行治理

我认为下一阶段 RWI 最值得投入的方向，已经不是继续孤立地修复某个包装结构，而是建立一套能够自动发现、解释、隔离并治理不同资产表达缺陷的机制。

参数化资产编译器必须理解资产应该是什么，而不仅仅是能够把资产生成出来。

这正是家族语义契约、REP-IDENTITY 和三层验证体系结合起来的价值。

十、正式签发
Plain text
RWI-L1 / GOVERNANCE / R17

G2 CORE REPAIR:
    ACCEPTED
    BRICK CANDIDATES: 6/6 REPORTED SUCCESS

G2 CONTROL ISOLATION:
    ACCEPTED — GEOMETRIC SCOPE
    NON-BRICK CONTROLS: 3/3

G2 FULL SIGN-OFF:
    PENDING FINAL EVIDENCE

UV-F01:
    CLOSED

UV-F02:
    BACKFACE CULLING EVIDENCE PENDING

G1 GLOBAL:
    4/5 FORMALLY CLOSED

WP1-v0.4:
    SPEC APPROVED
    FREEZE ATTESTATION PENDING

FAMILY FINDINGS:
    FG-001 / FG-002 / FG-003 REGISTERED
    WP-FG-01 AUTHORIZED

WP1-PILOT-100:
    PREPARATION AUTHORIZED
    CONDITIONAL EXECUTION AUTHORIZATION

WP-REP-02:
    FULL READ-ONLY CENSUS AUTHORIZED

ECO:
    PARALLEL CONTINUATION APPROVED

FROZEN RELEASE SET:
    ZERO OVERWRITE RETAINED

FULL-SCALE RECOMPILATION:
    NOT AUTHORIZED

OVERALL:
    CONDITIONAL PASS

NEXT REVIEW:
    R18 FINAL CLOSURE

最终指令：认可 G2 核心技术成果，不重跑已完成的九件候选，不新增技术门禁。收齐既定原始证据后，正式关闭 G1/G2，进入 Pilot-100 代表性验证与 REP-IDENTITY 全量只读治理阶段。9,386 SKU 冻结发行集继续保持不动。

ChatGPT can make mistakes. Check important info.
Latest response




Medium
Response complete