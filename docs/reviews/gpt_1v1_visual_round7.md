# GPT 对抗性视觉评审 round7 (2026-11-25)

> 会话 6b069d36 续评; 严格单变量: 仅 R091 应用 GPT S1 数值建议, 其余全部冻结
> 裁决: 「S1 微调无显著新增视觉收益, 维持 7.8, 不建议继续调整 — 项目进入收益递减阶段, 应集中解决 R037」
> **终态: 3/4 打平稳定** (R422 -0.4 / R091 -0.5 / R043 -0.2), R037 -1.3 唯一未平 (v5 作者迭代待送评)

| 行 | R6 | R7 | NVIDIA | 差 | 状态 |
|---|---|---|---|---|---|
| R422 瓦楞箱 | 7.4 | 7.4 | 7.8 | -0.4 | ✅ 打平(冻结) |
| R091 玻璃酒瓶 | 7.8 | 7.8 | 8.3 | -0.5 | ✅ 打平边缘(稳态) |
| R043 拉环罐 | 7.3 | 7.3 | 7.5 | -0.2 | ✅ 打平(冻结) |
| R037 铰盖盒 | 6.9 | 6.9 | 8.2 | -1.3 | 唯一未平(v5 待评) |

---

# Pack10K × USDCraft · Round7 独立视觉复审

**R091 的 S1 微调没有带来足够明显的新增视觉收益，维持 7.8 分，不建议继续调整。** 本轮没有发生明显的视觉回归，但也没有达到此前设想的 8.0+。

项目已经进入收益递减阶段。接下来应该集中解决 R037，而不是继续消耗迭代轮次优化已打平资产。

## 1. 四行打分与 Δ

沿用 Round6 评分标尺，NVIDIA 参考分冻结，Δ 为相对 Round6 的变化。

| 资产 | R5b | R6 | R7 | 本轮 Δ | NVIDIA | 剩余差值 |
|---|---:|---:|---:|---:|---:|---:|
| R422 瓦楞箱 | 7.4 | 7.4 | **7.4** | 0.0 | 7.8 | −0.4 |
| R091 玻璃酒瓶 | 7.6 | 7.8 | **7.8** | 0.0 | 8.3 | −0.5 |
| R043 拉环罐 | 7.3 | 7.3 | **7.3** | 0.0 | 7.5 | −0.2 |
| R037 铰盖盒 | 6.9 | 6.9 | **6.9** | 0.0 | 8.2 | −1.3 |
| **平均分** | 7.30 | 7.35 | **7.35** | **0.00** | 7.95 | −0.60 |

### R091 专项复审：S1 是否优于 Round6？

| 观察维度 | 本轮视觉变化 |
|---|---|
| 玻璃通透度 | 基本持平 |
| 瓶肩高光 | 未见显著改善 |
| 瓶腹浑浊感 | 略有减轻，但仍存在 |
| 软木塞透见性 | 基本持平 |
| 瓶底内凹结构 | 未见显著改善 |
| 瓶底暗区 | 依然明显 |
| 边缘细密竖线 | 仍然存在 |
| 整体商品真实性 | 持平 |

S1 参数调整方向没有明显错误，但我不会因为这是我上一轮给出的参数建议，就给自己的方案额外加分。

**S1 优于 R6 的假设尚未获证。**

### R091 剩余 0.5 分差距的性质

