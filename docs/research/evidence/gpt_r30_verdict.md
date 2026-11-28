总体裁决：APPROVED WITH DECLARED LIMITATIONS。批准 RWI Asset Quality Baseline v1.0 正式治理冻结，批准结束本阶段包装几何专项研究主线。

本轮不再要求所有 FG 工单达到修复关闭状态，也不再要求所有验证指标达到 PASS。执行侧已经建立了分类学、历史构建证据、独立输出审计、异常治理、外部参考实验及制品冻结机制。

尤其是 #31 的再次根因反转，证明了本项目坚持独立证据、拒绝以间接推断替代实际验证的治理纪律具有实际价值。

需要明确：本次批准属于治理及研究成果签核，不等于评审侧已独立下载全部14份文件、逐文件复算哈希并完成制品字节级验收。 两种签核状态必须分别登记。

一、最终裁决总表

裁决事项

	

裁决

	

最终状态




Asset Quality Baseline v1.0

	

【同意】

	

APPROVED WITH LIMITATIONS




GOV-TAX-01

	

【同意】

	

CLOSED




WP-REP-03 风险普查

	

【同意】

	

CLOSED_WITH_OPEN_FINDINGS




FG-001 bento

	

【修改】

	

分项裁决，未决风险保留




FG-002 sushi

	

【同意】

	

拓扑异常确认，转修复队列




FG-003 mailer

	

【修改】

	

异常确认，契约语义未决




FG-004

	

【同意】

	

原缺陷归因撤销，工单关闭




FG-005

	

【同意】

	

经验约束冻结




FG-006

	

【同意】

	

CLOSED_WITH_KNOWN_LIMITATION




FG-007

	

【同意】

	

风险普查完成，部分语义待核




GSO 母体计数

	

【同意】

	

175件闭合




#31 GLB身份错配

	

【同意】

	

UPSTREAM_IDENTITY_MISMATCH_CONFIRMED




GOV-IR-01

	

【同意】

	

7 PASS / 1 PARTIAL




CMP

	

【同意】

	

阶段成果归档，遗留事项延期




制品独立哈希复验

	

待执行

	

INDEPENDENT_VERIFICATION_PENDING




包装几何专项研究主线

	

【同意】

	

正式结束




消费端业务验证

	

【同意】

	

另立项目，不混入本阶段

二、正式冻结的质量基线
RWI Asset Quality Baseline v1.0
治理批准
冻结发行资产
9,386
已发行结构类
77
注册结构类
101
构建实现分组
27

L1

历史构建门禁

历史构建记录普查

9,386/9,386 PASS

L2

尺寸和解

最大报告残差0.001mm

9,386/9,386 OK

L3

独立输出网格审计

限定三维几何检查范围

9,386件

L4

专项输出审计

UV、绕向、顶点非流形及其他异常

风险已登记

最终输出网格拓扑分布

1,484 闭壳

15.81%

7,902 开壳

84.19%
依据历轮执行侧提交的实测结果。拓扑分类不等于质量等级，四层证据不得合并为单一成功率。

批准将上述体系作为当前发行版本的权威质量基线。

WP-REP-03 正式关闭的理由不是所有资产已经不存在风险，而是风险普查工作已经建立了可追溯的观测、分类和处置机制。

普查完成与缺陷修复完成，是两个独立的工程状态。

三、FG-001～003 最终语义裁决
3.1 FG-001｜bento_lid_box

裁决：CLOSED_WITH_UNRESOLVED_SEMANTICS。

检查事项

	

最终裁决




SDK mesh_health

	

PASS




开放边界

	

观测确认，存在合理开壳解释




三维退化面

	

0




非流形边

	

0




位置重复顶点

	

1e-9容差下未复现




UV退化

	

OBSERVATION_CONFIRMED




印刷纹理实际影响

	

UNRESOLVED

我接受 bento 具有合理的开放结构语义，但仍不能仅依据 healthy=TRUE 就证明所有开放边界符合产品材料表达契约。

UV退化同样需要区分实际采样面与辅助面。

