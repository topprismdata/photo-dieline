# Third-Party Notices

本仓主体代码 MIT 许可（见 `LICENSE`）。运行时依赖及其许可：

| 依赖 | 许可 | 用途 |
|---|---|---|
| NumPy | BSD-3-Clause | 折叠运动学数值计算 |
| Shapely | BSD-3-Clause | 2D 轮廓/并集/出血偏移 |
| jsonschema | MIT | Geometry IR Schema 校验 |
| Pillow | HPND / MIT-CMU | 照片证据读取 |
| Typer | MIT | CLI |
| pypdf | BSD-3-Clause | QA 门 G08 独立解析 PDF 交付物 |

## 方法与知识来源（非代码依赖）

- gable-top 屋顶包几何规则：公开包装工程常识（利乐式屋顶包拓扑）；
  结构知识参照自母仓 openusd-retail-twin 的 R40 实测定案（低坡+过脊立鳍），代码独立重写，无复制。
- DielineForge（GPL-3.0）与 TRELLIS.2：**未引入**本仓（ADR-005/004；M3 再评估）。
- FEFCO 结构图纸：未复制、未再分发（M2 若实现兼容结构，将按公开几何规则独立实现并单独核验许可）。

## 数据资产

- `examples/gable_top/reference_photo.jpg` — USDA 公有领域实拍（屋顶包参照证据），
  溯源/商标声明见 `examples/gable_top/PHOTO_PROVENANCE.md`（ADR-011 首条落地）。
- `assets/hdri/studio_small_09_2k.hdr` — Poly Haven HDRI（CC0），货架孪生渲染的环境光。
- `assets/ai_prints/*.png` 及其派生的 `assets/pillow_designs/design_*.png` — MiniMax H3-Image 本地推理生成的虚构品牌（TOPPRISM）包装印刷图；图案内容非真实品牌。模型权重的使用许可以其官方发布为准，入库时未做许可审查（待补）。
- **已出库**（2026-11-24）：`assets/food_patches/` 下 4 张第三方电商产品摄影裁片（无来源与许可记录，违反 ADR-011）。回退路径改为仓内自绘占位图。注意：这些文件在 2026-11-21 至 11-24 之间的 git 历史提交中仍然存在，清除历史需改写公开仓历史（待仓库所有者裁决）。

## 数据治理承诺（ADR-011）

任何进入本仓的照片/数据集样本将携带来源、许可与再分发元数据；客户品牌素材零容忍。
