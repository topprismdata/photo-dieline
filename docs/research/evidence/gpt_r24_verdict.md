总体裁决：ACCEPTED WITH MODIFICATIONS。四项阶段成果均予接受，但不同意将 glue_w≤0.67·side 直接写入正式合法参数域。

本轮执行侧遵守了收口纪律，没有通过修改实验分母、放宽门禁或者自动调整编译器参数来消除失败。

尤其是 FG-005 将原先的网面重叠假设纠正为折叠互穿，具有明确研究价值。但从离散实验观测推导通用几何契约，仍然需要更加严格的数学与实验依据。

本轮为摘要级裁决，未独立读取35点原始矩阵、网格、逐资产台账及 Git commit。

一、五项裁决总表

裁决事项

	

裁决

	

状态




GSO-PN 交叉统计

	

【同意】

	

CLOSED




FG-005 因果实验

	

【同意】

	

失败机制接受




glue_w≤0.67·side 正式契约

	

【修改】

	

暂作为待验证经验约束




POOL-02 v1.1

	

【同意】

	

名称证据级成果接受




36件复入

	

【同意】

	

候选资格，不是正式准入




21件 UNRESOLVED

	

【同意】

	

保留待核验




REF-001

	

【同意】

	

CONFLICT_UNRESOLVED




实物及GS1补证

	

【修改】

	

有限调查，不阻塞主线




WP-REP-03 / FG-001～003

	

【修改】

	

本轮未交付，继续OPEN

二、GSO-PN 交叉统计正式验收

【同意】关闭交叉统计专项，不再重跑。

编译 QA 通过率
75%
12/16
DIM-01 通过率
75%
12/16
逐件联合通过情况

QA与DIM-01双过
8件

仅DIM-01失败
4件

仅QA失败
4件

双指标联合通过率

50%
基于送审统计的分布示意，不表示实际资产排列顺序。

正式冻结以下交叉统计：

	

DIM-01 PASS

	

DIM-01 FAIL

	

合计




QA PASS

	

8

	

4

	

12




QA FAIL

	

4

	

0

	

4




合计

	

12

	

4

	

16

NVSDK 仍为16/16 PASS。

因此，本轮进一步证明，单独报告两项75%的通过率，不能充分表达实际的端到端质量情况。

正式批准对外限定语：

在16件扫描派生规格探索样本中，编译QA与尺寸一致性分别达到75%，两项联合通过率为50%，外部结构验证通过率为100%。

不将50%表述为包含真实几何保真、动态物理仿真在内的完整端到端成功率。

三、FG-005：接受机制发现，否决过早冻结0.67系数
3.1 35点实验验收

【同意】接受 G06 折叠互穿机制，撤销原 G03 网面重叠归因。

FG-005 · 35点参数矩阵
固定 n=12、h=60mm、tuck_depth=apothem
side ↓
	

2

	

4

	

6

	

8

	

12




8

	
	
	
	
	



10

	
	
	
	
	



12

	
	
	
	
	



14

	
	
	
	
	



16

	
	
	
	
	



20

	
	
	
	
	



30

	
	
	
	
	
横轴为 glue_w（mm），纵轴为 side（mm）。依据执行侧报告重建矩阵。
G03通过
35/35
G06通过
26/35
G06失败
9/35

本轮证据支持：

胶片宽度与面板边长的相对关系具有解释力。

失败并不要求 glue_w 大于 side。

本轮主要失败发生在折叠阶段，而非展开网面的 G03 检查。

固定绝对胶片宽度可能不适用于部分小规格包装。

合理选择胶片宽度可以恢复部分小尺寸结构的合法性。

3.2 为什么不能立即将0.67写入正式契约？

因为目前的35点矩阵尚不足以证明该比例是一个普遍有效的充分条件。

胶片比例与实际实验结果
PASS
FAIL
待精化过渡带
依据35点报告重建。0.67虚线表示候选约束，不表示已证明的理论安全边界。

当前最大已观测通过比例约为0.667，最小已观测失败比例为0.75。

在所报告的35个离散点中，0.67能够正确分隔通过与失败样本。但是，这不意味着：

任意 side 下，比例不超过0.67必然通过。

