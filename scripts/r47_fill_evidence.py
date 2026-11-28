"""R47: L3-01 证据包填充脚本 (用户 raw 值录入后运行一次)
输入: /tmp/r47_user_raw.json (用户回传的 raw 值)
输出: l3_01_evidence_pack_filled.json + dims_delta 计算表
纪律: raw_values 原样存档不可覆盖; 均值仅作展示字段; verdict 不在此脚本判定 (留 GPT 治理回路)
"""
import json, sys

RAW = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r47_user_raw.json"
raw = json.load(open(RAW))

pack = json.load(open("/Users/guohongbin/photo-dieline/docs/research/evidence/l3_01_evidence_pack.json"))

def mean3(vals):
    vals = [float(v) for v in vals]
    return round(sum(vals) / len(vals), 2)

# 填充链环1: 采购
pack["chain_link_1_real_product"]["purchase_status"] = "EXECUTED"
pack["chain_link_1_real_product"]["purchase_record_uri"] = raw.get("purchase_record_uri")

# 链环2: GTIN
pack["chain_link_2_identity"]["gtin"] = raw.get("gtin")
pack["chain_link_2_identity"]["gtin_status"] = "GTIN_VERIFIED" if raw.get("gtin") else "GTIN_UNVERIFIED"

# 链环3: 包装版本
pack["chain_link_3_package_version"]["version_evidence_uri"] = raw.get("package_version_photo_uri")
pack["chain_link_3_package_version"]["version_identified"] = raw.get("package_version_identified")

# 链环4: 测量 raw 值录入 (不可覆盖纪律: 原始数组原样保存)
mm = {}
for ev, key in (("EV-001_length_mm", "length"), ("EV-002_width_mm", "width"), ("EV-003_height_mm", "height")):
    pack["chain_link_4_raw_measurements"][ev]["raw_values"] = raw[key]
    mm[key] = mean3(raw[key])
pack["chain_link_4_raw_measurements"]["EV-004_full_mass_g"]["raw_values"] = raw["full_mass_g"]
pack["chain_link_4_raw_measurements"]["EV-005_empty_mass_g"]["raw_values"] = raw["empty_mass_g"]
mm["full_mass_g"] = mean3(raw["full_mass_g"])
mm["empty_mass_g"] = mean3(raw["empty_mass_g"])
pack["chain_link_4_raw_measurements"]["EV-006_slide_angle_deg"]["raw_values"] = raw["slide_angle_deg"]
mm["slide_angle_deg"] = mean3(raw["slide_angle_deg"])
pack["chain_link_4_raw_measurements"]["computed_means"] = mm

# 链环5: 印刷微距
pack["chain_link_5_print_macro"]["front_uri"] = raw.get("print_front_uri")
pack["chain_link_5_print_macro"]["back_uri"] = raw.get("print_back_uri")
pack["chain_link_5_print_macro"]["top_uri"] = raw.get("print_top_uri")

# 链环7: 差异计算 (实测均值 vs 资产声明 55/40/115)
declared = {"length": 55.0, "width": 40.0, "height": 115.0}
delta = {}
for k, dv in declared.items():
    m = mm[k]
    delta[k] = {"measured_mean_mm": m, "asset_declared_mm": dv,
                 "delta_mm": round(m - dv, 2), "delta_pct": round((m - dv) / dv * 100, 2)}
pack["chain_link_7_dims_delta"]["delta"] = delta
pack["chain_link_7_dims_delta"]["computed_at"] = "AI-side on raw receipt; verdict NOT set here"

# 链环8: verdict 保持 UNRESOLVED (GPT 治理回路裁决)
pack["chain_link_8_binding_verdict"]["verdict"] = "UNRESOLVED"
pack["chain_link_8_binding_verdict"]["note"] = "证据包已填充完整, verdict 留待 GPT 治理回路依据链环7差异计算裁决"

out = "/Users/guohongbin/photo-dieline/docs/research/evidence/l3_01_evidence_pack_filled.json"
json.dump(pack, open(out, "w"), indent=1, ensure_ascii=False)
print("FILLED:", out)
print("dims delta:", json.dumps(delta, ensure_ascii=False))