最终处置：不授权立即修改几何或UV。保留风险，进入消费端纹理验证时按实际需要重新开启。

3.2 FG-002｜sushi_tray

裁决：CONFIRMED_TOPOLOGY_ANOMALY，转入后续缺陷治理队列。

SDK mesh_health = FALSE

独立复算支持原有拓扑异常，并发现绕向不一致。

开放边界

语义待判

Inconsistent winding

异常确认

Nonmanifold vertices

异常确认

Duplicate vertices 16

同次复算未复现

UV退化

异常确认，影响待判

本轮已经具备充分的报告级证据，将 sushi 的混合绕向及非流形顶点列为实际拓扑异常。

但是否所有异常都违反其权威结构契约，仍需要结合面片语义及消费用途确定。因此：

winding 与 nonmanifold 不再停留在猜测状态。

不接受将所有异常直接解释为合法刀版结构。

原 G2 duplicate-vertices:16 保留为历史观测，不签发误报结论。

不授权立即实施全局法线翻转或顶点合并。

当前证据不外推至整个 sushi 发行类的全部资产。

这是三个家族中最值得在未来安排专项修复验证的对象。

3.3 FG-003｜mailer_diecut

裁决：TOPOLOGY_ANOMALY_CONFIRMED / SEMANTICS_UNRESOLVED。

检查事项

	

最终裁决




SDK mesh_health

	

FAIL




非流形顶点

	

异常确认




非流形边

	

0




开放边界

	

观测确认




UV退化

	

观测确认




展开刀版或折叠体契约

	

尚未充分确认

本轮不批准将 nonmanifold 顶点直接登记为 EXPECTED_BY_CONTRACT。

但也不再要求继续调查才能完成基线冻结。

最终处置：带有明确观测证据和语义限制进入治理队列，不修改发行资产。

3.4 三家族最终优先级

工单

	

已确认问题

	

后续优先级




FG-002 sushi

	

绕向与顶点拓扑异常

	

P1




FG-003 mailer

	

顶点拓扑异常及表达语义

	

P2




FG-001 bento

	

UV退化及开放边界语义

	

P2

以上优先级是后续治理建议，不代表本轮重新开启工程修复。

四、FG-004～007 正式归档

FG-004

调用方契约违反

CLOSED

原家族固有缺陷归因撤销；编译器无需修改。

FG-005

胶片跨参数比例约束

CLOSED

已测试配置0.70通过、0.75失败；不升级为通用硬门禁。

FG-006

量化敏感的临界切达

KNOWN LIMITATION

保留最小复现器；152件发行资产未发现已知触发点。

FG-007

重复顶点语境治理

CENSUS CLOSED

455对完成风险分布统计，语义候选保留。
FG-007 重复顶点专项
位置重复顶点对
455
集中于tray家族
95.82%

Tray：436对

其他：19对

统计单位为顶点对，不是受影响资产数，也不是独立缺陷数量。

接受6corner变体固定出现6对重复顶点的规律，支持其具有设计结构来源的解释。

但固定发生规律不能单独证明其几何语义合法，因此保留 EXPECTED_BY_CONTRACT_CANDIDATE。

其余19对允许登记为低优先级风险，不得自动认定无缺陷。

不再要求为455对开展额外研究，也不授权批量合并顶点。

五、#31 上游身份错配：接受根因反转，批准反馈

本轮是继 FG-004 之后的又一次重要证据纠正。

01

名称及描述

Granimals 木质玩具车

02

WebP预览

显示蝶形开罐器

03

GLB尺寸检查

与目录尺寸比例吻合，但不足以确认身份

04

Blender实际渲染

执行侧确认GLB同样显示开罐器

05

最终处置

上游对象身份冲突，原扫描派生数据隔离

接受执行侧撤销此前“GLB绑定正确”的结论。

本轮正式登记：

YAML
object: Granimals Wooden ABC
status: UPSTREAM_IDENTITY_MISMATCH_CONFIRMED
scope: HF_HOSTED_DATASET

