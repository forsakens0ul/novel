"""auto_fill_novel.py

批量为 new_novel/ 目录中的占位章节调用 OpenAI GPT-4 续写正文。
运行前：
1. pip install openai tqdm
2. 将环境变量 OPENAI_API_KEY 设置为你的 API Key。

默认跳过已写入正文（>200 字）的文件。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List

import openai
from tqdm import tqdm

# 调整为需要的模型与温度
def request_completion(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 2048) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=max_tokens,
    )
    return response["choices"][0]["message"]["content"].strip()


def load_chapters(base_dir: Path) -> List[Path]:
    return sorted(base_dir.glob("[0-9][0-9]_*.md"))


def has_content(md_path: Path) -> bool:
    text = md_path.read_text(encoding="utf-8")
    # 粗略判断正文长度
    return len(re.sub(r"[#>\s]", "", text)) > 200  # 去除标题空白后计数


def build_prompt(md_path: Path, prev_path: Path | None) -> str:
    title_line = md_path.read_text(encoding="utf-8").splitlines()[0]
    title = title_line.lstrip("# ")
    prev_snippet = ""
    if prev_path and prev_path.exists():
        # 提取上一章最后 200 字作为上下文
        tail = prev_path.read_text(encoding="utf-8")[-400:]
        prev_snippet = f"上一章结尾片段：\n{tail}\n\n"
    prompt_parts = [
        '你是一位科幻小说作家，将延续前一章剧情，写出新章节全文。\n',
        f'{prev_snippet}请以 Markdown 返回，开头保留原有标题"{title}"。\n',
        '要求：\n',
        '1. 字数约 2800-3200。\n',
        '2. 保持量子科幻 × 国风意象 × 细节悬丝的风格。\n',
        '3. 主角名为"林序"，女主"岳影"。\n',
        '4. 章节结尾留悬念，暗示下一章标题。\n',
    ]
    return "".join(prompt_parts)


def main():
    novel_dir = Path(__file__).resolve().parent / "new_novel"
    if not novel_dir.exists():
        print("❌ 未找到 new_novel 目录！", file=sys.stderr)
        sys.exit(1)

    chapter_files = load_chapters(novel_dir)
    for idx, md in enumerate(tqdm(chapter_files, desc="processing")):
        if has_content(md):
            continue
        prev_md = chapter_files[idx - 1] if idx > 0 else None
        prompt = build_prompt(md, prev_md)
        try:
            content = request_completion(prompt)
        except Exception as e:
            print(f"⚠️ 生成 {md.name} 失败：{e}")
            break
        # 覆盖写入
        md.write_text(content, encoding="utf-8")
        print(f"✅ 写入 {md}")


if __name__ == "__main__":
    if "OPENAI_API_KEY" not in os.environ:
        print("请先设置 OPENAI_API_KEY 环境变量！", file=sys.stderr)
        sys.exit(1)
    main() 