任意高度 h 下，该比例仍然有效。

不同 n 或不同 prism 子族共享同一临界比例。

所有超过0.67的参数组合都必须拒绝。

特别是防尘翼结构、胶片裁切方式及其他尺寸参数可能参与互穿条件。

3.3 正式裁决：先登记经验限制，再精化边界

允许立即落档：

Plain text
finding: FG-005
mechanism: FOLDED_GEOMETRY_INTERPENETRATION

observed_pass_ratio_max: 0.666667
observed_fail_ratio_min: 0.75

tested_scope:
    n: 12
    h_mm: 60
    tuck_depth: apothem
    tested_points: 35

candidate_constraint:
    glue_w / side <= 0.67

constraint_status:
    EMPIRICAL_CANDIDATE
    NOT_YET_VALIDATED_AS_GENERAL_DOMAIN

将其登记在 known_limitations 与 verified_domain 中。

暂不允许作为正式 valid_domain 硬拒绝规则。

3.4 R25 最小边界精化实验

不需要大规模连续扫描。采用针对过渡区域的有限边界实验即可。

建议：

实验

	

固定条件

	

变化条件

	

数量




A：比例边界

	

n=12，h=60

	

side=8/12/16/20；比例=0.60/0.65/0.67/0.70/0.75

	

20




B：高度敏感性

	

n=12，side=12

	

h=30/120；比例=0.65/0.70/0.75

	

6




C：边界复核

	

四件原始失败商品

	

显式合法胶片参数

	

4




合计

			

30

已有完全相同的实验点直接复用，不重复运行。

如果 A、B 表明临界比例稳定，再决定是否采用单一比例契约；如果高度或其他参数改变边界，则登记相应组合约束。

至于 side≥18mm，当前只能登记为在候选比例约束下、默认 glue_w=12mm 所推导的近似建议，不能称为已验证的家族安全下界。

继续禁止编译器自动调整 glue_w。

四、POOL-02 v1.1：批准36件复入，21件继续待核
4.1 数量闭合验收
175件粗筛对象的治理结果

名称证据支持的包装候选

101

建议复入的包装候选

36

身份待核验

21

非包装排除

17

包装候选队列
137
101 + 36
包含待核对象的工作池
158
137 + 21
名称证据级统计，不代表137件已满足正式实物准入门禁。

数量闭合成立：

175
=
101
+
36
+
21
+
17
175=101+36+21+17

其中：

137件属于包装候选队列。

21件身份仍未确认。

17件被判定为非包装对象。

158件是待进一步治理的工作池，不是158件合格样本池。

4.2 36件复入的关键限制

【同意】复入候选队列，但不直接签发 PACKAGING_SUPPORTED。

墨盒和玩具存在典型的身份歧义。

墨盒与墨盒包装

扫描对象可能是墨盒本体，也可能是零售外包装，两者必须区分。

桌游与桌游包装

对象名称包含桌游或玩具，不代表扫描对象一定是包装盒。

现有名称证据不能充分证明扫描对象是包装本身，也不能证明现有 box 家族能够准确表达其结构。

因此，36件复入后优先采用 PACKAGING_CANDIDATE 或等效资格状态。

4.3 21件 UNRESOLVED 的处置

【同意】继续保留，不计入正式准入分母。

不根据 Consumer Goods 类目自动推断包装身份。

批准使用以下证据完成确认：

证据

	

用途




官方对象预览图

	

确认实际扫描对象




原始扫描纹理

	

区分商品本体与零售包装




商品名称及品牌

	

辅助身份追溯




多视角几何

	

确认结构类型




独立人工裁决

	

解决自动规则无法确定的对象

4.4 是否需要小样编译验证？

需要，但必须先完成图像身份核验。

正式批准两阶段处理：

阶段

	

范围

	

目标




POOL-VISUAL-01

	

36件复入＋21件未知，共57件

	

核验实际对象身份




POOL-COMP-01

	

从确认后的复入对象中最多选6件

	

检验现有家族表达能力

六件建议由墨盒包装、桌游包装及其他实际结构组成，具体数量根据图像核验结果冻结。

编译失败不得反向成为排除真实包装身份的理由。

