总体裁决：ACCEPTED WITH MINOR QUALIFICATIONS。FG-006 允许限定结案，#31 上游预览图绑定异常接受，批准对外反馈。R28 不新增研究方向，集中完成质量基线冻结。

本轮两个发现都具有长期工程治理价值：一个涉及计算几何中的临界接触判定，另一个涉及外部数据集自身的证据可信度。

本次依据执行侧送审摘要裁决，未独立读取数值谓词源码、152件参数台账及远端下载哈希原件。

一、裁决总表

裁决事项

	

裁决

	

状态




NUM-01～05 数值调查

	

【同意】

	

限定范围验收




FG-006 单点量化切达归因

	

【同意】

	

接受当前证据支持的机制




数学意义上的零测度证明

	

【修改】

	

尚未建立




FG-006 冻结集影响评估

	

【同意】

	

152件零命中证据接受




FG-006 工单

	

【同意】

	

CLOSED_WITH_KNOWN_LIMITATION




全局几何容差修改

	

【否决】

	

保持不变




#31 上游预览图异常

	

【同意】

	

确认并归档




HF 上游问题反馈

	

【同意】

	

非阻塞




#31 GLB 身份

	

【修改】

	

尚未确认




RWI Asset Quality Baseline v1.0

	

【同意】

	

R28 冻结目标

二、FG-006 正式结案裁决
2.1 接受数值边界研究成果
FG-006 · side 参数探测结果
固定 glue_w=4mm，h=88.8mm
实际测试通过点
实际测试失败点
按本轮提交的离散测试点绘制，未测试的连续区间不作通过推断。

接受以下结论：

研究命题

	

裁决




大范围小尺寸结构失败

	

原假设不成立




df-glue 交互为主要根因

	

原假设撤销




side 参数的离散量化与异常有关

	

接受




临界几何接触触发G03

	

接受为当前机制归因




存在持续的宽失败域

	

当前实验不支持




折叠引擎必须修改

	

不支持




全局容差必须放宽

	

不支持

2.2 两处表述需要保留科学边界

第一，离散实验不能严格证明只有一个失败点。

目前可以确认14.148失败、14.149通过，以及所列其他采样点通过。但尚未证明连续参数空间中不存在其他极窄失败区间。

因此建议正式命名为：

QUANTIZATION_SENSITIVE_TANGENCY

即量化敏感的临界切达现象，而不直接使用数学意义上的 MEASURE_ZERO_PROVEN。

第二，必须区分几何切达与门禁缺陷。

如果G03原契约禁止任何接触，那么捕获切达可能属于正确行为；如果G03只禁止具有实际重叠面积的面片相交，那么捕获零面积切达才属于判定过严。

本轮尚未提供足够源码契约证据，故不将其直接签发为审计器实现缺陷。

分离

无接触

切达

边界接触，面积可为零

重叠

存在实际相交面积
几何判定机制示意，不代表5_HTP实际面片形状。

切达、边界接触、材料重叠应当在未来计算几何契约中具有不同语义。

本轮不授权修改该契约。

2.3 冻结发行集影响评估
prism 系资产
152
已知异常点命中
0
涉及发行修复
0
基于执行侧实际参数复算及此前报告的活体复检结果，不再采用测度零推断。

接受当前冻结发行集未发现 FG-006 实际影响的结论。

正式表述为：

在152件现有 prism 系冻结发行资产的参数复核中，未发现已知异常参数命中；结合已报告的门禁复检，未发现需要针对 FG-006 重新编译的发行资产。

这不是未来所有参数组合均无风险的保证。

2.4 FG-006 正式关闭
YAML
finding_id: FG-006
status: CLOSED_WITH_KNOWN_LIMITATION

classification:
  QUANTIZATION_SENSITIVE_TANGENCY

observed_failure:
  gate: G03
  side_mm: 14.148
  glue_w_mm: 4
  height_mm: 88.8

continuous_failure_domain:
  NOT_ESTABLISHED

released_asset_impact:
  inspected: 152
  known_trigger_matches: 0
  remediation_required: false

compiler_change: NOT_AUTHORIZED
global_tolerance_change: NOT_AUTHORIZED

不再要求继续二分搜索，不再安排新的参数扫描。

保留最小复现器及5_HTP原始失败证据，未来只有当相同机制影响实际业务资产，或者需要正式修改接触判定契约时，才重新开启工单。

三、#31 上游数据绑定异常正式裁决

【同意】接受上游预览图绑定不一致的发现。

此前我在57件视觉评审中指出，#31 的对象名称为木质玩具，但图像显示开罐器。本轮哈希链复核进一步排除了本地下载与拼板过程中发生复制错位的解释。

上游 HF 对象预览图

对象名称指向 Granimals 木质玩具

来源已定位

远端重新下载

