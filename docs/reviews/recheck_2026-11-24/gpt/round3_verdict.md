# GPT 第 3 轮复审判决 (PD-RECHECK-R3)

- 来源: ChatGPT relay 会话 6b04e20e-6b54-83ea-9404-cce4e946424f ("PhotoDieline审计评审" 线程, 与 R1 同线程续评)
- 抓取: browser relay + backend-api/conversation (Bearer), 2026-11-24; 原文快照 /tmp/pd_recheck/gpt_r3_final.txt
- 提示词: round3_prompt.txt (B0 证据 + 门禁合同补漏 + R2 裁决落实状态)
- 本轮总判: B0-A 有条件通过, 准入 B0-B; 无锚点 gable 确定性尺寸交付不批准; 门禁补漏方向批准, 四态验收合同尚未完全成立

# PD-RECHECK-R3｜B0 求解器与门禁合同独立复审

**本轮裁决：B0-A 受控数学求解能力有条件通过，允许进入 B0-B；无锚点 gable 的确定性尺寸交付不批准；门禁补漏方向批准，但四态验收合同尚未完全成立。**

这一轮有三个真正值得肯定的研究进展：

- 无尺度锚点时，长方体能够取得近乎零重投影误差，同时产生平均 29% 的尺度偏差。这直接证明了重投影收敛不能替代物理尺寸正确性。
- 独立投影对账实际发现了坐标系、OBJ 导入方向和空渲染问题，证明独立 oracle 不是形式上的冗余设计。
- B0 在合成域内显示出明显的尺寸恢复潜力，足以支持继续投资参数化逆向拟合路线，而不必恢复 CNN 扩张计划。

但我要攻击一个比你列出的五个竞争解释更基础的问题：**当前系统还没有完全分离求解器的数学可辨识性、观测条件下的测量可靠性，以及制造模板的适用性。**

这三者必须分别裁决。

证据基线：`e15cae8`，本轮以你提交的实验数字和整改描述为依据，尚未独立复现源码及实验产物。以下签署均为设计层裁决，不是对该提交的工程验收签字。

---

## 1. B0-A 验收表逐项签署

| R2 冻结验收项 | R3 提交证据 | 裁决 |
|---|---|---|
| 可辨识参数误差 ≤0.01mm | gable 最大约 3×10⁻¹²mm；cuboid 约 6×10⁻⁹mm | 签署受控条件下的数值正确性 |
| 重投影误差 ≤0.001px | 两类均远低于阈值 | 签署求解残差，不代表实际成像精度 |
| 无尺度锚点正确拒绝 | cuboid 114/114 不可辨识 | 签署该受控案例 |
| 退化场景不静默给出确定解 | cuboid 无锚点；gable 由 G02 拒绝 | **不完全通过**：G02 不是观测退化检测器 |
| 独立投影对账 | 224 个点，最大差 0.004px | 有条件签署，roll 系统性残差待解释 |
| 初始化、失败率与多解记录 | 12 起点，无已发现多解及失败 | 有条件签署，初值覆盖仍偏理想 |
| 异常输入和空渲染 | 已发现并修正 | 有条件签署，需核查排除样本统计 |

### 1.1 三处需要特别修正的证据口径

**第一，G02 域外拒绝不能证明 B0 识别了观测退化。**

屋顶坡角低于 5°，是模板适用域问题；相机正对纸盒、部分边缘不可见、关键点共线，则是观测可辨识性问题。

一个完全合法的 30° 屋顶包，也可能因为拍摄角度不良而无法可靠恢复屋顶高度。

因此，B0-A 验收表中的「退化场景不静默给确定解」仍缺独立证据。

**第二，12 个起点稳定，不等于没有多解。**

目前 `d0 = truth × U(0.8,1.25)` 实际借用了真值附近的信息。这适合验证局部数值求解能力，但不适合宣称全局优化鲁棒性。

建议把当前结论限定为：

> 在受控几何、已知对应关系及真值附近初始化条件下，12 个起点未发现不同的可行参数解。

后续需要加入无真值辅助的初始化、镜像候选、错误位姿初值和远离真值的起点。

**第三，114 个有效长方体帧的分母需要交代。**

如果原计划为 120 帧，则有六帧未进入有效样本。

必须将这六帧分别登记为生成失败、不可见、数据无效、求解失败或其他原因。不能从系统级成功率的分母中静默删除。

这是一个必须补齐的小证据缺口，因为真实业务系统不会只收到成功生成且关键点齐全的照片。

