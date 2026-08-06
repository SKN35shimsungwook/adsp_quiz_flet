# -*- coding: utf-8 -*-
"""오답노트: 퀴즈(개념+CBT 통합) 풀이 기록 기반 복습 필요/완료 목록. 그룹별 인라인 재시도 지원."""
import flet as ft

import db
import logic
from ui_common import ACCENT, CORRECT_COLOR, WRONG_COLOR, section_title
from view_quiz import start_focus_session


def build(ctx):
    con, user = ctx.con, ctx.user
    need, done, stats = db.get_wrong_question_ids(con, user)
    overall = db.get_overall_stats(con, user)

    controls = [
        section_title("오답노트"),
        ft.Container(height=4),
        ft.Text(f"누적 풀이 {overall['seen']} · 정답률 {overall['rate']}% · 복습 필요 {len(need)}", size=13, color="#6B7280"),
        ft.Container(height=10),
    ]

    if not need and not done:
        controls.append(ft.Text("아직 풀이 기록이 없어요. 퀴즈나 CBT를 먼저 풀어보세요.", size=13, color="#6B7280"))
        return controls

    if need:
        controls.append(ft.ElevatedButton(
            content=f"복습 필요 {len(need)}개 다시 풀기",
            on_click=lambda e: start_focus_session(ctx, need, "오답노트"),
            style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"),
        ))
        controls.append(ft.Container(height=10))
        controls.append(ft.Text("개념별로 바로 다시 풀어보세요. 맞히면 목록에서 자동으로 빠집니다.", size=12, color="#6B7280"))
        groups = logic.group_ids_by_tag(ctx.questions, need)
        for (subject, tag), ids in groups.items():
            controls.append(ft.Container(height=8))
            controls.append(ft.Text(f"{logic.SUBJECT_LABEL[subject]} · {tag}", size=13, weight=ft.FontWeight.W_600))
            for qid in ids:
                controls.append(_retry_row(ctx, qid, stats.get(qid)))
    else:
        controls.append(ft.Text("현재 복습이 필요한 문제가 없어요. 잘하고 있어요!", size=13, color=CORRECT_COLOR))

    if done:
        controls.append(ft.Container(height=16))
        controls.append(ft.Text(f"✅ 복습 완료 ({len(done)}개) — 예전엔 틀렸지만 최근엔 맞힌 문제", size=13, weight=ft.FontWeight.W_600))
        for qid in done[:30]:
            q = ctx.questions.get(qid)
            if q:
                controls.append(ft.Text(f"· {q['question'][:40]}{'...' if len(q['question']) > 40 else ''}", size=12, color="#6B7280"))

    return controls


def _retry_row(ctx, qid, stat):
    q = ctx.questions[qid]
    choices = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]]
    rg = ft.RadioGroup(
        value=None,
        content=ft.Column([ft.Radio(value=str(i), label=f"{'①②③④'[i]} {c}") for i, c in enumerate(choices)]),
    )
    feedback = ft.Text("", size=12)

    def check(e):
        if rg.value is None:
            return
        chosen = int(rg.value)
        is_correct = (chosen + 1) == q["answer"]
        db.record_attempt(ctx.con, ctx.user, qid, chosen + 1, is_correct)
        if is_correct:
            ctx.render()
        else:
            feedback.value = f"오답이에요. 정답: {'①②③④'[q['answer'] - 1]} {choices[q['answer'] - 1]}"
            feedback.color = WRONG_COLOR
            ctx.page.update()

    last = f" · 최근 {stat['last_result']}" if stat else ""
    return ft.Container(
        content=ft.Column([
            ft.Text(q["question"] + last, size=13),
            rg,
            ft.Row([ft.ElevatedButton(content="확인", on_click=check, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"))], spacing=6),
            feedback,
        ], spacing=4),
        padding=10, bgcolor="#FFFFFF", border=ft.Border.all(1, "#E5E7EB"), border_radius=8, margin=ft.Margin(0, 4, 0, 0),
    )
