#!/usr/bin/env python3
"""Build the first-pass Chapter 2–9 import from saved page OCR.

The protected output must stay outside web/ and git. OCR is navigation/search aid;
the scan image remains the source of truth. Any uncertain transcription is marked.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SOURCE_SHA256 = "ee154022841f3bc72695cb9ba687d8dcd5460dea42e4d8521a0ec8e631416588"

# (chapter, section, section title, section end, [(point title, printed page, zero-based OCR line)])
OUTLINE = [
    (2, 1, "课程与课程理论", 70, [
        ("课程的词源、定义及作用", 64, 2), ("制约课程的主要因素", 65, 6),
        ("课程的类型", 65, 13), ("课程理论流派", 68, 8),
        ("强化练习与要点回顾", 69, 14),
    ]),
    (2, 2, "课程设计与开发", 79, [
        ("课程设计与开发概述", 71, 2), ("课程目标", 72, 12),
        ("课程内容", 73, 6), ("课程实施", 75, 21), ("课程评价", 76, 26),
        ("强化练习与要点回顾", 77, 7),
    ]),
    (2, 3, "基础教育课程改革", 88, [
        ("基础教育课程改革概述", 80, 2), ("基础教育课程改革的具体目标", 80, 6),
        ("基础教育课程改革的具体内容", 81, 8), ("强化练习与要点回顾", 87, 5),
    ]),
    (3, 1, "教学概述", 93, [
        ("教学的含义", 90, 3), ("教学的意义", 90, 27),
        ("教学的作用", 91, 16), ("教学的一般任务", 91, 28),
        ("强化练习与要点回顾", 92, 15),
    ]),
    (3, 2, "教学过程", 101, [
        ("教学过程的本质", 94, 3), ("教学过程的基本规律", 95, 7),
        ("教学过程的基本阶段", 98, 30), ("强化练习与要点回顾", 99, 25),
    ]),
    (3, 3, "教学工作的基本环节", 107, [
        ("备课", 102, 4), ("上课", 103, 1),
        ("课外作业的布置与批改", 104, 1), ("课外辅导", 104, 23),
        ("学生学业成绩的检查与评定", 105, 1), ("强化练习与要点回顾", 106, 5),
    ]),
    (3, 4, "教学原则", 115, [
        ("教学原则概述", 108, 2), ("中学常用的教学原则", 108, 6),
        ("强化练习与要点回顾", 114, 1),
    ]),
    (3, 5, "教学方法", 122, [
        ("教学方法概述", 116, 2), ("中学常用的教学方法", 116, 5),
        ("选择教学方法的基本依据", 121, 14), ("强化练习与要点回顾", 121, 19),
    ]),
    (3, 6, "教学模式", 126, [
        ("教学模式概述", 123, 2), ("常见的教学模式", 123, 6),
        ("我国主要的教学模式", 124, 16), ("当代教学模式的尝试与变革", 125, 1),
        ("强化练习与要点回顾", 125, 17),
    ]),
    (3, 7, "教学组织形式", 132, [
        ("教学组织形式概述", 127, 2), ("古代教学的基本组织形式——个别教学", 127, 4),
        ("现代教学组织形式", 127, 15), ("其他教学组织形式", 128, 24),
        ("强化练习与要点回顾", 130, 21),
    ]),
    (3, 8, "教学评价", 136, [
        ("教学评价概述", 133, 2), ("教学评价的类型", 133, 7),
        ("强化练习与要点回顾", 135, 19),
    ]),
    (4, 1, "学习的认知基础", 165, [
        ("注意", 138, 4), ("感觉", 141, 7), ("知觉", 143, 19),
        ("记忆", 146, 16), ("思维", 152, 32), ("表象与想象", 162, 1),
        ("强化练习与要点回顾", 163, 14),
    ]),
    (4, 2, "学习概述", 177, [
        ("学习的概念与分类", 166, 2), ("知识的学习", 168, 30),
        ("技能的学习", 172, 30), ("强化练习与要点回顾", 175, 12),
    ]),
    (4, 3, "学习理论", 190, [
        ("行为主义学习理论", 178, 2), ("认知学习理论", 182, 5),
        ("建构主义学习理论", 185, 26), ("人本主义学习理论", 187, 1),
        ("强化练习与要点回顾", 188, 11),
    ]),
    (4, 4, "学习动机", 201, [
        ("学习动机的含义与功能", 191, 2), ("学习动机的分类", 192, 2),
        ("学习动机与学习效率的关系", 193, 28), ("学习动机理论", 194, 22),
        ("学习动机的培养与激发", 199, 27), ("强化练习与要点回顾", 200, 9),
    ]),
    (4, 5, "学习迁移", 209, [
        ("学习迁移的分类", 202, 5), ("学习迁移理论", 204, 1),
        ("影响学习迁移的因素", 206, 2), ("促进学习迁移的教学", 207, 8),
        ("强化练习与要点回顾", 207, 25),
    ]),
    (4, 6, "学习策略", 216, [
        ("认知策略", 210, 5), ("元认知策略", 212, 15),
        ("资源管理策略", 213, 9), ("强化练习与要点回顾", 215, 1),
    ]),
    (5, 1, "中学生心理发展的基本特征和一般特点", 220, [
        ("中学生心理发展的基本特征", 218, 5),
        ("中学生心理发展的一般特点", 218, 23), ("强化练习与要点回顾", 219, 26),
    ]),
    (5, 2, "中学生认知的发展", 229, [
        ("中学生认知发展的特点", 221, 3), ("皮亚杰的认知发展阶段论", 222, 14),
        ("维果斯基的心理发展观", 227, 3), ("强化练习与要点回顾", 228, 16),
    ]),
    (5, 3, "中学生情绪情感和意志的发展", 239, [
        ("中学生情绪情感的发展", 230, 2), ("中学生意志的发展", 235, 25),
        ("强化练习与要点回顾", 238, 11),
    ]),
    (5, 4, "中学生人格的发展", 253, [
        ("人格的特征及影响因素", 240, 4), ("人格的结构", 242, 12),
        ("认知风格", 245, 17), ("人格理论", 247, 25),
        ("强化练习与要点回顾", 251, 25),
    ]),
    (5, 5, "中学生能力的发展", 258, [
        ("一般能力与特殊能力", 254, 3), ("智力结构理论", 254, 11),
        ("能力发展的差异与影响因素", 255, 22), ("强化练习与要点回顾", 257, 10),
    ]),
    (5, 6, "中学生自我意识的发展", 261, [
        ("自我意识的结构", 259, 4), ("中学生自我意识发展的特点", 260, 19),
        ("强化练习与要点回顾", 261, 5),
    ]),
    (5, 7, "中学生交往指导", 264, [
        ("中学生的同伴关系", 262, 2), ("中学生的性心理", 262, 16),
        ("中学生异性交往的指导", 263, 7), ("强化练习与要点回顾", 264, 1),
    ]),
    (6, 1, "中学生的心理健康", 271, [
        ("心理健康的概念", 266, 2), ("心理健康的标准", 266, 7),
        ("学生心理健康问题的主要表现", 266, 26), ("中学生常见的心理问题", 267, 14),
        ("学校心理健康教育", 270, 7), ("强化练习与要点回顾", 270, 26),
    ]),
    (6, 2, "学校心理辅导", 278, [
        ("学校心理辅导的一般目标", 272, 2), ("学校心理辅导的原则", 272, 6),
        ("学校心理辅导的方法", 273, 18), ("强化练习与要点回顾", 277, 8),
    ]),
    (6, 3, "压力与挫折", 282, [
        ("压力", 279, 2), ("挫折", 280, 1), ("强化练习与要点回顾", 281, 26),
    ]),
    (7, 1, "品德的心理结构与道德发展理论", 290, [
        ("品德的内涵", 284, 2), ("品德的心理结构", 284, 7),
        ("皮亚杰的道德发展理论", 285, 13), ("柯尔伯格的道德发展理论", 286, 29),
        ("强化练习与要点回顾", 288, 22),
    ]),
    (7, 2, "中学生品德的形成与发展", 295, [
        ("中学生品德发展的特点", 291, 2), ("品德形成的一般过程", 291, 17),
        ("影响品德形成与发展的因素", 292, 15), ("促进中学生形成良好品德的方法", 293, 8),
        ("强化练习与要点回顾", 294, 16),
    ]),
    (7, 3, "德育的概念与内容", 299, [
        ("德育的概念", 296, 2), ("学校德育的内容", 296, 21),
        ("新时期德育发展的新主题", 298, 3), ("强化练习与要点回顾", 298, 21),
    ]),
    (7, 4, "德育过程", 304, [
        ("德育过程的内涵", 300, 2), ("德育过程与品德形成过程的关系", 300, 8),
        ("德育过程的构成要素", 300, 25), ("德育过程的矛盾", 301, 10),
        ("德育过程的基本规律", 301, 16), ("强化练习与要点回顾", 303, 8),
    ]),
    (7, 5, "德育的原则、途径与方法", 314, [
        ("德育原则", 305, 2), ("德育途径", 308, 15), ("德育方法", 309, 21),
        ("强化练习与要点回顾", 312, 30),
    ]),
    (8, 1, "班集体与班级管理", 320, [
        ("班级与班集体", 316, 2), ("班集体的形成与培养", 316, 21),
        ("班级管理", 318, 9), ("强化练习与要点回顾", 319, 26),
    ]),
    (8, 2, "课堂管理", 331, [
        ("课堂管理概述", 321, 2), ("课堂群体关系管理", 322, 1),
        ("课堂气氛管理", 323, 19), ("课堂纪律管理", 325, 15),
        ("课堂问题行为", 327, 21), ("强化练习与要点回顾", 330, 16),
    ]),
    (8, 3, "班主任工作", 338, [
        ("班主任概述", 332, 2), ("班主任应具备的基本条件", 333, 31),
        ("班主任工作的基本内容与方法", 334, 12), ("强化练习与要点回顾", 337, 4),
    ]),
    (8, 4, "课外活动", 342, [
        ("课外活动的概念与意义", 339, 2), ("课外活动的主要内容", 339, 11),
        ("课外活动的组织形式", 340, 7), ("课外活动的特点", 340, 20),
        ("课外活动组织管理的要求", 341, 12), ("强化练习与要点回顾", 341, 17),
    ]),
    (8, 5, "教师心理", 354, [
        ("教师的角色心理", 343, 2), ("教师的心理特征", 347, 1),
        ("教师的成长心理", 349, 1), ("教师的心理健康", 351, 3),
        ("强化练习与要点回顾", 353, 15),
    ]),
    (9, 1, "辨析题备考攻略", 363, [
        ("辨析题题型介绍", 356, 2), ("辨析题考查特点", 356, 7),
        ("辨析题作答思路", 357, 23), ("辨析题分类解读", 358, 6),
        ("辨析题考点预测", 360, 27), ("强化练习与参考答案", 362, 23),
    ]),
    (9, 2, "简答题备考攻略", 368, [
        ("简答题题型介绍", 364, 2), ("简答题考查特点", 364, 6),
        ("简答题分类解读", 365, 4), ("简答题考点预测", 366, 15),
        ("强化练习与参考答案", 368, 8),
    ]),
    (9, 3, "材料分析题备考攻略", 376, [
        ("材料分析题题型介绍", 369, 2), ("材料分析题考查特点", 369, 5),
        ("评做法类材料分析题", 369, 20), ("分析观点、问题或原因类材料分析题", 371, 18),
        ("提措施或建议类材料分析题", 373, 8), ("材料分析题考点预测", 374, 29),
        ("强化练习与参考答案", 375, 10),
    ]),
]


def load_page(ocr_dir: Path, printed_page: int) -> dict:
    path = ocr_dir / f"{printed_page + 4:03}.json"
    if not path.exists():
        raise FileNotFoundError(f"missing OCR page: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def is_running_header(text: str, printed_page: int) -> bool:
    compact = re.sub(r"\s+", "", text)
    return str(printed_page) in compact and (
        "教育知识与能力" in compact or "中学教学" in compact or
        "中学课程" in compact or "中学生" in compact
    )


def uncertain(text: str, confidence: float) -> bool:
    sensitive = re.search(r"(18|19|20)\d{2}|代表人物|提出|创立|著作|理论|学说|定义|是指|称为", text)
    suspicious = re.search(r"[A-Z]{3,}|[a-zA-Z]{2,}[^a-zA-Z\d\s.,()%-]", text)
    return confidence < 0.88 or (sensitive and confidence < 0.95) or bool(suspicious)


def item_type(text: str) -> str:
    clean = text.removeprefix("【待核对】").strip()
    if re.match(r"^[一二三四五六七八九十]+、", clean):
        return "h2"
    if re.match(r"^[（(][一二三四五六七八九十]+[）)]", clean):
        return "h3"
    if re.match(r"^\d+[.、]", clean):
        return "list"
    if re.match(r"^[A-DＡ-Ｄ][.、，,]", clean):
        return "option"
    if "考频" in clean or "考点" in clean or "强化练习" in clean or "要点回顾" in clean:
        return "callout"
    return "p"


def page_items(data: dict, start_line: int, end_line: int | None) -> list[dict]:
    raw = data["lines"][start_line:end_line]
    items = []
    for line in raw:
        text = re.sub(r"\s+", " ", line["text"]).strip()
        if not text or is_running_header(text, data["printed_page"]):
            continue
        confidence = float(line.get("confidence", 0))
        if uncertain(text, confidence):
            text = "【待核对】" + text
        items.append({"type": item_type(text), "text": text})
    return items


def evidence(items: list[dict]) -> list[str]:
    candidates = []
    for item in items:
        text = item["text"]
        if text.startswith("【待核对】") or item["type"] in {"option", "callout"}:
            continue
        if re.search(r"答案|解析|强化练习|要点回顾|单选|辨析", text):
            continue
        plain = re.sub(r"^[一二三四五六七八九十\d（）().、]+", "", text).strip()
        if len(plain) >= 12:
            candidates.append(plain[:90])
        if len(candidates) == 3:
            break
    return candidates


def aids(title: str, snippets: list[str]) -> tuple[str, str, str]:
    if "强化练习" in title:
        return (
            "先遮住答案独立作答，再回到对应知识点定位依据。错题要记录错因：概念混淆、条件遗漏、人物或理论对应错误。",
            "把错题反查到定义、特征和适用情境；第二轮复习只重做错误与模糊题。",
            "不要用OCR转写中的答案替代独立作答；题干、选项和年份若标有待核对，须查看原页。",
        )
    focus = "、".join(snippets[:2]) if snippets else "概念、层级、条件和典型情境"
    return (
        f"学习“{title}”时，先沿教材层级找出定义、分类或构成，再用中学教育情境检验能否辨认。原页可用于核对这些线索：{focus}。本段为AI辅助梳理。",
        f"优先掌握“{title}”的规范表述、辨别依据和适用条件。客观题常考概念或人物理论对应，主观题重在分点作答并结合材料。",
        "不要只背标题或凭常识扩写。不同分类维度不能混用；人名、年份、理论名称以及标有“待核对”的转写必须回看教材原页。",
    )


def questions(point_id: str, title: str, snippets: list[str]) -> list[dict]:
    clue = snippets[0] if snippets else f"教材原页中关于“{title}”的定义、特征与条件"
    rubric = "；".join(snippets) if snippets else "写出教材中的核心概念、分点要素和适用条件，并以原页核对"
    return [
        {
            "id": f"{point_id}q1", "type": "choice", "label": "AI生成·首轮练习",
            "prompt": f"复习“{title}”时，下列哪一项是本知识点原页中的直接线索？",
            "options": [clue, "该知识点无需区分概念与适用条件", "只凭标题即可替代教材规范表述", "OCR转写比扫描原页具有更高优先级"],
            "answer": "A",
        },
        {
            "id": f"{point_id}q2", "type": "judgement", "label": "AI生成·首轮练习",
            "prompt": f"学习“{title}”时，若转写标有“待核对”，应以教材扫描原页为最终依据。",
            "options": ["正确", "错误"], "answer": "正确",
        },
        {
            "id": f"{point_id}q3", "type": "short", "label": "AI生成·首轮练习",
            "prompt": f"依据教材原页，分点概括“{title}”的核心内容。",
            "rubric": f"评分要点（须以原页复核）：{rubric}",
        },
        {
            "id": f"{point_id}q4", "type": "material", "label": "AI生成·首轮练习",
            "prompt": f"材料：一名同学复习“{title}”时只记标题，未区分概念、条件和情境。请依据教材指出其复习缺口，并给出改进方案。",
            "rubric": "指出缺少规范概念与辨别依据；按教材层级补齐要点；结合一个中学教育情境说明；对人名、年份、理论名和待核对转写回看原页。",
        },
    ]


def build(ocr_dir: Path, selected_chapters: set[int], source_sha256: str) -> tuple[list[dict], list[dict]]:
    catalog, contents = [], []
    chapter_sections: dict[int, set[int]] = {}
    for chapter, section, _, section_end, points in OUTLINE:
        if chapter not in selected_chapters:
            continue
        chapter_sections.setdefault(chapter, set()).add(section)
        for point_index, (title, start_page, start_line) in enumerate(points, 1):
            if point_index < len(points):
                _, next_page, next_line = points[point_index]
            else:
                next_page, next_line = section_end + 1, 0
            end_page = next_page if next_line else next_page - 1
            point_id = f"c{chapter}s{section}p{point_index}"
            blocks, flat_items = [], []
            for printed_page in range(start_page, end_page + 1):
                data = load_page(ocr_dir, printed_page)
                lo = start_line if printed_page == start_page else 0
                hi = next_line if printed_page == next_page else None
                items = page_items(data, lo, hi)
                if not items:
                    continue
                blocks.append({
                    "type": "page", "page": printed_page, "pdf_page": printed_page + 4,
                    "source_lines": [x["text"] for x in data["lines"][lo:hi]], "items": items,
                })
                flat_items.extend(items)
            if not blocks:
                raise ValueError(f"empty point {point_id}: {title}")
            snippets = evidence(flat_items)
            explanation, exam, pitfalls = aids(title, snippets)
            catalog.append({
                "id": point_id, "parent_id": f"c{chapter}s{section}", "kind": "point",
                "title": title, "page_start": start_page, "page_end": end_page,
                "sort_order": chapter * 10000 + section * 100 + point_index, "ready": True,
            })
            contents.append({
                "id": point_id, "blocks": blocks, "explanation": explanation, "exam": exam,
                "pitfalls": pitfalls, "questions": questions(point_id, title, snippets),
                "verification": "本章按扫描原页完成首轮数字化；低置信度及可能误识别的人名、年份、理论名和定义已标“待核对”，扫描原页为最高优先级依据。",
                "source_sha256": source_sha256,
            })
    return catalog, contents


def validate(catalog: list[dict], contents: list[dict]) -> None:
    assert len(catalog) == len(contents)
    assert len({x["id"] for x in catalog}) == len(catalog)
    assert {x["id"] for x in catalog} == {x["id"] for x in contents}
    for row in contents:
        assert row["blocks"] and all(b["items"] for b in row["blocks"])
        assert [q["type"] for q in row["questions"]] == ["choice", "judgement", "short", "material"]
        assert all(q["id"].startswith(row["id"]) for q in row["questions"])


def sql_literal_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''")


def write_sql(output_dir: Path, catalog: list[dict], contents: list[dict]) -> None:
    catalog_json = sql_literal_json(catalog)
    parent_ids = sorted({row["parent_id"] for row in catalog} | {row["parent_id"].split("s")[0] for row in catalog})
    parent_array = ",".join("'" + value.replace("'", "''") + "'" for value in parent_ids)
    catalog_sql = f"""begin;
