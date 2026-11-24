"""E4: QA 门变异矩阵 — 对 gable_top IR 做单点破坏, 看哪道门拦 (run_qa 全流程)."""
import copy, json, re
import numpy as np
from photo_dieline.core.ir import from_raw, build, validate_dict, ARError
from photo_dieline.qa.pipeline import run_qa
from photo_dieline.export import svg as svgx, pdf as pdfx
from photo_dieline.parametric import gable_top

def artifacts(raw):
    ir = from_raw(raw)
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    svg = svgx.render(ir, x1 - x0, y1 - y0)
    pdf = pdfx.build_pdf(ir, x1 - x0, y1 - y0)
    return ir, svg, pdf

def run(label, mut=None, post=None, params=None, spec_measure=None):
    raw = gable_top.build_ir(params)
    if mut: mut(raw)
    if spec_measure:  # 走 build(): spec.measurements 与 params 不一致 → 修复后应在入口被拒 (ARError)
        import tempfile, os
        from PIL import Image
        d = tempfile.mkdtemp(); ph = os.path.join(d, "p.png"); Image.new("RGB", (1200, 1600)).save(ph)
        try:
            ir = build({"measurements": spec_measure}, ph, raw)
        except ARError as exc:
            print(f"{label:<58} ARError (输入被拒): {str(exc)[:90]}"); return
        x0, y0, x1, y1 = svgx.net_bbox(ir); svg = svgx.render(ir, x1-x0, y1-y0)
        pdf = pdfx.build_pdf(ir, x1-x0, y1-y0)
    else:
        try:
            ir, svg, pdf = artifacts(raw)
        except Exception as exc:
            print(f"{label:<58} BUILD-EXC {type(exc).__name__}: {str(exc)[:70]}"); return
    if post: svg, pdf = post(svg, pdf)
    rep = run_qa(ir, svg, pdf)
    gs = " ".join(f"{g['id']}:{g['status'][:4]}" for g in rep["gates"])
    print(f"{label:<58} {rep['status']:<9} {gs}")

def set_tdir(eid, v):
    def m(raw):
        for e in raw["edges"]:
            if e["id"] == eid: e["fold"]["target_dir_3d"] = list(v)
    return m
def set_mt(eid, v):
    def m(raw):
        for e in raw["edges"]:
            if e["id"] == eid: e["fold"]["mt_va"] = v
    return m
def poly(pid):
    return lambda raw: next(p for p in raw["panels"] if p["id"] == pid)

print("baseline:"); run("  (none)")
print("\n-- (a) QA 应拦的折叠/闭合破坏 --")
run("glue tdir -> (-1,0,0)  [粘口折向盒外, 未贴合]", set_tdir("e_glue", (-1, 0, 0)))
run("flapB tdir -> (0,0,-1) [背底板下垂未折]", set_tdir("e_bk_fl", (0, 0, -1)))
run("flapL tdir -> (1,0,0)   [左底板折到墙外]", set_tdir("e_wl_fl", (1, 0, 0)))
run("flapR tdir -> (1,0,0)   [右底板折到墙外]", set_tdir("e_wr_fl", (1, 0, 0)))
run("finB tdir == finF tdir  [两鳍重合穿插]", set_tdir("e_sl_fb", (0, 0.107, 0.994)))
run("finB tdir -> (0,-1,0)   [鳍倒伏在背上]", set_tdir("e_sl_fb", (0, -1, 0)))
run("flapL 高 W/2 -> W       [左右底板穿插 22.5mm]",
    lambda r: [poly("flapL")(r)["polygon_2d"].__setitem__(i, [x, y*2]) for i, (x, y) in enumerate(list(poly("flapL")(r)["polygon_2d"])) if y < 0])
run("glue 宽 12 -> 2         [粘口宽错]", 
    lambda r: [poly("glue")(r)["polygon_2d"].__setitem__(i, [10.0, y]) for i, (x, y) in enumerate(list(poly("glue")(r)["polygon_2d"])) if x == 0.0])
print("\n-- (b) 参数域/证据 --")
run("fin_gap_mm=40 (Ef=14, 2*Ef=28 < 40) [超域被钳位]", params={"fin_gap_mm": 40.0})
run("Hr=0.001 / D=45         [近退化]", params={"Hr": 0.001})
run("W=nan", params={"W": float("nan")})
run("W=inf", params={"W": float("inf")})
run("params W=50 但 measurements W=45 MEASURED [值不一致]",
    spec_measure=[{"name": "W", "value_mm": 45.0, "status": "MEASURED"},
                  {"name": "D", "value_mm": 45.0, "status": "MEASURED"}], params={"W": 50.0})
print("\n-- (c) 折线语义 --")
run("全部 mt_va MOUNTAIN<->VALLEY 互换",
    lambda r: [e["fold"].__setitem__("mt_va", "VALLEY" if e["fold"]["mt_va"] == "MOUNTAIN" else "MOUNTAIN") for e in r["edges"]])
run("全部 mt_va -> SCORE", lambda r: [e["fold"].__setitem__("mt_va", "SCORE") for e in r["edges"]])
run("e_bk_sl tdir 加轴分量 (0.3,-0.88,0.47) [不垂直铰链]", set_tdir("e_bk_sl", (0.3, -0.88, 0.47)))
print("\n-- (d) 拓扑 --")
def overlap(r):  # front 左移 5mm 与 wallR 重叠
    p = poly("front")(r); p["polygon_2d"] = [[x - 5, y] for x, y in p["polygon_2d"]]
