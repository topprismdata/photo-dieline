# GPT 对抗性视觉评审 round12 (2026-11-25)

> 会话 6b069d36 续评; R091 增印刷酒标 (UV 圆柱投影), R037 黑棚俯拍
> **GPT 抓到实验纪律违规**: 标记冻结的 R422/R043 实际渲染图相较 R11 已变 (竞态修正时重渲未声明) — 「不能以代码已修复代替交付图像已修复, 不能继承冻结分数」
> 按实际图像重评: R422 6.5 (暗调版回归 -0.9) / R091 7.5 (-0.3, 黑棚暗执行过头削弱玻璃可读性) / R043 7.3 (罐身恢复银白) / R037 7.1 (-0.2)

## 教训 (GPT 原话)

- 「曝光方向变暗本身没错, 但这次暗过头了, 且削弱了玻璃可读性」
- 「检查渲染产物、HTML 图片引用路径及缓存, 排除新旧版本混用」
- **冻结 = 图像级冻结** (渲染参数与输出图像都不可变), 非仅几何冻结

## 状态

| 行 | R11 | R12 | NVIDIA | 裁决 |
|---|---|---|---|---|
| R422 | 7.4 | 6.5 | 7.8 | 回归 (暗调版) |
| R091 | 7.8 | 7.5 | 8.3 | 回落 (-0.3) |
| R043 | 7.3 | 7.3 | 7.5 | 守住 |
| R037 | 7.5 | 7.1 | 8.2 | -0.2 |

---

# Pack10K × USDCraft · Round12 独立视觉复审

**酒标增加细节密度的研究方向成立，但当前酒标投影存在明显的几何与排版问题，R091 不应加分。**

另外，本轮出现了一个比酒标更严重的实验纪律问题：标记为冻结的 R422 和 R043，其实际渲染图相较 Round11 已经明显改变。因此，本轮必须按实际交付图像重新评分，不能直接继承冻结分数。

## 1. 四行评分与 Δ

沿用 Round11 的视觉评价标尺，NVIDIA 参考分不变。

| 资产 | R11 | R12 | 本轮 Δ | NVIDIA | 差值 | 裁决 |
|---|---:|---:|---:|---:|---:|---|
| R422 瓦楞箱 | 7.4 | **6.5** | −0.9 | 7.8 | −1.3 | 回归 |
| R091 酒瓶 | 7.8 | **7.5** | −0.3 | 8.3 | −0.8 | 回归 |
| R043 拉环罐 | 7.3 | **7.6** | +0.3 | 7.5 | +0.1 | 打平 |
| R037 保鲜盒 | 7.8 | **7.8** | 0.0 | 8.2 | −0.4 | 打平 |
| **平均分** | 7.58 | **7.35** | **−0.23** | 7.95 | −0.60 | 回退 |

### R422 瓦楞箱：6.5/10

明显回归，不能继承原有 7.4 分。

- 主体大幅缩小，目测宽度仅占画面约35%，之前约为72%。
- 牛皮纸色泽退化为灰白色。
- 封箱胶带的视觉对比度降低。
- 背景占据过多画面，商品展示效果下降。

应检查自动取景算法是否将新增的超大地面或摄影棚对象纳入资产包围盒计算。

### R091 玻璃酒瓶：7.5/10

商品语义有所增强，但酒标的实际贴合效果不合格，抵消了新增印刷细节的收益。具体问题见下文。

### R043 拉环饮料罐：7.6/10

本轮反而出现了值得保留的改善。

- 罐身从此前近乎黑色恢复为银白色。
- 顶盖、拉环及底部金属边缘更加清晰。
- 商品类别识别度提升。
- 罐肩仍存在过重的黑色反射带，背景也有明显的光照分界。

虽然标记为冻结，但实际上不是 Round11 的原有图像。

### R037 铰盖保鲜盒：7.8/10

维持原有裁决。半透明盒身、白色盒盖及双扣件的视觉分层仍然成立，没有观察到足以改变评分的实质性变化。

## 2. R091 酒标专项评审

我已将本轮酒瓶区域放大检查。酒标本身的设计方向没有问题，**问题出在三维贴合与 UV 映射实现。**

