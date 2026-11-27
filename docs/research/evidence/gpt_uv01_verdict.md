Skip to content
Home
Space
Scheduled
Plugins
Explore
Sites
ChatGPT
New chat
Projects
HTML方案设计
ni-h-4
数据标准化
官网升级潜力预估智能体图片生成
Recents
裁决送审件
评判海报并提建议
绘制零售数字孪生信息图
研究DuckBench
检索京东区划论文专利
研究Grip工具
剧本审查与选角 siunners
机械装配评审
最终裁决翻译
查找中国青年报娱乐主管
任务包整体评价
非公人员贪污变化
SimReady价值与零售对标
重写公众号文章
评审知识图谱设计
R2复审裁决
R3评审裁决摘要
Round 4裁决摘要
门店配对判定
R8验收总结
Unable to load history
Retry
裁决送审件
You said:
执行侧提交 R09-14：G1 证据闭合 + WP1-v0.4 FZ 证据（接你 R13 治理裁决书的 FZ-01..04 与 G1 五项）。

===== G1 五项状态 =====
① 历史 175 件身份追溯：**关闭**（实物 NVSDK sha256:725e97d4afa6877fe49389f9a8d6300174ee7143a25279c26511ef88247347f0 + 运行入口 scripts/nvidia_audit_all.py:31 backend='physx' 显式绑定 + 202 件唯一身份台账（0 重复，分组 liquor16/dairy2/nv960_20/variant60/tde100/legacy4）+ 175→202 追加式更正记录。SDK 版本 = USDCraft v1.0.0 (2026-10-30, code/CHANGELOG.md)）。
② MaterialBindingAPI 补丁：**关闭**（三处显式 Apply 各有回归；独立 commit；修复前后绑定关系/路径/语义一致；usdchecker 红灯→exit=0 原始日志在案）。
③ G1-03 不变量台账：**关闭**（S0 winding 矛盾已修——台账字段统一 trimesh is_winding_consistent 权威口径=False，附口径说明；三阶段几何不变量：verts12/tris20/bbox/面积0.0575/边30 全同）。
④ G1-04 UV：面内仿射一致 20/20 (residual<1e-4) ✅；非对称诊断纹理已生成（左红右蓝+L/R 角标+渐变斜线）；Blender 渲染级对照 = OPEN（依你 §4.3 轻量管线待指派）。
⑤ G1-05 影响范围分离：**关闭**（_BUILDERS 映射证明家族修复仅 brick 系 2 类；导出参数默认 False，唯一生产调用点未传参→字节级零变化）。

===== FZ-01..04 =====
FZ-01 协议 v0.4 全文已提交（docs/research/wp1_protocol_v04.md，sha256 前 16 位 a8520db78d77dd6b）。
FZ-02 selftest 源码+十例输入+原始输出（scripts/wp1_protocol_selftest.py，sha256 前 16 位 a2aa50c7081f8c00，10/10 PASS 原始输出已随上轮提交）。
FZ-03 202 件历史资产身份台账已关闭（本消息①）。
FZ-04 抽样脚本/种子/输入快照/Pilot-100 名单固定——抽样规则已登记（协议 §5），种子与名单待持样方清单交付时一并冻结。

===== 新增负向回归（R09-10 FZ-02 补充，全部过） =====
W11 DIM-01 阈值边界（恰在 1mm 内过/1.01mm 拒）| W12 验证器未运行 → VALIDATION_PENDING 无 PASS 声明 | W13 冻结输入变更 → 拒绝执行。

===== 请裁决 =====
1. G1 五项是否全部关闭（授权 G2 九件候选）。
2. WP1-v0.4 是否签发 FROZEN。
3. 指派下一步（含 G2 执行与 ECO-CPG-01 后续）。
…
Show more
ChatGPT said:
RWI-L1｜R14 治理裁决书

送审编号：R09-14
裁决角色：L-a
继承依据：R13 治理裁决书 D01–D05

总体裁决：CONDITIONAL PASS。

本轮已经进入工程收口阶段，不再存在需要重新设计的架构级问题。但执行侧明确报告 G1-04 尚有 OPEN 项，FZ-04 尚未完成实际抽样冻结，因此不能签发 G1 全闭，也不能签发 WP1 完整 FROZEN。

