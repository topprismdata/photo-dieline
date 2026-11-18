# PhotoDieline

**实物包装照片 → 印刷级 1:1 刀版图。** From physical packaging to manufacturing geometry.

开源工具链：输入手机照片 + 少量实测尺寸，重建折叠纸包装（屋顶包/瓦楞箱/纸盒）的参数化制造几何，输出分层 1:1 刀版 SVG/PDF（裁切/压线/粘口/出血/套准），并用纯数值折叠仿真验证回包闭合。

> 姊妹仓：[openusd-retail-twin](https://github.com/topprismdata/openusd-retail-twin)（零售商品数字孪生与视觉 AI 管线）。本仓与其完全独立。

## 架构一图

```
照片 + 实测尺寸 ─► 箱型识别 ─► 参数化模板 ─► Geometry IR ─►┬─► 1:1 分层 SVG/PDF
                (T1分类/T2回归, M2)   (唯一制造几何协议)      └─► 折叠数值验证 + QA 报告
```

三条铁律：

1. **参数化主干**：制造几何永远由模板+几何内核生成，模型只提供"类型+参数"建议（ADR-001/009）。
2. **证据分级**：实测 > 可信来源 > 约束推导 > 模型推断 > 默认值；模型值永不覆盖实测（ADR-003）。
3. **三态交付**：DRAFT → VALIDATED（数值 QA 全过）→ PRINT-READY（印厂人工签核）；系统不得自动升级（ADR-008）。

## 里程碑

| 阶段 | 内容 | 状态 |
|---|---|---|
| **M1** | gable-top 屋顶包垂直切片：照片+三尺寸 → Geometry IR → 自研 2D 布局 → 1:1 分层 SVG/PDF → 纯 Python 折叠 QA（十门） | ✅ **VALIDATED**（CI 可复跑：`pytest tests/`） |
| M2 | 模板库扩展（FEFCO 0201）＋ **Twins Data Engine**（合成孪生数据飞轮）＋ T1 箱型分类 / T2 参数回归 | 设计冻结（`docs/tde-spec.md`） |
| M3 | TRELLIS.2 视觉辅证 · 智能补参交互 · 端到端候选 IR 研究 | 规划 |

## 快速开始（M1 垂直切片）

```bash
pip install -e ".[dev]"

# 一条命令: 照片 + 实测尺寸 → IR / 1:1 分层 SVG / 分层 PDF / QA 报告
# 仓内自带公版参照照 (USDA PD): 也可换成你自己的实拍
photo-dieline build --spec examples/gable_top/spec.json \
  --photo examples/gable_top/reference_photo.jpg --out examples/gable_top/artifacts

pytest tests/   # 13 项机器验收 (16 项合同的可自动判定部分)
```

输出 `artifacts/`：`geometry-ir.json`（五对象协议）· `dieline.svg` · `dieline.pdf`（7 图层 OCGroups）·
`qa-report.json`（G01-G10 门禁）。照片门 ≥1000px；折叠闭合残差 ≤0.2mm；golden 尺寸 ≤0.5mm。

## 设计文档

- [DESIGN.md](DESIGN.md) — 架构方案 V1.0（GPT 三轮评审冻结版）
- [docs/adr/README.md](docs/adr/README.md) — 11 项架构决策台账
- [docs/reviews/gpt_design_all_rounds.md](docs/reviews/gpt_design_all_rounds.md) — GPT 评审原始判决全文

## License

MIT（见 [LICENSE](LICENSE)）。第三方依赖与数据来源许可见 `THIRD_PARTY_NOTICES.md`（随 M1 交付）。
