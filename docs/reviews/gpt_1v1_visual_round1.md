# Pack10K × NVIDIA USDCraft-10K 视觉质量对抗性评审

## 一、总体裁决

**Pack10K 目前是合格的参数化几何白模，但还不是合格的高质量数字商品资产。** 与 NVIDIA 的差距不仅在 Cycles 渲染，更在资产表达层的完整性。

八组对比中，NVIDIA 在视觉质量上全部获胜。我们的问题不是单纯的灯光不好，而是几何细节、材质物理属性、摄影布光、构图呈现四个层级同时存在差距。

尤其需要警惕页面顶部的 **100% vs 25.6%**：这组数字反映的是既定工程门禁的通过率，不能代表视觉质量、商品真实性或资产完整性。甚至可能给观看者造成反效果——数字显示我们遥遥领先，图片却显示我们明显落后。

本次评分不考虑工程门禁、三角面数量、参数化能力和生成效率，只考虑图片所表达的商品资产质量。评分以 10 分为专业商业级 3D 商品资产渲染，而不是以 NVIDIA 为满分基准。

## 二、八组逐一评分

<box gap={3}>
  <row align=start>
    <box flex={1} gap=1>
      **01 · R422 瓦楞包裹箱**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">4.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.8</title>
      </row>
    </box>
    <box flex={3}>
      左侧像一个无厚度的纸质容器，没有箱盖、折痕、瓦楞截面及纸板接缝。光照过于平淡，右侧有明确的封箱结构、胶带和接触阴影。这是八组中相对容易追赶的一组，但必须先统一开箱与封箱状态。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **02 · R043 拉环饮料罐**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">2.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.5</title>
      </row>
    </box>
    <box flex={3}>
      左侧多边形轮廓极其明显，看起来是一次性纸杯，而不是饮料罐。缺少罐肩、卷边、罐底、拉环和金属材质。右侧也存在白色区域层次不足的问题，但至少能直接识别商品类别。单靠渲染无法追平。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **03 · R091 酒瓶**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">1.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.3</title>
      </row>
    </box>
    <box flex={3}>
      左侧是多边形纸筒，完全没有瓶肩、瓶颈、瓶塞及玻璃光学特征。右侧具有透明玻璃、曲面反射和底部厚度感。这不是同一种商品的不同渲染，而是两种不同资产。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **04 · R040 梅森罐**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">2.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.0</title>
      </row>
    </box>
    <box flex={3}>
      左侧呈现明显的折面，罐口没有任何厚度表达，底部灰色区域疑似开口或背景透出，需要检查几何。右侧具有旋盖、瓶肩、玻璃壁和底部结构。左右的材质与形态均不等价。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **05 · R415 敞口周转箱**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.5</title>
      </row>
    </box>
    <box flex={3}>
      左侧白色区域几乎融为一体，内壁、底面和外壁缺乏明暗分离，部分边缘贴近或超出画框。右侧的蓝色塑料、圆角、翻边、提手孔和柔和反射使其具有明确工业产品特征。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **06 · R037 铰盖保鲜盒**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.2</title>
      </row>
    </box>
    <box flex={3}>
      左侧没有展示可识别的铰链、盒盖或锁扣，而且纵横比例与右侧差异很大。暖黄色光照无法代替真实材质。右侧半透明塑料、盖体分离和卡扣结构明显提升了可信度。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **07 · R423 分体盖容器**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.8</title>
      </row>
    </box>
    <box flex={3}>
      左侧采用分体展示，理论上有利于结构研究，但两部分看起来像两个普通纸箱，无法直观判断盖与底座的配合关系。前方组件底部疑似镂空。右侧具备加强筋、把手、盖沿等功能性细节。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **08 · R026 面包箱**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.5</title>
      </row>
    </box>
    <box flex={3}>
      左侧依旧是一个敞口矩形纸盒，没有展示插盖结构。右侧具有盖板、前部活动面板、旋钮和接缝。右侧也存在曝光偏高的问题，但功能结构完整度远高于左侧。
    </box>
  </row>
</box>

## 三、整体量化对比

<grid columns={2}>
  <grid-item>
    <caption>Pack10K 平均视觉评分</caption>
    <title size="3xl" color="#DC2626" tabularNums={true}>2.88 / 10</title>
  </grid-item>
  <grid-item>
    <caption>NVIDIA 平均视觉评分</caption>
    <title size="3xl" tabularNums={true}>7.95 / 10</title>
  </grid-item>
</grid>