本轮依据执行侧提交摘要进行裁决，未独立复算原始文件、哈希及运行日志。以下关闭状态属于治理层对送审证据的条件认可，不冒充独立实物审计。

一、三项裁决总表

裁决事项

	

裁决

	

状态




G1 五项关闭

	

【修改】

	

4 CLOSED / 1 OPEN




G2 九件候选执行

	

【修改】

	

保留条件授权




WP1-v0.4 冻结

	

【修改】

	

协议规范允许冻结，实验实例待冻结




G1-04 轻量渲染验证

	

【同意】

	

立即执行




ECO-CPG-01 后续

	

【同意】

	

独立并行

二、G1 五项逐项裁决
4 / 5
G1 关闭进度
G1-01

历史验证器身份追溯

CLOSED

G1-02

MaterialBindingAPI 补丁

CLOSED

G1-03

几何不变量台账

CLOSED

G1-04

UV 渲染级验证

OPEN

G1-05

影响范围分离

CLOSED

G1-01｜历史验证器身份追溯

【同意】关闭。

本轮提供的证据要素满足 R13-D01 的关闭要求：

验证器完整 SHA256。

USDCraft v1.0.0 版本标识。

历史调用入口显式指定 backend='physx'。

202 件唯一资产身份台账。

175→202 追加式更正记录。

分组计数闭合：

分组

	

数量




liquor

	

16




dairy

	

2




nv960

	

20




variant

	

60




tde

	

100




legacy

	

4




合计

	

202

接受历史验证器身份追溯关闭，不再要求全量重跑 202 件。

但保留以下语义限制：

使用 PhysX backend 的 USD 验证器通过，不等于已经在 Isaac Sim 中执行动态物理仿真并通过。

另外，历史运行脚本与验证器版本的关联，应作为证据包的一部分永久保留。若后续发现版本关联不成立，重新开启该项。

G1-02｜MaterialBindingAPI 独立补丁

【同意】关闭。

三处显式 Apply 均有回归覆盖，独立 commit，修复前后绑定路径、关系与语义不变，原始红灯及修复成功日志在案。

不再增加专项回归要求。

正式接受该补丁进入后续候选资产编译基线。

G1-03｜几何不变量台账

【同意】关闭。

接受以 trimesh.is_winding_consistent 为绕向一致性的权威判定口径，且 S0 的实际状态为 False。

这里必须强调：关闭的是台账语义矛盾及几何不变量检查，并不是将 S0 的绕向缺陷判定为通过。

不变量

	

三阶段结果




顶点数

	

12，一致




三角面数

	

20，一致




BBox

	

一致




表面积

	

0.0575，一致




边数

	

30，一致

这些指标支持几何规模与外形未发生变化，但不能单独证明拓扑、顶点对应关系及 UV 语义完整一致。

后者由既有拓扑检查和 G1-04 专项门禁负责，不在本项重复扩大范围。

G1-04｜UV 保真验证

【修改】保持 OPEN，立即指派关闭任务。

面内仿射残差小于 1e-4，20/20 通过，是有效的数学证据。

但它仍然不能完全代替最终渲染级验证。尤其对于绕向修复，需要排除以下问题：

印刷纹理发生左右镜像。

顶点与面角 UV 对应关系错位。

背面剔除造成印刷面消失。

绕向修复引入法线或材质表现异常。

因此，本项不得跳过。

G1-05｜影响范围分离

【同意】关闭。

接受 _BUILDERS 映射与生产调用点分析所报告的影响范围。

家族修复限于 brick 系两类；导出规范化参数默认 False，生产调用点未启用该参数。

这意味着本轮可以采用受控候选路线开展验证，不需要立即重新生成全部 9,386 SKU。

三、G1-04 正式任务书：轻量 UV 渲染验证

任务编号：R14-UV-01
优先级：P0
执行授权：IMMEDIATE

本任务只解决 UV 保真问题，不进行视觉美化，不进行材质升级，不进行全量资产渲染。

3.1 验证设计
验证设计示意图，并非本轮实际渲染结果。
3.2 最小执行矩阵

覆盖 brick 系受影响的两个结构家族，每个家族至少选取一个已经登记的代表资产。

变量

	

冻结要求




资产

	

两个家族各一件




对照阶段

	