### 1.2 B0 与 CNN 的对比：认可优势，但收窄结论

<card gap={3}>
  <title size="md">Gable · 比例 MAE 与关键点噪声的关系</title>
  <Chart content={{"chartType":"line","xKey":"noise","xAxisLabel":"关键点噪声 σ（px）","series":[{"dataKey":"one","label":"B0 一条实测边"},{"dataKey":"two","label":"B0 两条实测边"},{"dataKey":"cnn","label":"CNN 对照"}],"data":[{"noise":"0.25","one":0.0011,"two":0.0008,"cnn":0.0314},{"noise":"0.5","one":0.0023,"two":0.0015,"cnn":0.0314},{"noise":"1","one":0.0046,"two":0.0034,"cnn":0.0314},{"noise":"2","one":0.0084,"two":0.0061,"cnn":0.0314},{"noise":"4","one":0.0201,"two":0.0135,"cnn":0.0314}]}}/>
  <grid columns={2}>
    <grid-item>
      <caption>σ=1px 时相对 CNN</caption>
      <title size="2xl" color="success">−85.4%</title>
      <caption>一条实测边</caption>
    </grid-item>
    <grid-item>
      <caption>σ=4px 时相对 CNN</caption>
      <title size="2xl" color="success">−36.0%</title>
      <caption>一条实测边</caption>
    </grid-item>
  </grid>
  <caption>CNN 水平线为固定对照值，并非 CNN 在各噪声档下的独立实验结果。</caption>
</card>

<card gap={2}>
  <title size="md">Cuboid · 增加第二条实测边的价值</title>
  <Chart content={{"chartType":"line","xKey":"noise","xAxisLabel":"关键点噪声 σ（px）","series":[{"dataKey":"one","label":"一条实测边"},{"dataKey":"two","label":"两条实测边"}],"data":[{"noise":"0.25","one":0.0013,"two":0.0005},{"noise":"0.5","one":0.0029,"two":0.0008},{"noise":"1","one":0.0057,"two":0.002},{"noise":"2","one":0.0132,"two":0.0037},{"noise":"4","one":0.0241,"two":0.007}]}}/>
  <caption>第二条实测边在较高噪声条件下仍然提供明显约束价值。</caption>
</card>

我发现当前 CNN 对照还有两个混杂变量，你没有明确指出。

| 混杂变量 | 对比较结果的影响 |
|---|---|
| B0 使用已知语义对应的关键点 | CNN 必须从 RGB 自行提取有效观测 |
| B0 使用一条或两条实测边 | CNN 是否获得相同的额外测量信息尚不明确 |

因此，当前实验不是两种完整视觉测量系统的公平竞赛，而是：

**在额外几何观测和尺度约束可用的条件下，数学求解器的能力上限，明显优于现有 CNN 直接回归的实测表现。**

这个结论已经足够支持路线决策，但不足以发表「解析几何比 CNN 精确七倍」的普遍性声明。

另外，两条实测边模式必须同时报告：

- 全部参数 MAE。
- 仅未提供给求解器的参数 MAE。
- 实测边自身存在测量误差时的结果。

如果把直接输入的真值参数计入平均误差，第二条实测边的收益可能被部分放大。

### 1.3 关于 0.004px 投影偏差

我不要求因为 0.004px 而阻断 B0-B。

但也不同意直接认定它没有实际影响。

普通条件下，它远小于你测试的最小 0.25px 噪声；然而在弱可辨识条件下，微小投影偏差可能沿尺度歧义方向被显著放大。

建议补一个成本很低的 roll 扫描：

| 变量 | 取值 |
|---|---|
| Roll | 0°、±15°、±45°、±90° |
| 其余相机参数 | 全部固定 |
| 比较对象 | 投影坐标、相机外参矩阵、相机基向量 |
| 输出 | 有符号的二维残差，而非仅最大绝对值 |

如果残差来源于 Blender 内部浮点精度，可以记录为已解释的数值误差；如果呈稳定的方向相关模式，则修正坐标变换。

**B0-A 最终裁决：CONDITIONAL PASS，批准进入 B0-B，不批准声明全局求解及观测退化验证已完成。**

---

## 2. 无锚点 gable：交付误差棒，还是拒绝？

**裁决：拒绝作为制造尺寸交付；允许作为带有明确先验来源和不确定性的研究估计输出。**

### 2.1 你所谓的无锚点，其实不是无尺度约束