<box gap={2}>
  <row align=center>
    <box background="#DC2626" size="10px" radius="2px"/>
    <caption>Pack10K</caption>
    <box background="#16A34A" size="10px" radius="2px"/>
    <caption>NVIDIA</caption>
  </row>
  {#each [["瓦楞包裹箱",4.5,7.8],["拉环饮料罐",2,7.5],["酒瓶",1.5,8.3],["梅森罐",2,8],["敞口周转箱",3.5,8.5],["铰盖保鲜盒",3,8.2],["分体盖容器",3.5,7.8],["面包箱",3,7.5]] as d}
    <row align=center gap={2}>
      <box width="90px"><text size="sm">{d[0]}</text></box>
      <box flex={1} gap=1>
        <row align=center>
          <box background="#DC2626" height={11} width={`${d[1]*10}%`} radius="2px"/>
          <text size="xs" tabularNums>{d[1].toFixed(1)}</text>
        </row>
        <row align=center>
          <box background="#16A34A" height={11} width={`${d[2]*10}%`} radius="2px"/>
          <text size="xs" tabularNums>{d[2].toFixed(1)}</text>
        </row>
      </box>
    </row>
  {/each}
</box>

这些是基于截图的专家主观评分，不是经过多人盲测校准的客观指标。

## 四、视觉差距按影响大小排序

以下六个维度的权重是本轮评审建议，用于指导整改投入，并非通过消融实验测出的贡献率。

<box gap={3}>
  {#each [{n:"01",name:"资产形态与功能结构",v:35,desc:"瓶颈、盖体、提手、锁扣、拉环、折叠结构缺失。"}, {n:"02",name:"几何精细度",v:20,desc:"圆柱折面、零厚度视觉、锐边、缺少倒角。"}, {n:"03",name:"PBR 物理材质",v:18,desc:"纸张、金属、玻璃、塑料缺乏对应的光学特征。"}, {n:"04",name:"灯光与曝光控制",v:12,desc:"白色区域细节消失、内外壁明暗分离不足。"}, {n:"05",name:"环境与接触阴影",v:9,desc:"缺少落地感、空间感和物体重量感。"}, {n:"06",name:"相机取景与构图",v:6,desc:"主体过大、裁边、留白不足、展示状态不统一。"}] as d}
    <box gap=1>
      <row align=center>
        <text color="secondary" size="sm">{d.n}</text>
        **{d.name}**
        <spacer/>
        **{d.v}%**
      </row>
      <box height={8} radius="full" background="surface-tertiary">
        <box height={8} radius="full" background={d.v>=20?"#DC2626":d.v>=12?"#D97706":"#64748B"} width={`${d.v}%`}/>
      </box>
      <caption>{d.desc}</caption>
    </box>
  {/each}
</box>

最值得重视的是：**约 55% 的整改权重属于几何与资产形态，不属于传统摄影渲染。** 增加 Cycles 采样数、提高分辨率、换 HDRI，都不能让纸筒变成酒瓶。

## 五、哪些能修，哪些不能靠渲染修

### A. 纯渲染层问题——不修改源几何

<grid columns={2} gap={3}>
  <grid-item>
    <AsyncImage query="professional 3d product render plain kraft cardboard open box dark grey studio soft shadows" aspectRatio="4:3"/>
    **背景与地面**
    <caption>深灰无缝摄影棚、真实接触阴影。</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="white empty packaging box studio product photography soft directional lighting visible interior walls" aspectRatio="4:3"/>
    **曝光与层次**
    <caption>白色纸盒也应能清楚区分内外壁。</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="macro kraft paper cardboard material fine paper fibre surface texture product photography" aspectRatio="4:3"/>
    **纸材质感**
    <caption>微观纤维、粗糙度及漫反射。</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="minimal cardboard packaging box isolated centered three quarter view studio product rendering full object" aspectRatio="4:3"/>
    **标准化取景**
    <caption>完整轮廓、合理留白、统一视角。</caption>
  </grid-item>
</grid>

以上为整改方向的视觉参考，并非本批资产实测效果。

### B. 渲染代理几何——可程序化批量修复

不改变参数化母本，只为展示生成派生网格。

| 问题 | 修复手段 | 难度 |
|---|---|---|
| 纸板没有厚度 | Solidify 或显式厚度网格 | 低 |
| 盒体边缘过锐 | 微小物理倒角 | 低 |
| 圆筒多边形化 | 提高曲线离散精度 | 低 |
| 曲面法线不自然 | Smooth by Angle、法线修正 | 低 |
| 底面疑似缺失 | 核查拓扑，按设计补全 | 中 |
| 折线不可见 | 根据刀版压线生成细节 | 中 |
| 瓦楞纸截面缺失 | 参数化截面或局部纹理 | 中 |

这里不能简单使用全局 Subdivision。纸盒的折线、面板和直角必须保留，圆柱曲面则应该有足够的离散精度。

### C. 资产本质差距——需要新增资产能力

<box gap={3}>
  <row align=start>
    <AsyncImage query="unbranded aluminum beverage can pull tab lid neck bottom rim 3d product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **饮料罐**
      必须增加罐肩、卷边、拉环、罐底等结构，并使用金属材质。纸杯模板不能等价替代。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="empty green glass wine bottle cork studio product rendering realistic glass thickness" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **玻璃酒瓶**
      必须有旋转体轮廓、瓶肩、瓶颈、瓶口、玻璃厚度和瓶底结构。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="empty clear glass mason jar with white screw lid studio product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **梅森罐**
      必须有盖体、螺纹或对应封口结构、玻璃壁和瓶底。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="blue plastic industrial storage tote container rounded corners handle holes studio product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **塑料周转箱**
      必须有注塑圆角、加强筋、提手孔、翻边及合理壁厚。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="translucent plastic food storage container white lid locking clips product studio render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **保鲜盒及分体盖容器**
      必须有独立组件、装配关系、密封边、铰链或卡扣结构。
    </box>
  </row>
</box>

如果 Pack10K 的定位仍然是纸包装数据集，不应该为了追赶 NVIDIA 而强行扩展玻璃、金属和注塑资产。这会偏离原本的刀版与参数化包装研究目标。

## 六、可执行渲染整改清单

按投入产出比排序，以下参数作为首轮实验起点，不建议未经实测直接批量应用。

| 优先级 | 整改任务 | 建议技术方案 | 成本 |
|---|---|---|---|
| P0-01 | 修正取景 | 根据 evaluated bounding box 自动适配，主体占画面约75%–82% | 极低 |
| P0-02 | 增加地面 | 无缝摄影棚，深灰背景，保留真实接触阴影 | 极低 |
| P0-03 | 修正曝光 | AgX 色彩管理，控制白色区域高光及内壁层次 | 极低 |
| P0-04 | 重建灯光 | 大面积主灯、低强度补光、后侧轮廓灯 | 低 |
| P0-05 | 修复圆柱折面 | 渲染代理采用64–128段，按屏幕误差调整 | 低 |
| P0-06 | 增加纸板厚度 | 按纸材规格赋予真实厚度 | 低 |
| P1-01 | 微倒角 | 按材料与厚度控制倒角，2–3 segments 起步 | 低 |
| P1-02 | 建立纸材库 | 白卡纸、牛皮纸、瓦楞纸、涂布纸 | 中 |
| P1-03 | 纸张微观纹理 | Procedural Noise + Roughness + 微弱 Bump | 低 |
| P1-04 | 折叠细节 | 从 Geometry IR / 刀版生成压痕、接缝、粘口 | 中 |
| P1-05 | 完整组件 | 补齐箱盖、插舌及真实装配状态 | 中 |
| P2-01 | 渲染质量 | 1024×1024、128–256 samples、降噪 | 低 |
| P2-02 | 非纸包装资产 | 新增旋转体、金属罐、注塑容器资产族 | 高 |

### 建议冻结的摄影棚基线

<card gap={2}>
  <svg viewBox="0 0 340 270" width="100%">
    <rect x="42" y="24" width="256" height="210" rx="12" fill="#888888" opacity=".08" stroke="#888888" strokeDasharray="5 4"/>
    <ellipse cx="170" cy="136" rx="72" ry="45" fill="#888888" opacity=".12"/>
    <polygon points="135,118 190,99 218,125 163,144" fill="#e9d9b8" stroke="#a99674"/>
    <polygon points="135,118 163,144 163,180 135,154" fill="#ab9672" stroke="#a99674"/>
    <polygon points="163,144 218,125 218,161 163,180" fill="#d4bc90" stroke="#a99674"/>
    <g transform="rotate(-30 70 64)">
      <rect x="39" y="49" width="62" height="30" rx="3" fill="#eab308" fillOpacity=".24" stroke="#ca8a04"/>
      <path d="M45 57 H95 M45 64 H95 M45 71 H95" stroke="#ca8a04" strokeOpacity=".5"/>
    </g>
    <path d="M91 83 L139 120" stroke="#ca8a04" strokeDasharray="4 3"/>
    <text x="13" y="25" fontSize="11" fill="currentColor">主光 100%</text>
    <g transform="rotate(30 274 74)">
      <rect x="250" y="60" width="48" height="28" rx="3" fill="#60a5fa" fillOpacity=".2" stroke="#60a5fa"/>
    </g>
    <path d="M258 88 L207 122" stroke="#60a5fa" strokeDasharray="4 3"/>
    <text x="239" y="42" fontSize="11" fill="currentColor">补光 25–40%</text>
    <rect x="147" y="34" width="46" height="20" rx="3" fill="#94a3b8" fillOpacity=".4" stroke="#94a3b8"/>
    <path d="M170 55 L175 104" stroke="#94a3b8" strokeDasharray="4 3"/>
    <text x="170" y="15" textAnchor="middle" fontSize="11" fill="currentColor">轮廓光 30–60%</text>
    <g transform="rotate(22 99 218)">
      <rect x="80" y="207" width="38" height="23" rx="3" fill="#64748b"/>
      <rect x="88" y="197" width="22" height="12" rx="2" fill="#94a3b8"/>
    </g>
    <path d="M106 197 L156 167" stroke="currentColor" strokeOpacity=".4" strokeDasharray="4 3"/>
    <text x="100" y="250" textAnchor="middle" fontSize="11" fill="currentColor">Camera 70–85mm</text>
    <text x="241" y="215" textAnchor="middle" fontSize="11" fill="currentColor">无缝灰色地面</text>
    <text x="241" y="230" textAnchor="middle" fontSize="10" fill="#888888">Shadow / Contact</text>
  </svg>
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>相机俯角</caption>
      **20°–30°**
    </grid-item>
    <grid-item>
      <caption>相机方位</caption>
      **35°–45°**
    </grid-item>
    <grid-item>
      <caption>焦距（全画幅等效）</caption>
      **70–85 mm**
    </grid-item>
    <grid-item>
      <caption>色彩管理</caption>
      **AgX**
    </grid-item>
    <grid-item>
      <caption>背景</caption>
      **中性深灰**
    </grid-item>
    <grid-item>
      <caption>输出分辨率</caption>
      **1024 × 1024**
    </grid-item>
  </grid>
</card>

灯光百分比表示相对主灯的初始功率设置，并不等于实际表面照度比，最终需要根据灯具面积、距离及曝光重新校准。

## 七、架构层面：不要污染参数化母本

结合 Pack10K 的研究定位，我不建议直接在源几何上堆叠商业摄影所需的细节，而应该将几何真值与渲染资产分离。<MemoryCite />

<box border radius="xl" padding={3} gap={2}>
  <box background="surface" radius="md" padding={3} align=center>
    **L0 · Geometry IR 参数化母本**
    <caption>尺寸真值、刀版、拓扑、折叠关系</caption>
    <caption>不允许因视觉整改而改变</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box background="surface" radius="md" padding={3} align=center>
    **L1 · Render Geometry Proxy**
    <caption>厚度、倒角、曲面细分、压痕、接缝</caption>
    <caption>可重建、可追溯、可丢弃</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box background="surface" radius="md" padding={3} align=center>
    **L2 · PBR Appearance**
    <caption>纸张、印刷、粗糙度、微观纹理</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box background="surface" radius="md" padding={3} align=center>
    **L3 · Studio Rendering**
    <caption>相机、灯光、环境、曝光、阴影</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <grid columns={2} gap={2}>
    <grid-item>
      <box border radius="md" padding={2} align=center>
        **工程验证图**
        <caption>结构与尺寸可读</caption>
      </box>
    </grid-item>
    <grid-item>
      <box border radius="md" padding={2} align=center>
        **商业资产图**
        <caption>真实感与视觉质量</caption>
      </box>
    </grid-item>
  </grid>
</box>

这种做法能够保留 Pack10K 的低面数、尺寸可控、参数可重建等优势，同时避免将工程计算网格直接当作最终视觉资产。

## 八、下一轮实验怎么做

不要现在就整改全部 10K 资产，也不要同时修改全部参数。建议只选 R422 瓦楞箱作为实验对象，进行七组单变量递进实验。

| 实验 | 唯一新增改动 | 验证目标 |
|---|---|---|
| E0 | 原始版本 | 冻结基准 |
| E1 | 自动取景 | 完整轮廓 |
| E2 | 地面与背景 | 接触阴影与落地感 |
| E3 | 灯光 | 内外壁层次 |
| E4 | 曝光与色彩管理 | 高光细节 |
| E5 | 厚度与倒角代理 | 物理结构感 |
| E6 | PBR 纸材 | 材质真实性 |
| E7 | 折痕与接缝 | 包装结构可信度 |

每一轮保留此前参数，禁止同时引入额外变化。完成后将八张图匿名打乱，进行同标尺盲评，并保存场景参数与渲染耗时。

### 建议建立七项视觉验收门禁

| 门禁 | 验收标准 |
|---|---|
| VG01 构图 | 主体无裁切，四周留白合理 |
| VG02 曝光 | 纸面细节无明显高光溢出 |
| VG03 接触 | 正常摆放状态下有真实接触阴影 |
| VG04 曲面 | 圆柱轮廓无肉眼明显的离散折面 |
| VG05 材质 | 白卡、牛皮纸等材质可以视觉区分 |
| VG06 结构 | 厚度、折痕及装配关系符合设计 |
| VG07 保真 | 渲染整改不改变母本尺寸与刀版真值 |

首轮建议以 R422 从 4.5 分提升至 7.0 分以上为目标，而不是直接承诺达到 NVIDIA 水平。

## 九、对当前 NVIDIA 对标方法的质疑

这是我认为比渲染整改更重要的问题。

当前页面使用了“同构形态”“直接同构”等描述，但截图实际呈现的是：

| 对比组 | 同类别视觉对标是否成立 |
|---|---|
| 瓦楞箱 vs 瓦楞箱 | 有条件成立，需统一开合状态 |
| 纸杯 vs 饮料罐 | 不成立 |
| 纸筒 vs 酒瓶 | 不成立 |
| 纸板棱柱 vs 梅森罐 | 不成立 |
| 纸托盘 vs 塑料周转箱 | 仅粗粒度形态相似 |
| 纸盒 vs 铰盖保鲜盒 | 不成立 |
| 分体纸盒 vs 带盖塑料箱 | 部分结构类比 |
| 插盖纸盒 vs 面包箱 | 不成立 |

**拓扑抽象相似，不等于商品资产同构。**

建议将整个对标体系拆成三个相互独立的榜单：

- **Engineering Benchmark**：尺寸一致性、拓扑合法性、参数可重建性。
- **Visual Benchmark**：渲染真实性、几何细节、材质、摄影表现。
- **Semantic Benchmark**：商品类别、部件完整性、功能结构一致性。

当前工程门禁的原始代码、V5 尺寸对账规则、相机参数及源 USD 文件均未提供，因此本轮不能独立确认 100% 与 25.6% 的工程结论是否公平，也不能确认左右摄影条件确实完全一致。

---

## 十、最终裁决

| 评审项目 | 裁决 |
|---|---|
| 当前视觉展示质量 | <text color="danger" weight="medium">RETAKE</text> |
| 参数化几何作为研究母本 | 保留 |
| Cycles 渲染管线 | 需要整改 |
| 纸包装渲染代理层 | 建议新增 |
| 非纸包装资产扩展 | 暂不启动 |
| 当前一对一视觉对标 | 需要重构 |
| 全量 10K 重新渲染 | 暂缓 |

**优先把一种真实纸箱做到专业级，再通过程序化管线复制到其他纸包装族。**

目前最不应该做的是花大量算力将 10,000 个低精度白模渲染得更清晰。那只会得到 10,000 张更清晰的低精度白模。## 二、八组逐一评分

<box gap={3}>
  <row align=start>
    <box flex={1} gap=1>
      **01 · R422 瓦楞包裹箱**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">4.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.8</title>
      </row>
    </box>
    <box flex={3}>
      左侧像一个无厚度的纸质容器，没有箱盖、折痕、瓦楞截面及纸板接缝。光照过于平淡，右侧有明确的封箱结构、胶带和接触阴影。这是八组中相对容易追赶的一组，但必须先统一开箱与封箱状态。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **02 · R043 拉环饮料罐**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">2.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.5</title>
      </row>
    </box>
    <box flex={3}>
      左侧多边形轮廓极其明显，看起来是一次性纸杯，而不是饮料罐。缺少罐肩、卷边、罐底、拉环和金属材质。右侧也存在白色区域层次不足的问题，但至少能直接识别商品类别。单靠渲染无法追平。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **03 · R091 酒瓶**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">1.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.3</title>
      </row>
    </box>
    <box flex={3}>
      左侧是多边形纸筒，完全没有瓶肩、瓶颈、瓶塞及玻璃光学特征。右侧具有透明玻璃、曲面反射和底部厚度感。这不是同一种商品的不同渲染，而是两种不同资产。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **04 · R040 梅森罐**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">2.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.0</title>
      </row>
    </box>
    <box flex={3}>
      左侧呈现明显的折面，罐口没有任何厚度表达，底部灰色区域疑似开口或背景透出，需要检查几何。右侧具有旋盖、瓶肩、玻璃壁和底部结构。左右的材质与形态均不等价。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **05 · R415 敞口周转箱**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.5</title>
      </row>
    </box>
    <box flex={3}>
      左侧白色区域几乎融为一体，内壁、底面和外壁缺乏明暗分离，部分边缘贴近或超出画框。右侧的蓝色塑料、圆角、翻边、提手孔和柔和反射使其具有明确工业产品特征。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **06 · R037 铰盖保鲜盒**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">8.2</title>
      </row>
    </box>
    <box flex={3}>
      左侧没有展示可识别的铰链、盒盖或锁扣，而且纵横比例与右侧差异很大。暖黄色光照无法代替真实材质。右侧半透明塑料、盖体分离和卡扣结构明显提升了可信度。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **07 · R423 分体盖容器**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.5</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.8</title>
      </row>
    </box>
    <box flex={3}>
      左侧采用分体展示，理论上有利于结构研究，但两部分看起来像两个普通纸箱，无法直观判断盖与底座的配合关系。前方组件底部疑似镂空。右侧具备加强筋、把手、盖沿等功能性细节。
    </box>
  </row>
  <divider/>
  <row align=start>
    <box flex={1} gap=1>
      **08 · R026 面包箱**
      <caption>Pack10K / NVIDIA</caption>
      <row align=center>
        <title size="2xl" color="secondary">3.0</title>
        <text color="secondary">vs</text>
        <title size="2xl">7.5</title>
      </row>
    </box>
    <box flex={3}>
      左侧依旧是一个敞口矩形纸盒，没有展示插盖结构。右侧具有盖板、前部活动面板、旋钮和接缝。右侧也存在曝光偏高的问题，但功能结构完整度远高于左侧。
    </box>
  </row>
</box>

## 三、整体量化对比

<grid columns={2}>
  <grid-item>
    <caption>Pack10K 平均视觉评分</caption>
    <title size="3xl" color="#DC2626" tabularNums={true}>2.88 / 10</title>
  </grid-item>
  <grid-item>
    <caption>NVIDIA 平均视觉评分</caption>
    <title size="3xl" tabularNums={true}>7.95 / 10</title>
  </grid-item>
</grid>

<box gap={2}>
  <row align=center>
    <box background="#DC2626" size="10px" radius="2px"/>
    <caption>Pack10K</caption>
    <box background="#16A34A" size="10px" radius="2px"/>
    <caption>NVIDIA</caption>
  </row>
  {#each [["瓦楞包裹箱",4.5,7.8],["拉环饮料罐",2,7.5],["酒瓶",1.5,8.3],["梅森罐",2,8],["敞口周转箱",3.5,8.5],["铰盖保鲜盒",3,8.2],["分体盖容器",3.5,7.8],["面包箱",3,7.5]] as d}
    <row align=center gap={2}>
      <box width="90px"><text size="sm">{d[0]}</text></box>
      <box flex={1} gap=1>
        <row align=center>
          <box background="#DC2626" height={11} width={`${d[1]*10}%`} radius="2px"/>
          <text size="xs" tabularNums>{d[1].toFixed(1)}</text>
        </row>
        <row align=center>
          <box background="#16A34A" height={11} width={`${d[2]*10}%`} radius="2px"/>
          <text size="xs" tabularNums>{d[2].toFixed(1)}</text>
        </row>
      </box>
    </row>
  {/each}
</box>

这些是基于截图的专家主观评分，不是经过多人盲测校准的客观指标。

## 四、视觉差距按影响大小排序

以下六个维度的权重是本轮评审建议，用于指导整改投入，并非通过消融实验测出的贡献率。

<box gap={3}>
  {#each [{n:"01",name:"资产形态与功能结构",v:35,desc:"瓶颈、盖体、提手、锁扣、拉环、折叠结构缺失。"}, {n:"02",name:"几何精细度",v:20,desc:"圆柱折面、零厚度视觉、锐边、缺少倒角。"}, {n:"03",name:"PBR 物理材质",v:18,desc:"纸张、金属、玻璃、塑料缺乏对应的光学特征。"}, {n:"04",name:"灯光与曝光控制",v:12,desc:"白色区域细节消失、内外壁明暗分离不足。"}, {n:"05",name:"环境与接触阴影",v:9,desc:"缺少落地感、空间感和物体重量感。"}, {n:"06",name:"相机取景与构图",v:6,desc:"主体过大、裁边、留白不足、展示状态不统一。"}] as d}
    <box gap=1>
      <row align=center>
        <text color="secondary" size="sm">{d.n}</text>
        **{d.name}**
        <spacer/>
        **{d.v}%**
      </row>
      <box height={8} radius="full" background="surface-tertiary">
        <box height={8} radius="full" background={d.v>=20?"#DC2626":d.v>=12?"#D97706":"#64748B"} width={`${d.v}%`}/>
      </box>
      <caption>{d.desc}</caption>
    </box>
  {/each}
</box>

最值得重视的是：**约 55% 的整改权重属于几何与资产形态，不属于传统摄影渲染。** 增加 Cycles 采样数、提高分辨率、换 HDRI，都不能让纸筒变成酒瓶。

## 五、哪些能修，哪些不能靠渲染修

### A. 纯渲染层问题——不修改源几何

<grid columns={2} gap={3}>
  <grid-item>
    <AsyncImage query="professional 3d product render plain kraft cardboard open box dark grey studio soft shadows" aspectRatio="4:3"/>
    **背景与地面**
    <caption>深灰无缝摄影棚、真实接触阴影。</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="white empty packaging box studio product photography soft directional lighting visible interior walls" aspectRatio="4:3"/>
    **曝光与层次**
    <caption>白色纸盒也应能清楚区分内外壁。</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="macro kraft paper cardboard material fine paper fibre surface texture product photography" aspectRatio="4:3"/>
    **纸材质感**
    <caption>微观纤维、粗糙度及漫反射。</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="minimal cardboard packaging box isolated centered three quarter view studio product rendering full object" aspectRatio="4:3"/>
    **标准化取景**
    <caption>完整轮廓、合理留白、统一视角。</caption>
  </grid-item>
</grid>

以上为整改方向的视觉参考，并非本批资产实测效果。

### B. 渲染代理几何——可程序化批量修复

不改变参数化母本，只为展示生成派生网格。

| 问题 | 修复手段 | 难度 |
|---|---|---|
| 纸板没有厚度 | Solidify 或显式厚度网格 | 低 |
| 盒体边缘过锐 | 微小物理倒角 | 低 |
| 圆筒多边形化 | 提高曲线离散精度 | 低 |
| 曲面法线不自然 | Smooth by Angle、法线修正 | 低 |
| 底面疑似缺失 | 核查拓扑，按设计补全 | 中 |
| 折线不可见 | 根据刀版压线生成细节 | 中 |
| 瓦楞纸截面缺失 | 参数化截面或局部纹理 | 中 |

这里不能简单使用全局 Subdivision。纸盒的折线、面板和直角必须保留，圆柱曲面则应该有足够的离散精度。

### C. 资产本质差距——需要新增资产能力

<box gap={3}>
  <row align=start>
    <AsyncImage query="unbranded aluminum beverage can pull tab lid neck bottom rim 3d product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **饮料罐**
      必须增加罐肩、卷边、拉环、罐底等结构，并使用金属材质。纸杯模板不能等价替代。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="empty green glass wine bottle cork studio product rendering realistic glass thickness" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **玻璃酒瓶**
      必须有旋转体轮廓、瓶肩、瓶颈、瓶口、玻璃厚度和瓶底结构。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="empty clear glass mason jar with white screw lid studio product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **梅森罐**
      必须有盖体、螺纹或对应封口结构、玻璃壁和瓶底。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="blue plastic industrial storage tote container rounded corners handle holes studio product render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **塑料周转箱**
      必须有注塑圆角、加强筋、提手孔、翻边及合理壁厚。
    </box>
  </row>
  <divider/>
  <row align=start>
    <AsyncImage query="translucent plastic food storage container white lid locking clips product studio render" aspectRatio="1:1" maxWidth="112px"/>
    <box flex={1}>
      **保鲜盒及分体盖容器**
      必须有独立组件、装配关系、密封边、铰链或卡扣结构。
    </box>
  </row>
</box>

如果 Pack10K 的定位仍然是纸包装数据集，不应该为了追赶 NVIDIA 而强行扩展玻璃、金属和注塑资产。这会偏离原本的刀版与参数化包装研究目标。

## 六、可执行渲染整改清单

按投入产出比排序，以下参数作为首轮实验起点，不建议未经实测直接批量应用。

| 优先级 | 整改任务 | 建议技术方案 | 成本 |
|---|---|---|---|
| P0-01 | 修正取景 | 根据 evaluated bounding box 自动适配，主体占画面约75%–82% | 极低 |
| P0-02 | 增加地面 | 无缝摄影棚，深灰背景，保留真实接触阴影 | 极低 |
| P0-03 | 修正曝光 | AgX 色彩管理，控制白色区域高光及内壁层次 | 极低 |
| P0-04 | 重建灯光 | 大面积主灯、低强度补光、后侧轮廓灯 | 低 |
| P0-05 | 修复圆柱折面 | 渲染代理采用64–128段，按屏幕误差调整 | 低 |
| P0-06 | 增加纸板厚度 | 按纸材规格赋予真实厚度 | 低 |
| P1-01 | 微倒角 | 按材料与厚度控制倒角，2–3 segments 起步 | 低 |
| P1-02 | 建立纸材库 | 白卡纸、牛皮纸、瓦楞纸、涂布纸 | 中 |
| P1-03 | 纸张微观纹理 | Procedural Noise + Roughness + 微弱 Bump | 低 |
| P1-04 | 折叠细节 | 从 Geometry IR / 刀版生成压痕、接缝、粘口 | 中 |
| P1-05 | 完整组件 | 补齐箱盖、插舌及真实装配状态 | 中 |
| P2-01 | 渲染质量 | 1024×1024、128–256 samples、降噪 | 低 |
| P2-02 | 非纸包装资产 | 新增旋转体、金属罐、注塑容器资产族 | 高 |

### 建议冻结的摄影棚基线

<card gap={2}>
  <svg viewBox="0 0 340 270" width="100%">
    <rect x="42" y="24" width="256" height="210" rx="12" fill="#888888" opacity=".08" stroke="#888888" strokeDasharray="5 4"/>
    <ellipse cx="170" cy="136" rx="72" ry="45" fill="#888888" opacity=".12"/>
    <polygon points="135,118 190,99 218,125 163,144" fill="#e9d9b8" stroke="#a99674"/>
    <polygon points="135,118 163,144 163,180 135,154" fill="#ab9672" stroke="#a99674"/>
    <polygon points="163,144 218,125 218,161 163,180" fill="#d4bc90" stroke="#a99674"/>
    <g transform="rotate(-30 70 64)">
      <rect x="39" y="49" width="62" height="30" rx="3" fill="#eab308" fillOpacity=".24" stroke="#ca8a04"/>
      <path d="M45 57 H95 M45 64 H95 M45 71 H95" stroke="#ca8a04" strokeOpacity=".5"/>
    </g>
    <path d="M91 83 L139 120" stroke="#ca8a04" strokeDasharray="4 3"/>
    <text x="13" y="25" fontSize="11" fill="currentColor">主光 100%</text>
    <g transform="rotate(30 274 74)">
      <rect x="250" y="60" width="48" height="28" rx="3" fill="#60a5fa" fillOpacity=".2" stroke="#60a5fa"/>
    </g>
    <path d="M258 88 L207 122" stroke="#60a5fa" strokeDasharray="4 3"/>
    <text x="239" y="42" fontSize="11" fill="currentColor">补光 25–40%</text>
    <rect x="147" y="34" width="46" height="20" rx="3" fill="#94a3b8" fillOpacity=".4" stroke="#94a3b8"/>
    <path d="M170 55 L175 104" stroke="#94a3b8" strokeDasharray="4 3"/>
    <text x="170" y="15" textAnchor="middle" fontSize="11" fill="currentColor">轮廓光 30–60%</text>
    <g transform="rotate(22 99 218)">
      <rect x="80" y="207" width="38" height="23" rx="3" fill="#64748b"/>
      <rect x="88" y="197" width="22" height="12" rx="2" fill="#94a3b8"/>
    </g>
    <path d="M106 197 L156 167" stroke="currentColor" strokeOpacity=".4" strokeDasharray="4 3"/>
    <text x="100" y="250" textAnchor="middle" fontSize="11" fill="currentColor">Camera 70–85mm</text>
    <text x="241" y="215" textAnchor="middle" fontSize="11" fill="currentColor">无缝灰色地面</text>
    <text x="241" y="230" textAnchor="middle" fontSize="10" fill="#888888">Shadow / Contact</text>
  </svg>
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>相机俯角</caption>
      **20°–30°**
    </grid-item>
    <grid-item>
      <caption>相机方位</caption>
      **35°–45°**
    </grid-item>
    <grid-item>
      <caption>焦距（全画幅等效）</caption>
      **70–85 mm**
    </grid-item>
    <grid-item>
      <caption>色彩管理</caption>
      **AgX**
    </grid-item>
    <grid-item>
      <caption>背景</caption>
      **中性深灰**
    </grid-item>
    <grid-item>
      <caption>输出分辨率</caption>
      **1024 × 1024**
    </grid-item>
  </grid>
</card>

灯光百分比表示相对主灯的初始功率设置，并不等于实际表面照度比，最终需要根据灯具面积、距离及曝光重新校准。

## 七、架构层面：不要污染参数化母本

结合 Pack10K 的研究定位，我不建议直接在源几何上堆叠商业摄影所需的细节，而应该将几何真值与渲染资产分离。<MemoryCite />

<box border radius="xl" padding={3} gap={2}>
  <box background="surface" radius="md" padding={3} align=center>
    **L0 · Geometry IR 参数化母本**
    <caption>尺寸真值、刀版、拓扑、折叠关系</caption>
    <caption>不允许因视觉整改而改变</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box background="surface" radius="md" padding={3} align=center>
    **L1 · Render Geometry Proxy**
    <caption>厚度、倒角、曲面细分、压痕、接缝</caption>
    <caption>可重建、可追溯、可丢弃</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box background="surface" radius="md" padding={3} align=center>
    **L2 · PBR Appearance**
    <caption>纸张、印刷、粗糙度、微观纹理</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box background="surface" radius="md" padding={3} align=center>
    **L3 · Studio Rendering**
    <caption>相机、灯光、环境、曝光、阴影</caption>
  </box>
  <row justify=center><icon name="arrow-down" color="secondary" size="lg"/></row>
  <grid columns={2} gap={2}>
    <grid-item>
      <box border radius="md" padding={2} align=center>
        **工程验证图**
        <caption>结构与尺寸可读</caption>
      </box>
    </grid-item>
    <grid-item>
      <box border radius="md" padding={2} align=center>
        **商业资产图**
        <caption>真实感与视觉质量</caption>
      </box>
    </grid-item>
  </grid>
</box>

这种做法能够保留 Pack10K 的低面数、尺寸可控、参数可重建等优势，同时避免将工程计算网格直接当作最终视觉资产。

## 八、下一轮实验怎么做

不要现在就整改全部 10K 资产，也不要同时修改全部参数。建议只选 R422 瓦楞箱作为实验对象，进行七组单变量递进实验。

| 实验 | 唯一新增改动 | 验证目标 |
|---|---|---|
| E0 | 原始版本 | 冻结基准 |
| E1 | 自动取景 | 完整轮廓 |
| E2 | 地面与背景 | 接触阴影与落地感 |
| E3 | 灯光 | 内外壁层次 |
| E4 | 曝光与色彩管理 | 高光细节 |
| E5 | 厚度与倒角代理 | 物理结构感 |
| E6 | PBR 纸材 | 材质真实性 |
| E7 | 折痕与接缝 | 包装结构可信度 |

每一轮保留此前参数，禁止同时引入额外变化。完成后将八张图匿名打乱，进行同标尺盲评，并保存场景参数与渲染耗时。

### 建议建立七项视觉验收门禁

| 门禁 | 验收标准 |
|---|---|
| VG01 构图 | 主体无裁切，四周留白合理 |
| VG02 曝光 | 纸面细节无明显高光溢出 |
| VG03 接触 | 正常摆放状态下有真实接触阴影 |
| VG04 曲面 | 圆柱轮廓无肉眼明显的离散折面 |
| VG05 材质 | 白卡、牛皮纸等材质可以视觉区分 |
| VG06 结构 | 厚度、折痕及装配关系符合设计 |
| VG07 保真 | 渲染整改不改变母本尺寸与刀版真值 |

首轮建议以 R422 从 4.5 分提升至 7.0 分以上为目标，而不是直接承诺达到 NVIDIA 水平。

## 九、对当前 NVIDIA 对标方法的质疑

这是我认为比渲染整改更重要的问题。

当前页面使用了“同构形态”“直接同构”等描述，但截图实际呈现的是：

| 对比组 | 同类别视觉对标是否成立 |
|---|---|
| 瓦楞箱 vs 瓦楞箱 | 有条件成立，需统一开合状态 |
| 纸杯 vs 饮料罐 | 不成立 |
| 纸筒 vs 酒瓶 | 不成立 |
| 纸板棱柱 vs 梅森罐 | 不成立 |
| 纸托盘 vs 塑料周转箱 | 仅粗粒度形态相似 |
| 纸盒 vs 铰盖保鲜盒 | 不成立 |
| 分体纸盒 vs 带盖塑料箱 | 部分结构类比 |
| 插盖纸盒 vs 面包箱 | 不成立 |

**拓扑抽象相似，不等于商品资产同构。**

建议将整个对标体系拆成三个相互独立的榜单：

- **Engineering Benchmark**：尺寸一致性、拓扑合法性、参数可重建性。
- **Visual Benchmark**：渲染真实性、几何细节、材质、摄影表现。
- **Semantic Benchmark**：商品类别、部件完整性、功能结构一致性。

当前工程门禁的原始代码、V5 尺寸对账规则、相机参数及源 USD 文件均未提供，因此本轮不能独立确认 100% 与 25.6% 的工程结论是否公平，也不能确认左右摄影条件确实完全一致。

---

## 十、最终裁决

| 评审项目 | 裁决 |
|---|---|
| 当前视觉展示质量 | <text color="danger" weight="medium">RETAKE</text> |
| 参数化几何作为研究母本 | 保留 |
| Cycles 渲染管线 | 需要整改 |
| 纸包装渲染代理层 | 建议新增 |
| 非纸包装资产扩展 | 暂不启动 |
| 当前一对一视觉对标 | 需要重构 |
| 全量 10K 重新渲染 | 暂缓 |

**优先把一种真实纸箱做到专业级，再通过程序化管线复制到其他纸包装族。**

目前最不应该做的是花大量算力将 10,000 个低精度白模渲染得更清晰。那只会得到 10,000 张更清晰的低精度白模。