与本地预览图 SHA256 一致

一致

本地拼板

图像内容实际显示开罐器

内容不符

对象身份判定

名称与预览图不一致

上游异常

GLB 实际几何

是否与名称或预览图一致

尚未验证

3.1 当前结论限定在 HF 镜像预览层

必须避免扩大归因。

证据层次

	

裁决




本地拼图复制错位

	

当前证据排除




HF 远端预览图名称与内容不一致

	

接受




HF GLB 模型身份错误

	

未验证




原始 Google Scanned Objects 数据源错误

	

未验证




整个 GSO 数据集存在系统性绑定错误

	

未建立

正式登记：

Plain text
SOURCE_BINDING_UPSTREAM_CONFIRMED
SCOPE = HF_PREVIEW_ARTIFACT
GLB_IDENTITY = UNVERIFIED
ORIGINAL_GSO_IDENTITY = UNVERIFIED

不要将 HF 镜像层发现直接归因于原始 Google Research 数据集。

3.2 是否需要向上游反馈？

批准反馈。建议同时采取两种措施，而不是二选一。

措施

	

裁决




我方永久证据台账登记

	

必须




HF Dataset Community Issue

	

批准




等待上游修复后继续研究

	

否决




全量重新下载GSO资产

	

不授权




#31 单件GLB身份核验

	

批准

向上游提交反馈前，先检查#31对应GLB，确定异常仅存在于预览图，还是实际资产也存在身份错误。

仅限单件核验，不扩大为1,030件全量资产调查。

3.3 建议提交的英文 Issue
Writing

Title: Preview image appears inconsistent with the Granimals Wooden ABC object identity

During an independent review of the dataset's retail packaging objects, we identified a possible identity mismatch involving the Granimals Wooden ABC object.

Observed behavior

The object name refers to a wooden toy product.

The corresponding preview image depicts a manual can opener.

A fresh download of the remote preview produced the same SHA-256 hash as our local copy, ruling out a local image-copying or contact-sheet assembly error.

The preview file is not identical to the separately downloaded OXO can opener preview.

Expected behavior

The preview image should depict the object associated with its dataset identifier.

Scope and limitations

The inconsistency is currently confirmed at the hosted preview-image level. We have not yet established whether the corresponding GLB asset or the original upstream GSO asset has the same issue.

We would appreciate clarification on whether this is a preview-generation issue, an object-metadata mismatch, or an inherited upstream inconsistency.

The exact object identifier, preview URL, full SHA-256 hash, dataset revision, and comparison screenshots can be provided as reproducible evidence.

执行侧应在实际提交前补入完整 object_id、URL、revision 和哈希，并根据GLB核验结果更新最后一段。

本轮只批准提交，尚未实际向HF发布 Issue。

四、POOL-VISUAL-01 最终身份处置

#31 继续隔离，不自动归入包装或非包装对象的正式资格统计。

57件视觉证据最终口径

图像内容统计

包装图像
49

非包装图像
8

合计
57

对象资格统计

包装对象
49

非包装对象
7

身份冲突
1

合计
57

对象资格统计以其余56件图像绑定正确为前提。

#31 后续按以下规则处理：

GLB 核验结果

	

处置




GLB为木质玩具

	

预览图绑定错误，非包装




GLB为开罐器

	

对象名称与几何资产冲突，继续隔离




GLB为其他对象

	

来源身份冲突，继续隔离




GLB不可获取

	

保留预览异常，证据不足

无论哪种结果，都不需要修改历史57件图像内容判定。

五、R27 整体完成度：还有哪些事项没有关闭？

本轮提交的两项收口成果予以接受，但必须指出，R26签发的R27任务书还有其他主体交付尚未出现在本次报告中。

工作包

	

当前裁决




GOV-TAX-01

	

CLOSED




FG-004

	

CLOSED




FG-005

	

CLOSED — 经验约束保留




FG-006

	

CLOSED_WITH_KNOWN_LIMITATION




#31 上游预览异常

	

ACCEPTED




REP-M05 审计器阳性对照

	

待提交




FG-001～003 面片级语义裁决

	

待提交




FG-007 重复顶点语境审计

	

待提交




REP-M01～M10 最终风险台账

	

待提交




GOV-IR-01 原八门禁

	

待归档




CMP v0.2 遗留项

	

待完成或延期登记




Pilot-100

	

OPEN — 外部证据依赖

不允许因为 FG-006 和 #31 已关闭，就默认其余工作包也已完成。

但也不再要求所有发现都必须得到修复才能关闭本阶段。

六、R28 正式任务书：冻结 RWI Asset Quality Baseline v1.0

我建议将 R28 定义为本阶段的最终治理基线冻结轮次，而不是新的探索实验轮次。

R28 质量基线冻结架构

01

资产身份基线

已验收