`fin_gap = 3mm` 本身就是一个绝对长度。

因此，gable 实验与 cuboid 实验存在重要区别。

<box border radius="lg" padding={3} gap={3}>
  <grid columns={2} gap={3}>
    <grid-item>
      <box gap={1}>
        <svg viewBox="0 0 150 145" width="100%">
          <path d="M33 38L94 38L122 21L61 21Z M94 38L122 21V111L94 128Z M33 38H94V128H33Z" fill="#94a3b8" fillOpacity=".17" stroke="#64748b"/>
          <path d="M22 38V128M17 38H27M17 128H27" stroke="currentColor"/>
          <text x="13" y="86" fontSize="13" textAnchor="middle" fill="currentColor">?</text>
          <text x="75" y="141" textAnchor="middle" fill="currentColor" fontSize="10">整体尺度可任意变化</text>
        </svg>
        **Cuboid：真正无尺度锚点**
        <caption>绝对尺寸结构性不可辨识</caption>
      </box>
    </grid-item>
    <grid-item>
      <box gap={1}>
        <svg viewBox="0 0 150 145" width="100%">
          <path d="M30 57L63 29L94 57V130H30Z M63 29L91 13L122 41L94 57Z M94 57L122 41V114L94 130Z" fill="#94a3b8" fillOpacity=".18" stroke="#64748b"/>
          <path d="M63 29V14L91 -2V13" fill="#2563eb" fillOpacity=".2" stroke="#2563eb"/>
          <circle cx="65" cy="20" r="13" fill="none" stroke="#dc2626" strokeWidth="2"/>
          <path d="M78 20L111 9" stroke="#dc2626"/>
          <text x="117" y="10" fontSize="10" fill="#dc2626">3mm</text>
        </svg>
        **Gable：模板隐含尺度**
        <caption>依赖固定 fin_gap 先验恢复尺度</caption>
      </box>
    </grid-item>
  </grid>
</box>

建议实验枚举改为：

| 尺度模式 | 含义 |
|---|---|
| `NO_METRIC_ANCHOR` | 不含任何绝对长度信息 |
| `TEMPLATE_PRIOR_ANCHOR` | 仅含模板默认长度 |
| `MEASURED_ANCHOR_1` | 一条真实测量边 |
| `MEASURED_ANCHOR_2` | 两条真实测量边 |

这不是名称上的细节，而是尺寸证据来源的根本区别。

### 2.2 必须补一个 fin_gap 先验敏感性实验

如果真实 fin_gap 为 3mm，但求解器错误地假定它为 2.5mm，那么在纯尺度等价条件下，全部恢复尺寸可能产生约 16.7% 的系统性偏差。

{@body const [gapValue,setGapValue]=DIL.useState(3)}
<card gap={3}>
  <title size="md">隐含尺度先验的误差传播</title>
  <caption>理想尺度等价模型：真实 fin_gap=3mm，真实盒宽=60mm</caption>
  <row>
    <label>求解器假定的 fin_gap</label>
    <spacer/>
    **{gapValue.toFixed(1)} mm**
  </row>
  <slider min={1} max={5} step={0.1} value={gapValue} onChange={setGapValue} marks={[{"value":1,"label":"1"},{"value":3,"label":"3"},{"value":5,"label":"5"}]}/>
  <svg viewBox="0 0 320 125" width="100%">
    <rect x="22" y="14" width="276" height="97" rx="4" fill="none" stroke="currentColor" strokeOpacity=".1"/>
    <rect x="30" y="25" width="150" height="27" fill="#64748b" fillOpacity=".65" rx="2"/>
    <text x="37" y="42" fontSize="11" fill="white">真实宽度 60mm</text>
    <rect x="30" y="69" width={150*gapValue/3} height="27" fill={Math.abs(gapValue-3)<0.01?"#16a34a":"#d97706"} fillOpacity=".8" rx="2"/>
    <text x="37" y="86" fontSize="11" fill="white">{(60*gapValue/3).toFixed(0)}mm</text>
  </svg>
  <grid columns={2}>
    <grid-item>
      <caption>估计盒宽</caption>
      <title size="2xl">{(60*gapValue/3).toFixed(1)} mm</title>
    </grid-item>
    <grid-item>
      <caption>尺度偏差</caption>
      <title size="2xl" color={Math.abs(gapValue-3)<0.01?"success":"warning"}>{((gapValue/3-1)*100).toFixed(1)}%</title>
    </grid-item>
  </grid>
  <caption>理论示例，非 R3 实测结果。实际传播取决于其他约束、几何模型与观测条件。</caption>
