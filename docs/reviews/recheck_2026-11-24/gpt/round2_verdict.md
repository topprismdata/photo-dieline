# GPT 第 2 轮整改复审判决 (PD-RECHECK-R2)

- 来源: ChatGPT relay 会话 (browser relay, backend-api 抓取); 原文快照 /tmp/pd_recheck/gpt_r2_{main,raw}.txt (未入仓)
- 提示词: round3Prompt 同目录无 R2 版; R2 评审由整改证据 + OPTIMIZATION_PLAN v2 驱动
- 判决格式为 ChatGPT 画布导出原样 (card/box 标记), 未编辑
- 本轮总判: A1–A3 有条件通过, A4 未形成完整闭环; 分级认可; 折线语义与 L2 验收定义需修订

---

## 2. R2-2：查表基线能否排除变体记忆？

**裁决：排除了最简单的离散变体查表解释，但不能排除更广义的变体记忆与插值机制。**

这一轮新增的查表实验有很高的信息价值，比直接扩大训练集更值得做。

<card gap={3}>
  <title size="md">同一合成留出集 · 比例 MAE</title>
  <caption>误差越低越好</caption>
  {#each [["DINOv2 最近邻查表",0.0564,"#94a3b8"],["中位数基线",0.0495,"#94a3b8"],["参数空间 Oracle 查表",0.0228,"#64748b"],["CNN 回归",0.0166,"#16a34a"]] as item}
    <box gap={1}>
      <row>
        <text size="sm">{item[0]}</text>
        <spacer/>
        <text weight="medium" tabularNums={true}>{item[1].toFixed(4)}</text>
      </row>
      <box height={22} radius="sm" background="surface-tertiary">
        <box height="100%" radius="sm" background={item[2]} width={`${item[1]/0.06*100}%`}/>
      </box>
    </box>
  {/each}
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>CNN 相对 Oracle 查表</caption>
      <title size="2xl" color="success">−27.2%</title>
    </grid-item>
    <grid-item>
      <caption>CNN 相对中位数基线</caption>
      <title size="2xl" color="success">−66.5%</title>
    </grid-item>
  </grid>
  <caption>依据提交数据计算，未独立复现。</caption>
</card>

### 2.1 你仍然有一处过度表述

你将参数空间 Oracle 查表称为「任何查表法的下界」，这个说法不够严格。

它实际上是：

> 在相同损失函数下，输出必须是某一个已见训练标签时，单标签查表方法的理论误差下界。

以下方法仍然可以突破这个下界：

- 多个已见变体的加权平均。
- 在已见变体之间进行连续参数插值。
- 先识别模板，再依据视觉代理变量修正尺寸。
- 对不同尺寸参数分别查表、重新组合。

所以 CNN 超越 Oracle 查表，证明了它具有超越离散标签选择的预测能力，却没有证明它使用的是正确的几何测量机制。

| 竞争假设 | R2 更新后的证据状态 |
|---|---|
| 纯离散变体查表 | 已受到强反证 |
| 变体记忆＋连续插值 | 仍成立为竞争假设 |
| 渲染颜色或纹理捷径 | 未排除 |
| 取景尺度捷径 | 未排除 |
| 真正学习透视几何 | 有可能，尚未证实 |
| 几何覆盖稀疏是主因 | 仍未证实 |

### 2.2 E4 优先做哪一个？

**首选 E4-B：同外观、连续变化几何。**

但我建议把 E4-B 和 E4-A 组合成一个成本很低的双因素反事实实验。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">E4-B+：几何 × 外观反事实矩阵</title>
  <svg viewBox="0 0 340 235" width="100%">
    <text x="195" y="14" textAnchor="middle" fontSize="11" fill="currentColor">几何连续变化 →</text>
    {#each [0,1,2,3,4] as n}
      <text x={86+n*51} y="33" textAnchor="middle" fill="currentColor" fontSize="10">{["−20%","−10%","基准","+10%","+20%"][n]}</text>
      {#each [0,1,2] as m}
        <g transform={`translate(${66+n*51},${43+m*58})`}>
          <rect x={8-n*2} y="8" width={18+n*4} height="35" fill={["#cbd5e1","#2563eb","#ca8a04"][m]} fillOpacity=".55" stroke="currentColor" strokeOpacity=".4"/>
          <path d={`M${8-n*2} 8l9 -7h${18+n*4}l-9 7M${26+n*2} 8l9 -7v35l-9 7`} fill="none" stroke="currentColor" strokeOpacity=".6"/>
          {#if m===2}
            <path d={`M${11-n*2} 19h${12+n*4}M${11-n*2} 23h${12+n*4}M${11-n*2} 27h${12+n*4}`} stroke="currentColor" strokeOpacity=".5"/>
          {/if}
        </g>
      {/each}
    {/each}
    {#each ["白模","纯色","印刷"] as l,i}
      <text x="38" y={69+i*58} fontSize="11" textAnchor="middle" fill="currentColor">{l}</text>
    {/each}
    <text x="195" y="230" fontSize="10" textAnchor="middle" fill="currentColor" opacity=".7">同一相机内参、位姿与距离；仅改变指定变量</text>
  </svg>
  <caption>示意矩阵。正式实验应同时覆盖多个独立参数方向及多个相机位姿。</caption>
</box>

不需要重新训练，直接使用冻结 CNN 做推理。

评价四个指标：

| 指标 | 判断内容 |
|---|---|
| 响应斜率 | 真值变化 10%，预测是否产生相应变化 |
| 单调性 | 尺寸持续增大时，预测是否也持续增大 |
| 外观敏感度 | 尺寸不变、外观变化时，预测漂移多少 |
| 参数串扰 | 只改变 W 时，D/H 等无关参数是否异常变化 |

再记录预测值是否集中在原有 24 个训练变体附近。

如果预测形成明显阶梯，说明变体记忆仍然占据主导；如果预测连续但高度依赖外观，则说明模型可能在进行捷径插值。

**E4-B+ 的结果不论好坏，都比增加十倍训练数据提供更多路线决策信息。**

---

## 3. R2-3：折线语义与观察面约定

### 3.1 内面作为观察面是否可以？

**可以。不要求内部几何约定必须以印刷面为准。**

Mountain / Valley 本身具有观察方向依赖性，从纸张另一侧观察时，两者会互换。<Cite refs={["turn639123search36","turn639123search7"]}/>

但是你现在把三个不同概念放在了同一个约定里，需要拆开。

<box border radius="lg" padding={3} gap={3}>
  <title size="md">折线语义应该分为三个层次</title>
  <svg viewBox="0 0 340 192" width="100%">
    <text x="170" y="14" fontSize="12" textAnchor="middle" fill="currentColor">同一条物理折线，从相反面观察</text>
    <path d="M24 60L85 115L146 60" stroke="#2563eb" strokeWidth="5" fill="none" strokeLinejoin="round"/>
    <path d="M194 115L255 60L316 115" stroke="#2563eb" strokeWidth="5" fill="none" strokeLinejoin="round"/>
    {#each [85,255] as x}
      <path d={`M${x} 26v19m-5 -6l5 6l5 -6`} stroke="currentColor" fill="none" strokeWidth="1.5"/>
    {/each}
    <text x="85" y="139" fontSize="13" textAnchor="middle" fill="currentColor">VALLEY</text>
    <text x="255" y="139" fontSize="13" textAnchor="middle" fill="currentColor">MOUNTAIN</text>
    <text x="85" y="157" fontSize="10" textAnchor="middle" fill="currentColor" opacity=".7">从参考面 A 观察</text>
    <text x="255" y="157" fontSize="10" textAnchor="middle" fill="currentColor" opacity=".7">从参考面 B 观察</text>
    <text x="170" y="184" textAnchor="middle" fontSize="11" fill="currentColor">几何关系不变，观察语义翻转</text>
  </svg>
  <divider/>
  <row align="start">
    <box flex={1} gap={1}>
      **几何层**

      <caption>有向铰链轴、带符号折角、父子变换</caption>
    </box>
    <box flex={1} gap={1}>
      **语义层**

      <caption>参考面 A/B、M/V 标签、内外面映射</caption>
    </box>
    <box flex={1} gap={1}>
      **制造层**

      <caption>印刷面、压线工艺面、材料及设备要求</caption>
    </box>
  </row>
</box>

你的 `polygon_2d` 正面约定可以作为几何内部的 reference side A。

但不要直接规定它永远是盒内面或者印刷面，因为不同模板的物理方向与双面印刷情况可能不同。

我建议在 Geometry IR 增加以下语义：

| 字段建议 | 含义 |
|---|---|
| `reference_side` | 展开图统一参考面 A/B |
| `hinge_axis` | 有向铰链轴 |
| `fold_angle_signed` | 基于约定计算的带符号折角 |
| `mountain_valley` | 相对于指定参考面的折叠语义 |
| `exterior_side` | 成品外表面映射 |
| `print_side` | 印刷面，可为未知或双面 |
| `crease_process_side` | 制造压线工艺要求 |
| `convention_version` | 折线约定版本 |

这里还要增加一条硬性约束：**二维笛卡尔坐标与 SVG 的 Y 轴向下坐标必须明确转换**，否则 CCW 判断可能在导出时反转。

### 3.2 1066 条不一致折线能否自动重标？

**反对直接批量自动重标；同意自动生成修正候选。**

因为目前尚不清楚是 M/V 标签错了，还是 `target_dir_3d` 本身错了。

如果直接按 `target_dir_3d` 推导全部标签，你会让两套数据变得完全一致，但可能只是把错误同步到了第二个字段。

这就是另一种共因失效。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">1066 条折线的整改流程</title>
  <svg viewBox="0 0 340 237" width="100%">
    <rect x="85" y="5" width="170" height="32" rx="5" fill="#64748b" fillOpacity=".12" stroke="#64748b"/>
    <text x="170" y="25" fontSize="11" textAnchor="middle" fill="currentColor">自动推导候选 M/V 标签</text>
    <path d="M170 37V51" stroke="currentColor" strokeOpacity=".6"/>
    <rect x="55" y="51" width="230" height="38" rx="5" fill="#64748b" fillOpacity=".12" stroke="#64748b"/>
    <text x="170" y="67" fontSize="11" textAnchor="middle" fill="currentColor">独立验证成品方向与接缝</text>
    <text x="170" y="80" fontSize="10" textAnchor="middle" fill="currentColor">目标几何不能仅由现有折角定义</text>
    <path d="M170 89V102H83V114M170 102H257V114" stroke="currentColor" strokeOpacity=".6" fill="none"/>
    <rect x="9" y="114" width="148" height="43" rx="5" fill="#16a34a" fillOpacity=".08" stroke="#16a34a"/>
    <text x="83" y="132" fontSize="11" textAnchor="middle" fill="currentColor">已验证的结构族</text>
    <text x="83" y="145" fontSize="10" textAnchor="middle" fill="currentColor">允许批量生成修订</text>
    <rect x="183" y="114" width="148" height="43" rx="5" fill="#d97706" fillOpacity=".08" stroke="#d97706"/>
    <text x="257" y="132" fontSize="11" textAnchor="middle" fill="currentColor">结构或方向未证实</text>
    <text x="257" y="145" fontSize="10" textAnchor="middle" fill="currentColor">保留 UNKNOWN / 待审</text>
    <path d="M83 157V173" stroke="currentColor" strokeOpacity=".6"/>
    <rect x="9" y="173" width="148" height="47" rx="5" fill="#64748b" fillOpacity=".1" stroke="#64748b"/>
    <text x="83" y="191" fontSize="11" textAnchor="middle" fill="currentColor">生成差异台账</text>
    <text x="83" y="205" fontSize="10" textAnchor="middle" fill="currentColor">旧值、新值、理由与证据</text>
  </svg>
</box>

60 个模板内部混用两种约定，说明这很可能不是简单的全局正负号翻转。

但也不需要人工审查 1591 条折线。应当按结构族审查基础折线模式，在确认生成规则后，再将修正传播到参数变体。

**签署意见：内部观察面约定批准；无条件批量重标不批准。**

---

## 4. R2-4：扰动灵敏度作为 L2 判据是否合理？

你的担忧完全成立。

**裁决：扰动灵敏度应是 L2 的必要测试之一，但不是充分条件；甚至不应要求所有折线在所有角度下都必然产生非法结果。**

考虑一个极端的验证器：

```python
def validate(ir):
    return ir == golden_ir
```

它能够发现所有折角变化、所有面板移动和所有尺寸修改。

如果只评价负向变异检测率，这个毫无泛化能力的验证器甚至可能得到 100 分。

### 4.1 需要同时评价四种结果

{@body const [strictness,setStrictness]=DIL.useState("balanced")}
<card gap={3}>
  <title size="md">验证器不能只追求敏感</title>
  <segmented-control size="md" value={strictness} onChange={setStrictness} options={[{"label":"过度宽松","value":"loose"},{"label":"合理门禁","value":"balanced"},{"label":"过度严格","value":"strict"}]}/>
  <grid columns={2} gap={2}>
    {#each (strictness==="loose"?[["合法样本","通过",true],["非法样本","漏检",false]]:strictness==="strict"?[["合法样本","误杀",false],["非法样本","拒绝",true]]:[["合法样本","通过",true],["非法样本","拒绝",true]]) as cell}
      <grid-item>
        <box background="surface-secondary" radius="md" padding={3} align="center" gap={1}>
          <caption>{cell[0]}</caption>
          <icon name={cell[2]?"check-circle":"x-circle"} color={cell[2]?"success":"danger"} size="2xl"/>
          **{cell[1]}**
        </box>
      </grid-item>
    {/each}
  </grid>
  <text size="sm" color="secondary">{strictness==="loose"?"灵敏度不足：无法阻止错误刀版。":strictness==="strict"?"特异性不足：把合法参数变化也当作错误。":"同时验证合法变化能够通过、非法变化能够被拒绝。"}</text>
</card>

### 4.2 我要求新增的正向挑战集

| 编号 | 合法变化 | 预期结果 |
|---|---|---|
| POS-01 | 整体二维平移 | 通过 |
| POS-02 | 整体旋转及坐标系一致转换 | 通过 |
| POS-03 | 合法参数域内改变 W/D/H | 通过 |
| POS-04 | 共线边增加或删除中间顶点 | 通过 |
| POS-05 | 面板及折线记录重新排序 | 通过 |
| POS-06 | 父子面及铰链方向等价转换 | 通过 |
| POS-07 | 容差范围内的小角度偏差 | 按容差通过 |
| POS-08 | 参考面翻转且 M/V 同步翻转 | 通过 |
| POS-09 | 允许的替代折叠顺序 | 通过 |
| POS-10 | 不改变目标功能的合法结构自由度 | 通过 |

其中 POS-09 和 POS-10 应按模板声明适用，不能全园强制。

### 4.3 扰动探针还需要增加局部尺度

目前的 +35°、−35°、180° 都是较大的破坏。

它们能够发现严重的折向错误，但不能说明系统能够检测制造容差边缘的微小偏差。

建议建立如下测试：

| 扰动等级 | 示例 | 目的 |
|---|---|---|
| 等价扰动 | ±360°（适用终态角度时） | 不应误杀等价终态 |
| 容差内扰动 | ±0.1° 等 | 验证数值鲁棒性 |
| 容差边界扰动 | 根据实际特征尺寸计算 | 验证阈值行为 |
| 中等非法扰动 | ±5°、±10° | 验证有效灵敏度 |
| 严重破坏 | ±35°、180° | 验证重大结构异常 |

同样的折角变化，对于不同长度的面板会产生不同的末端偏差。

{@body const [length,setLength]=DIL.useState(50)}
{@body const [angle,setAngle]=DIL.useState(1)}
<card gap={3}>
  <title size="md">折角扰动与边缘位移</title>
  <svg viewBox="0 0 340 146" width="100%">
    <g transform="translate(35 112)">
      <path d="M0 0H275" stroke="currentColor" strokeOpacity=".15" strokeDasharray="4 4"/>
      <path d={`M0 0H${length*1.35}`} stroke="#64748b" strokeWidth="3"/>
      <path d={`M0 0L${length*1.35*Math.cos(angle*Math.PI/180)} ${-length*1.35*Math.sin(angle*Math.PI/180)}`} stroke="#2563eb" strokeWidth="3"/>
      <path d={`M${length*1.35} 0L${length*1.35*Math.cos(angle*Math.PI/180)} ${-length*1.35*Math.sin(angle*Math.PI/180)}`} stroke="#dc2626" strokeWidth="2" strokeDasharray="3 2"/>
      <circle r="4" fill="currentColor"/>
      <text x="4" y="18" fill="currentColor" fontSize="10">铰链轴</text>
    </g>
  </svg>
  <row>
    <label>铰链至测量点距离</label>
    <spacer/>
    **{length} mm**
  </row>
  <slider min={10} max={150} step={5} value={length} onChange={setLength}/>
  <row>
    <label>折角偏差</label>
    <spacer/>
    **{angle.toFixed(1)}°**
  </row>
  <slider min={0} max={35} step={0.1} value={angle} onChange={setAngle}/>
  <divider/>
  <caption>测量点相对目标位置的三维位移</caption>
  <title size="2xl" color={2*length*Math.sin(angle*Math.PI/360)>0.5?"warning":"success"} tabularNums={true}>{(2*length*Math.sin(angle*Math.PI/360)).toFixed(3)} mm</title>
  <caption>以刚性面板绕铰链旋转计算。0.5mm 仅作演示阈值，不是统一制造公差。</caption>
</card>

因此，L2 应当评价特征几何偏差，而不是仅评价角度是否与默认值一致。

### 4.4 修订后的 L2 定义

| 子门 | 验证内容 |
|---|---|
| L2-A | 折线语义、参考面和有向铰链一致 |
| L2-B | 目标终态几何及接缝成立 |
| L2-C | 指定折叠路径可达、无禁止干涉 |
| L2-D | 非法变异能够被指定门拒绝 |
| L2-E | 合法等价变换和参数变化能够通过 |

只有 A–E 在声明的适用参数域内均通过，才允许登记完整 L2。

当前 gable_top 建议登记为 `L2-KINEMATIC`，同时保留哪些子门已通过、哪些尚未测试。

不要为了提高 L2 数量而弱化定义。

---

## 5. R2-5：粘口宽度从 12mm 变成 2mm

**裁决：应增加制造特征约束门禁，不应完全留给人，也不能全局硬编码 12mm 为最小宽度。**

你发现的是一个很典型的问题：几何有效不等于制造有效。

<grid columns={2} gap={3}>
  <grid-item>
    <box border radius="md" padding={2} gap={1}>
      <svg viewBox="0 0 150 140" width="100%">
        <rect x="12" y="28" width="43" height="92" fill="#16a34a" fillOpacity=".22" stroke="#16a34a"/>
        <rect x="55" y="28" width="80" height="92" fill="#94a3b8" fillOpacity=".17" stroke="#64748b"/>
        <path d="M55 28V120" stroke="#2563eb" strokeDasharray="4 3"/>
        <path d="M12 17H55M12 13V21M55 13V21" stroke="currentColor" strokeWidth="1"/>
        <text x="33" y="10" textAnchor="middle" fontSize="10" fill="currentColor">12mm</text>
        <rect x="19" y="36" width="29" height="76" fill="#16a34a" fillOpacity=".18" stroke="#16a34a" strokeDasharray="3 2"/>
      </svg>
      **原设计粘口**
      <caption>存在较大的有效粘合区域</caption>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="md" padding={2} gap={1}>
      <svg viewBox="0 0 150 140" width="100%">
        <rect x="48" y="28" width="7" height="92" fill="#dc2626" fillOpacity=".3" stroke="#dc2626"/>
        <rect x="55" y="28" width="80" height="92" fill="#94a3b8" fillOpacity=".17" stroke="#64748b"/>
        <path d="M55 28V120" stroke="#2563eb" strokeDasharray="4 3"/>
        <path d="M48 17H55M48 13V21M55 13V21" stroke="currentColor"/>
        <text x="51.5" y="10" textAnchor="middle" fontSize="10" fill="currentColor">2mm</text>
      </svg>
      **变异设计粘口**
      <caption>几何仍可闭合，工艺能力存疑</caption>
    </box>
  </grid-item>
</grid>

### 5.1 应拆成三个验收层次

| 层次 | 检查内容 | 2mm 粘口如何处置 |
|---|---|---|
| 设计一致性 | 是否与冻结的 12mm 设计要求一致 | 如果没有授权变更，直接 FAIL |
| 参数合法性 | 是否属于模板声明的参数范围 | 超范围则 FAIL |
| 工艺可行性 | 有效粘合宽度、材料、胶型、设备与负载 | 有证据则裁决，无证据则 UNKNOWN |

这三个判断不能混为一谈。

特别是如果变异探针同时把 `spec.glue_w` 改成 2mm，并重新生成了全部几何，那么它可能不是几何破坏，而是一个新的、未经验证的设计。

如果没有明确的最小粘口宽度约束，验证器不能凭空判定它错误。

### 5.2 建议新增 Manufacturing Feature Constraints

不需要现在就实现复杂的纸板力学仿真，先建立特征级的可计算约束。

| 特征 | 可自动验证的约束 |
|---|---|
| 粘口 | 有效搭接宽度、面积、涂胶边距 |
| 插舌 | 宽度、长度及目标插槽匹配 |
| 插槽 | 开口宽度、材料厚度补偿 |
| 压线 | 最小间距、距裁切边距离 |
| 锁底 | 锁合重叠量与干涉 |
| 窄连接桥 | 最小剩余材料宽度 |
| 出血 | 指定印刷区域的覆盖范围 |

每条工艺约束必须具有来源、适用材料、模板范围、阈值、版本及验证状态。

这里必须引入 `NOT_ASSESSED` 或 `UNKNOWN` 状态。没有工艺规范时，不允许默认 PASS。

**2mm 粘口可以通过纯几何门，但不得因此自动升级为制造可行。**

---

## 6. R2-6：清单 V2 与下一步顺序

清单 V2 的总体方向批准。

但有两个顺序问题和一个重要遗漏需要纠正。

### 6.1 不要先全面整改 100 类折线，再做 B0

现在已经知道折线语义错误大范围存在。

此时全面投入模板整改，并不能帮助回答项目最根本的问题：**照片是否能够提供足够的信息来恢复目标制造参数？**

因此应当建立两个独立工作包。

<box border radius="lg" padding={3} gap={3}>
  <grid columns={2} gap={2}>
    <grid-item>
      <box gap={2}>
        **WP-G：制造几何可信性**

        <box border radius="md" padding={2} gap={1}>
          <caption>第一阶段</caption>
          A1–A4 剩余门禁收口
        </box>
        <box align="center"><icon name="arrow-down" color="secondary"/></box>
        <box border radius="md" padding={2} gap={1}>
          <caption>第二阶段</caption>
          M/V 语义模型与正向挑战集
        </box>
        <box align="center"><icon name="arrow-down" color="secondary"/></box>
        <box border radius="md" padding={2} gap={1}>
          <caption>第三阶段</caption>
          核心模板族制造验证
        </box>
      </box>
    </grid-item>
    <grid-item>
      <box gap={2}>
        **WP-V：视觉测量可行性**

        <box border radius="md" padding={2} gap={1}>
          <caption>第一阶段</caption>
          B0 合成解析几何
        </box>
        <box align="center"><icon name="arrow-down" color="secondary"/></box>
        <box border radius="md" padding={2} gap={1}>
          <caption>第二阶段</caption>
          噪声、退化与可辨识测试
        </box>
        <box align="center"><icon name="arrow-down" color="secondary"/></box>
        <box border radius="md" padding={2} gap={1}>
          <caption>第三阶段</caption>
          实物真值盲测
        </box>
      </box>
    </grid-item>
  </grid>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box border radius="md" padding={3} align="center">
    **真实照片 → 制造参数 → 刀版 → 实物**
    <caption>两条工作包均通过后进行端到端联合验收</caption>
  </box>
</box>

两个工作包并行推进，不必相互阻塞。

### 6.2 在拿到实物前，能不能用合成渲染先打通 B0？

**完全可以，而且是当前最高价值的技术研究工作。**

不过我反对一上来就使用 Blender 渲染图片。

应该进一步拆成四级，先剥离所有非必要变量。

<box border radius="lg" padding={3} gap={3}>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 90" width="95px">
      <g stroke="#64748b" fill="none" strokeWidth="1.5">
        <path d="M17 30L45 13L85 26L57 43L17 30V68L57 82L85 64V26M57 43V82M45 13V51L85 64M17 68L45 51" />
      </g>
      {#each [[17,30],[45,13],[85,26],[57,43],[17,68],[57,82],[85,64]] as p}
        <circle cx={p[0]} cy={p[1]} r="3" fill="#2563eb"/>
      {/each}
    </svg>
    <box flex={1} gap={1}>
      **B0-A｜精确投影坐标**

      手算独立三维几何，直接生成精确二维关键点。不使用渲染、不使用 CNN。

      <caption>验证求解器数学正确性。</caption>
    </box>
  </row>
  <divider/>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 90" width="95px">
      <path d="M17 30L45 13L85 26L57 43L17 30V68L57 82L85 64V26M57 43V82" stroke="#64748b" fill="none" strokeWidth="1.4"/>
      {#each [[17,30],[45,13],[85,26],[57,43],[17,68],[57,82],[85,64]] as p,i}
        <circle cx={p[0]} cy={p[1]} r="6" fill="#2563eb" fillOpacity=".12" stroke="#2563eb" strokeOpacity=".5"/>
        <circle cx={p[0]+(i%2?3:-2)} cy={p[1]+(i%3?2:-3)} r="2.5" fill="#dc2626"/>
      {/each}
    </svg>
    <box flex={1} gap={1}>
      **B0-B｜带噪声关键点**

      对二维观测注入 0.25–4px 噪声，测试相机姿态、尺寸及取景大小对误差的影响。

      <caption>建立测量精度上限和退化边界。</caption>
    </box>
  </row>
  <divider/>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 90" width="95px">
      <path d="M17 30L45 13L85 26L57 43Z" fill="#cbd5e1" stroke="#64748b"/>
      <path d="M17 30L57 43V82L17 68Z" fill="#e2e8f0" stroke="#64748b"/>
      <path d="M57 43L85 26V64L57 82Z" fill="#94a3b8" stroke="#64748b"/>
      {#each [[17,30],[45,13],[85,26],[57,43],[17,68],[57,82],[85,64]] as p}
        <circle cx={p[0]} cy={p[1]} r="2.7" fill="#2563eb"/>
      {/each}
    </svg>
    <box flex={1} gap={1}>
      **B0-C｜独立合成渲染**

      使用 Blender 独立相机链路生成白模图，人工标记可见关键点，核对投影坐标。

      <caption>发现坐标系、相机模型及渲染接口错误。</caption>
    </box>
  </row>
  <divider/>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 90" width="95px">
      <rect x="2" y="2" width="96" height="86" rx="4" fill="#94a3b8" fillOpacity=".12"/>
      <path d="M17 30L45 13L85 26L57 43Z" fill="#dbeafe" stroke="#64748b"/>
      <path d="M17 30L57 43V82L17 68Z" fill="#2563eb" fillOpacity=".6" stroke="#64748b"/>
      <path d="M57 43L85 26V64L57 82Z" fill="#1d4ed8" fillOpacity=".7" stroke="#64748b"/>
      <path d="M21 42L52 51M21 47L52 56M21 52L52 61" stroke="white" strokeOpacity=".9"/>
    </svg>
    <box flex={1} gap={1}>
      **B1｜自动视觉观测**

      自动提取关键点、轮廓和边线，再调用冻结的 B0 求解器。

      <caption>这一阶段才评价视觉识别能力。</caption>
    </box>
  </row>
</box>

OpenCV 已提供 `solvePnP`、`projectPoints` 及重投影优化相关工具，可以作为独立投影和位姿计算的基础，但标准 PnP 假定三维点已知；未知包装尺寸仍然需要你自己的参数化联合求解。<Cite refs={["turn639123search0","turn639123search3","turn639123search8"]}/>

### 6.3 B0 最容易踩的五个坑

| 风险 | 必须采取的控制 |
|---|---|
| 生成器和求解器共享同一投影错误 | 至少两套独立投影实现 |
| 把待测尺寸同时作为输入 | 明确区分尺度锚定参数和待估参数 |
| 低重投影误差但尺寸错误 | 同时评价物理尺寸误差 |
| 退化视角仍返回高置信结果 | 检查参数可辨识性及 Jacobian 条件 |
| 将不可见结构作为已恢复参数 | 输出 UNKNOWN 或请求补测 |

尤其是第三项：一个优化器可能找到错误的尺寸和相机位姿组合，同时获得非常小的重投影误差。

因此 B0 必须报告参数误差、重投影误差以及可辨识状态，而不能只报告优化收敛。

### 6.4 建议冻结 B0 实验矩阵

第一轮只需要长方体和 gable_top 两类，不需要全模板动物园。

| 实验维度 | 建议取值 |
|---|---|
| 结构族 | 长方体、gable_top |
| 几何参数组 | 每族 24 组独立参数 |
| 可见视角 | 正面、三分之四侧面、近退化侧面、俯视、低视角等 |
| 相机内参 | 已知、带扰动、部分未知 |
| 关键点噪声 | 0 / 0.25 / 0.5 / 1 / 2 / 4px |
| 尺度信息 | 无锚点、一个实测边长、两个实测边长 |
| 视角数量 | 1 / 3 / 6 |
| 初始化 | 真值附近、粗略估计、多初值 |

不必全因子穷举，第一轮按单变量实验开展，再增加针对性组合挑战。

建议验收目标如下：

| 指标 | B0-A 无噪声受控条件 |
|---|---|
| 可辨识的物理参数 | 最大绝对误差 ≤0.01mm |
| 重投影误差 | ≤0.001px |
| 尺度不可辨识场景 | 正确报告不可辨识 |
| 退化场景 | 不允许静默给出确定解 |
| 独立投影对账 | 通过 |
| 参数结果与初始化关系 | 记录失败率和多解情况 |

这些是**建议的合成数学求解器门槛**，不是实拍精度承诺。

如果 B0-A 尚未通过，不进入 B0-B；如果 B0-B 显示现实像素误差下无法达到毫米级要求，不急着开发自动关键点模型，而应该研究如何增加有效观测或主动补测。

---

## 7. 现在就能做的事情 Top 3

不需要实物，不需要等待仓库所有者，也不需要扩大 CNN 训练资源。

<box border radius="lg" padding={3} gap={3}>
  <row align="start">
    <title size="2xl" color="secondary">01</title>
    <box flex={1} gap={1}>
      **B0-A/B：独立解析几何求解器与可辨识性实验**

      建议投入：2–3 人日。

      先做长方体，再做 gable_top。建立精确投影、噪声响应、尺度歧义、退化视角测试。

      **交付物：** 冻结求解器、独立 oracle、误差曲线、失败样本库及路线裁决报告。

      <caption>最高研究信息增益：直接回答项目北极星是否具有数学与观测基础。</caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="2xl" color="secondary">02</title>
    <box flex={1} gap={1}>
      **门禁 V2：正负双向挑战集与折线语义迁移设计**

      建议投入：1–2 人日。

      完整回放 27 项探针，增加十类合法变化；补 A4 专项验证；建立参考面、折线和制造面映射。

      **交付物：** L2-A…E 验收定义、1066 条折线修订候选台账、正负挑战集。

      <caption>最高工程治理价值：防止从原来的门禁过松走向新的门禁过严。</caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="2xl" color="secondary">03</title>
    <box flex={1} gap={1}>
      **E4-B+：冻结 CNN 的反事实实验**

      建议投入：0.5–1 人日。

      不重新训练，仅改变几何和外观，观察响应斜率、单调性、外观敏感度及参数串扰。

      **交付物：** 反事实测试集、预测响应曲线、竞争假设更新台账。

      <caption>最低实验成本：判断已有 CNN 究竟有哪些能力值得继承。</caption>
    </box>
  </row>
</box>

在此期间，我明确不建议推进以下事项：全园 1066 条折线直接重标、逐一修复全部 100 类模板、训练几何扩大十倍、引入新的三维基础模型，以及在尚无材料工艺证据时声明可制造。

---

## 8. R2 最终裁决汇总

| 裁决编号 | 结论 |
|---|---|
| R2-1 整改签署 | 部分签署，A1–A3 有条件通过，A4 未通过 |
| R2-2 查表归因 | 排除简单离散查表，保留记忆＋插值假设 |
| R2-3 折线语义 | 内部观察面批准，自动候选批准，直接批量重标不批准 |
| R2-4 L2 灵敏度 | 必须增加合法变化挑战、可达性及容差测试 |
| R2-5 粘口 2mm | 几何门允许独立判断，制造特征约束必须新增 |
| R2-6 下一阶段 | V2 清单批准，B0 优先，与门禁完善并行 |

**一句总评：R1 是揭露虚假确定性，R2 已开始建立真实的验证能力；R3 最值得证明的，不是更多模板能够通过门禁，而是系统能够准确区分正确、错误、合法变化和不可辨识这四种本质不同的结果。**