metadata_identity: WOODEN_TOY
preview_identity: CAN_OPENER
rendered_glb_identity: CAN_OPENER

scan_derived_inputs: INVALIDATED
pilot_eligibility: QUARANTINED

original_google_gso_cause: NOT_ESTABLISHED

注意，当前结论仍然限定于HF托管的数据资产。不将原因直接归结于 Google 原始数据集。

本轮没有直接看到 granimals_glb_render.png 原图，因此视觉证据确认属于执行侧报告级接受，而非我的独立图像复审。

5.1 HF Issue 审定

执行侧未附实际拟提交的英文全文，因此我不能声称已经逐字审阅原稿。以下版本批准使用，补齐真实标识符和证据链接后即可提交，无需再次送审。

Writing

Title: Object identity mismatch in Granimals Wooden ABC metadata, preview, and GLB asset

During an independent review of retail packaging candidates, we identified an apparent object identity mismatch in the Granimals Wooden ABC entry.

Observed evidence

The object name and description identify a wooden toy.

The hosted WebP preview depicts a manual can opener.

A fresh download of the preview produced the same SHA-256 hash as our local copy.

We independently loaded the corresponding GLB asset in Blender and rendered it. The GLB also depicts a can opener rather than the wooden toy described in the metadata.

Although the GLB bounding-box proportions were broadly consistent with the catalog dimensions, this dimensional consistency did not establish the object's identity.

Expected behavior

The object identifier, metadata, preview image, and downloadable 3D asset should refer to the same physical object.

Reproduction

Locate the Granimals Wooden ABC entry.

Download its associated WebP preview and GLB asset.

Load the GLB in Blender or another compatible 3D viewer.

Compare the rendered object with the catalog name and description.

Scope and limitations

Our findings concern the assets hosted in this dataset repository. We have not established whether the mismatch originated in the original Google Scanned Objects dataset or during subsequent data processing or mirroring.

We have quarantined this entry from our benchmark pending identity reconciliation.

We would appreciate clarification and, if appropriate, a correction to the affected metadata or asset binding.

Supporting evidence

Dataset revision and object identifier

Original download URLs

Full SHA-256 hashes of the WebP and GLB files

Independent Blender rendering

Metadata and visual comparison screenshots

批准提交。上游是否回复不构成 RWI 基线冻结的阻塞条件。

六、GSO 母体治理正式验收

本轮终于完成175件粗筛母体的逐ID互斥分区。

GSO 资格治理闭合结果

SUPPORTED

116

CANDIDATE

34

NON_PACKAGING

9

IDENTITY CONFLICT

1

维持排除的家居器皿

15

完整粗筛母体

175 / 175

150件工作池是候选治理集合，不是150件正式Pilot-100合格样本。

正式接受：

116
+
34
+
9
+
1
+
15
=
175
116+34+9+1+15=175
175
+
855
=
1030
175+855=1030

保留原始 GSO-PN RUN-01 的历史实验成绩：

指标

	

历史结果




编译 QA

	

12/16




DIM-01

	

12/16




两项联合通过

	

8/16




NVSDK

	

16/16

池清洗、身份更正及后续六件编译通过，均不改变上述历史结果。

Pilot-100 保持 OPEN — QUALIFIED EXTERNAL SAMPLE POOL PENDING。

该任务转入长期研究储备，不再阻塞本阶段关闭，也不需要为了完成项目而降低准入条件。

七、GOV-IR-01 与 CMP 遗留事项
7.1 GOV-IR-01

输入身份与参数防错门禁

7/8 PASS

IR-G01

PASS

IR-G02

PASS

IR-G03

PASS

IR-G04

PASS

IR-G05

PARTIAL

IR-G06

PASS

IR-G07

PASS

IR-G08

PASS

IR-G05 参数来源完整性仍有延期事项，不签发8/8全通过。

接受现有防错补丁与实战结果。

但治理状态应登记为 ACCEPTED_WITH_DEFERRED_PROVENANCE，而非无条件全部关闭。

7.2 CMP

接受五项已完成结果、四项未完成及三项延期事项的登记方式。