</card>

我要求实验加入三个条件：

- 真实 fin_gap 与模板先验完全一致。
- 真实 fin_gap 随机变化，但求解器仍固定为 3mm。
- fin_gap 不再固定，作为自由参数参与求解。

第三组应该重新暴露绝对尺度自由度。若没有暴露，则需要怀疑还有其他隐藏的尺寸先验。

### 2.3 条件数阈值应该设为 10⁴ 还是 10⁶？

**两个都不应直接作为最终交付门槛。**

条件数依赖参数单位、参数化方式和所计算的矩阵。

例如，同一个参数从 mm 改为 m，如果没有无量纲归一化，条件数可能显著变化，但包装本身没有任何变化。

如果你计算的是 Schur 补后的信息矩阵，其条件数通常还相当于对应有效 Jacobian 条件数的平方，而不能直接拿两者的阈值比较。

Ceres Solver 的协方差文档也明确区分了尺度自由度、结构性秩亏和数值秩亏问题。<Cite refs={["turn970879search0","turn970879search1"]}/>

我建议采用三级判定。

| 层次 | 判据 | 不通过时 |
|---|---|---|
| I：结构可辨识 | 消除位姿干扰后，目标参数方向是否存在零空间 | `UNIDENTIFIABLE` |
| II：数值稳定性 | 无量纲化、白化后的有效 Jacobian 奇异值谱 | `ILL_CONDITIONED` |
| III：任务精度 | 参数置信区间是否满足特征容差 | `INSUFFICIENT_PRECISION` |

临时研究阈值可以这样制定，前提是使用无量纲有效 Jacobian 对应的信息矩阵：

| 信息矩阵条件数 | 建议处置 |
|---|---|
| ≤10⁴ | 进入精度验收，不自动通过 |
| 10⁴–10⁶ | 标记弱可辨识，追加非线性区间及扰动测试 |
| ≥10⁶ | 暂停自动尺寸交付 |
| 秩亏 | 直接拒绝对应不可辨识参数 |

这只是**建议的数值诊断策略，不是有外部标准背书的测量精度分界**。

最终应由参数级不确定性控制是否可以交付。

### 2.4 误差棒怎么计算？

定义物理参数为 \(\theta\)，位姿等干扰参数为 \(\eta\)，观测协方差为 \(\Sigma\)。

消去干扰参数后的局部信息矩阵：

\[
S=H_{\theta\theta}-
H_{\theta\eta}H_{\eta\eta}^{+}H_{\eta\theta}
\]

其中：

\[
H=J^\top\Sigma^{-1}J
\]

在局部满秩且线性近似有效时，参数协方差可以近似为：

\[
C_\theta \approx S^{-1}
\]

但对 gable 当前这样的弱可辨识场景，仅凭局部协方差可能产生不可靠区间。

建议额外使用 Monte Carlo 与 Profile Likelihood。后者能够通过固定某个参数、重新优化其他参数来观察是否存在宽广的等价解区域。Raue 等人的研究提供了结构可辨识性与实际可辨识性分离的成熟方法。<Cite refs={["turn970879search3","turn970879search8"]}/>

还有一个必须防范的问题：**秩亏方向使用伪逆后，不能把被截断的零特征值误解释为零方差。** 对这些方向应该显式报告不可辨识，而不是输出虚假的高精度误差棒。

对当前 88/120 帧 accepted、2px 噪声下误差达到约 11mm 的结果，我的处置很明确：

- 不作为已恢复的制造尺寸。
- 保留为 `PRIOR_DEPENDENT_ESTIMATE`。
- 请求额外实测边或其他能够提供独立尺度的信息。

---

## 3. B0-B 最小充分实验集

你的原始矩阵包含多个维度，但如果全部展开，实验成本会迅速失控。

我建议采用 **五个主实验＋一个组合压力测试**，不做全因子穷举。

### 3.1 冻结实验方案

| 编号 | 实验变量 | 最小取值 | 验证问题 |
|---|---|---|---|
| B01 | 尺度先验 | 无锚点、模板先验、实测一边 | 真正的尺度可辨识性 |
| B02 | 观测退化 | 正面、近正面、三分之四视角 | 参数恢复是否依赖视角 |
| B03 | 噪声结构 | 独立高斯、系统偏差、相关误差 | 理想点噪声是否高估性能 |
| B04 | 相机内参 | 真值、焦距±2%/±5%、部分未知 | 内参与几何是否发生混淆 |
| B05 | 视角数量 | 1、3；另设三张近重复视角 | 额外观测是否真正增加信息 |
| B06 | 组合压力测试 | 相关噪声＋内参误差＋不利视角 | 是否出现高置信错误 |