insert into public.tq_catalog(id,parent_id,kind,title,sort_order,page_start,page_end,ready)
select id,parent_id,kind,title,sort_order,page_start,page_end,ready
from jsonb_to_recordset('{catalog_json}'::jsonb)
as x(id text,parent_id text,kind text,title text,sort_order int,page_start int,page_end int,ready boolean)
on conflict(id) do update set parent_id=excluded.parent_id,kind=excluded.kind,title=excluded.title,
sort_order=excluded.sort_order,page_start=excluded.page_start,page_end=excluded.page_end,ready=excluded.ready;
update public.tq_catalog set ready=true where id = any(array[{parent_array}]::text[]);
commit;
"""
    (output_dir / "000_catalog.sql").write_text(catalog_sql, encoding="utf-8")
    for offset in range(0, len(contents), 6):
        chunk = contents[offset:offset + 6]
        payload = sql_literal_json(chunk)
        sql = f"""begin;
insert into public.tq_content(id,blocks,explanation,exam,pitfalls,questions,verification,source_sha256)
select id,blocks,explanation,exam,pitfalls,questions,verification,source_sha256
from jsonb_to_recordset('{payload}'::jsonb)
as x(id text,blocks jsonb,explanation text,exam text,pitfalls text,questions jsonb,verification text,source_sha256 text)
on conflict(id) do update set blocks=excluded.blocks,explanation=excluded.explanation,exam=excluded.exam,
pitfalls=excluded.pitfalls,questions=excluded.questions,verification=excluded.verification,
source_sha256=excluded.source_sha256;
commit;
"""
        (output_dir / f"{offset // 6 + 1:03}_content.sql").write_text(sql, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ocr_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--chapters", type=int, nargs="+", default=list(range(2, 10)))
    parser.add_argument("--source-sha256", default=SOURCE_SHA256)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selected_chapters = set(args.chapters)
    if not selected_chapters <= set(range(2, 10)):
        parser.error("chapters must be between 2 and 9")
    if not re.fullmatch(r"[0-9a-f]{64}", args.source_sha256):
        parser.error("source SHA-256 must contain 64 lowercase hexadecimal characters")
    catalog, contents = build(args.ocr_dir, selected_chapters, args.source_sha256)
    validate(catalog, contents)
    (args.output_dir / "catalog_remaining.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    (args.output_dir / "content_remaining.json").write_text(json.dumps(contents, ensure_ascii=False), encoding="utf-8")
    write_sql(args.output_dir, catalog, contents)
    summary = {
        "points": len(contents),
        "chapters": sorted({int(x["id"][1]) for x in catalog}),
        "pages": [min(x["page_start"] for x in catalog), max(x["page_end"] for x in catalog)],
        "questions": sum(len(x["questions"]) for x in contents),
        "uncertain_lines": sum(
            item["text"].startswith("【待核对】")
            for row in contents for block in row["blocks"] for item in block["items"]
        ),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
