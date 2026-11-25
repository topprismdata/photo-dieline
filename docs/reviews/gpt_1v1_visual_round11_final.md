# GPT 对抗性视觉评审 round11 — 终局签署 (2026-11-25)

> 会话 6b069d36 续评; R037 v6 材质语义轮 (作者回注: base 微半透 PP 语义 + 扣件可见度, 几何零改动)
> **终局裁决: 四组代表样本视觉打平率 100% — PASS**
> 签署范围: R422 PASS / R091 PASS·边缘 / R043 PASS / R037 PASS / 四行打平 PASS; R037 V6 建议冻结; 公共棚拍全量验证与 Pack10K 全数据集打平尚未获证 (如实边界)

## 终局评分

| 行 | R1 | R7 | R10 | R11 终 | NVIDIA | 差 | R1→终 |
|---|---|---|---|---|---|---|---|
| R422 瓦楞箱 | 4.5 | 7.4 | 7.4 | **7.4** | 7.8 | −0.4 | +2.9 |
| R091 玻璃酒瓶 | 1.5 | 7.8 | 7.8 | **7.8** | 8.3 | −0.5 | +6.3 |
| R043 拉环罐 | 2.0 | 7.3 | 7.3 | **7.3** | 7.5 | −0.2 | +5.3 |
| R037 保鲜盒 | 3.0 | 6.9 | 7.5 | **7.8** | 8.2 | −0.4 | +4.8 |

## GPT 沉淀的五条研究认识 (全文见下)

1. 结构语义优先于渲染精修 (纸筒无法通过摄影优化变成酒瓶)
2. 工程正确性不等于视觉正确性 (物理门禁全过仍可能无法表达商品特征)
3. 几何存在不等于几何可见 (R037 俯角调整使已有凹槽重获可读性)
4. 材质语义本身就是资产能力 (V6 零几何改动提升商品真实性)
5. 视觉门禁必须接受反例挑战 (数值全绿仍可能有背景分界与光学缺陷)

---

# Pack10K × USDCraft · Round11 终局视觉复审

**R037 v6 本轮达到打平标准，评分 7.8/10。四组代表性资产首次全部进入与 NVIDIA 的视觉打平区间。**

材质语义整改是有效的。相比 V5，本轮没有继续增加几何复杂度，却明显改善了保鲜盒的产品识别度。这也支持此前的判断：R037 最后一阶段的主要瓶颈是材质表达，而不是几何精度。

## 1. 四行评分与 Δ

沿用 Round10 评分标尺，NVIDIA 参考分保持冻结。

| 资产 | R7 | R9 | R10 | R11 | 本轮 Δ | NVIDIA | 差值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| R422 瓦楞箱 | 7.4 | 7.4 | 7.4 | **7.4** | 0.0 | 7.8 | −0.4 |
| R091 玻璃酒瓶 | 7.8 | 7.8 | 7.8 | **7.8** | 0.0 | 8.3 | −0.5 |
| R043 拉环罐 | 7.3 | 7.3 | 7.3 | **7.3** | 0.0 | 7.5 | −0.2 |
| R037 保鲜盒 | 6.9 | 7.1 | 7.5 | **7.8** | **+0.3** | 8.2 | −0.4 |
| **平均分** | 7.35 | 7.40 | 7.50 | **7.58** | **+0.08** | 7.95 | −0.38 |