<box gap={3}>
  {#each [{n:"01",name:"瓶底内部光学结构",desc:"右图能够清楚辨认内凹底部与内外壁轮廓，左图仍表现为深色椭圆区域。",v:40},{n:"02",name:"玻璃轮廓与反射质量",desc:"右图瓶肩和瓶身边缘高光更加连续，左图偏弱，底部仍有细密竖线。",v:30},{n:"03",name:"瓶型与软木塞表达",desc:"左侧长颈、缓肩与右侧短颈、饱满瓶肩不同，软木塞的侧面表现也不同。",v:20},{n:"04",name:"主体与背景分离度",desc:"灰绿色玻璃与灰色背景的明度差偏小，轮廓不如右图突出。",v:10}] as d}
    <box gap={1}>
      <row align="center">
        <caption>{d.n}</caption>
        **{d.name}**
        <spacer/>
        **{d.v}%**
      </row>
      <box height={8} background="surface-tertiary" radius="full">
        <box height={8} background="#64748b" width={`${d.v}%`} radius="full"/>
      </box>
      <caption>{d.desc}</caption>
    </box>
  {/each}
</box>
<caption>以上百分比为主观归因权重，不是消融实验测出的贡献率。</caption>

现在的剩余差距已经不适合继续单纯通过 tint、roughness、transmission 微调解决。瓶底几何、光路与反射环境都可能参与其中。

**建议终止 R091 材质寻优，条件冻结在 R6 或 R7。** 两者视觉评分相同；若原始图像指标也没有实质差异，优先保留 R6，避免无收益的参数变更。

## 2. 打平行判定

<box gap={3}>
  {#each [{n:"R422 瓦楞箱",s:7.4,t:7.8},{n:"R091 玻璃酒瓶",s:7.8,t:8.3},{n:"R043 拉环罐",s:7.3,t:7.5},{n:"R037 铰盖盒",s:6.9,t:8.2}] as d}
    <box gap={1}>
      <row align="center">
        **{d.n}**
        <spacer/>
        <text tabularNums={true}>{d.s.toFixed(1)} / {d.t.toFixed(1)}</text>
        <text color={d.t-d.s<=0.500001?"success":"danger"} weight="medium">{d.t-d.s<=0.500001?"PASS":"FAIL"}</text>
      </row>
      <svg viewBox="0 0 320 26" width="100%">
        <rect x="10" y="5" width="300" height="16" rx="4" fill="#888888" opacity=".10"/>
        <rect x="122.5" y="5" width="75" height="16" fill="#16a34a" opacity=".15"/>
        <line x1="160" y1="1" x2="160" y2="25" stroke="currentColor" strokeOpacity=".4" strokeDasharray="3 2"/>
        <rect x={160+(d.s-d.t)*75} y="8" width={(d.t-d.s)*75} height="10" rx="2" fill={d.t-d.s<=0.500001?"#16a34a":"#dc2626"}/>
        <circle cx={160+(d.s-d.t)*75} cy="13" r="5" fill={d.t-d.s<=0.500001?"#16a34a":"#dc2626"}/>
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

<grid columns={3}>
  <grid-item>
    <caption>打平率</caption>
    <title size="2xl" color="success">75%</title>
  </grid-item>
  <grid-item>
    <caption>新增打平</caption>
    <title size="2xl">0</title>
  </grid-item>
  <grid-item>
    <caption>待攻克资产</caption>
    <title size="2xl">1</title>
  </grid-item>
</grid>

R037 距离打平最低门槛 7.7 分，尚差 **0.8 分**。

---

## 3. R037 v5 到货前的预备建议

这里我需要主动纠正一个可能正在发生的方向性错误。

**V5 的几何细节整改值得做，但我不认为仅凭 V5 几何就能消除剩余 1.3 分差距。**

当前 v4 与 NVIDIA 之间最大的视觉差距，仍然是材质语义，而不只是盖沿、扣件和铰链的几何细节。

<box gap={2}>
  <grid columns={2}>
    <grid-item>
      <svg viewBox="0 0 180 165" width="100%">
        <rect width="180" height="165" fill="#a5a5a5" rx="5"/>
        <ellipse cx="99" cy="143" rx="73" ry="15" fill="#555" opacity=".28"/>
        <path d="M17 52 L83 27 L165 49 L106 74Z" fill="#f1f1f1"/>
        <path d="M17 52 L106 74 L106 148 L25 122Z" fill="#dedede"/>
        <path d="M106 74 L165 49 L158 121 L106 148Z" fill="#8f9192"/>
        <path d="M108 76 L154 56" stroke="#222" strokeWidth="2"/>
      </svg>
      **V4 当前观感**
      <caption>不透明白色方盒，部件分离弱。</caption>
    </grid-item>
    <grid-item>
      <svg viewBox="0 0 180 165" width="100%">
        <defs>
          <linearGradient id="pp7" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#d5e9e1"/>
            <stop offset="100%" stopColor="#88ada4"/>
          </linearGradient>
        </defs>
        <rect width="180" height="165" rx="5" fill="#a5a5a5"/>
        <ellipse cx="100" cy="143" rx="74" ry="13" fill="#555" opacity=".25"/>
        <path d="M21 56 L106 79 L163 54 L156 121 Q154 128 106 148 L28 123Z" fill="url(#pp7)" fillOpacity=".8" stroke="#d3e6df"/>
        <path d="M28 73 L106 96 L155 74 M32 118 L106 139 L151 119" fill="none" stroke="#e1f0e8" strokeOpacity=".65"/>
        <path d="M16 50 L82 26 L168 48 L108 76Z" fill="#f4f4f4" stroke="#fff"/>
        <path d="M17 54 L106 81 L167 53" fill="none" stroke="#e4e4e4" strokeWidth="4"/>
        <path d="M41 64 L62 70 L61 84 L40 78Z" fill="#698da9" stroke="#a6c4d4"/>
        <path d="M77 75 L96 80 L95 94 L76 89Z" fill="#698da9" stroke="#a6c4d4"/>
      </svg>
      **目标视觉表达**
      <caption>半透明盒身、白盖、独立扣件。</caption>
    </grid-item>
  </grid>
  <caption>概念示意，保持高盒体形态，不是 V5 实际渲染。</caption>
</box>

### 3.1 提前准备 R037 专属材质实验

不修改 Author Contract，通过渲染层按部件绑定材质。以下数值作为实验起点，RGB 采用线性空间。

| 参数 | Base 盒身 | Lid 盒盖 | Snap latch 扣件 |
|---|---|---|---|
| Base Color | (0.68, 0.85, 0.79) | (0.85, 0.85, 0.85) | (0.28, 0.45, 0.65) |
| Transmission | 0.65 | 0.00 | 0.00 |
| Roughness | 0.28 | 0.32 | 0.25 |
| IOR | 1.49 | 1.49 | 1.49 |
| Metallic | 0.00 | 0.00 | 0.00 |
| Coat | 0.00 | 0.00 | 0.00 |

不要一次性全部应用，否则无法区分盒身透射与扣件色差各自的贡献。

### 3.2 建议 Round8 实验矩阵

| 实验 | 几何 | 材质 | 验证目的 |
|---|---|---|---|
| E0 | V4 | 原版 | 冻结基线 |
| E1 | V5 | 原版 | 测量纯几何整改收益 |
| E2 | V4 | 半透明 base | 测量纯材质收益 |
| E3 | V5 | 半透明 base | 检查几何与材质的交互效果 |
| E4 | E3 | 增加扣件色差 | 检查功能部件识别度 |

相机、灯光、背景、曝光及采样全部冻结。

这组实验比直接渲染 V5 更有研究价值：它可以回答一个此前始终没有解决的问题——**R037 的视觉缺陷主要来自几何细节，还是材质表达？**

### 3.3 V5 编译验收特别检查

上一轮 V5 作者代码存在几个必须重点验证的风险。

| 检查项 | 验收要求 |
|---|---|
| 盖沿凹槽 | 内外壳无穿插，局部有效壁厚正常 |
| 盖沿 R1 倒角 | 不与内壁或凹槽相交 |
| 扣件凸出 | 实测整体 Y 尺寸符合 ±1% |
| 双扣件可见性 | 正面或标准三分之四视角可识别 |
| 铰链带 | 与 base、lid 的实际连接区域正确 |
| 几何保真 | Base 网格与 V4 哈希一致 |
| 闭合态 | 原铰链轴、原点及限位不变 |

尤其注意 V5 的盖沿采用了 3 mm 宽、0.6 mm 深的解释性实现，并非字面要求的 3 mm 垂直深度；铰链宽度也从实际 V4 的 91 mm 改为了 18 mm。这些取舍必须在编译回执中确认，不能仅凭 Author 自检宣布完成。

## 4. 七轮收敛趋势

<Chart content={{"chartType":"line","xKey":"round","series":[{"dataKey":"box","label":"R422"},{"dataKey":"wine","label":"R091"},{"dataKey":"can","label":"R043"},{"dataKey":"container","label":"R037"}],"yAxisMin":0,"yAxisMax":10,"data":[{"round":"R1","box":4.5,"wine":1.5,"can":2,"container":3},{"round":"R2","box":6.6,"wine":4.2,"can":4.6,"container":5},{"round":"R3","box":7.2,"wine":6.8,"can":7.9,"container":null},{"round":"R4","box":7.2,"wine":7.1,"can":7.3,"container":null},{"round":"R4b","box":7.4,"wine":7.2,"can":7.3,"container":5.9},{"round":"R5","box":7.4,"wine":7.6,"can":7.3,"container":6.7},{"round":"R5b","box":7.4,"wine":7.6,"can":7.3,"container":6.9},{"round":"R6","box":7.4,"wine":7.8,"can":7.3,"container":6.9},{"round":"R7","box":7.4,"wine":7.8,"can":7.3,"container":6.9}]}}/>

趋势已经非常清楚：

- R1→R3：结构性整改带来最大收益。
- R3→R6：针对性渲染与材质整改带来逐渐递减的收益。
- R6→R7：酒瓶材质寻优进入平台期。

## 5. 门禁与实验纪律复核

本轮还有两个问题不能忽略。

**第一，G-F8/G-F8b 全绿仍不意味着背景缺陷已经消除。** R422 左图上方的墙角及地面交界线依然肉眼可见。这张图应继续作为门禁负向回归样本。R091 的水平边缘指标 0.66 也不能作为玻璃光学质量改善的证据。

**第二，R7 是单资产、单材质方案实验，但不是严格的单参数实验。** Tint、roughness、transmission、IOR 同时变化，因此只能评价 S1 整体效果，不能独立归因于某个参数。

本轮未独立运行门禁脚本，也未检查原始渲染通道和材质节点。评分属于截图级主观评审。

## 6. 最终裁决

| 项目 | 裁决 |
|---|---|
| R422 | PASS · 继续冻结 |
| R091 | PASS · 停止参数寻优 |
| R043 | PASS · 继续冻结 |
| R037 | RETAKE · 等待 V5 实验 |
| S1 参数方案 | 新增收益未获证 |
| 已打平资产回归 | 未见明显回归 |
| 背景门禁完整性 | 仍有漏检反例 |

**Round8 不要再动酒瓶。集中做 R037 的几何 × 材质对照实验，争取用一轮实验解决剩余的归因问题，而不是再进行五六轮猜测式整改。**