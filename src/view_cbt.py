# -*- coding: utf-8 -*-
"""CBT 모드 (연습/실전). 실제 기출문제(source='cbt')만 대상으로 한다."""
import flet as ft

import db
import logic
from ui_common import ACCENT, CORRECT_COLOR, WRONG_COLOR, pill, section_title, subject_filter_row

PRACTICE_LIMIT = 10


def _mode_row(ctx):
    s = ctx.state

    def pick(mode):
        def _click(e):
            s.cbt_mode = mode
            s.cbt_pool = []
            s.cbt_answers = {}
            s.cbt_checked = {}
            s.cbt_submitted = False
            ctx.render()
        return _click

    def btn(label, mode):
        selected = s.cbt_mode == mode
        return ft.FilledButton(
            content=label, on_click=pick(mode),
            style=ft.ButtonStyle(bgcolor=ACCENT if selected else "#E5E7EB", color="#FFFFFF" if selected else "#374151"),
        )

    return ft.Row([btn("연습", "연습"), btn("실전", "실전")], spacing=8)


def _start_practice(ctx, subject_key):
    s = ctx.state
    s.cbt_subject = subject_key
    subjects = [1, 2, 3] if subject_key == "전체" else [int(subject_key)]
    s.cbt_pool = logic.pick_cbt_pool(ctx.questions, ctx.cbt_ids, subjects, limit=PRACTICE_LIMIT)
    s.cbt_answers = {}
    s.cbt_checked = {}
    ctx.render()


def _start_exam(ctx):
    s = ctx.state
    s.cbt_pool = logic.pick_cbt_exam_pool(ctx.questions, ctx.cbt_ids)
    s.cbt_answers = {}
    s.cbt_checked = {}
    s.cbt_submitted = False
    ctx.render()


def build(ctx):
    s = ctx.state
    controls = [section_title("CBT 모드"), ft.Container(height=6), _mode_row(ctx), ft.Container(height=10)]

    if s.cbt_mode == "연습":
        controls.extend(_build_practice(ctx))
    else:
        controls.extend(_build_exam(ctx))
    return controls


def _question_block(ctx, qid, radio_refs, checked_map):
    q = ctx.questions[qid]
    choices = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]]
    prev_val = ctx.state.cbt_answers.get(qid)
    rg = ft.RadioGroup(
        value=str(prev_val) if prev_val is not None else None,
        content=ft.Column([ft.Radio(value=str(i), label=f"{'①②③④'[i]} {c}") for i, c in enumerate(choices)]),
    )
    radio_refs[qid] = rg

    block = [
        ft.Row([pill(logic.SUBJECT_LABEL[q["subject"]]), pill(q["tag"], color="#9CA3AF")], spacing=6, wrap=True),
        ft.Text(q["question"], size=15, weight=ft.FontWeight.W_600),
        rg,
    ]

    if checked_map.get(qid):
        chosen = ctx.state.cbt_answers.get(qid)
        is_correct = chosen is not None and (chosen + 1) == q["answer"]
        color = CORRECT_COLOR if is_correct else WRONG_COLOR
        text = "정답!" if is_correct else f"오답 · 정답: {'①②③④'[q['answer'] - 1]} {choices[q['answer'] - 1]}"
        block.append(ft.Container(content=ft.Text(text, color="#FFFFFF", size=13), bgcolor=color, padding=8, border_radius=6))
        block.append(ft.Text(q["explanation"], size=12, color="#374151"))

    return ft.Container(
        content=ft.Column(block, spacing=6),
        padding=12, bgcolor="#F9FAFB", border_radius=10, margin=ft.Margin(0, 0, 0, 10),
    )