S0 / S1 / S2，沿用现有定义




纹理

	

已生成的非对称诊断纹理




分辨率

	

512×512




相机

	

六个轴向正交视角




材质

	

Emission 诊断材质




色彩管理

	

固定




背景

	

固定




随机种子

	

固定（若涉及随机采样）

合计 36 张诊断渲染图，不要求照片级 Cycles 渲染。

建议采用 Blender Eevee 或等效轻量渲染路径。另保留背面剔除开启的补充诊断，用于验证绕向修复是否符合预期。

3.3 机器验收门禁

门禁

	

通过条件




UV-R01

	

原有 20/20 仿射检查继续通过




UV-R02

	

左右红蓝纹理的空间对应关系保持一致




UV-R03

	

L/R 角标无非预期镜像、旋转、错位




UV-R04

	

渐变斜线无非预期断裂、方向改变




UV-R05

	

修复后无新增异常缺面




UV-R06

	

全部诊断图、运行脚本、配置及日志可复现

不采用整张图片逐像素完全相等作为唯一判据。绕向修复可能合法改变背面可见性，因此需要区分：

应当保持不变： UV 空间对应关系。

允许且预期发生变化： 缺陷绕向修复后的可见性与法线表现。

禁止发生变化： 非预期纹理镜像、印刷方向及面角对应关系错误。

全部通过即可送审关闭 G1-04，不再追加其他视觉实验。

四、WP1-v0.4 冻结裁决

【修改】拆分协议冻结与实验实例冻结。

本轮 FZ-04 暴露了一个值得修正的治理问题：协议本身已经可以完成设计冻结，但 Pilot-100 实际名单受持样方清单交付制约。

两者不应混为一个状态，否则会出现外部业务依赖阻塞已经成熟的技术规范。

4.1 FZ-01–04 逐项裁决

门禁

	

当前判定

	

理由




FZ-01

	

条件通过

	

协议全文已登记，归档时补齐完整 SHA256




FZ-02

	

条件通过

	

W01–W13 报告全部通过




FZ-03

	

通过

	

202 件历史身份台账关闭




FZ-04

	

OPEN

	

尚无实际冻结输入、种子与抽样名单

4.2 新增 W11–W13

测试

	

裁决




W11 尺寸阈值边界

	

接受，但需覆盖绝对与相对阈值两个分支




W12 验证器未运行

	

接受




W13 冻结输入变更

	

接受

W11 有一个需要明确的测试前提。

DIM-01 的冻结公式为：

𝑇
(
𝑑
)
=
max
⁡
(
1
 mm
,
0.01
𝑑
)
T(d)=max(1 mm,0.01d)

因此，1.01mm 偏差并不是在所有情况下都应拒绝。

标称尺寸

	

容差

	

1.01mm 偏差




50mm

	

1mm

	

FAIL




100mm

	

1mm

	

FAIL




200mm

	

2mm

	

PASS




500mm

	

5mm

	

PASS

执行侧需要确认 W11 的标称尺寸，并覆盖相对阈值生效的情况。若原测试已覆盖，不必增加用例；若没有，只扩展 W11，不升级协议版本。

另外，R13 要求的重复资产拒绝以及八终态互斥、完备性检查，需要在 W01–W10 中明确标注对应测试编号。

4.3 双层冻结机制正式签发

协议规范冻结

批准冻结
八终态、五指标、阈值公式、抽样方法、证据契约、状态判定

SPEC-FROZEN

实验实例冻结

等待输入
持样方清单、输入快照、随机种子、Pilot-100 名单及实际资产身份

RUN-FREEZE-PENDING

批准 v0.4 协议规范进入冻结流程，补齐上述证据登记和 W11 覆盖后，即可标记 SPEC-FROZEN。

不签发不加限定的 FROZEN。

同时，正式修改 R13-D05 中的 G2 前置条件：

G2 九件候选属于工程修复验证，不应被 Pilot-100 的持样方清单阻塞。G2 只依赖 G1 全闭、协议规范冻结及 G2 自身九件候选输入冻结。

这是本轮唯一实质性的治理机制调整。

五、G2 九件候选执行授权

【同意】条件授权，条件满足后自动生效。

不需要等待持样方提交 Pilot-100 完整清单。

5.1 G2 自动生效条件

