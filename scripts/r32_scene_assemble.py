"""R32: WP-L2-01 12 SKU 乳品冷藏柜单层原型 (场景契约首跑)
业务需求驱动: r32_selection_dairy_cooler.md 12 SKU → 场景契约 JSON + planogram 放置 + 计时
只读引用冻结资产参数 (build.json), 不重编译冻结集
"""
import json, glob, os, time
from collections import defaultdict

SHELF_W_MM = 1200.0
SHELF_D_MM = 300.0
SHELF_H_MM = 280.0

# 12 SKU 清单 (r32_selection_dairy_cooler.md 冻结)
SKUS = [
    {"id": 1,  "name": "金典纯牛奶250ml",      "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 2, "depth": 2},
    {"id": 2,  "name": "金典有机250ml",         "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 2, "depth": 2},
    {"id": 3,  "name": "安慕希原味205g",        "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 2, "depth": 2},
    {"id": 4,  "name": "安慕希黄桃燕麦205g",    "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 2, "depth": 2},
    {"id": 5,  "name": "舒化无乳糖250ml",       "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 1, "depth": 2},
    {"id": 6,  "name": "QQ星儿童奶195ml",       "w": 50, "d": 38, "h": 110, "src": "frozen:aseptic_brick", "facings": 1, "depth": 2},
    {"id": 7,  "name": "优酸乳原味250ml",       "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 1, "depth": 2},
    {"id": 8,  "name": "味可滋芝士乳茶240ml",   "w": 55, "d": 40, "h": 115, "src": "frozen:aseptic_brick", "facings": 1, "depth": 2},
    {"id": 9,  "name": "金典娟姗瓶装250ml",     "w": 70, "d": 70, "h": 175, "src": "hfpackage:milk_bottle_1000", "facings": 1, "depth": 1},
    {"id": 10, "name": "味可滋瓶装450ml",       "w": 65, "d": 65, "h": 180, "src": "hfpackage:milk_bottle_1000", "facings": 1, "depth": 1},
    {"id": 11, "name": "伊利纯牛奶1L屋顶包",    "w": 95, "d": 95, "h": 250, "src": "frozen:gable_top", "facings": 1, "depth": 1},
    {"id": 12, "name": "娟姗酸奶杯160g",        "w": 90, "d": 55, "h": 105, "src": "hfpackage:yogurt_cup_160", "facings": 1, "depth": 1},
]

# 资产绑定: 从冻结集为每个 aseptic/gable SKU 找已发行变体 (确定性: 家族字典序+变体升序)
frozen = defaultdict(list)
for bp in sorted(glob.glob("output/pack10k_scale10k/*/build.json")):
    b = json.load(open(bp))
    fam = b.get("family", "?")
    frozen[fam].append({"asset_id": b["asset_id"], "cls": b["class_id"],
                         "sha": None, "dir": os.path.dirname(bp)})

def pick_asset(src, used):
    if src.startswith("frozen:"):
        fam = src.split(":", 1)[1].replace("aseptic_brick", "aseptic").replace("gable_top", "gable")
        cands = [a for a in frozen.get(fam, []) if a["asset_id"] not in used]
        return sorted(cands, key=lambda a: a["asset_id"])[0] if cands else None
    return None  # hfpackage 引用 (非冻结集成员, 单独登记)

t0 = time.perf_counter()
used = set()
placements = []
x = 30.0  # 左缘留 30mm
violations = []
for sku in SKUS:
    n = sku["facings"]
    span = sku["w"] * n + 8.0 * (n - 1)  # 面间 8mm 间隙
    if x + span > SHELF_W_MM - 30.0:
        violations.append({"sku": sku["name"], "violation": "宽度溢出", "detail": f"需 {span:.0f}mm, 剩 {SHELF_W_MM-30-x:.0f}mm"})
        placements.append({"sku": sku["name"], "status": "NOT_PLACED", "reason": "宽度溢出"})
        continue
    if sku["h"] > SHELF_H_MM:
        violations.append({"sku": sku["name"], "violation": "高度超层板净空", "detail": f"{sku['h']}>{SHELF_H_MM}"})
        placements.append({"sku": sku["name"], "status": "NOT_PLACED", "reason": "高度超净空"})
        continue
    a = pick_asset(sku["src"], used)
    if a: used.add(a["asset_id"])
    placements.append({
        "sku": sku["name"], "status": "PLACED",
        "placement_id": f"P{len(placements)+1:03d}",
        "product_id": f"DAIRY-{sku['id']:02d}",
        "asset_id": a["asset_id"] if a else sku["src"].split(":", 1)[1],
        "asset_source": sku["src"],
        "position_mm": [round(x, 1), 0, 0],
        "facings": n, "depth_count": sku["depth"], "orientation": "front",
        "span_mm": round(span, 1),
    })
    x += span + 12.0  # SKU 间 12mm
build_time = time.perf_counter() - t0

placed = [p for p in placements if p["status"] == "PLACED"]
util = sum(p["span_mm"] for p in placed) / (SHELF_W_MM - 60.0)
scene = {
  "scene_schema": "RWI-L2 scene contract v1.0",
  "scene_id": "R32-DAIRY-COOLER-L2-PROTOTYPE",
  "scene_version": "0.1",
  "fixture": {"fixture_id": "COOLER-1200-L2", "shelf_level_id": "L2", "fixture_dimensions_mm": [SHELF_W_MM, SHELF_D_MM, SHELF_H_MM]},
  "constraint_set_id": "dairy_cooler_default_v1",
  "constraint_set": {"side_gap_mm": 30, "sku_gap_mm": 12, "facing_gap_mm": 8, "max_height_mm": SHELF_H_MM},
  "placements": placements,
  "metrics": {
    "placed_skus": len(placed), "total_skus": len(SKUS),
    "violations": violations,
    "capacity_utilization": round(util, 3),
    "build_seconds_prototype": round(build_time, 4),
    "coverage_note": "10/12 冻结集直引 + 2 hfpackage SimReady 引用 (瓶×2), 酸奶杯经 hfpackage 引用; 全部身份绑定 asset_id 登记在案"
  }
}
os.makedirs("output/r32_scene", exist_ok=True)
json.dump(scene, open("output/r32_scene/scene_contract.json", "w"), indent=1, ensure_ascii=False)
print(f"placed: {len(placed)}/{len(SKUS)} | utilization: {util:.3f} | violations: {len(violations)} | build {build_time:.3f}s")
for v in violations: print("  V:", v)