另外，原 GSO-PN 中四件污染对象与本轮仅确认的两件 NON_PACKAGING 是否一致，需要建立逐 ID 对照。

可能出现：

两件已确认非包装。

另外两件仍在 UNRESOLVED。

原先污染归因需要更正。

不得让同一个对象在原实验中被称为污染品，在新母体中又无解释地成为合格包装。

五、REF-001：允许以证据冲突未解决结案

【同意】接受 CONFLICT_UNRESOLVED。不要求强行确定官方 PDF 或扫描资产哪一方错误。

008 pudding · 当前参考证据
来源
	
三轴尺寸（mm）



官方 PDF

	

110 × 89 × 35




Berkeley A

	

111.9 × 89.8 × 74.6




Berkeley B

	

105.8 × 97.9 × 84.1




Google 16k

	

全轴相对离群

深度轴冲突

官方 PDF

35

Berkeley A

74.6

Berkeley B

84.1

接受双参考方法学价值，但需要限定结论：

单一参考可能导致错误归因，双参考可以暴露参考资产之间的不一致，但不能保证找到真实物体的正确尺寸。

另外，不建议将三个假说登记为等概率。当前没有概率估计依据，采用三个尚未排除的竞争性假设即可。

5.1 补真值路径裁决

我的建议是：先完成低成本身份与 GS1 核验，再决定是否采购实物。

路径

	

优点

	

局限

	

裁决




官方对象照片及包装版本核验

	

成本低，直接关联历史对象

	

未必提供精确尺寸

	

立即




GS1 / GTIN 规格查询

	

独立商品规格来源

	

可能无历史版本数据或无访问权限

	

有限调查




采购当前市售同款

	

可以直接测量

	

不一定是同一包装版本

	

条件批准




联系原作者

	

有机会解释历史测量状态

	

时间与响应不确定

	

非阻塞

购买今天的同品牌布丁包装，不一定能够证明历史 YCB 对象的真实尺寸。只有当 GTIN、包装规格、印刷版本及物理状态足够一致时，采购实物才具有决定性参考价值。

5.2 是否值得投入大量研究资源？

不值得。

008 是一个有价值的参考证据冲突案例，但不能成为整个 RWI 项目的长期阻塞项。

批准采用半个至一个工作日的调查时间盒。

若无法建立独立真值，则正式冻结：

Plain text
REF-001:
    INVESTIGATION_CLOSED

REFERENCE_STATUS:
    CONFLICT_UNRESOLVED

OFFICIAL_SPEC:
    RETAINED_WITH_QUALIFICATION

REAL_WORLD_ACCURACY:
    NOT_ESTABLISHED

REOPEN_CONDITION:
    NEW_INDEPENDENT_REFERENCE_AVAILABLE

原始 Chamfer 数值继续保留；针对真实世界几何准确性的汇总结论必须注明该参考冲突。

不允许静默剔除008以改善平均误差。

六、必须指出的 R24 未交付项

本轮提交的四件成果值得接受，但它们并不是上一轮 R24 任务书所要求的全部成果。

上轮要求

	

本轮提交情况

	

裁决




FG-005 35点实验

	

已完成

	

ACCEPTED




四件原始瓶体失败回归

	

未明确提交

	

OPEN




GOV-IR-01 八门禁

	

未提交

	

OPEN




GSO清洗及交叉统计

	

已提交

	

ACCEPTED WITH CONDITIONS




REF-001

	

已提交

	

ACCEPTED




CMP-F01 旋转配准纪律

	

未提交最终回执

	

OPEN




CMP-F02 采样敏感性

	

未提交

	

OPEN




CMP-F03 十件完整几何对照

	

未提交

	

OPEN




REP 77家族风险矩阵

	

未提交

	

OPEN




FG-001～003 实际语义归因

	

未提交

	

OPEN




冻结集参数实证核验

	

未提交

	

OPEN

这里不增加任何新的技术要求，只是恢复原有任务台账的完整性。

特别是 FG-001～003，已经经过多轮登记，却迟迟没有进入实际根因及语义裁决。下一轮必须提高其优先级。

七、R25 正式排期