六视角模式可以延后。先证明三视角比单视角有效，再研究三到六的边际收益。

建议从当前已冻结的长方体和 gable 参数组中，选择覆盖常规尺寸与极端比例的代表性子集。每一组都使用配对观测和固定随机种子，避免不同实验条件的样本难度不同。

### 3.2 最高优先级不是增加视角，而是改变噪声模型

你对 i.i.d. 高斯噪声的自我质疑完全正确。

<box border radius="lg" padding={3} gap={3}>
  <grid columns={3} gap={2}>
    {#each ["independent","inward","correlated"] as mode}
      <grid-item>
        <box gap={1}>
          <svg viewBox="0 0 108 110" width="100%">
            <path d="M17 29L42 13L91 28L65 44Z M17 29V80L65 96V44M65 96L91 80V28" stroke="#64748b" fill="#94a3b8" fillOpacity=".09"/>
            {#each [[17,29],[42,13],[91,28],[65,44],[17,80],[65,96],[91,80]] as p,i}
              <circle cx={p[0]} cy={p[1]} r="2.7" fill="#2563eb"/>
              <path d={`M${p[0]} ${p[1]}L${p[0]+(mode==="independent"?[4,-3,3,-4,2,3,-3][i]:mode==="inward"?(54-p[0])*.13:4)} ${p[1]+(mode==="independent"?[-3,3,-4,1,4,-2,3][i]:mode==="inward"?(55-p[1])*.13:-3)}`} stroke="#dc2626" strokeWidth="1.5"/>
              <circle cx={p[0]+(mode==="independent"?[4,-3,3,-4,2,3,-3][i]:mode==="inward"?(54-p[0])*.13:4)} cy={p[1]+(mode==="independent"?[-3,3,-4,1,4,-2,3][i]:mode==="inward"?(55-p[1])*.13:-3)} r="2.5" fill="#dc2626"/>
            {/each}
          </svg>
          **{mode==="independent"?"独立噪声":mode==="inward"?"内缩偏差":"相关偏移"}**
          <caption>{mode==="independent"?"当前实验":mode==="inward"?"轮廓点系统偏差":"同面或同边误差"}</caption>
        </box>
      </grid-item>
    {/each}
  </grid>
  <row align="center" justify="center" gap={3}>
    <row gap={1} align="center"><box size="9px" radius="full" background="#2563eb"/><caption>真实点</caption></row>
    <row gap={1} align="center"><box size="9px" radius="full" background="#dc2626"/><caption>观测点</caption></row>
  </row>
</box>

独立噪声可能通过多个点相互抵消，而一致的系统性偏移不一定会。

最值得补的四类扰动是：

| 扰动 | 建议第一轮设置 |
|---|---|
| 角点向面内偏移 | 0.5 / 1 / 2px |
| 同一边或同一面的相关误差 | 共享扰动＋少量独立噪声 |
| 语义对应错误 | 交换一个相邻角点 |
| 关键点缺失 | 移除一个屋脊点或一组侧面点 |

对于语义对应错误，不要求求解器永远恢复正确值，但必须能评估残差、拒识或多候选解释。

### 3.3 多视角不等于多信息

这是 B05 必须包含三张近重复视角的原因。

<grid columns={2} gap={3}>
  <grid-item>
    <box gap={1}>
      <svg viewBox="0 0 150 145" width="100%">
        <rect x="58" y="54" width="35" height="37" fill="#94a3b8" fillOpacity=".2" stroke="#64748b"/>
        <path d="M75 72L26 117M75 72L37 126M75 72L49 132" stroke="#d97706" strokeDasharray="4 3"/>
        {#each [[26,117],[37,126],[49,132]] as p}
          <rect x={p[0]-5} y={p[1]-4} width="10" height="8" rx="1" fill="#d97706"/>
        {/each}
      </svg>
      **三张近重复照片**
      <caption>观测数量增加，参数耦合未必解除。</caption>
    </box>
  </grid-item>
  <grid-item>
    <box gap={1}>
      <svg viewBox="0 0 150 145" width="100%">
        <rect x="58" y="54" width="35" height="37" fill="#94a3b8" fillOpacity=".2" stroke="#64748b"/>
        <path d="M75 72L20 112M75 72L125 105M75 72L93 12" stroke="#16a34a" strokeDasharray="4 3"/>
        {#each [[20,112],[125,105],[93,12]] as p}
          <rect x={p[0]-5} y={p[1]-4} width="10" height="8" rx="1" fill="#16a34a"/>
        {/each}
      </svg>
      **三个互补观测方向**
      <caption>有机会解除不同参数之间的耦合。</caption>
    </box>
  </grid-item>
</grid>

另外，即使使用多个互补视角，只要相机平移尺度未知且不存在真实长度锚点，绝对尺度歧义仍然可能存在。

所以必须分别验证：

- 多视角对比例估计的收益。
- 多视角对带尺度约束的物理参数估计的收益。
- 多视角能否正确保留无绝对尺度场景的不可辨识状态。

### 3.4 B0-B 验收不应再只看 MAE

| 指标 | 目的 |
|---|---|
| MAE / P95 / 最大尺寸误差 | 评价典型及尾部风险 |
| 未输入尺寸的独立误差 | 防止真值输入污染评估 |
| 自动接受覆盖率 | 系统愿意交付多少结果 |
| 接受样本中的超容差比例 | 系统交付错误尺寸的风险 |
| 95% 区间经验覆盖率 | 验证误差棒是否可信 |
| 不可辨识召回率 | 退化问题是否被发现 |
| 合法可辨识场景的误拒率 | 防止通过拒绝一切获得零风险 |

这一轮不需要追求全部场景达到 0.5mm。

更重要的是建立一条可信的**风险—覆盖率曲线**：在指定尺寸精度下，系统可以自动接受多少照片；剩下的是否能够通过补测恢复。

---

## 4. 门禁 V2：两个漏洞与四分法复审

### 4.1 铰链正交性门禁

**有条件签署。**

如果 `target_dir_3d` 的定义确实是与铰链垂直的单位面内方向，那么要求：

\[
\|d\|=1,\qquad a^\top d=0
\]

是数学不变量，不需要包装行业标准来背书。

但 `1e-3` 是数值容差，不是制造容差。

对于单位向量，它对应的正交角偏差约为 0.057°。如果该误差实际传递到 500mm 长的几何特征，偏差量级可达约 0.5mm。

因此应区分：

| 容差类型 | 用途 |
|---|---|
| 浮点数值容差 | 判断解析构造是否正确 |
| 输入数据容差 | 处理外部序列化和测量误差 |
| 特征几何容差 | 判断最终制造尺寸是否满足要求 |

如果所有向量都由程序精确构造，我建议先实测正常样本的浮点残差分布，再决定是否需要如此宽松的 `1e-3`。

还应补充零向量、NaN、Inf、非单位长度及反向但正交的向量测试。

最后一类尤其重要：正交性成立，不代表折向正确。

### 4.2 屋脊坡角 ≥5°

**批准作为当前模板的暂定适用域，不批准作为通用制造或可辨识性标准。**

你现在的 G02 可以合法地表达：

> 本版本 gable_top 模板不支持低于 5° 的屋脊坡角。

但不能表达：

> 低于 5° 的屋顶包装一定错误、不可制造或无法被视觉识别。

这三种声明的证据要求完全不同。

建议将 5° 登记为：

| 属性 | 建议值 |
|---|---|
| 类型 | `MODEL_DOMAIN_LIMIT` |
| 来源 | 当前实现与研究假设 |
| 外部标准支持 | 未验证 |
| 制造含义 | 不作声明 |
| 视觉可辨识含义 | 不作声明 |
| 超界结果 | `OUT_OF_MODEL_DOMAIN` |

补测 4.99°、5.00°、5.01° 等边界场景，并单独验证不同分辨率和视角下屋脊高度的恢复能力。

**无需为每一个建模阈值寻找外部论文，但必须说明该阈值究竟限制了什么。**

### 4.3 四分法是否已经落实？

尚未完全落实。我认为 R2 的四分法本身也需要进一步精化。

正确、错误、合法变化和不可辨识并不是四个完全互斥的全局状态。

例如，一个包装可以同时是合法设计、数值折叠正确，但仅凭当前照片无法恢复其尺寸。

所以建议不要设计一个四值总枚举，而采用正交状态。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">建议的多维验证合同</title>
  <table>
    <table-row>
      <table-cell width="37%">
        <caption>验证维度</caption>
      </table-cell>
      <table-cell>
        <caption>独立状态</caption>
      </table-cell>
    </table-row>
    {#each [
      ["输入完整性","VALID / INVALID / MISSING"],
      ["模型适用域","IN_DOMAIN / OUT_OF_DOMAIN"],
      ["参数可辨识性","IDENTIFIABLE / UNIDENTIFIABLE"],
      ["测量可靠性","SUFFICIENT / INSUFFICIENT / NOT_ASSESSED"],
      ["展开几何","PASS / FAIL / NOT_TESTED"],
      ["折叠终态","PASS / FAIL / NOT_TESTED"],
      ["折叠路径","PASS / FAIL / NOT_TESTED"],
      ["制造工艺","PASS / FAIL / NOT_ASSESSED"]
    ] as r}
      <table-row>
        <table-cell>**{r[0]}**</table-cell>
        <table-cell><text size="sm">{r[1]}</text></table-cell>
      </table-row>
    {/each}
  </table>
  <divider/>
  <caption>交付等级由各维度证据共同决定，任一关键维度 UNKNOWN 都不得被全局 VALIDATED 掩盖。</caption>
</box>

R3 四分法实际证据如下：

| 类别 | 当前证据 | 裁决 |
|---|---|---|
| 正确 | baseline VALIDATED | 受控金标通过 |
| 错误 | 26 DRAFT | 基本通过，待核对逐项拒绝原因 |
| 合法变化 | 四种等价变换通过 | 部分通过 |
| 不可辨识 | B0 尺度自由度检测 | 部分通过 |
| 模型域外 | G02 拒绝 | 独立成立，不应混入不可辨识 |

合法变化还缺少最有价值的一项：**改变合法 W/D/H 后重新生成几何，仍能通过全部对应门禁。**

现有四种主要是表示层等价变换，没有充分证明验证器能够容许真正的几何设计变化。

### 4.4 最终变异矩阵有一处账目问题

你给出的数字为：

| 结果 | 数量 |
|---|---:|
| DRAFT | 26 |
| BUILD-EXC | 3 |
| ARError | 1 |
| 合计 | 30 |
| baseline VALIDATED | 另计 |

但你称之为 27 项探针完整回放。

可能是新增了三个挑战，或者统计层级不同，但本轮材料没有说明。

我暂不签署「27 项探针全部完成」这条结论，要求补齐 case ID 对账。

同时必须分辨：

- `BUILD-EXC` 是预期的非法输入拒绝，还是意外程序崩溃？
- `ARError` 是探针自身异常，还是被测系统明确拒绝？
- 拒绝是否来自预期门禁，而不是不相关异常？
- 变异是否真正改变了目标几何或语义？

异常退出不能无条件计为门禁成功。这一点已经被此前两个 no-op 探针证明非常重要。

---

## 5. R2 剩余整改项复审

| 项目 | R3 裁决 | 剩余问题 |
|---|---|---|
| 照片使用情况显式记录 | 签署 | 正确避免虚假视觉测量声明 |
| CLI `--photo` 可选 | 签署设计 | 区分参数化生成与视觉测量入口 |
| A4 实测覆盖与约束传播 | 尚不签署 | 未看到冲突实测、派生尺寸重算、非 gable 分发的专项结果 |
| L2_KINEMATIC 降级 | 签署 | 已正确限定终态运动学证明范围 |
| 制造约束 NOT_ASSESSED | 签署设计 | 修正枚举拼写，防止旧值被读取器误识别 |
| 1066 条折线暂不重标 | 签署 | 避免未经独立结构证据的批量同步错误 |
| 局部尺度扰动探针 | 未完成 | 尚缺容差边界测试 |
| 折叠路径可达性 | 未完成 | 不得恢复完整 L2 声明 |
| 独立 PDF 实际渲染 | 本轮未补证 | A2 仍保持有条件通过 |

特别注意：你在报告里写的是 `NOT_ASSESED`，少了一个 S。若仓内确实如此，请统一修订为 `NOT_ASSESSED`，同时验证 Schema、报告生成器和读取器不会因为未知枚举值而静默默认通过。

---

## 6. 距离下一轮签署还差什么？

我建议 R4 不再增加大量功能，只完成以下三个工作包。

<box border radius="lg" padding={3} gap={3}>
  <row align="start" gap={2}>
    <box background="#dc2626" radius="sm" width="5px" height="64px"/>
    <box flex={1} gap={1}>
      **WP1 · 可辨识性与尺度来源合同**

      <caption>P0 · 最高优先级</caption>
      消除隐含尺度歧义，建立参数级精度与拒绝机制。
    </box>
  </row>
  <divider/>
  <row align="start" gap={2}>
    <box background="#dc2626" radius="sm" width="5px" height="64px"/>
    <box flex={1} gap={1}>
      **WP2 · B0-B 最小压力实验**

      <caption>P0 · 最高研究信息增益</caption>
      证明非理想观测下求解器能够识别高风险结果，而不仅是在理想情况下获得高精度。
    </box>
  </row>
  <divider/>
  <row align="start" gap={2}>
    <box background="#d97706" radius="sm" width="5px" height="64px"/>
    <box flex={1} gap={1}>
      **WP3 · 门禁合同证据收口**

      <caption>P0 · 最高工程治理价值</caption>
      完整对账探针、验证合法参数变化、补齐 A4 与独立导出证据。
    </box>
  </row>
</box>

### R4 正式验收清单

{@body const tasks=[
["WP1","真正无尺度锚点的 gable 实验"],
["WP1","fin_gap 先验误差传播与自由参数消融"],
["WP1","无量纲可辨识性计算及参数级区间"],
["WP1","不可辨识或精度不足的结果禁止升级交付"],
["WP2","合法模板的退化视角测试"],
["WP2","系统性与相关像素噪声测试"],
["WP2","相机内参扰动及部分未知实验"],
["WP2","单视角、互补三视角、重复三视角对照"],
["WP2","无真值辅助初始化、roll 残差和六帧排除说明"],
["WP3","27/30 项变异矩阵逐 ID 对账"],
["WP3","合法 W/D/H 参数变化与局部容差挑战"],
["WP3","A4 实测约束传播及 CLI 分发专项测试"],
["WP3","PDF 独立渲染及图层语义证据"]
]}
{@body const [completed,setCompleted]=DIL.useState(tasks.map(()=>false))}
<card gap={3}>
  <row align="center">
    <title size="md">R4 验收跟踪</title>
    <spacer/>
    <caption>{completed.filter(Boolean).length}/{tasks.length}</caption>
  </row>
  <box height={7} background="surface-tertiary" radius="full">
    <box height="100%" background="#16a34a" radius="full" width={`${completed.filter(Boolean).length/tasks.length*100}%`}/>
  </box>
  {#each ["WP1","WP2","WP3"] as group}
    **{group}**
    {#each tasks as task,i}
      {#if task[0]===group}
        <checkbox key={i} checked={completed[i]} onChange={v=>setCompleted(old=>old.map((c,j)=>j===i?v:c))}>{task[1]}</checkbox>
      {/if}
    {/each}
  {/each}
  <button variant="outline" block onClick={()=>GenUI.copy(tasks.map((t,i)=>(completed[i]?"[x] ":"[ ] ")+t[0]+" "+t[1]).join("\n"))}><icon name="copy" size="sm"/> 复制执行清单</button>
</card>

不需要等待真实实物即可完成以上工作。

但是 B0-B 通过以后，应冻结求解器基线，等待真实包装数据，而不是无限增加合成实验。实拍验证、真实刀版复原、物理试制仍然是独立的后续验收阶段。

---

## 7. R3 最终签署表

| 裁决项 | 结果 |
|---|---|
| B0-A 理想条件数学正确性 | PASS |
| B0-A 整体验收 | CONDITIONAL PASS |
| 进入 B0-B | APPROVED |
| 参数化逆向拟合作为主路线 | APPROVED |
| CNN 扩大训练 | 继续暂停 |
| B0 比 CNN 精确七倍的普遍性声明 | NOT APPROVED |
| 无锚点 gable 制造尺寸交付 | REJECTED |
| 带先验的不确定性研究估计 | APPROVED |
| G04 铰链正交性 | CONDITIONAL PASS |
| G02 5° 模型适用域 | APPROVED |
| 5° 作为制造或视觉标准 | NOT APPROVED |
| 四分法完整验收 | PARTIAL PASS |
| gable_top 终态运动学等级 | 保留 L2_KINEMATIC |
| 完整 L2 / L3 / L4 | 未验收 |
| 全园折线批量重标 | 不批准 |

## 8. 一句总评

**R3 已经证明参数化逆向几何值得成为 PhotoDieline 的研究主干；R4 要证明的则是，当数学上能够求出一个答案、但观测证据不足以保证这个答案正确时，系统有能力拒绝交付它。**