run("front 整体左移 5mm [与 wallR 面积重叠]", overlap)
def manifold(r):  # 加第三块板共享 wallL|back 折线
    r["panels"].append({"id": "extra", "role": "wall", "polygon_2d": [[57.0, 0], [102.0, 0], [102.0, 100], [57.0, 100]]})
    r["edges"].append({"id": "e_x", "kind": "FOLD", "seg_2d": [[57, 0], [57, 100]],
                       "fold": {"mt_va": "VALLEY", "parent": "back", "child": "extra", "target_dir_3d": [1, 0, 0]}})
run("第三块板共享 wallL|back 折线 [非流形: 3 面板共边]", manifold)
def dangling(r):  # 折线端点落在面板顶点上但子板不在折线另一侧 (折线为对角线)
    r["panels"].append({"id": "dg", "role": "wall", "polygon_2d": [[200, 0], [210, 0], [210, 100], [200, 100]]})
    r["edges"].append({"id": "e_dg", "kind": "FOLD", "seg_2d": [[200, 0], [210, 100]],
                       "fold": {"mt_va": "VALLEY", "parent": "dg", "child": "front", "target_dir_3d": [0, -1, 0]}})
run("front 改挂到悬空板的对角线 [悬空折线/错挂]", dangling)
def gap_panels(r):  # flapL 与 flapB 之间留 1mm 缝 (union 不连通)
    p = poly("flapL")(r); p["polygon_2d"] = [[x - 1, y] for x, y in p["polygon_2d"]]
def detach(r):  # finB 整体上移 1mm 与 slopeB 分离
    p = poly("finB")(r); p["polygon_2d"] = [[x, y + 1] for x, y in p["polygon_2d"]]
run("finB 上移 1mm [网断开, 折线悬空]", detach)
print("\n-- (e) 导出物 --")
run("SVG width/height/viewBox 全部缩半 (非 1:1)", post=lambda s, p: (re.sub(r'width="([\d.]+)mm" height="([\d.]+)mm"\n viewBox="0 0 ([\d.]+) ([\d.]+)"',
    lambda m: f'width="{float(m.group(1))/2}mm" height="{float(m.group(2))/2}mm"\n viewBox="0 0 {float(m.group(3))/2} {float(m.group(4))/2}"', s), p))
run("SVG 所有几何清空, 只留 <g id> 与一条 0.3 线", post=lambda s, p: (re.sub(r"<g id=\"(\w[\w-]*)\">.*?</g>",
    lambda m: f'<g id="{m.group(1)}"></g>' if m.group(1) != "INFO" else '<g id="INFO"><line stroke-width="0.3"/></g>', s, flags=re.S), p))
run("SVG CUT 层内容换成折线 (语义互换)", post=lambda s, p: (s.replace('id="CUT"', 'id="TMP"').replace('id="CREASE-VALLEY"', 'id="CUT"').replace('id="TMP"', 'id="CREASE-VALLEY"'), p))
run("SVG 删除 50mm 校验条", post=lambda s, p: (re.sub(r'<line x1="12\.000" y1="8\.000" x2="62\.000" y2="8\.000"[^>]*/>', '', s), p))
run("SVG 校验条改 40mm", post=lambda s, p: (s.replace('x2="62.000" y2="8.000"', 'x2="52.000" y2="8.000"'), p))
print("\n-- (f) PDF 篡改 (重压缩内容流) --")
import zlib
def rebuild_pdf(s, mutate):
    st = re.search(rb"stream\n(.*?)\nendstream", s, re.S)
    rawc = zlib.decompress(st.group(1)).decode("latin-1"); new = mutate(rawc)
    comp = zlib.compress(new.encode("latin-1"))
    return s[:st.start(1)] + comp + s[st.end(1):]
run("PDF 校验条 50mm -> 40mm", post=lambda s, p: (s, rebuild_pdf(p, lambda c: c.replace("174.8031 22.6772 l", "146.4567 22.6772 l"))))
run("PDF 内容流清空 (只剩 INFO 文本, MediaBox/OCG 不动)", post=lambda s, p: (s, rebuild_pdf(p, lambda c: c[c.find("BT"):])))
run("PDF MediaBox 改成 A4 (内容不变)", post=lambda s, p: (s, re.sub(rb"/MediaBox \[0 0 [\d.]+ [\d.]+\]", b"/MediaBox [0 0 595.28 841.89]", p)))
run("PDF 内容流整体缩半 (内容仍含一条 50mm 线以外的几何)", post=lambda s, p: (s, rebuild_pdf(p, lambda c: c.replace("174.8031 22.6772 l", "174.8031 22.6772 l").replace("/P1 BDC", "/P1 BDC\n0.5 0 0 0.5 0 0 cm"))))
run("PDF 内容流加 0.5 缩放 cm (在最前, 校验条实际 25mm)", post=lambda s, p: (s, rebuild_pdf(p, lambda c: "0.5 0 0 0.5 0 0 cm\n" + c)))
