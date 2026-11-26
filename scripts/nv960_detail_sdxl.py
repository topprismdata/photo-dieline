#!/tmp/sdvenv/bin/python3
"""NV960 parity 细节增强 pass (SD1.5 img2img, MPS)。

用法: python3 nv960_detail_sdxl.py <img> [<img>...] [--strength 0.35]
基模: SG161222/Realistic_Vision_V5.1_noVAE (本地缓存); LoRA: Lykon/detail-tweaker-lora
内容保全: 低 denoise + lineart 保形; 仅提高频细节密度。
"""
import argparse
import sys
from pathlib import Path

import torch
from diffusers import AutoPipelineForImage2Image, DPMSolverMultistepScheduler
from PIL import Image

BASE = "SG161222/Realistic_Vision_V5.1_noVAE"
LORA = "Lykon/detail-tweaker-lora"
POS = ("retail equipment product photograph, studio lighting, extremely detailed surface texture, "
       "crisp material edges, fine mechanical details, sharp focus, professional catalog photo")
NEG = ("blurry, soft focus, low contrast, cartoon, painting, deformed, watermark, text overlay")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--strength", type=float, default=0.35)
    ap.add_argument("--guidance", type=float, default=5.0)
    a = ap.parse_args()

    pipe = AutoPipelineForImage2Image.from_pretrained(BASE, torch_dtype=torch.float32, safety_checker=None)
    try:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    except Exception as e:  # noqa: BLE001
        print(f"调度器替换跳过(用默认): {e}", file=sys.stderr)
    try:
        pipe.load_lora_weights(LORA, weight_name="detail_tweaker_lora.safetensors")
        pipe.cross_attention_kwargs = {"scale": 1.2}
    except Exception as e:  # noqa: BLE001
        print(f"LoRA 加载失败(继续无LoRA): {e}", file=sys.stderr)
    pipe.enable_attention_slicing(4)
    pipe.enable_vae_slicing()
    pipe = pipe.to("mps")
    pipe.set_progress_bar_config(disable=True)

    for p in a.images:
        src = Path(p)
        im = Image.open(src).convert("RGB").resize((1024, 1024), Image.LANCZOS)
        g = torch.Generator("mps").manual_seed(42)
        with torch.inference_mode():
            out = pipe(prompt=POS, negative_prompt=NEG, image=im, strength=a.strength,
                       guidance_scale=a.guidance, num_inference_steps=28, generator=g).images[0]
        out.save(src)
        print(f"增强完成: {src.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