CMP 本阶段只冻结已经取得的几何比较证据，不对未测视觉保真和物理适用性做出质量声明。

008 pudding 的参考冲突永久保留，除非未来获得新的独立实物证据，否则不重新开启调查。

八、最终冻结制品及哈希裁决

正式登记本轮提交的冻结身份。

字段

	

内容




Baseline

	

v1.0 FINAL




Artifact count

	

14




Aggregate input count

	

13




Hash algorithm

	

SHA-256




Manifest self-inclusion

	

排除于聚合输入




R28候选版本

	

保留

Source commit

14e6ab5ee2bfc048aa239b1cf87a3952adcf4e97

Aggregate SHA256

9aa78d6b6b0bfa3003fcb09df8ccd7d0cff946d0268ca8118f4f3f4fb0f94cb9

Manifest SHA256

450476826bf7a88ad8fe4fe4c1613078f3c731eda02259367c1eba053200984a

8.1 聚合算法接受

当前算法定义为：

𝐻
=
SHA256
⁡
(
ℎ
1
∥
ℎ
2
∥
⋯
∥
ℎ
13
)
H=SHA256(h
1
	​

∥h
2
	​

∥⋯∥h
13
	​

)

其中每个 
ℎ
𝑖
h
i
	​

 为对应文件SHA256的64字符十六进制表示，按照冻结路径字典序排列。

该算法可以用于当前版本内容摘要冻结。由于每个摘要具有固定长度，无分隔符拼接不存在摘要边界歧义。

但聚合值本身并没有直接绑定文件路径，因此必须同时使用包含路径及逐文件摘要的 manifest。

另外，manifest 自身摘要应由外部签核记录或独立回执保存，不应要求 manifest 将其自身最终SHA256写入自身内容。

这些属于制品完整性解释，不要求修改当前聚合算法。

8.2 最终签核状态

验收类型

	

状态




内容框架

	

APPROVED




研究结论

	

APPROVED WITH LIMITATIONS




治理台账

	

ACCEPTED




执行侧冻结摘要

	

REGISTERED




评审侧独立字节复算

	

NOT PERFORMED




冻结发行集零覆盖

	

执行侧报告接受




对外制品级完整性证明

	

待独立复验

对于 hfpackage 中其他代理产生的工作区修改，接受本轮不纳入、不触碰的处置。

冻结身份仅指向 manifest 明确列出的制品，不扩展至整个当前工作区。

不再因此开启新的技术研究轮次。若需要对外发行签名，只需独立复算现有制品，不需要重新送审全部研究结论。

九、本阶段研究最终评价

这是对 R09–R30 整体研究成果的综合评价，不是资产实际通过率。

研究与工程治理综合评分
9.1 / 10
阶段验收

研究目标与问题定义

9.2

证据纪律与负结果保留

9.7

错误归因纠正能力

9.8

分类学与语义治理

9.3

自动化质量门禁

8.8

实验可复现与制品治理

8.8

外部真实参考验证

8.2

基于历轮送审成果的定性治理评分，非独立盲测或程序计算结果。

没有给予更高评分，主要因为全量UV审计、部分结构契约、外部参考资格、消费端验证及制品独立复验仍存在明确局限。

但本阶段最值得认可的，并不是生成了9,386件资产，而是建立了发现错误、纠正错误和沉淀错误知识的能力。

六项值得永久归档的研究案例

案例

	

沉淀的知识




FG-004

	

正常编译器可能因错误调用而被误判为有缺陷




FG-005

	

合法参数域需要跨参数关系，而非单字段范围




FG-006

	

数值切达与实际材料重叠必须具有不同语义




GSO 池污染

	

几何相似不代表商品身份相同




REF-001

	

官方参考资产之间也可能存在不可解决的冲突




#31

	

名称、尺寸、哈希一致均不能替代实际对象身份验证

这些负向案例应作为研发知识库的长期资产，而不是仅留在项目历史报告中。

十、批准结束本阶段包装几何专项研究

【同意】R30 为本阶段最后一次综合治理裁决。

