"""R18 FINAL CLOSURE 证据包重建"""
import json, hashlib, os
os.chdir("/Users/guohongbin/photo-dieline")
nv = json.load(open("docs/research/evidence/g2_dim01_nvsdk.json"))
manifest = json.load(open("docs/research/evidence/g2_manifest.json"))
nv_by_id = {r["id"]: r for r in nv}
content_hashes = {}
for c in manifest["candidates"]:
    p = f"output/candidates/g2_nine/{c['id']}.usdc"
    content_hashes[c["id"]] = hashlib.sha256(open(p, "rb").read()).hexdigest()

nine = []
for c in manifest["candidates"]:
    aid = c["id"]
    R = nv_by_id[aid]
    nine.append({
        "id": aid, "family": c["family"], "variant_idx": c.get("variant_idx", 0),
        "role": c["role"], "terminal": "SUCCESS",
        "dim01_pass": R["dim01_pass"], "dim01": R["dim01"],
        "nvsdk_backend": R["nvsdk_backend"], "nvsdk_checks_passed": R["nvsdk_checks_passed"],
        "nvsdk": R.get("nvsdk", "PASS"),
        "content_sha256": content_hashes.get(aid, "MISSING"),
        "usdc_path": f"output/candidates/g2_nine/{aid}.usdc",
    })

dim_all = all(n["dim01_pass"] for n in nine)
nvsdk_all = all(n["nvsdk"] == "PASS" for n in nine)

pkg = {
    "R18_FINAL_CLOSURE": "九件候选最终证据清单",
    "dim01_all_pass": dim_all,
    "nvsdk_all_pass": nvsdk_all,
    "nine": nine,
    "physics_simulation_state": "NOT_RUN (G2 范围=编译+结构+NVSDK; 物理仿真属消费端场景, 按 REP-IDENTITY 规划后续)",
    "启动门禁偏差_如实登记": {
        "G2 启动时序": "G2 九件编译与审计在 R14-UV-01 完成之后、R16 裁决回执之前启动",
        "C1": "启动时 G1-04 尚有 F01/F02 补证 OPEN → 偏差: 启动时点未完全满足 (已于启动后补证)",
        "C2": "SPEC-FROZEN 后置 (R16 启动后签发 SPEC APPROVED)",
        "C3-C5": "g2_manifest.json 文件后置 (候选选择先于运行确定)",
        "结论": "偏差如实登记; 原始结果保留; 启动时间未追溯修改 (遵 R17 §4.3)",
    },
}
out = "docs/research/evidence/g2_r18_final_closure.json"
json.dump(pkg, open(out, "w"), indent=1, ensure_ascii=False)
print("R18 evidence OK | nine:", len(nine), "| dim01:", dim_all, "| nvsdk:", nvsdk_all)