<box gap={3}>
  <row align=start>
    <svg viewBox="0 0 120 190" width="110px">
      <rect width="120" height="190" rx="5" fill="#777"/>
      <path d="M48 12 H72 V62 Q72 76 89 99 V174 Q60 184 31 174 V99 Q48 76 48 62Z" fill="#64837a" stroke="#a5bcb5"/>
      <rect x="49" y="8" width="22" height="9" rx="2" fill="#ded5b9"/>
      <path d="M28 94 Q60 80 92 94 V147 Q60 159 28 147Z" fill="#eee9dd" stroke="#c5b77e"/>
      <ellipse cx="60" cy="94" rx="32" ry="9" fill="#eee9dd" fillOpacity=".6" stroke="#c5b77e"/>
      <path d="M31 96 Q60 105 89 96 M31 144 Q60 155 89 144" fill="none" stroke="#baa568"/>
      <text x="29" y="123" fontFamily="serif" fontSize="13" fill="#555">ck10K</text>
      <ellipse cx="60" cy="93" rx="36" ry="15" fill="none" stroke="#dc2626" strokeWidth="2" strokeDasharray="4 3"/>
    </svg>
    <box flex={1} gap={1}>
      **当前缺陷：酒标像独立套筒**
      <text size="sm">酒标上沿与瓶肩之间出现明显空隙，可以看见标签内侧。视觉上不像粘贴在玻璃表面的纸标，而像套在瓶身上的独立纸筒。</text>
      <caption>严重程度：P0</caption>
    </box>
  </row>
  <divider/>
  <row align=start>
    <svg viewBox="0 0 120 190" width="110px">
      <rect width="120" height="190" rx="5" fill="#777"/>
      <path d="M48 12 H72 V62 Q72 76 89 99 V174 Q60 184 31 174 V99 Q48 76 48 62Z" fill="#64837a" stroke="#a5bcb5"/>
      <rect x="49" y="8" width="22" height="9" rx="2" fill="#ded5b9"/>
      <path d="M31 108 Q60 114 89 108 V146 Q60 153 31 146Z" fill="#f1ead9" stroke="#c5b77e"/>
      <path d="M34 112 Q60 117 86 112 M34 143 Q60 150 86 143" fill="none" stroke="#b39742"/>
      <text x="60" y="124" fontSize="9" fontFamily="serif" textAnchor="middle" fill="#742525">Château</text>
      <text x="60" y="135" fontSize="10" fontFamily="serif" textAnchor="middle" fill="#742525">Pack10K</text>
      <text x="60" y="143" fontSize="4" textAnchor="middle" fill="#742525">GRAND VIN 2020</text>
    </svg>
    <box flex={1} gap={1}>
      **正确目标：贴合瓶身表面**
      <text size="sm">纸标紧贴玻璃曲面，限定在实际直身段内，文字朝向标准主视角，保留上下玻璃区域的光学信息。</text>
      <caption>整改目标示意，非实际渲染。</caption>
    </box>
  </row>
</box>

### 五项专项检查

| 检查项 | 裁决 | 视觉证据 |
|---|---|---|
| 商品语义 | 改善 | 更容易识别为有品牌的酒类商品 |
| 标签贴合 | FAIL | 上沿明显悬空，呈纸筒状 |
| UV 朝向 | FAIL | 正面只能读到部分 Pack10K 字样 |
| 标签比例 | 需整改 | 高度偏大，遮挡较多玻璃结构 |
| 印刷质感 | 部分通过 | 金线和葡萄纹存在，但对比度偏低 |

**这不是一张合格酒标贴在合格酒瓶上，而是一张设计合理的酒标被错误地映射到了酒瓶上。**

## 3. E1 客观指标如何评价？

<grid columns={2}>
  <grid-item>
    <caption>边缘密度 E1</caption>
    <title size="2xl">+27.9%</title>
    <caption>0.0068 → 0.0087</caption>
  </grid-item>
  <grid-item>
    <caption>方向熵</caption>
    <title size="2xl">0.900</title>
    <caption>参考值 0.705</caption>
  </grid-item>
</grid>