def _build_practice(ctx):
    s = ctx.state
    if not s.cbt_pool:
        return [
            ft.Text("과목을 선택하면 실제 기출문제 10문항을 풀어볼 수 있어요.", size=13, color="#6B7280"),
            ft.Container(height=8),
            subject_filter_row(s.cbt_subject, lambda v: _start_practice(ctx, v)),
        ]

    radio_refs = {}
    blocks = [_question_block(ctx, qid, radio_refs, s.cbt_checked) for qid in s.cbt_pool]

    def check_one(qid):
        def _click(e):
            rg = radio_refs[qid]
            if rg.value is None:
                return
            chosen = int(rg.value)
            s.cbt_answers[qid] = chosen
            if not s.cbt_checked.get(qid):
                is_correct = (chosen + 1) == ctx.questions[qid]["answer"]
                db.record_attempt(ctx.con, ctx.user, qid, chosen + 1, is_correct)
            s.cbt_checked[qid] = True
            ctx.render()
        return _click

    for i, qid in enumerate(s.cbt_pool):
        blocks[i].content.controls.append(
            ft.OutlinedButton(content="정답 확인", on_click=check_one(qid), disabled=s.cbt_checked.get(qid, False))
        )

    def grade_all(e):
        for qid in s.cbt_pool:
            rg = radio_refs[qid]
            if rg.value is None:
                continue
            chosen = int(rg.value)
            s.cbt_answers[qid] = chosen
            if not s.cbt_checked.get(qid):
                is_correct = (chosen + 1) == ctx.questions[qid]["answer"]
                db.record_attempt(ctx.con, ctx.user, qid, chosen + 1, is_correct)
            s.cbt_checked[qid] = True
        ctx.render()

    correct_n = sum(
        1 for qid in s.cbt_pool
        if s.cbt_checked.get(qid) and s.cbt_answers.get(qid) is not None and (s.cbt_answers[qid] + 1) == ctx.questions[qid]["answer"]
    )
    checked_n = sum(1 for qid in s.cbt_pool if s.cbt_checked.get(qid))

    out = list(blocks)
    out.append(ft.Row([
        ft.ElevatedButton(content="전체 채점", on_click=grade_all, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
        ft.OutlinedButton(content="새 문제 세트", on_click=lambda e: _start_practice(ctx, s.cbt_subject)),
    ], spacing=8))
    if checked_n:
        out.append(ft.Text(f"채점 결과 {correct_n}/{checked_n}", size=14, weight=ft.FontWeight.W_600))
    return out


def _build_exam(ctx):
    s = ctx.state
    if not s.cbt_pool:
        return [
            ft.Text(
                f"실제 출제 기준과 동일하게 총 {sum(logic.EXAM_SUBJECT_COUNTS.values())}문항"
                f"(1과목 {logic.EXAM_SUBJECT_COUNTS[1]} · 2과목 {logic.EXAM_SUBJECT_COUNTS[2]} · 3과목 {logic.EXAM_SUBJECT_COUNTS[3]})"
                "을 실전처럼 풀어봅니다.",
                size=13, color="#6B7280",
            ),
            ft.Container(height=8),
            ft.ElevatedButton(content="실전 시작", on_click=lambda e: _start_exam(ctx), style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
        ]

    if s.cbt_submitted:
        return _exam_result(ctx)

    radio_refs = {}
    blocks = []
    for qid in s.cbt_pool:
        q = ctx.questions[qid]
        choices = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]]
        prev_val = s.cbt_answers.get(qid)
        rg = ft.RadioGroup(
            value=str(prev_val) if prev_val is not None else None,
            content=ft.Column([ft.Radio(value=str(i), label=f"{'①②③④'[i]} {c}") for i, c in enumerate(choices)]),
        )
        radio_refs[qid] = rg
        blocks.append(ft.Container(
            content=ft.Column([
                ft.Row([pill(logic.SUBJECT_LABEL[q["subject"]]), pill(q["tag"], color="#9CA3AF")], spacing=6, wrap=True),
                ft.Text(q["question"], size=15, weight=ft.FontWeight.W_600),
                rg,
            ], spacing=6),
            padding=12, bgcolor="#F9FAFB", border_radius=10, margin=ft.Margin(0, 0, 0, 10),
        ))

    def submit(e):
        for qid in s.cbt_pool:
            rg = radio_refs[qid]
            if rg.value is not None:
                s.cbt_answers[qid] = int(rg.value)
        for qid in s.cbt_pool:
            chosen = s.cbt_answers.get(qid)
            if chosen is not None:
                is_correct = (chosen + 1) == ctx.questions[qid]["answer"]
                db.record_attempt(ctx.con, ctx.user, qid, chosen + 1, is_correct)
        s.cbt_submitted = True
        ctx.render()

    out = list(blocks)
    out.append(ft.Text(f"{len(s.cbt_pool)}문항 중 답한 문항: {len(s.cbt_answers)}", size=13, color="#6B7280"))
    out.append(ft.ElevatedButton(content="제출", on_click=submit, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")))
    return out


def _exam_result(ctx):
    s = ctx.state
    per_subject = {}
    correct_n = 0
    for qid in s.cbt_pool:
        q = ctx.questions[qid]
        chosen = s.cbt_answers.get(qid)
        is_correct = chosen is not None and (chosen + 1) == q["answer"]
        d = per_subject.setdefault(q["subject"], {"correct": 0, "total": 0})
        d["total"] += 1
        if is_correct:
            d["correct"] += 1
            correct_n += 1

    fail_subjects = [s2 for s2, n in logic.EXAM_MIN_CORRECT.items() if per_subject.get(s2, {"correct": 0})["correct"] < n]
    total_score = correct_n * logic.POINTS_PER_Q
    overall_pass = (correct_n >= logic.EXAM_TOTAL_PASS) and not fail_subjects

    rows = []
    for subj in (1, 2, 3):
        d = per_subject.get(subj, {"correct": 0, "total": logic.EXAM_SUBJECT_COUNTS[subj]})
        rows.append(ft.Text(f"{logic.SUBJECT_LABEL[subj]}: {d['correct']}/{d['total']}문항 · {d['correct'] * logic.POINTS_PER_Q}점", size=13))

    verdict_color = CORRECT_COLOR if overall_pass else WRONG_COLOR
    verdict_text = "합격 예상" if overall_pass else "불합격 예상"
    reason = []
    if correct_n < logic.EXAM_TOTAL_PASS:
        reason.append(f"총점 미달({total_score}점/{logic.EXAM_TOTAL_PASS * logic.POINTS_PER_Q}점)")
    if fail_subjects:
        reason.append("과락 과목: " + ", ".join(logic.SUBJECT_LABEL[s2] for s2 in fail_subjects))

    return [
        ft.Container(
            content=ft.Column([
                ft.Text(verdict_text, size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Text(f"총점 {total_score}점/{logic.EXAM_TOTAL_PASS * logic.POINTS_PER_Q + 0}점 · {correct_n}/{len(s.cbt_pool)}문항 정답", color="#FFFFFF", size=13),
                *([ft.Text(" / ".join(reason), color="#FFFFFF", size=12)] if reason else []),
            ], spacing=4),
            bgcolor=verdict_color, padding=16, border_radius=12,
        ),
        ft.Container(height=12),
        *rows,
        ft.Container(height=16),
        ft.ElevatedButton(content="다시 시작", on_click=lambda e: _start_exam(ctx), style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
    ]
