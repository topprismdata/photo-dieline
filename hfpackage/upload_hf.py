#!/usr/bin/env python3
"""Pack10K HF 发布脚本 — 需要 WRITE 角色_token。

用法: HF_WRITE_TOKEN=hf_xxx python upload_hf.py
(创建 hyperion911/pack10k-retail-twin dataset 仓并全量上传)
"""
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

HERE = Path(__file__).resolve().parent
REPO = "hyperion911/pack10k-retail-twin"


def main() -> int:
    tok = os.environ.get("HF_WRITE_TOKEN")
    if not tok:
        print("需要 HF_WRITE_TOKEN (Settings→Access Tokens→New token, 勾选 Write)")
        return 1
    api = HfApi(token=tok)
    api.create_repo(REPO, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(
        repo_id=REPO,
        repo_type="dataset",
        folder_path=str(HERE),
        commit_message="Pack10K v0.1: 4 families, physx PASS 15, GPT round4b 2/4 tie",
    )
    print(f"已发布: https://huggingface.co/datasets/{REPO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