条件

	

要求




C1

	

G1-04 六项门禁全部通过，证据归档




C2

	

WP1-v0.4 规范冻结完成




C3

	

九件候选资产 ID、输入、版本、哈希冻结




C4

	

编译器与验证器版本固定




C5

	

执行参数明确记录，包括规范化开关及 backend

执行侧完成 C1–C5 后，可直接执行 G2，不需要为启动许可单独再送审一次。

但最终 G2 验收仍由 L-a 裁决。

5.2 G2 禁止事项

不得在九件执行过程中修改协议。

不得以临时调整输入方式消除失败。

不得将失败候选移出分母。

不得把验证器通过记为动态物理仿真通过。

不得将九件候选通过推断为全家族通过。

不得将九件工程候选自动计入 Pilot-100 随机抽样统计。

G2 的研究目标不是追求 9/9 PASS，而是检验修复及验证契约是否能够在真实工程流程中成立。

六、ECO-CPG-01 后续指派

【同意】启动第二阶段，但不进入大规模合成数据生产。

考虑到此前 Benchmark A 中纯合成语料、域随机化等路线尚未证明有效的真实场景迁移能力，ECO 后续必须坚持外部证据优先，不能因为发现产业先例就直接扩大生产投入。

ECO 三条工作线

工作包

	

内容

	

优先级




ECO-CPG-02

	

Neurolabs 方法论及公开技术证据归档

	

P1




ECO-CPG-03

	

RWI 长期托管原则实施试点

	

P1




ECO-CPG-04

	

零售合成数据真实迁移技术缺口研究

	

P2

ECO-CPG-02： 冻结现有样例图、可获取的代码、数据后处理三重过滤方法及出处。记录原始数据集不可获取状态，不再反复寻找同一失效下载链接。

ECO-CPG-03： 选择一个已有冻结资产包，建立完整 manifest、SHA256、许可证、复现入口及独立归档副本。实际验证从归档下载后能否恢复原始资产。不以 DOI 生成成功作为唯一验收条件。

ECO-CPG-04： 重点研究几何真实度、商品印刷特征、真实背景建模、合成与真实样本混合训练、真实场景评测五个方向。先形成外部证据矩阵和单变量实验建议，不立即开展大规模训练。

ECO 全线不得占用 G1-04 和 G2 的关键路径。

七、下一轮执行任务台账

任务

	

优先级

	

交付物

	

执行状态




R14-UV-01

	

P0

	

36 张诊断图及六项门禁

	

立即执行




R14-FZ-01

	

P0

	

完整哈希、W11 双分支覆盖、状态测试映射

	

立即执行




R14-G2-PREP

	

P0

	

九件候选冻结 manifest

	

并行准备




R14-G2-RUN

	

P1

	

九件逐资产验证证据

	

条件自动授权




R14-PILOT-FZ

	

P1

	

持样方快照、种子、抽样名单

	

等待输入




ECO-CPG-02

	

P1

	

外部研究证据档案

	

并行




ECO-CPG-03

	

P1

	

长期归档试点及下载复测

	

并行




ECO-CPG-04

	

P2

	

技术缺口矩阵

	

排队

八、本轮治理评分

以下为基于送审摘要的治理成熟度评价，不是资产质量评分。

验证器身份与溯源

9.5 / 10

修复范围控制

9.5 / 10

几何不变量治理

9.2 / 10

UV 验证完整性

8.0 / 10

协议机器可执行性

9.0 / 10

实验输入冻结

7.5 / 10

综合治理成熟度

8.8 / 10

当前没有必要再启动一轮全面方案评审。剩余问题已经具体化为可执行、可验收的工程任务。

九、正式签发
Plain text
RWI-L1 / GOVERNANCE / R14

G1-01 VALIDATOR IDENTITY
    CLOSED
    HISTORICAL COUNT = 202

G1-02 MATERIAL BINDING API
    CLOSED

G1-03 GEOMETRIC INVARIANTS
    CLOSED

G1-04 UV RENDER VALIDATION
    OPEN
    R14-UV-01 AUTHORIZED

G1-05 IMPACT ISOLATION
    CLOSED

G1 GLOBAL
    4/5 CLOSED
    PENDING UV VALIDATION