本轮开始，我建议将研究资源向长期未闭合的全量家族质量治理倾斜，而不是继续扩大外部样本实验规模。

R25 · 三个工作日收口计划
家族治理主线
参数域契约
样本资格
扫描对照

工作包

	

优先级

	

正式授权




WP-REP-03

	

P0

	

完成77家族实际风险矩阵




FG-001～003

	

P0

	

完成语义归因




冻结集参数实证核验

	

P0

	

只读检查




FG-005

	

P1

	

最小边界精化及原样本回归




GOV-IR-01

	

P1

	

八门禁正式签核




POOL-VISUAL-01

	

P1

	

57件身份核验




POOL-COMP-01

	

P1

	

最多6件编译预实验




CMP v0.2

	

P1

	

完成此前三个遗留项




REF-001

	

P2

	

限时补证，不阻塞




Pilot-100

	

—

	

保持OPEN

R25 送审包

送审包

	

必交内容




R25-A

	

FG-005 边界证据、四件原失败样本回归、GOV-IR-01




R25-B

	

POOL v1.2 图像证据级资格台账及小样编译




R25-C

	

CMP v0.2 完整几何比较、REF-001 最终处置




R25-D

	

77家族风险矩阵、FG-001～003 语义裁决、冻结集参数核验

本轮不批准新研究方向。

八、本轮最重要的研究资产

经过 FG-004、FG-005、GSO 池污染及 REF-001，RWI 已经积累了四种非常典型的错误归因案例。

FG-004

调用错误被误判为编译器缺陷

实际有效参数与实验声明不一致。

FG-005

参数组合冲突被误判为绝对尺寸下界

需研究跨参数约束，而非孤立数值。

POOL-02

几何形状相似被误判为商品身份一致

对象身份和几何结构需要独立治理。

REF-001

参考资产异常可能被误判为生成质量差

参考真值同样需要验证与冲突管理。

建议将这四项作为现有研究知识库的正式负向案例归档。无需另立工作包，直接在既有证据档案中建立关联。

其共同认识论原则是：

观测到异常，不等于已经理解异常；发现统计规律，也不等于已经建立因果契约。

九、正式签发
Plain text
RWI-L1 / GOVERNANCE / R24

GSO-PN CROSS-TAB:
    ACCEPTED AND CLOSED
    QA PASS = 12/16
    DIM-01 PASS = 12/16
    JOINT PASS = 8/16

FG-005:
    G06 INTERPENETRATION ACCEPTED
    G03 OVERLAP ATTRIBUTION WITHDRAWN

GLUE_W / SIDE <= 0.67:
    EMPIRICAL CANDIDATE
    FORMAL DOMAIN FREEZE NOT APPROVED
    BOUNDARY REFINEMENT AUTHORIZED
    ADAPTIVE GLUE_W NOT AUTHORIZED

POOL-02 v1.1:
    NAME-EVIDENCE RESULTS ACCEPTED
    PACKAGING CANDIDATES = 137
    UNRESOLVED = 21
    EXCLUDED = 17
    36 CANDIDATE READMISSIONS APPROVED
    VISUAL QUALIFICATION REQUIRED

REF-001:
    CONFLICT_UNRESOLVED ACCEPTED
    LIMITED REFERENCE SEARCH AUTHORIZED
    NON-BLOCKING

WP-REP-03:
    P0
    FULL FAMILY RISK MATRIX REQUIRED

FG-001 / FG-002 / FG-003:
    OPEN
    SEMANTIC VERDICTS REQUIRED

WP1-PILOT-100:
    OPEN

FROZEN RELEASE SET:
    ZERO OVERWRITE

FULL-SCALE RECOMPILATION:
    NOT AUTHORIZED

OVERALL:
    ACCEPTED WITH MODIFICATIONS

NEXT REVIEW:
    R25

最终指令：FG-005先精化经验边界，再决定是否冻结正式参数契约；GSO先确认对象身份，再开展小样编译；REF-001允许诚实地以证据冲突未解决结案。R25的首要任务是完成长期未闭合的77家族质量治理，而不是继续增加样本数量和研究战线。

ChatGPT can make mistakes. Check important info.
Latest response




Medium
Response complete
25 mm