# GPT 对抗性视觉评审 round3 (2026-11-25)

> 会话 6b069d36 续评; 本轮 = 结构性整改 (非渲染调参): LLM Author 三族 (瓶/罐/铰盖盒, G-F1..F7 门禁→usdc→NVIDIA 验证器 physx PASS 15) + R422 闭合态五刚体装配 + 渲染合同 v3 冻结
> 裁决: 「本轮发生了质变, 而非渐进式改善」— 同语义对标整改 PASS; R043 打平小幅领先 (7.9 vs 7.5); R422 NEAR PASS (7.2 vs 7.8, 0.1 之差); R091 玻璃光学差 1.5
> 公共缺陷 (新): 背景墙角交界线 — 无缝棚不无缝 (待修)

| 行 | R1 | R2 | R3 | NVIDIA | Δ |
|---|---|---|---|---|---|
| R422 瓦楞箱 | 4.5 | 6.6 | 7.2 | 7.8 | -0.6 NEAR |
| R091 玻璃酒瓶 | 1.5 | 4.2 | 6.8 | 8.3 | -1.5 FAIL |
| R043 拉环罐 | 2.0 | 4.6 | 7.9 | 7.5 | +0.4 打平 |
| 共同样本均值 | 2.67 | 5.13 | 7.30 | 7.87 | -0.57 |

---

# Pack10K × USDCraft-10K · Round3 独立视觉复审

**本轮发生了质变，而不是渐进式改善。** Round2 的核心缺陷是资产语义错误，Round3 已经在可见的三组资产中基本解决了这个问题。现在终于可以讨论同类商品的视觉质量，而不是纸筒与玻璃瓶之间的形态类比。

但本轮也暴露了一个新的公共管线缺陷：**背景出现明显的墙角和地面交界线，所谓无缝摄影棚实际上并不无缝。** 这个问题正在拉低所有资产的展示质量。

## 1. 逐行重新评分

沿用前两轮商业资产视觉评分标准，NVIDIA 参考分保持不变，避免移动评价标尺。