WP1-v0.4
    SPEC FREEZE APPROVED WITH CONDITIONS
    RUN FREEZE PENDING

G2 NINE CANDIDATES
    CONDITIONAL AUTO-AUTHORIZATION
    ON C1-C5 SATISFIED

ECO-CPG-01
    SCOUTING CLOSED
    FOLLOW-UP AUTHORIZED IN PARALLEL

PILOT-100
    EXECUTION NOT YET AUTHORIZED

FULL-SCALE RECOMPILATION
    NOT AUTHORIZED

OVERALL: CONDITIONAL PASS
NEXT REVIEW: R15

最终指令：不再为 G1-04 单独开启一轮治理讨论。执行侧完成轻量渲染验证、规范冻结和九件输入冻结后，按本轮授权直接执行 G2。R15 提交 G1 关闭证据与 G2 实际执行结果，争取一次完成验收。

You said:
执行侧提交 R14-UV-01 完成报告（commit ce0d5d8；脚本 scripts/wp_uv01_render.py；36 张渲染 output/candidates/aseptic_brick_v0000/wp_a12/uv_verify/；证据 docs/research/evidence/r14_uv01_evidence.json + uv_r01_affine_allstages.json）。


===== 执行矩阵 =====
brick 系两家族 (aseptic_brick, brick_250ml) × S0/S1/S2 三阶段 × 六正交视角 (px/nx/py/ny/pz/nz) = **36 张 512×512 Eevee Emission 诊断渲染**，全部成功。

===== 六门禁结果 =====
| 门禁 | 结果 | 证据 |
|---|---|---|
| UV-R01 仿射一致 | **PASS** | S0 40/40, S1 40/40, S2 40/40 (residual<1e-4)，两家族各 20 面 |
| UV-R02 红蓝空间对应 | **PASS** | 三阶段 meanAbsDiff = 0.00（px/py/pz 全视角），红蓝分区占比逐位一致 |
| UV-R03 L/R 角标 | **PASS** | 无镜像/旋转/错位（仿射一致即无角交换；渲染目验 L/R 标正常）|
| UV-R04 渐变斜线 | **PASS** | 无断裂/无方向改变（跨阶段 diff 0.0）|
| UV-R05 无新增缺面 | **PASS** | 全部渲染非黑占比正常 |
| UV-R06 可复现 | **PASS** | 脚本+纹理+36 渲染入库 |

===== G1-04 关闭请求 =====
六门禁全过 → 请求关闭 G1-04。关闭后 G1 五项全闭 → 按 R09-10/R09-12 授权执行 G2 九件候选（aseptic/brick250 各最小/典型/最大 + 非 brick 对照 3 件，MaterialBindingAPI 独立补丁不混入）。

===== 请裁决 =====
1. UV-R01..R06 六门禁是否验收，G1-04 是否关闭。
2. G2 九件候选是否授权执行。
3. G2 执行的送审要求（九件候选的审计+诊断证据清单）。
4. 并行项确认（WP-V 联合报告已提交待裁 / ECO 已关闭侦察）。
…
Show more
ChatGPT said:
RWI-L1｜R15 治理裁决书

送审对象：R14-UV-01，commit ce0d5d8
裁决角色：L-a
继承依据：R09-10 / R09-12 / R13 / R14

总体裁决：CONDITIONAL PASS。

本轮 UV 验证的执行矩阵符合任务书，证据方向正确，已经具备关闭 G1 的基本条件。但报告存在两个需要收口的证据缺口：六视角渲染与三视角差分的覆盖差异，以及 UV-R05 缺面判定的充分性。

本轮依据执行侧摘要裁决，未读取 commit 实物、36 张原始渲染及两个 JSON 证据文件，不将本次裁决冒充独立程序复验。

一、四项裁决总表

裁决事项

	

裁决

	

状态




UV-R01–R06

	

【修改】

	

4 项接受，2 项待补证




G1-04

	

【修改】

	

条件关闭




G2 九件候选

	

【同意】

	

保留自动执行授权




G2 送审协议

	

【同意】

	

本轮签发




WP-V 联合报告

	

【同意】

	

独立待裁，不阻塞 G2




ECO-CPG-01

	

【同意】

	

侦察关闭，后续研究并行

二、UV-R01–R06 逐项验收
2.1 执行矩阵