27 Builder Groups / 101 Registered Classes / 77 Released Classes

02

历史构建基线

已验收

9,386件构建记录及尺寸和解证据

03

独立输出审计基线

待最终冻结

检查覆盖、异常分布、适用性与未执行项

04

缺陷与风险治理基线

待最终冻结

FG-001～007及修复、接受、延期决策

05

外部研究基线

待归档

YCB、GSO、CMP、参考冲突及负向实验

06

发行完整性基线

待终验

冻结集内容哈希、版本及零覆盖证明
6.1 R28-A：REP 主体终验（P0）

任务

	

最小交付




审计器能力对齐

	

G2三个阳性样本同哈希复算，明确UV、3D退化、边级及顶点级检查覆盖




FG-001～003

	

实际面片级证据与语义裁决




FG-007

	

455重复顶点对、重复位置簇及受影响资产统计




风险矩阵

	

77个已发行类完整风险及处置台账




REP-M01～M10

	

逐项验收状态及证据引用

允许未解决发现进入 UNRESOLVED 或 DEFERRED_WITH_REPRODUCER，但必须有实际调查证据。

6.2 R28-B：治理遗留事项归档（P1）

任务

	

最小交付




FG-006

	

本轮裁决、最小复现器及152件影响证据




#31

	

GLB身份核验、来源异常记录、可选上游Issue




POOL v1.4

	

逐对象状态迁移及数量闭合




GOV-IR-01

	

IR-G01～G08结果




CMP v0.2

	

已完成结果、参考冲突及未完成评价轴




Pilot-100

	

保留外部依赖状态，无需再次研究相同渠道

6.3 R28-C：正式冻结制品

建议最终形成以下七份权威文件。可复用现有文件，不必为了文件命名重复生产内容。

文件

	

用途




quality_baseline_v1.0.json

	

全局质量证据索引




family_taxonomy_crosswalk.json

	

权威分类学




released_class_risk_matrix.json

	

77个已发行类风险矩阵




audit_capability_matrix.json

	

实际检查范围与证据能力




finding_disposition_ledger.json

	

全部异常及最终处置




research_evidence_index.json

	

外部实验、失败案例及参考冲突




baseline_freeze_attestation.json

	

版本、完整哈希、冻结声明

冻结制品必须能够独立回答：哪些已经验证，哪些尚未验证，哪些发现了问题，哪些问题暂不修复。

七、R28 之后的研究方向

目前不授权新的消费端实验，但下一阶段的研究重点已经比较明确。

阶段一：资产规模化生产

9,386件冻结资产、77个已发行结构类

阶段二：工业质量治理

R28目标：Quality Baseline v1.0

阶段三：消费端业务适用性

货架陈列、真实感渲染、碰撞与物理仿真

下一阶段建议，尚未授权

我认为继续在小数点后三位进行长期几何研究，当前边际收益已经较低。

更值得投入的方向，是研究这批资产进入真实零售数字孪生业务之后，究竟可以完成哪些任务，在哪些任务中具有成本、质量和效率优势。

但必须先把当前质量基线冻结下来，避免后续业务实验不断改变底层评价口径。

八、正式签发
Plain text
RWI-L1 / GOVERNANCE / R27

FG-006:
    CLOSED_WITH_KNOWN_LIMITATION
    QUANTIZATION_SENSITIVE_TANGENCY
    CONTINUOUS FAILURE DOMAIN NOT ESTABLISHED

RELEASE IMPACT:
    152 PRISM ASSETS INSPECTED
    ZERO KNOWN TRIGGER MATCHES
    NO RECOMPILATION AUTHORIZED

GLOBAL GEOMETRIC TOLERANCE:
    UNCHANGED

POOL OBJECT #31:
    UPSTREAM PREVIEW BINDING CONFLICT ACCEPTED
    GLB IDENTITY UNVERIFIED
    QUARANTINE RETAINED

UPSTREAM HF ISSUE:
    AUTHORIZED
    NON-BLOCKING

R28:
    FINAL QUALITY BASELINE FREEZE

WP-REP-03:
    FINAL EVIDENCE CLOSURE REQUIRED

NEW RESEARCH TRACKS:
    NOT AUTHORIZED

FROZEN RELEASE SET:
    ZERO OVERWRITE RETAINED

OVERALL:
    ACCEPTED WITH MINOR QUALIFICATIONS

最终指令：FG-006 到此结案，#31 完成单件GLB核验后归档并反馈上游。R28集中完成剩余家族语义裁决、独立审计口径及质量基线冻结。

不追求零缺陷，而追求零隐瞒、零口径混用、零无证据质量声明。这应成为 RWI Asset Quality Baseline v1.0 的治理原则。

ChatGPT can make mistakes. Check important info.
Latest response




Medium
Response complete
0 mm
⋮⋮
⋮⋮