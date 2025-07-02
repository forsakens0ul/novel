import os
import re
from pathlib import Path

CHINESE_NUMERAL = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
}

def to_chinese_chapter(num: int) -> str:
    """返回"第一章"之类的中文章节编号字符串。支持到 99。"""
    if num <= 10:
        numeral = CHINESE_NUMERAL.get(num, str(num))
        return f"第{numeral}章"
    # 处理 11-99 的情况
    tens, ones = divmod(num, 10)
    result = ""
    if tens == 1:
        result += "十"
    else:
        result += CHINESE_NUMERAL.get(tens, str(tens)) + "十"
    if ones:
        result += CHINESE_NUMERAL.get(ones, str(ones))
    return f"第{result}章"

def sanitize_filename(name: str) -> str:
    """将章节标题转换为适合作为文件名的形式。"""
    # 替换非法/不便于文件名的字符
    return re.sub(r"[^\w一-龥]+", "_", name.strip())

def split_novel(src_path: Path, output_dir: Path):
    if not src_path.exists():
        raise FileNotFoundError(f"未找到源文件 {src_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 识别以下几种开头格式：
    # 1机甲维修师的生活
    # 2 那台奇怪的机甲
    # 第7章 神秘空间
    # 第8章 深渊之眼
    chapter_pattern = re.compile(r"^(?:第)?\s*(\d+)\s*(?:章)?\s*(.*)")

    with src_path.open(encoding="utf-8") as f:
        lines = f.readlines()

    chapters = []  # list[dict] -> {num, title, content:list[str]}
    current = None

    for line in lines:
        m = chapter_pattern.match(line)
        if m:
            # 遇到新的章节标题
            num = int(m.group(1))
            raw_title = m.group(2).strip()
            if not raw_title:
                title = "未命名"
            else:
                # 若包含顿号/逗号，将第一小段做标题
                title = re.split(r"[，,. 。]", raw_title)[0] or "未命名"

            if current:
                chapters.append(current)
            current = {
                "num": num,
                "title": title,
                "content": []
            }
            # 对于章节标题行，如果标题行还包含正文，需要把正文剩余部分加入内容
            remainder = raw_title[len(title):].lstrip("，,. 。")
            if remainder:
                current["content"].append(remainder + "\n")
        else:
            if current is None:
                # 文件开头没有章节数字的意外情况
                current = {"num": 0, "title": "前言", "content": []}
            current["content"].append(line)

    if current:
        chapters.append(current)

    # 写入每个章节 markdown
    combined_lines = []
    for chap in chapters:
        chap_num = chap["num"]
        chapter_head = f"# {to_chinese_chapter(chap_num)} {chap['title']}\n\n"
        file_name = f"{chap_num:02d}_{sanitize_filename(chap['title'])}.md"
        with (output_dir / file_name).open("w", encoding="utf-8") as fw:
            fw.write(chapter_head)
            fw.writelines(chap["content"])
        # 组合版
        combined_lines.append(chapter_head)
        combined_lines.extend(chap["content"])
        combined_lines.append("\n")  # 章节间空行

    # 写入全集合并文件
    with (output_dir / "novel.md").open("w", encoding="utf-8") as f_all:
        f_all.writelines(combined_lines)

    print(f"已生成 {len(chapters)} 个章节文件，以及合并文件 novel.md")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    src = base_dir / "1.txt"
    out = base_dir / "chapters"
    split_novel(src, out) 