两家族 × 三阶段 × 六视角，共36张诊断渲染，符合 R14-UV-01 最小执行矩阵。

结构家族
2
对照阶段
3
正交视角
6
单家族 18 张，两家族共 36 张。示意图，非实际送审渲染。

仿射检查

120 / 120

诊断渲染完成

36 / 36
2.2 六项门禁裁决

门禁

	

裁决

	

理由




UV-R01 仿射一致

	

【同意】PASS

	

两家族、三阶段共120次面级检查通过




UV-R02 红蓝空间对应

	

【修改】PARTIAL

	

仅明确报告 px/py/pz 差分，三个负轴视角缺量化记录




UV-R03 L/R 角标

	

【同意】PASS

	

仿射检查与渲染目验共同支持印刷方向保真




UV-R04 渐变斜线

	

【同意】PASS

	

已报告的跨阶段零差分支持纹理连续性




UV-R05 无新增缺面

	

【修改】PARTIAL

	

非黑像素占比正常不足以证明局部没有缺面




UV-R06 可复现性

	

【同意】条件 PASS

	

已登记脚本、纹理和36张结果，待归档实物复跑

2.3 两项必须补证的问题

F01｜六视角量化覆盖不完整

报告写明：

三阶段 meanAbsDiff = 0.00（px/py/pz 全视角）

但是 px、py、pz 只有三个正轴视角，并不是六个视角。

要求使用现有36张渲染图，补算 nx、ny、nz，无需重新渲染。

两家族 × 六视角 × 两组基准对照（S0→S1、S0→S2），应形成完整的 24 条差分记录。

同时确认 0.00 是真实零值还是显示精度舍入。建议同时登记：

指标

	

用途




mean_abs_diff

	

整体差异




max_abs_diff

	

最大局部差异




changed_pixel_count

	

变化像素数量




foreground_mask_diff

	

前景轮廓变化

如果确实完全一致，直接登记实际值，不需要设计新的容差指标。

F02｜UV-R05 缺面证据不足

整体非黑像素占比正常，不能排除局部缺面。即便一个面积很小的三角面消失，整体非黑占比仍可能处于正常范围。

此外，R14 要求的背面剔除开启补充诊断，本轮未明确报告是否执行。

最小补证方式：

利用现有36张图片检查前景掩码及局部差异。

开启背面剔除，对两个家族进行补充诊断。

明确区分 S0 原有绕向缺陷、S1 合法修复变化及 S2 新增异常。

不要求 S0 与修复后在背面剔除开启时完全一致。

补证范围仅限这两项。禁止扩展为新一轮材质、纹理、光照或照片级真实性研究。

三、G1-04 关闭裁决

【修改】条件关闭，补证通过后自动转为 CLOSED。

G1-01

历史验证器身份追溯

CLOSED

G1-02

MaterialBindingAPI

CLOSED

G1-03

几何不变量

CLOSED

G1-04

UV 保真验证

CONDITIONAL

G1-05

影响范围分离

CLOSED

不需要为 F01、F02 再单独召开一轮治理评审。

执行侧完成补证并通过既定门禁后，允许依据本轮授权关闭 G1-04，下一轮随 G2 完整证据一并复核。

如果补证发现异常，则保持 OPEN，不得自动放行。

四、G2 九件候选执行授权

【同意】维持 R14 条件自动授权。

接受本轮提出的九件候选设计：两个受影响家族分别覆盖最小、典型、最大规格，再增加三个非 brick 对照资产。

这是一个合理的工程验证设计，能够同时检查修复有效性、规格边界及影响范围隔离。

4.1 九件候选矩阵

编号

	

家族

	

规格

	

验证目的




G2-01

	

aseptic_brick

	

最小

	

下边界




G2-02

	

aseptic_brick

	

典型

	

常规规格




G2-03

	

aseptic_brick

	

最大

	

上边界




G2-04

	

brick_250ml

	

最小

	

下边界




G2-05

	

brick_250ml

	

典型

	

常规规格




G2-06

	

brick_250ml

	

最大

	

上边界




G2-07

	

非 brick 对照 A

	

冻结规格

	

导出影响隔离




G2-08

	

非 brick 对照 B

	

冻结规格

	

导出影响隔离




G2-09

	

非 brick 对照 C

	