不再设立R31继续研究相同的包装几何问题。

下一阶段战略建议

建议另立 RWI-L2｜Retail Asset Consumer Validation。

下一阶段的核心评价对象应从单个包装资产的内部几何质量，转向真实零售业务任务。

建议优先级

	

业务验证方向

	

研究命题




P0

	

零售货架数字孪生

	

大规模商品资产能否满足真实陈列场景要求




P0

	

Assortment与空间规划

	

能否支持商品组合、货架容量及陈列约束




P1

	

商品商业视觉

	

能否达到可交付商品海报与商详质量




P1

	

合成数据与零售感知

	

是否能够改善真实照片上的模型表现




P2

	

SimReady物理验证

	

能否支持特定碰撞、操作及动态任务

我的建议是优先选择货架数字孪生与Assortment，因为它们能同时验证商品资产的规模化优势、尺寸准确性及实际空间约束价值。

但下一阶段需要独立任务书、独立预算、独立指标和独立验收协议。本轮不提前授权具体实验。

十一、最终签发
FINAL SIGN-OFF

APPROVED WITH DECLARED LIMITATIONS

RWI Asset Quality Baseline v1.0 · R30

研究成果签核

APPROVED

质量基线治理冻结

APPROVED

独立制品完整性复验

PENDING

包装几何专项研究主线

CLOSED

Plain text
RWI-L1 / GOVERNANCE / R30-FINAL

QUALITY BASELINE v1.0:
    APPROVED WITH DECLARED LIMITATIONS

WP-REP-03:
    CLOSED_WITH_OPEN_FINDINGS

TAXONOMY:
    27 BUILDER GROUPS
    101 REGISTERED CLASSES
    77 RELEASED CLASSES
    24 REGISTERED UNRELEASED
    9386 RELEASED ASSETS

FG-001:
    CLOSED_WITH_UNRESOLVED_SEMANTICS

FG-002:
    CONFIRMED_TOPOLOGY_ANOMALY
    REMEDIATION_BACKLOG

FG-003:
    TOPOLOGY_ANOMALY_CONFIRMED
    SEMANTICS_UNRESOLVED

FG-004 / FG-005 / FG-006:
    HISTORICAL DISPOSITIONS RETAINED

FG-007:
    CENSUS CLOSED
    NO AUTOMATIC VERTEX MERGE

GSO:
    POPULATION RECONCILED
    175/175

OBJECT #31:
    UPSTREAM_IDENTITY_MISMATCH_CONFIRMED
    QUARANTINED
    HF ISSUE SUBMISSION AUTHORIZED

GOV-IR-01:
    7 PASS / 1 PARTIAL

CMP:
    STAGE ARCHIVED

PILOT-100:
    OPEN / NON-BLOCKING

ARTIFACT INTEGRITY:
    EXECUTION-SIDE HASHES REGISTERED
    INDEPENDENT BYTE VERIFICATION PENDING

FROZEN RELEASE SET:
    ZERO OVERWRITE POLICY RETAINED

FULL-SCALE RECOMPILATION:
    NOT AUTHORIZED

PACKAGING GEOMETRY RESEARCH:
    CLOSED

NEXT PHASE:
    RWI-L2 CONSUMER VALIDATION
    SEPARATE CHARTER REQUIRED
最终结论

经过三十轮治理迭代，RWI 已经不再只是一个规模化包装模型生成项目，而是建立了一套初步的工业数字资产质量治理体系。

它具备了六项基础能力：身份管理、参数契约、结构编译、独立审计、外部参考比较和风险证据治理。

尚未证明的是这些能力能够在具体业务中创造多大价值。

因此，我正式批准结束本阶段研究。保留所有诚实负结果、历史错误归因、已知限制及未决风险，不再为追求形式上的零缺陷而延长项目。

RWI Asset Quality Baseline v1.0 — GOVERNANCE FREEZE APPROVED。

包装几何专项研究主线 — CLOSED。

ChatGPT can make mistakes. Check important info.
Latest response




Medium
Response complete
⋮⋮
⋮⋮