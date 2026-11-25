# GPT 对抗性视觉评审 round5b (2026-11-25)

> 会话 6b069d36 续评; R091 材质库通透度调整 (rough 0.02/传 0.85), R037 v4 薄壁 0.9mm 盖缝视角, R422/R043 冻结
> 裁决: 改善有限, 无新增打平; 分数稳定 — R422 7.4 (-0.4)✅ / R091 7.6 (-0.7) / R043 7.3 (-0.2)✅ / R037 6.9 (-1.3, +0.2 缓慢收敛)
> **关键发现 (GPT): G-F8 假阴性反例** — R422 墙角 + R091 斜向分界线仍可见但门禁 PASS; 需升级 G-F8b (斜向线/角点检测), 不能以 G-F8 PASS 等同背景缺陷消除

| 行 | R5 | R5b | NVIDIA | 差 | 状态 |
|---|---|---|---|---|---|
| R422 瓦楞箱 | 7.4 | 7.4 | 7.8 | -0.4 | ✅ 打平(冻结) |
| R091 玻璃酒瓶 | 7.6 | 7.6 | 8.3 | -0.7 | 未平 |
| R043 拉环罐 | 7.3 | 7.3 | 7.5 | -0.2 | ✅ 打平(冻结) |
| R037 铰盖盒 | 6.7 | 6.9 | 8.2 | -1.3 | 收敛中(+0.2) |

---

# Pack10K × USDCraft · Round5b 独立复审

**本轮改善有限，尚未新增打平资产。** R037 的背景确实比上一轮干净，但薄壁改造没有在闭合态渲染中充分体现；R091 调整了粗糙度和透射率，但从实际图片看，玻璃通透度的改善并不显著。

另外，G-F8 虽然四件全绿，但 R422 的墙角和 R091 的背景斜向分界线仍然清晰可见。**这已经构成图像门禁漏检的反例，不能继续把 G-F8 PASS 等同于背景缺陷消除。**

## 1. 四行评分与 Δ

沿用 Round5 评分尺度，NVIDIA 参考分保持冻结。

| 资产 | R4b | R5 | R5b | 本轮 Δ | NVIDIA | 当前差值 |
|---|---:|---:|---:|---:|---:|---:|
| R422 瓦楞箱 | 7.4 | 7.4 | **7.4** | 0.0 | 7.8 | −0.4 |
| R091 玻璃酒瓶 | 7.2 | 7.6 | **7.6** | 0.0 | 8.3 | −0.7 |
| R043 拉环罐 | 7.3 | 7.3 | **7.3** | 0.0 | 7.5 | −0.2 |
| R037 铰盖盒 | 5.9 | 6.7 | **6.9** | +0.2 | 8.2 | −1.3 |
| **平均分** | 6.95 | 7.25 | **7.30** | **+0.05** | 7.95 | −0.65 |