冻结规格

	

导出影响隔离

三个对照资产建议选择不同的结构或 builder 路径，而不是任意挑选三个同质资产。

最小、典型、最大规格的定义必须提前登记。若长、宽、高存在不同极值，不允许未经说明将体积最大等同于所有尺寸均达到最大。

4.2 执行前置条件

仍然执行 R14 的 C1–C5，不降低门禁。

条件

	

本轮状态




C1：G1 五项全闭

	

F01、F02 补证后生效




C2：WP1-v0.4 SPEC-FROZEN

	

本轮未提供最终冻结回执




C3：九件候选输入冻结

	

待登记完整 manifest




C4：编译器及验证器版本冻结

	

待执行 manifest 确认




C5：执行参数冻结

	

待执行 manifest 确认

特别提醒：上一轮提出的 W11 双阈值分支覆盖、完整协议哈希、重复资产及八终态测试映射，本轮没有提交完成回执。

因此不能默认为 C2 已通过。

4.3 MaterialBindingAPI 补丁隔离

同意执行侧“不混入”的原则，但必须明确基线含义。

如果 MaterialBindingAPI 补丁已经正式合入基线，则 G2 的修复前后两组必须共同包含该补丁。

如果尚未合入，则两组均不包含，并单独记录由此产生的验证结果。

不允许对照组不含补丁、实验组含补丁，否则绕向修复、导出规范化和材质 API 三个变量将发生混杂。

五、G2 正式送审协议

本轮签发 R15-G2-EVIDENCE-v1.0。

5.1 对照实验结构
对照实验必须固定非研究变量。若单独归因家族修复和导出规范化，继续保留 S0/S1/S2 中间阶段证据。
5.2 六类送审证据

证据包

	

必交内容




E01 输入冻结

	

九件资产 ID、规格、选样规则、输入 SHA256




E02 环境冻结

	

编译器 commit、SDK 版本、验证器 SHA256、依赖及运行参数




E03 几何审计

	

顶点、面、边、BBox、面积、绕向、水密性及 DIM-01




E04 USD 审计

	

原始 usdchecker 输出、NVSDK 输出、backend、exit code、失败规则




E05 诊断证据

	

阶段差异、UV 保真、拓扑变化及非 brick 对照结果




E06 裁决台账

	

九件唯一终态、证据路径、失败原因、未执行项及汇总

如果执行动态物理仿真，应另外保存仿真环境、运行参数、初始状态、运行结果及通过标准。不能仅保存 PhysX backend 验证器的 PASS 记录。

5.3 九件资产逐件审计字段

建议以一份 JSONL 或 CSV 权威台账登记，不接受只有 Markdown 汇总表的送审包。

Plain text
asset_id
family_id
selection_role
input_sha256

baseline_commit
candidate_commit
validator_sha256
validator_backend
normalization_enabled

baseline_output_sha256
candidate_output_sha256

vertex_count
triangle_count
edge_count
bbox_before
bbox_after
surface_area_before
surface_area_after
winding_before
winding_after
watertight_before
watertight_after

dimension_nominal
dimension_measured
dimension_error
dimension_tolerance
dimension_verdict

uv_affine_result
uv_render_result
compiler_gate_result
usdchecker_result
nvsdk_result
physics_execution_status
physics_result

expected_change
observed_change
unexpected_change
final_state
evidence_paths

final_state 必须采用 WP1-v0.4 已冻结的枚举，不允许 G2 自创新的业务终态。

5.4 G2 专项门禁

门禁

	

验收标准




G2-M01

	

9/9 候选身份完整、唯一




G2-M02

	

输入、版本、参数与输出证据绑定完整




G2-M03

	

六件 brick 资产的目标绕向缺陷按契约修复




G2-M04

	

DIM-01 按绝对与相对容差公式执行




G2-M05

	

无非预期几何、拓扑及 UV 变化




G2-M06

	

三件非 brick 对照无非预期变化




G2-M07

	

外部验证原始结果全部登记，包括失败




G2-M08

	

三层验证语义严格分离




G2-M09

	

九件终态互斥、完备、可复算




G2-M10

	

失败候选不得删除、替换或事后调整分母

其中，M03 和 M06 是本轮最重要的两个技术门禁。

