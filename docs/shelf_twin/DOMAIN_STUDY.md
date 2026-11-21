# 货架孪生领域研究 — 行业标准架构 vs 我们管线 (2026-11-21)

触发: 用户指出"先学货架孪生"。检索行业做法 (NVIDIA SimReady/Omniverse 零售线, Lowe's, DreamVu, Hyperverse, Algomine, TwinStore, Nordic BIM) + 本地 simready-usd-pipeline-mac 技能。

## 行业标准架构 (五层)

```
① 陈列证据层  Planogram 陈列表 (SKU/排面数/层高/位置/段)
              ↑ 来源: 真店审计/POS/实拍量测 — 结构化数据, 非美术直觉
② SKU 资产层  SimReady USD 资产库: 实测尺寸+语义标签(SemanticsLabelsAPI)
              + 实验室实测物理参数 (DreamVu 2200 件实拍扫描即此路线)
③ 装配层      Planogram → 3D 布局引擎: 夹具参数化 + SKU 实例化
              (Algomine: 先分群再定位, 复刻品类经理工作流; Nordic BIM:
               planogram 数据直喂 BIM 模型的夹具几何)
④ 验证层      物理静置/接触 (MuJoCo) + 语义分割覆盖门 + 渲染对齐门
              (SimReady spec: SL.001/SL.003/SL.MAT.001)
⑤ 应用层      陈列合规审计/补货/布局优化/合成数据 (Lowe's: twin 每日多次
              同步真店, 布局重配/补货/planogram 测试)
```

## 我们管线对标

| 层 | 行业标准 | 我们现状 | 判定 |
|---|---|---|---|
| ① 陈列证据 | 结构化 planogram 数据 | RECONCILIATION.md 手绘对账表 (proto-planogram) | ⚠️ 有证据无结构 |
| ② SKU 资产 | USD+语义+实测物理 | PIL 印刷+程序化网格→crop 贴图, 无 USD/语义/物理 | ❌ 最大缺口 |
| ③ 装配 | planogram 消费引擎 | build_hxl_shelf.py 隐式程序化排面 | ⚠️ 能跑但不消费数据层 |
| ④ 验证 | 物理+语义+渲染 | 盲评三协议+像素门+参照对齐 (超行业平均); 无物理/语义门 | ✅ 渲染门超前 / ❌ 物理语义门缺 |
| ⑤ 应用 | 合规/补货/优化 | 仅合成数据展示 | 未展开 |

## 结论

1. **感知渲染循环没有白做**: 它是行业标准第④层的"渲染对齐门", 我们这块超行业平均 (三层盲评协议+负结果存证纪律)。
2. **缺的是证据-仿真层**: planogram 数据结构化 + SKU 资产 USD 语义化 + 物理验证 — 这正是 ESR 北极星 (Evidence-Simulation-Ready) 的字面要求。
3. **路线修正** (ESR 化三步):
   - Step A: 对账表 → `planogram.json` 结构化陈列表 (层高/段/SKU/排面/位置, 从参照照片量测取证)
   - Step B: SKU 资产 USD 化 — 实测尺寸 `phys:dimensionsMM` + `SemanticsLabelsAPI` 语义 + 质量参数, MuJoCo 静置验证 (复用 simready-usd-pipeline-mac 管线)
   - Step C: 装配脚本改写为 planogram.json 消费者 (数据驱动布局, 场景脚本只留夹具+灯光+相机)
   - Step D: 验证门扩展: 物理 + 语义覆盖 + 既有盲评 (三门齐全 = ESR 合规样例)

## 来源

- NVIDIA Smart Stores / Lowe's case: https://www.nvidia.com/en-us/industries/retail/smart-stores/ ; https://blogs.nvidia.com/blog/2022/09/20/lowes-retail-digital-twins-omniverse/
- DreamVu grocery SimReady (实拍扫描+实测物理): https://www.dreamvu.ai/press/dreamvu-launches-the-largest-grocery-simready-asset-library-built-from-real-world-capture
- Hyperverse retail shelf products (100+ rigid USD): https://www.hyperverse.sh/assets/rigid-and-articulated/warehouse-and-logistics/retail-products
- NVIDIA simready-assets (HF): https://huggingface.co/datasets/nvidia/simready-assets
- Algomine planogram ML 管线: https://algomine.ai/stories/ai-planogram-generation-system-virtual-software-company/
- Nordic BIM planogram×BIM: https://www.nordicbim.com/en/insights/bim-and-planogram-the-future-of-retail
- TwinStore (VLM store twin): https://arxiv.org/html/2610.30909v1
- 本地技能: simready-usd-pipeline-mac (Blender→usd-core 语义→MuJoCo→CPU 分割门)