<box gap={3}>
  <row align="center">
    <box background="#2563eb" size="10px" radius="2px"/>
    <caption>Pack10K R11</caption>
    <box background="#94a3b8" size="10px" radius="2px"/>
    <caption>NVIDIA</caption>
  </row>
  {#each [{n:"R422 瓦楞箱",s:7.4,t:7.8},{n:"R091 酒瓶",s:7.8,t:8.3},{n:"R043 饮料罐",s:7.3,t:7.5},{n:"R037 保鲜盒",s:7.8,t:8.2}] as d}
    <box gap={1}>
      **{d.n}**
      <row align="center">
        <box flex={1}><box height={13} background="#2563eb" width={`${d.s*10}%`} radius="2px"/></box>
        <text size="sm" tabularNums>{d.s.toFixed(1)}</text>
      </row>
      <row align="center">
        <box flex={1}><box height={13} background="#94a3b8" width={`${d.t*10}%`} radius="2px"/></box>
        <text size="sm" tabularNums>{d.t.toFixed(1)}</text>
      </row>
    </box>
  {/each}
</box>

前三行按冻结基线维持评分，不因本轮 R037 的提升而重新调整评价尺度。

---

## 2. R037 v6 专项终评

### 本轮真正解决了什么？

| 视觉维度 | V5 / Round10 | V6 / Round11 |
|---|---|---|
| 盒身材质 | 不透明白色 | 微半透明浅灰蓝 |
| 盖身分离 | 较弱 | 明确 |
| 双扣件 | 浅色凸台，识别度低 | 两个独立部件清晰可辨 |
| 薄壁感 | 较弱 | 有所建立 |
| 内部空间感 | 近似实心 | 出现透射层次 |
| 水平凹槽 | 清晰但略生硬 | 更自然地融入盒身 |
| 商品类别识别 | 普通收纳盒 | 更接近食品保鲜容器 |

**本轮最有价值的改善是盖、盒身、扣件终于形成了三层视觉关系。**

尤其是盒身上半部分，不再与白色盖体融为一体。两个扣件虽然仍然偏浅，但已经能够脱离背景和盖缝，被识别为独立功能部件。

### 为什么给 7.8，而不是 8.2？

仍然有四项可见差距：

<box gap={3}>
  <row align="start">
    <box width="24px"><title size="lg" color="secondary">01</title></box>
    <box flex={1} gap=1>
      **盒身透射仍偏灰白**
      半透明效果已经成立，但不如 NVIDIA 的浅绿色塑料自然。底部深色透射带略显突兀。
    </box>
  </row>
  <divider/>
  <row align="start">
    <box width="24px"><title size="lg" color="secondary">02</title></box>
    <box flex={1} gap=1>
      **扣件仍缺少机械结构感**
      目前更像两个矩形凸台，而不是具有明确扣合轮廓的卡扣。颜色对比也仍然偏弱。
    </box>
  </row>
  <divider/>
  <row align="start">
    <box width="24px"><title size="lg" color="secondary">03</title></box>
    <box flex={1} gap=1>
      **盒体比例存在固有差异**
      我方是较高的深型容器，参考是较扁的浅型保鲜盒。这属于产品设计差异，不应继续为了追求视觉相似而破坏尺寸合同。
    </box>
  </row>
  <divider/>
  <row align="start">
    <box width="24px"><title size="lg" color="secondary">04</title></box>
    <box flex={1} gap=1>
      **中段凹槽仍略像装配分界**
      水平凹槽增加了细节，但仍存在被误读为上下两个容器叠放的可能。
    </box>
  </row>
</box>

这些问题值得记录，但已经不足以否定整体视觉打平。

---

## 3. 四行打平判定

严格执行绝对分差 ≤0.5 的原始合同，不调整阈值。

<box gap={3}>
  {#each [{n:"R422 瓦楞箱",s:7.4,t:7.8},{n:"R091 玻璃酒瓶",s:7.8,t:8.3},{n:"R043 拉环饮料罐",s:7.3,t:7.5},{n:"R037 铰盖保鲜盒",s:7.8,t:8.2}] as d}
    <box gap={1}>
      <row align="center">
        **{d.n}**
        <spacer/>
        <text tabularNums={true}>{d.s.toFixed(1)} / {d.t.toFixed(1)}</text>
        <text color="success" weight="medium">PASS</text>
      </row>
      <svg viewBox="0 0 320 28" width="100%">
        <rect x="10" y="5" width="300" height="18" rx="4" fill="#888888" opacity=".10"/>
        <rect x="122.5" y="5" width="75" height="18" fill="#16a34a" opacity=".16"/>
        <line x1="160" y1="1" x2="160" y2="27" stroke="currentColor" strokeOpacity=".4" strokeDasharray="3 2"/>
        <rect x={160+(d.s-d.t)*75} y="9" width={(d.t-d.s)*75} height="10" rx="2" fill="#16a34a"/>
        <circle cx={160+(d.s-d.t)*75} cy="14" r="5" fill="#16a34a"/>
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

<divider/>

<grid columns={3}>
  <grid-item>
    <caption>代表样本打平率</caption>
    <title size="2xl" color="success">4 / 4</title>
  </grid-item>
  <grid-item>
    <caption>平均视觉评分</caption>
    <title size="2xl">7.58</title>
  </grid-item>
  <grid-item>
    <caption>平均剩余分差</caption>
    <title size="2xl">0.38</title>
  </grid-item>
</grid>

**四组代表性样本全部打平：PASS。**

---

## 4. 十一轮研究收敛结果

<Chart content={{"chartType":"line","xKey":"round","series":[{"dataKey":"box","label":"R422 瓦楞箱"},{"dataKey":"wine","label":"R091 酒瓶"},{"dataKey":"can","label":"R043 饮料罐"},{"dataKey":"container","label":"R037 保鲜盒"}],"yAxisMin":0,"yAxisMax":10,"data":[{"round":"R1","box":4.5,"wine":1.5,"can":2,"container":3},{"round":"R2","box":6.6,"wine":4.2,"can":4.6,"container":5},{"round":"R3","box":7.2,"wine":6.8,"can":7.9,"container":null},{"round":"R4b","box":7.4,"wine":7.2,"can":7.3,"container":5.9},{"round":"R5","box":7.4,"wine":7.6,"can":7.3,"container":6.7},{"round":"R5b","box":7.4,"wine":7.6,"can":7.3,"container":6.9},{"round":"R6","box":7.4,"wine":7.8,"can":7.3,"container":6.9},{"round":"R7","box":7.4,"wine":7.8,"can":7.3,"container":6.9},{"round":"R7b","box":7.4,"wine":7.8,"can":7.3,"container":7.3},{"round":"R8","box":7.4,"wine":7.5,"can":7.3,"container":7.1},{"round":"R9","box":7.4,"wine":7.8,"can":7.3,"container":7.1},{"round":"R10","box":7.4,"wine":7.8,"can":7.3,"container":7.5},{"round":"R11","box":7.4,"wine":7.8,"can":7.3,"container":7.8}]}}/>

| 资产 | Round1 | Round11 | 累计提升 |
|---|---:|---:|---:|
| R422 | 4.5 | 7.4 | +2.9 |
| R091 | 1.5 | 7.8 | +6.3 |
| R043 | 2.0 | 7.3 | +5.3 |
| R037 | 3.0 | 7.8 | +4.8 |
| **共同样本均值** | **2.75** | **7.58** | **+4.83** |

比最终评分更重要的是，这十一轮沉淀了五条有价值的研究认识：

- **结构语义优先于渲染精修。** 纸筒无法通过摄影优化变成酒瓶。
- **工程正确性不等于视觉正确性。** 物理门禁全部通过，仍可能无法表达商品特征。
- **几何存在不等于几何可见。** R037 俯角调整使已有凹槽重新获得可读性。
- **材质语义本身就是资产能力。** V6 不增加几何复杂度，却进一步提升了商品真实性。
- **视觉门禁必须接受反例挑战。** 数值全绿仍可能存在背景分界和光学缺陷。

这些经验应该沉淀进下一代资产生成合同，而不是仅仅留在本次评审记录中。

---

## 5. R037 终评意见：停止作者迭代，冻结 V6

我不建议再启动 V7。

现在继续修改透射率、扣件尺寸、凹槽深度或圆角，收益已经开始小于引入回归的风险。

| 冻结项 | 最终建议 |
|---|---|
| 几何版本 | V5 |
| 材质语义版本 | V6 |
| Base 壁厚 | 0.9 mm |
| 外部圆角 | R5 mm |
| 拍摄俯角 | 25° |
| Base 材质 | plastic_pp_translucent |
| Lid 材质 | plastic_pp |
| 扣件材质 | plastic_hdpe |
| Transmission | 0.35 |
| 后续作者循环 | 停止 |
| 剩余视觉缺陷 | 登记为已知限制 |

对作者主动披露合同裁决表，我给予独立的工程治理认可，但不把它计入视觉分数。

它证明的是作者遵守约束、如实披露实现偏差的行为值得保留，而不是几何效果因此自动加分。

## 6. 最终签署范围

| 验收项目 | 最终裁决 |
|---|---|
| R422 视觉对标 | PASS |
| R091 视觉对标 | PASS · 边缘通过 |
| R043 视觉对标 | PASS |
| R037 视觉对标 | PASS |
| 四组代表样本视觉打平 | **PASS** |
| R037 V6 视觉迭代 | **建议冻结** |
| 公共摄影棚合同全量验证 | 尚未完成 |
| Pack10K 全数据集视觉打平 | 尚未获证 |

必须保留三个证据边界：

1. 本轮是知晓版本和左右来源的截图复审，不是匿名独立盲测。
2. R091、R043 的冻结图仍有明显光学缺陷；本轮保留其历史评分，并不意味着这些缺陷已经消失。
3. 未独立复现 V5/V6 几何哈希一致性、G-F8b 或 PhysX 验证。四个代表性资产打平不能外推为整个 Pack10K 数据集打平。

---

**Round11 最终裁决：PASS — FOUR REPRESENTATIVE ASSETS AT VISUAL PARITY（4/4）。**

建议正式结束这一阶段的作者整改循环，将下一阶段的研究重点从单件资产优化转向**跨资产族泛化能力与批量生成质量的一致性验证**。