一个证明修复有效，一个证明修复没有扩大破坏范围。

5.5 G2 失败处理纪律

G2 是一次冻结后的工程实验，不是九件资产的反复调试过程。

若出现失败：

保留第一次运行结果。

记录失败阶段及原始错误。

提交根因假设与最小修复建议。

后续修复采用新版本、新运行编号。

不覆盖原始 G2 结果。

我接受 G2 出现诚实的负结果，但不接受通过修改分母、输入或规则制造 9/9 PASS。

六、并行研究项裁决
6.1 WP-V 联合报告

【同意】进入独立裁决队列。

当前只收到 WP-V 已提交的状态说明，未收到联合报告正文，故不对其技术结论签核。

WP-V 与 G2 原则上保持独立。只有当 WP-V 发现直接影响 G2 输入、验证器可信性或既定安全门禁的 P0 问题时，才允许阻断 G2。

不得因为联合报告仍在等待裁决而暂停已经授权的工程任务。

6.2 ECO-CPG-01

【同意】保持侦察关闭状态，不重新开启。

继承 R13、R14 裁决：

工作包

	

状态




ECO-CPG-01 产业侦察

	

CLOSED




CPGDet-129 数据集

	

EVIDENCE_UNAVAILABLE




ECO-CPG-02 方法论证据归档

	

已授权




ECO-CPG-03 长期托管试点

	

已授权




ECO-CPG-04 真实迁移技术缺口

	

排队执行




大规模合成数据生产

	

未授权

不因外部数据集无法获取降低研究证据标准，也不因产业先例成立提前宣布 RWI 已具备真实零售感知迁移能力。

七、下一步执行顺序
关键路径 A

UV 补证 F01 / F02

关闭 G1-04
关键路径 B

SPEC-FROZEN

完成 R14 遗留冻结条件

G1 全闭 + 规范冻结 + 九件输入冻结

C1–C5 全部满足

G2 九件候选正式执行

无需再次申请启动许可

R16 独立验收

九件审计、诊断证据、终态复算

独立并行线

WP-V 裁决 / ECO 后续 / Pilot-100 输入准备

任务编号

	

优先级

	

交付物




R15-UV-F01

	

P0

	

24 条完整跨阶段差分记录




R15-UV-F02

	

P0

	

缺面及背面剔除诊断




R15-SPEC

	

P0

	

SPEC-FROZEN 最终回执




R15-G2-FREEZE

	

P0

	

九件冻结 manifest




R15-G2-RUN

	

P1

	

六类证据包、十项专项门禁




R15-WPV

	

P1

	

联合报告独立裁决




ECO 后续

	

P1/P2

	

沿用 R14 任务书

八、正式签发
Plain text
RWI-L1 / GOVERNANCE / R15

R14-UV-01
    EXECUTION MATRIX ACCEPTED
    AFFINE CHECKS REPORTED 120/120
    RENDERS REPORTED 36/36

UV-R01: ACCEPTED
UV-R02: PARTIAL — SIX-VIEW COVERAGE
UV-R03: ACCEPTED
UV-R04: ACCEPTED
UV-R05: PARTIAL — MISSING-FACE EVIDENCE
UV-R06: CONDITIONALLY ACCEPTED

G1-04
    CONDITIONAL CLOSURE
    AUTO-CLOSE ON F01/F02 PASS

G2 NINE CANDIDATES
    CONDITIONAL AUTO-AUTHORIZATION
    R14 C1-C5 RETAINED

R15-G2-EVIDENCE-v1.0
    APPROVED

WP-V
    INDEPENDENT REVIEW PENDING

ECO-CPG-01
    SCOUTING CLOSED
    FOLLOW-UP PARALLEL AUTHORIZED

PILOT-100
    EXECUTION NOT YET AUTHORIZED

FULL-SCALE RECOMPILATION
    NOT AUTHORIZED

OVERALL: CONDITIONAL PASS
NEXT REVIEW: R16

最终指令：不增加研究范围，不重新执行已经通过的仿射验证，不重新渲染全部36张图片。完成两项最小 UV 补证及协议规范冻结后，直接执行 G2 九件候选。下一轮必须提交实际工程结果，而不是再次提交执行计划。

ChatGPT can make mistakes. Check important info.
Latest response




Medium
Response complete