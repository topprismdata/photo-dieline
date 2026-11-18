# Third-Party Notices

本仓主体代码 MIT 许可（见 `LICENSE`）。运行时依赖及其许可：

| 依赖 | 许可 | 用途 |
|---|---|---|
| NumPy | BSD-3-Clause | 折叠运动学数值计算 |
| Shapely | BSD-3-Clause | 2D 轮廓/并集/出血偏移 |
| jsonschema | MIT | Geometry IR Schema 校验 |
| Pillow | HPND / MIT-CMU | 照片证据读取 |
| Typer | MIT | CLI |

## 方法与知识来源（非代码依赖）

- gable-top 屋顶包几何规则：公开包装工程常识（利乐式屋顶包拓扑）；
  结构知识参照自母仓 openusd-retail-twin 的 R40 实测定案（低坡+过脊立鳍），代码独立重写，无复制。
- DielineForge（GPL-3.0）与 TRELLIS.2：**未引入**本仓（ADR-005/004；M3 再评估）。
- FEFCO 结构图纸：未复制、未再分发（M2 若实现兼容结构，将按公开几何规则独立实现并单独核验许可）。

## 数据资产

- `examples/gable_top/reference_photo.jpg` — USDA 公有领域实拍（屋顶包参照证据），
  溯源/商标声明见 `examples/gable_top/PHOTO_PROVENANCE.md`（ADR-011 首条落地）。

## 数据治理承诺（ADR-011）

任何进入本仓的照片/数据集样本将携带来源、许可与再分发元数据；客户品牌素材零容忍。