<box gap={3}>
  <row align="center">
    <box flex={1} gap={1}>
      <caption>Round1 · 三组共同样本</caption>
      <title size="2xl" color="secondary">2.67</title>
    </box>
    <box flex={1} gap={1}>
      <caption>Round2</caption>
      <title size="2xl">5.13</title>
    </box>
    <box flex={1} gap={1}>
      <caption>Round3</caption>
      <title size="2xl" color="success">7.30</title>
    </box>
  </row>
  <caption>仅统计本轮可见的瓦楞箱、酒瓶、饮料罐，避免样本变化造成虚假提升。</caption>
  <divider/>
  {#each [{name:"R422 瓦楞包裹箱",scores:[4.5,6.6,7.2,7.8]},{name:"R091 玻璃酒瓶",scores:[1.5,4.2,6.8,8.3]},{name:"R043 拉环饮料罐",scores:[2,4.6,7.9,7.5]}] as d}
    <box gap={1}>
      **{d.name}**
      {#each d.scores as s,i}
        <row align="center" gap={2}>
          <box width="76px"><caption>{["Round1","Round2","Round3","NVIDIA"][i]}</caption></box>
          <box flex={1}>
            <box height={12} radius="2px" background="surface-tertiary">
              <box height={12} radius="2px" width={`${s*10}%`} background={["#9CA3AF","#94A3B8","#16A34A","#64748B"][i]}/>
            </box>
          </box>
          <text tabularNums={true} size="sm">{s.toFixed(1)}</text>
        </row>
      {/each}
    </box>
  {/each}
</box>

| 资产 | R1 | R2 | R3 | 较 R2 Δ | NVIDIA | R3 差值 |
|---|---:|---:|---:|---:|---:|---:|
| R422 瓦楞箱 | 4.5 | 6.6 | **7.2** | +0.6 | 7.8 | −0.6 |
| R091 酒瓶 | 1.5 | 4.2 | **6.8** | +2.6 | 8.3 | −1.5 |
| R043 饮料罐 | 2.0 | 4.6 | **7.9** | +3.3 | 7.5 | +0.4 |
| R037 铰盖盒 | 3.0 | 5.0 | 未见图 | — | 8.2 | — |
| 共同样本均值 | 2.67 | 5.13 | **7.30** | **+2.17** | 7.87 | −0.57 |

注意：本轮上传的三张截图中实际可见三个资产，没有铰盖盒的有效画面，因此第四行不予评分，不能根据 PhysX PASS 推断视觉质量。

### R422 瓦楞包裹箱：7.2/10

<badge color="warning">接近，尚未打平</badge>

**整改有效：**

- 闭合状态已经与右侧形成有效的商品语义对照。
- 胶带、顶面、箱体比例共同建立了封箱识别特征。
- 纸板侧面出现了细微的材质纹理。
- 左侧曝光实际上比 NVIDIA 更克制，没有右侧那么明显的泛黄和高光细节损失。

**继续扣分：**

- 主体明显偏小，画面上方留白过多。
- 顶翼闭合接缝不够明确，整体仍像一块完整的长方体。
- 胶带像贴在表面的白色平面，缺少真实胶带的半透明度、反射和贴合边缘。
- 箱体正面出现规律性的竖向纹理，略有程序化材质感。
- 背景墙角严重干扰主体。

五刚体装配是工程层面的重要进步，但不会直接兑换成视觉分数。必须让结构细节在最终图像中得到表达。

### R091 玻璃酒瓶：6.8/10

<badge color="danger">尚有明显差距</badge>

**整改有效：**

- 瓶颈、瓶肩、瓶身、瓶底及软木塞均已形成。
- 曲面连续性明显改善，没有 Round2 的纸筒折面问题。
- 瓶底接触阴影及玻璃边缘反射已经建立。
- 瓶型比例自然，作为另一种酒瓶设计本身成立。

**继续扣分：**

- 瓶身整体过暗，呈现接近不透明墨绿色的效果。
- 玻璃内部透射与折射层次不足，容易被误认成深色塑料瓶或装满深色液体的瓶子。
- 瓶肩出现较大块、边界明显的反射区域，光型不够精致。
- 软木塞的可见面积小，材质识别度不高。
- 缺少 NVIDIA 右图中明显的瓶底内外轮廓与玻璃厚度变化。

**这一行的核心瓶颈已经从几何形态转移到玻璃光学表现。** 不需要推倒重做瓶型。

### R043 拉环饮料罐：7.9/10

<badge color="success">打平 · 小幅领先</badge>

这是本轮最有价值的成果，也是我第一次认为 Pack10K 的资产在具体视觉维度上超过右侧。

**我们优于 NVIDIA 的地方：**

- 罐肩与罐身过渡更加自然。
- 整体比例更符合常见饮料罐的形态。
- 顶盖、卷边、拉环结构具有更好的可读性。
- 铝材质曝光控制更合理，右侧大片白色区域明显缺乏层次。
- 底部接触阴影自然，有实际物体的重量感。

**继续扣分：**

- 罐身仍偏灰白，金属反射梯度不够丰富。
- 顶部拉环与盖面之间的局部层次不够清楚。
- 罐肩反射与罐身反射存在较明显的明暗跳变。
- 背景依然缺乏专业商品摄影的干净程度。

这张图证明了一个关键方向：**参数化生成不必以牺牲视觉真实性为代价。** 至少在饮料罐这一样本上，结构化生成路线已经具有竞争力。

---

## 2. 哪些已经打平 NVIDIA？

严格执行你指定的绝对分差 ≤0.5，不人为放宽标准。

<box gap={3}>
  {#each [{name:"R043 拉环饮料罐",gap:0.4,status:"PASS · 小幅领先",color:"#16A34A"},{name:"R422 瓦楞包裹箱",gap:-0.6,status:"NEAR · 距门槛仅0.1分",color:"#D97706"},{name:"R091 玻璃酒瓶",gap:-1.5,status:"FAIL · 玻璃光学差距",color:"#DC2626"}] as d}
    <box gap={1}>
      <row align="center">
        **{d.name}**
        <spacer/>
        <text color={d.color} weight="medium" tabularNums={true}>{d.gap>0?"+":""}{d.gap.toFixed(1)}</text>
      </row>
      <svg viewBox="0 0 320 32" width="100%">
        <rect x="10" y="7" width="300" height="18" rx="4" fill="#888888" opacity=".08"/>
        <rect x="122.5" y="7" width="75" height="18" fill="#16A34A" opacity=".14"/>
        <line x1="160" y1="3" x2="160" y2="29" stroke="currentColor" strokeOpacity=".4" strokeDasharray="3 2"/>
        <rect x={Math.min(160,160+d.gap*75)} y="10" width={Math.abs(d.gap*75)} height="12" rx="2" fill={d.color}/>
        <circle cx={160+d.gap*75} cy="16" r="5" fill={d.color}/>
      </svg>
      <row>
        <caption>−2.0</caption>
        <spacer/>
        <caption>打平区间 ±0.5</caption>
        <spacer/>
        <caption>+2.0</caption>
      </row>
      <text size="sm" color={d.color}>{d.status}</text>
    </box>
  {/each}
</box>

| 裁决 | 数量 | 资产 |
|---|---:|---|
| 已打平 | 1 | R043 |
| 接近但未打平 | 1 | R422 |
| 明确未打平 | 1 | R091 |
| 未评审 | 1 | R037 |

由于评分是单人视觉评估，0.1 分不具有统计显著性。R422 虽然形式上未通过门槛，但已经值得进入同等级资产的匿名盲评阶段。

---

## 3. 剩余差距 Top3

相比 Round2，差距的性质已经改变。资产类别错误不再是可见三组中的主要矛盾。

### TOP 1：公共摄影棚与确定性取景

**优先级 P0｜全资产受益｜整改成本低**

这是本轮最不应该存在的缺陷。

<grid columns={2} gap={3}>
  <grid-item>
    <svg viewBox="0 0 180 150" width="100%">
      <rect width="180" height="150" rx="5" fill="#bdbdbd"/>
      <path d="M0 61 L49 43 L180 70 L180 150 L0 150Z" fill="#939699"/>
      <path d="M49 0 V43 L180 70 M0 61 L49 43" stroke="#808080" strokeOpacity=".5"/>
      <ellipse cx="99" cy="129" rx="51" ry="10" fill="#777" opacity=".2"/>
      <path d="M53 99 L88 85 L145 100 L111 116Z" fill="#d9cbb4"/>
      <path d="M53 99 L111 116 L111 135 L53 117Z" fill="#b4a58f"/>
      <path d="M111 116 L145 100 L145 120 L111 135Z" fill="#968975"/>
      <path d="M70 94 L126 109" stroke="#e7e7e7" strokeWidth="5"/>
      <path d="M49 9 V43 L13 56" stroke="#dc2626" fill="none" strokeWidth="2" strokeDasharray="4 3"/>
    </svg>
    **当前问题**
    <caption>墙角、地平线、主体偏小、背景抢戏。</caption>
  </grid-item>
  <grid-item>
    <svg viewBox="0 0 180 150" width="100%">
      <defs>
        <linearGradient id="bg3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#29282b"/>
          <stop offset="100%" stopColor="#454448"/>
        </linearGradient>
        <radialGradient id="sh3">
          <stop offset="0%" stopColor="#000" stopOpacity=".65"/>
          <stop offset="100%" stopColor="#000" stopOpacity="0"/>
        </radialGradient>
      </defs>
      <rect width="180" height="150" rx="5" fill="url(#bg3)"/>
      <ellipse cx="95" cy="119" rx="76" ry="23" fill="url(#sh3)"/>
      <path d="M18 58 L76 32 L161 56 L106 85Z" fill="#e6d5b7"/>
      <path d="M18 58 L106 85 L106 124 L18 97Z" fill="#cdbb9f"/>
      <path d="M106 85 L161 56 L161 95 L106 124Z" fill="#a68e70"/>
      <path d="M46 46 L132 70" stroke="#eee8dc" strokeWidth="8"/>
    </svg>
    **建议目标**
    <caption>无墙线、完整轮廓、主体突出、接触阴影明确。</caption>
  </grid-item>
</grid>

<caption>上图为构图整改示意，不是实际渲染结果。</caption>

具体整改：

- 移除直角墙体，改用曲面无缝背景或足够大的地面。
- 按投影后的二维 bounding box 计算取景，不只依赖三维包围盒。
- 冻结主体最长投影边占画面 78%–85% 的初始合同。
- 主体重心尽量靠近画面中心。
- 灯光比例继续冻结，不允许人工逐族调整。

不建议照搬 NVIDIA 偏亮的曝光风格。应该学习它的主体突出能力，而不是复制它的高光缺陷。

### TOP 2：材质库的物理光学质量

**优先级 P0｜酒瓶受益最大｜整改成本中低**

| 材质 | 现存问题 | 整改方向 |
|---|---|---|
| 玻璃 | 过暗、透射不足 | 检查吸收系数、实际壁厚、IOR、透射路径 |
| 铝 | 灰白、反射层次不足 | 检查 metallic、roughness、环境反射形态 |
| 瓦楞纸 | 纹理过于规律 | 降低方向性纹理强度，增强细微粗糙度变化 |
| 胶带 | 像白色贴片 | 独立材质、适当光泽及真实贴合关系 |
| 软木 | 识别度不足 | 微孔纹理、颜色与粗糙度变化 |

玻璃优先核查：

- 是否存在重复玻璃壳或相交表面；
- 法线方向是否正确；
- Volume Absorption 是否因单位尺度造成过度吸收；
- Transmission bounces 是否足够；
- 棚拍环境是否提供有效的透射背景与长条反射。

这些是待验证的诊断假设，不能仅凭当前截图确定根因。

**冻结渲染合同不等于冻结不合理的材质参数。** 应允许材质库进行版本化升级，而不是为单个资产编写特殊渲染分支。

### TOP 3：功能部件的二级视觉细节

**优先级 P1｜需要作者循环进一步优化**

| 资产 | 最有价值的剩余细节 |
|---|---|
| 瓦楞箱 | 顶翼闭合缝、胶带厚度、折叠边 |
| 酒瓶 | 瓶口、瓶底内凹结构、玻璃厚度表达 |
| 饮料罐 | 拉环轮廓、开启刻线、卷封细节 |
| 铰盖盒 | 待提供图片后裁决 |

不建议盲目增加三角面数量。应该以功能部件的视觉可识别性为目标，要求每一处新增几何都有明确的物理或语义依据。

---

## 4. 三轮整改的研究价值

<box border radius="lg" padding={3} gap={3}>
  <row align="center">
    <box width="54px">
      <title size="lg" color="secondary">R1</title>
      <title size="xl">2.67</title>
    </box>
    <box flex={1}>
      **参数化几何阶段**
      <caption>尺寸与工程门禁优先，视觉真实性不足。</caption>
    </box>
  </row>
  <divider/>
  <row align="center">
    <box width="54px">
      <title size="lg" color="secondary">R2</title>
      <title size="xl">5.13</title>
    </box>
    <box flex={1}>
      **渲染管线阶段**
      <caption>解决基础摄影与展示问题，但仍受资产语义限制。</caption>
    </box>
  </row>
  <divider/>
  <row align="center">
    <box width="54px">
      <title size="lg" color="success">R3</title>
      <title size="xl">7.30</title>
    </box>
    <box flex={1}>
      **语义资产生成阶段**
      <caption>LLM 作者循环、功能部件、装配关系、物理材质，开始具备对标能力。</caption>
    </box>
  </row>
  <divider/>
  <row align="center">
    <box width="54px">
      <title size="lg" color="secondary">R4</title>
      <title size="xl">目标</title>
    </box>
    <box flex={1}>
      **公共管线收敛阶段**
      <caption>不增加资产族，集中解决摄影棚、材质光学及二级细节。</caption>
    </box>
  </row>
</box>

本轮最重要的成果不是平均分提高，而是 **LLM Author + 合同约束 + 自动门禁 + USD 编译 + 物理验证 + 视觉评审** 这条生产路线，已经在可见样本中展示出实际价值。

但三轮均包含多项同时发生的改动，因此不能把分数提升单独归因于 LLM 作者循环、材质库或渲染合同中的任何一项。

## 5. 最终裁决

| 验收项 | 裁决 |
|---|---|
| 同语义资产对标整改 | PASS（可见三组） |
| LLM 作者产出视觉质量 | 有条件通过 |
| R043 饮料罐 | PASS |
| R422 瓦楞箱 | NEAR PASS |
| R091 酒瓶 | RETAKE |
| R037 铰盖盒 | NOT_TESTED |
| 公共摄影棚合同 v3 | RETAKE |
| 材质库 | 有条件通过 |
| 全量资产视觉质量对标 | 尚未获证 |

本轮未独立运行 G-F1..F7、USD 或 PhysX 验证器，因此工程门禁通过属于你提供的证据，不是本次视觉评审独立复现的结论。

**Round4 不建议再扩大资产族。** 冻结现有几何，先做公共摄影棚整改和玻璃材质单变量实验，再组织匿名盲评。如果这两项能够收敛，Pack10K 有机会在这几个代表性资产上实现真正的视觉与工程双维度对标。

**Round3 总裁决：CONDITIONAL PASS。**