<box gap={2}>
  {#each [{n:"原版酒瓶",v:0.0068},{n:"印刷酒标版",v:0.0087},{n:"此前 NVIDIA E1 参照",v:0.025}] as d,i}
    <row align=center>
      <box width="122px"><text size="sm">{d.n}</text></box>
      <box flex={1}>
        <box height={14} radius="2px" background="surface-tertiary">
          <box height={14} radius="2px" width={`${d.v/0.025*100}%`} background={i===1?"#2563eb":"#94a3b8"}/>
        </box>
      </box>
      <text size="sm" tabularNums>{d.v.toFixed(4)}</text>
    </row>
  {/each}
</box>

<caption>0.025 为 Round8 报告中的参照值，只有在 ROI、分辨率及检测算法一致时才能直接比较。</caption>

本轮实验支持一个有价值的研究假设：**印刷图案可以增加图像细节密度，而不必增加主体网格的复杂度。**

但不能进一步推导出视觉质量超过 NVIDIA。

原因是 E1 和方向熵无法区分以下情况：

| 边缘来源 | 是否属于有效商品细节 |
|---|---|
| 正确贴合的品牌文字 | 是 |
| 葡萄藤印刷图案 | 是 |
| 真实纸标边缘 | 是 |
| 悬空纸筒上沿 | 否 |
| UV 拉伸或错误接缝 | 否 |
| 异常光照分界 | 否 |

建议将 E1 拆分为三个独立指标：

- **E1-G：几何结构细节密度**
- **E1-M：材质与印刷细节密度**
- **E1-A：异常伪影边缘密度**

前两项可以作为质量贡献，第三项应该作为缺陷，而不是奖励。

尤其需要注意，NVIDIA 参考图是无标签玻璃瓶。新增酒标后，Pack10K 在商品表达能力上增加了一个维度，但已经不再是严格等条件的裸瓶视觉对标。

## 4. 打平行判定

按照绝对分差 ≤0.5 的原合同：

<box gap={3}>
  {#each [{n:"R422 瓦楞箱",s:6.5,t:7.8},{n:"R091 酒瓶",s:7.5,t:8.3},{n:"R043 拉环罐",s:7.6,t:7.5},{n:"R037 保鲜盒",s:7.8,t:8.2}] as d}
    <box gap={1}>
      <row align=center>
        **{d.n}**
        <spacer/>
        <text tabularNums>{d.s.toFixed(1)} / {d.t.toFixed(1)}</text>
        <text color={Math.abs(d.s-d.t)<=0.500001?"success":"danger"} weight="medium">{Math.abs(d.s-d.t)<=0.500001?"PASS":"FAIL"}</text>
      </row>
      <svg viewBox="0 0 320 28" width="100%">
        <rect x="10" y="5" width="300" height="18" rx="4" fill="#888888" opacity=".10"/>
        <rect x="122.5" y="5" width="75" height="18" fill="#16a34a" opacity=".15"/>
        <line x1="160" y1="1" x2="160" y2="27" stroke="currentColor" strokeOpacity=".4" strokeDasharray="3 2"/>
        <rect x={Math.min(160,160+(d.s-d.t)*75)} y="9" width={Math.abs(d.t-d.s)*75} height="10" rx="2" fill={Math.abs(d.s-d.t)<=0.500001?"#16a34a":"#dc2626"}/>
        <circle cx={160+(d.s-d.t)*75} cy="14" r="5" fill={Math.abs(d.s-d.t)<=0.500001?"#16a34a":"#dc2626"}/>
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
    <caption>Round11 冻结基线</caption>
    <title size="2xl">4 / 4 PASS</title>
  </grid-item>
  <grid-item>
    <caption>Round12 实际交付图</caption>
    <title size="2xl">2 / 4 PASS</title>
  </grid-item>
</grid>

Round11 的历史通过记录仍然有效，但不能自动继承到发生变化的 Round12 渲染产物上。

## 5. R091 终评整改建议

不再修改瓶型、玻璃材质和灯光。**只修复酒标投影算法。**

| 优先级 | 整改项 | 具体要求 |
|---|---|---|
| P0 | 曲面贴合 | 从实际瓶身外表面提取标签区域，禁止使用固定半径独立圆筒 |
| P0 | 标签偏移 | 沿表面法线偏移 0.05–0.15 mm，作为防止 Z-fighting 的起始值 |
| P0 | 轴向范围 | 根据实际瓶肩起点确定标签上沿，不直接假定 Z=170 mm 仍为直身段 |
| P0 | UV 朝向 | 令中央品牌文字对准标准相机方位 |
| P1 | 标签高度 | 建议先测试 70、80、90 mm 三档 |
| P1 | 印刷材质 | 非金属纸张，roughness 0.45–0.60 |
| P1 | 构图恢复 | 主体高度占画面约 80%–85% |
| P2 | UV 接缝 | 放在瓶身背面，避免正面文字跨接缝 |

### 建议新增酒标专项门禁

| 门禁 | 验收条件 |
|---|---|
| L01 贴合 | 标签与玻璃表面距离符合设定偏移 |
| L02 无悬空 | 不存在脱离瓶身的套筒结构 |
| L03 UV 保真 | 字体、边框和花纹无明显拉伸 |
| L04 文字可读 | 主视图完整呈现核心品牌文字 |
| L05 几何冻结 | 裸瓶母本几何哈希不变 |
| L06 光学保留 | 标签外玻璃区域无明显回归 |
| L07 实验一致性 | 其余资产渲染文件哈希不变 |

## 6. 最终裁决

| 项目 | 裁决 |
|---|---|
| 印刷纹理提升 E1 的研究方向 | PASS |
| 商品语义增强 | PASS |
| 当前酒标贴合实现 | **FAIL** |
| R091 视觉突破 7.8 | 未达成 |
| 冻结资产一致性 | FAIL |
| G-F8 / G-F8b | 报告通过，未独立复验 |
| Round12 综合 | **RETAKE** |

本轮基于截图及局部放大检查，未读取实际酒标网格、UV 数据、Blender 场景或门禁脚本。因此，悬空套筒的具体实现根因尚需工程侧确认。评分属于主观视觉评估，E1 改善幅度来自你的实测报告。

我建议将 R091 分成两个永久保留的资产版本：`bottle_wine_raw` 用于裸瓶工程与视觉对标，`bottle_wine_branded` 用于印刷材质、商品识别与合成数据研究。

**酒标这个研究方向值得保留，但当前实现还远没有达到无可挑剔的程度。修好贴合算法比继续增加印刷细节重要得多。**