<box gap={3}>
  {#each [{n:"R422 瓦楞箱",v:[7.4,7.4,7.8]},{n:"R091 玻璃酒瓶",v:[7.6,7.6,8.3]},{n:"R043 拉环罐",v:[7.3,7.3,7.5]},{n:"R037 铰盖盒",v:[6.7,6.9,8.2]}] as d}
    <box gap={1}>
      **{d.n}**
      {#each d.v as s,i}
        <row align="center" gap={2}>
          <box width="60px"><caption>{["R5","R5b","NVIDIA"][i]}</caption></box>
          <box flex={1}>
            <box height={11} radius="2px" background="surface-tertiary">
              <box height={11} radius="2px" width={`${s*10}%`} background={["#94a3b8","#2563eb","#64748b"][i]}/>
            </box>
          </box>
          <text size="sm" tabularNums={true}>{s.toFixed(1)}</text>
        </row>
      {/each}
    </box>
  {/each}
</box>

### R422 瓦楞包裹箱：7.4（Δ 0.0）

冻结资产，维持原评分。闭合箱结构、胶带、纸板颜色均成立，但墙角、主体偏小、纸面规律性竖纹等问题仍在。

### R091 玻璃酒瓶：7.6（Δ 0.0）

本轮没有足够明确的视觉证据支持加分。

- 瓶腹仍然存在明显的灰绿色浑浊感。
- 瓶底仍是一块深色椭圆区域，内外壁结构没有右侧清楚。
- 瓶底右侧的细密竖线值得检查，可能来自网格法线、反射或折射，不应直接当作玻璃细节改善。
- 瓶肩高光仍然偏弱。
- 软木塞与瓶颈交界仍然发黑。

降低 roughness、提高 transmission 是合理的探索方向，但**参数变化不等于视觉效果已经改善**。目前证据不足以证明这组调整有效，也不足以判定其无效。

### R043 拉环饮料罐：7.3（Δ 0.0）

冻结资产，维持原评分。顶部黑色反射带仍然存在，但整体形态、拉环及金属罐识别度足以维持打平裁决。

### R037 铰盖保鲜盒：6.9（Δ +0.2）

本轮最明确的进步来自背景表现，而不是已经证实的薄壁视觉收益。

- 上轮顶部黑色背景带已消失。
- 盖沿黑色缝线清晰，盒盖与盒体的分离感有所改善。
- 圆角自然，整体轮廓稳定。
- 但闭合态下无法直接判断 0.9 mm 壁厚带来的视觉贡献。
- 盒身依然不透明，仍有明显的厚实白色方盒感。
- 双扣件与铰链仍然没有获得充分的视觉表达。
- V4 要求新增的 Z40 水平凹槽带和盖沿环形凹槽，在本图中没有清晰的可识别证据。

**54g 是工程侧的质量指标，不是视觉真实性指标。** 不能因为减重成功就认定视觉上的厚重感已经解决。

## 2. 打平行判定

<box gap={3}>
  {#each [{n:"R422 瓦楞箱",g:-0.4},{n:"R091 玻璃酒瓶",g:-0.7},{n:"R043 拉环罐",g:-0.2},{n:"R037 铰盖盒",g:-1.3}] as d}
    <box gap={1}>
      <row align="center">
        **{d.n}**
        <spacer/>
        <text color={Math.abs(d.g)<=0.5?"success":"danger"} weight="medium">{d.g.toFixed(1)} 分 · {Math.abs(d.g)<=0.5?"PASS":"FAIL"}</text>
      </row>
      <svg viewBox="0 0 320 28" width="100%">
        <rect x="10" y="5" width="300" height="18" rx="4" fill="#888888" opacity=".10"/>
        <rect x="122.5" y="5" width="75" height="18" fill="#16a34a" opacity=".16"/>
        <line x1="160" y1="1" x2="160" y2="27" stroke="currentColor" strokeOpacity=".4" strokeDasharray="3 2"/>
        <rect x={160+d.g*75} y="8" width={Math.abs(d.g*75)} height="12" rx="2" fill={Math.abs(d.g)<=0.5?"#16a34a":"#dc2626"}/>
        <circle cx={160+d.g*75} cy="14" r="5" fill={Math.abs(d.g)<=0.5?"#16a34a":"#dc2626"}/>
      </svg>
    </box>
  {/each}
  <row>
    <caption>−2.0</caption>
    <spacer/>
    <caption>打平区间 ±0.5</caption>
    <spacer/>
    <caption>+2.0</caption>
  </row>
</box>

<grid columns={2}>
  <grid-item>
    <caption>当前打平率</caption>
    <title size="2xl">2 / 4</title>
  </grid-item>
  <grid-item>
    <caption>本轮新增打平</caption>
    <title size="2xl">0</title>
  </grid-item>
</grid>

R091 距离打平门槛还差 0.2 分，R037 还差 0.8 分。但不应为了跨过主观评分阈值而反复进行微小调参，应优先解决能够被稳定观察和复现的缺陷。

## 3. R091 下一杠杆：停止盲目调整通透度

连续几轮整改之后，应该从参数试错进入光路诊断。

| 优先级 | 实验 | 唯一改动 | 验证目的 |
|---|---|---|---|
| P0 | G01 | 暂时关闭 Volume Absorption（若存在） | 判断瓶底发黑是否来自体积吸收 |
| P0 | G02 | Transmission bounces 提至 16 | 排除透射路径截断 |
| P1 | G03 | Transmission 0.85→1.0 | 隔离非透射成分的影响 |
| P1 | G04 | 调整公共透射背景亮度 | 检验玻璃内部纵深 |
| P2 | G05 | 校核瓶底几何及法线 | 排除重复壳面、自相交和异常折射 |

所有实验均从 R5b 冻结基线独立启动。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">瓶底光学诊断重点</title>
  <grid columns={2}>
    <grid-item>
      <svg viewBox="0 0 160 205" width="100%">
        <defs>
          <linearGradient id="glass5a" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#52796e"/>
            <stop offset="50%" stopColor="#3e625a"/>
            <stop offset="100%" stopColor="#63877c"/>
          </linearGradient>
        </defs>
        <rect width="160" height="205" rx="6" fill="#a4a6a5"/>
        <path d="M68 18 H92 V65 C92 85 109 106 109 125 V181 Q80 195 51 181 V125 C51 106 68 85 68 65Z" fill="url(#glass5a)" stroke="#77988e"/>
        <rect x="70" y="13" width="20" height="8" rx="2" fill="#e6d8b8"/>
        <ellipse cx="80" cy="180" rx="27" ry="9" fill="#172e29"/>
        <ellipse cx="80" cy="178" rx="35" ry="18" fill="none" stroke="#dc2626" strokeWidth="2" strokeDasharray="4 3"/>
        <path d="M115 169 L139 143" stroke="#dc2626" strokeWidth="1.5"/>
        <text x="140" y="133" fontSize="9" textAnchor="end" fill="#8b2222">底部暗区</text>
      </svg>
      **当前问题**
      <caption>底部过暗，内部结构不清晰。</caption>
    </grid-item>
    <grid-item>
      <svg viewBox="0 0 160 205" width="100%">
        <defs>
          <linearGradient id="glass5b" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#8aaf9c"/>
            <stop offset="12%" stopColor="#477a60"/>
            <stop offset="50%" stopColor="#759a87"/>
            <stop offset="90%" stopColor="#46705b"/>
            <stop offset="100%" stopColor="#abc6b3"/>
          </linearGradient>
        </defs>
        <rect width="160" height="205" rx="6" fill="#333b38"/>
        <path d="M68 18 H92 V65 C92 85 109 106 109 125 V181 Q80 195 51 181 V125 C51 106 68 85 68 65Z" fill="url(#glass5b)" fillOpacity=".8" stroke="#afcdbb"/>
        <rect x="70" y="13" width="20" height="12" rx="2" fill="#e6d8b8"/>
        <path d="M61 122 V172 Q80 183 99 172 V122" fill="none" stroke="#b5d5c1" strokeOpacity=".65"/>
        <ellipse cx="80" cy="177" rx="23" ry="8" fill="none" stroke="#b5d5c1"/>
        <path d="M58 121 Q60 103 71 81" fill="none" stroke="#d4e7de" strokeWidth="2.5" strokeLinecap="round"/>
      </svg>
      **目标效果**
      <caption>玻璃内外壁、底厚及折射轮廓可读。</caption>
    </grid-item>
  </grid>
  <caption>光学目标示意，非实际渲染结果。</caption>
</box>

**我的首选是 G01 和 G02，而不是继续降低 roughness。** 目前 0.02 已经很低，进一步降低可能只是让异常反射更加锐利，并不能解决玻璃内部的发黑问题。

---

## 4. R037 下一杠杆：暂停几何作者循环

我认为此前把「过厚、过实、过白」主要归因于壁厚，是一次不够严谨的归因。

对于闭合态且不透明的塑料盒，壁厚从 1.5 mm 降至 0.9 mm，通常不会直接改变主要外表面的视觉效果。V4 本轮的表现也不足以证明减薄能够解决厚重感。

真正值得优先验证的是材质语义与功能部件表达。

<box gap={3}>
  <row align="start">
    <AsyncImage query="translucent polypropylene food storage container white lid transparent frosted plastic body studio product photography" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1} gap={1}>
      **P0 · 盒身半透明 PP**
      保持盖体不透明，单独改变 base 的光学材质。让内部空间与薄壁结构能够被观察到。
      <caption>最高优先级，不改变几何。</caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <AsyncImage query="plastic food container snap locking clips blue latch close up lid seam" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1} gap={1}>
      **P1 · 扣件材质分层**
      为扣件引入独立的颜色或粗糙度，明确功能部件边界。前提是扣件确实暴露在外表面，而不是藏在盒壁内部。
      <caption>先检查几何可见性，再修改材质。</caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <AsyncImage query="hinged plastic food storage container lid partially open showing thin wall product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1} gap={1}>
      **P2 · 开盖结构验证图**
      通过原有 revolute joint 生成开盖 30° 的辅助视图，验证壁厚、盖沿台阶、双扣件与内部空间。
      <caption>辅助证据，不替代闭合态对标主图。</caption>
    </box>
  </row>
</box>

### R037 实验顺序

| 实验 | 唯一改动 | 验收目标 |
|---|---|---|
| H01 | Base 半透明材质 | 消除实心白块感 |
| H02 | 扣件独立材质 | 功能件可识别 |
| H03 | 开盖 30° | 证明薄壁与盖体结构 |
| H04 | 正交侧视辅助图 | 核验 Z40 凹槽及深度 |
| H05 | 公共相机方位调整 | 主图同时表达盖缝与至少一个扣件 |

注意：v3/v4 的 `material_id = plastic_pp` 是冻结合同的一部分。H01、H02 应优先通过渲染材质绑定层实现，不应擅自修改 Author Contract。

## 5. G-F8 门禁必须修订

这轮最有研究价值的发现，可能反而不是酒瓶或者保鲜盒，而是 G-F8 的假阴性。

<grid columns={2}>
  <grid-item>
    <svg viewBox="0 0 180 140" width="100%">
      <rect width="180" height="140" rx="5" fill="#bbb"/>
      <path d="M0 39 L52 25 L180 50 V140 H0Z" fill="#999"/>
      <path d="M52 0 V25 L180 50 M52 25 L0 39" fill="none" stroke="#dc2626" strokeWidth="2"/>
      <path d="M42 85 L86 70 L139 85 L96 102Z" fill="#dfcfb5"/>
      <path d="M42 85 L96 102 V122 L42 105Z" fill="#c1ae8f"/>
      <path d="M96 102 L139 85 V105 L96 122Z" fill="#a9997e"/>
      <path d="M8 4 V136 M172 4 V136" stroke="#16a34a" strokeWidth="2" strokeDasharray="4 3"/>
    </svg>
    **现有 G-F8**
    <caption>边距采样通过，但背景内部仍存在墙角。</caption>
  </grid-item>
  <grid-item>
    <svg viewBox="0 0 180 140" width="100%">
      <rect width="180" height="140" rx="5" fill="#aaa"/>
      <path d="M0 39 L52 25 L180 50 V140 H0Z" fill="#999"/>
      {#each Array.from({length:8}) as _,i}
        <line x1={i*24+6} y1="0" x2={i*24+6} y2="140" stroke="#16a34a" strokeOpacity=".35" strokeDasharray="3 3"/>
      {/each}
      {#each Array.from({length:6}) as _,i}
        <line x1="0" y1={i*25+5} x2="180" y2={i*25+5} stroke="#16a34a" strokeOpacity=".35" strokeDasharray="3 3"/>
      {/each}
      <path d="M42 85 L86 70 L139 85 L96 102Z" fill="#dfcfb5"/>
      <path d="M42 85 L96 102 V122 L42 105Z" fill="#c1ae8f"/>
      <path d="M96 102 L139 85 V105 L96 122Z" fill="#a9997e"/>
      <path d="M52 0 V25 L180 50 M52 25 L0 39" fill="none" stroke="#dc2626" strokeWidth="2.5" strokeDasharray="5 2"/>
    </svg>
    **建议 G-F8b**
    <caption>主体遮罩之外的二维背景区域检测。</caption>
  </grid-item>
</grid>

| 子门禁 | 检查对象 |
|---|---|
| F8a | 原有边距水平阶跃，继续保留 |
| F8b | 背景区域长直线与斜线检测 |
| F8c | 背景异常高对比区域检测 |
| F8d | 已知缺陷图片负向回归测试 |

直接把现有 R422 墙角图、R091 斜线图、Round5 R037 黑色背景带作为负向测试种子。

门禁升级后，必须能拒绝这些已知缺陷，同时允许正常的平滑渐变与接触阴影。

## 6. 最终裁决

| 项目 | 裁决 |
|---|---|
| R422 / R043 冻结 | PASS |
| R091 材质参数调整 | 视觉收益尚未获证 |
| R037 v4 薄壁结构 | 工程 PASS（据提交报告） |
| R037 v4 视觉表现 | 小幅改善 |
| G-F8 门禁覆盖能力 | FAIL，存在明确漏检 |
| 四资产全部打平 | 未达成 |
| Round5b 综合裁决 | **CONDITIONAL PASS** |

本次没有独立运行编译器、材质节点诊断及 G-F8 脚本。评分仅依据提交截图；0.2 分的变化也不能视为具有统计显著性的改善。此外，R091 同时修改了两个材质参数，R037 同时发生了几何与背景表现变化，因此本轮不具备严格的单变量归因条件。

**Round6 应当冻结几何，攻克光学与材质表达。不要再启动 v5 几何作者循环，直到现有 v4 的视觉瓶颈被实验证明确实来自几何。**