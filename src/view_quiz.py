# -*- coding: utf-8 -*-
"""퀴즈 연습모드 (그리고 '자주 틀리는 개념 집중풀기'도 같은 세션 엔진을 재사용한다)."""
import flet as ft

import db
import logic
from ui_common import ACCENT, CORRECT_COLOR, WRONG_COLOR, empty_state, pill, section_title


def start_new_pool(ctx, subject_key):
    s = ctx.state
    s.quiz_subject = subject_key
    subjects = [1, 2, 3] if subject_key == "전체" else [int(subject_key)]
    s.quiz_pool = logic.pick_pool(ctx.questions, subjects)
    s.quiz_idx = 0
    s.quiz_chosen = None
    s.quiz_answered = False
    ctx.render()


def start_focus_session(ctx, qids, return_nav):
    """자주 틀리는 개념 탭에서 '이 개념 집중 풀기'를 눌렀을 때 호출."""
    s = ctx.state
    s.quiz_pool = list(qids)
    s.quiz_idx = 0
    s.quiz_chosen = None
    s.quiz_answered = False
    s.quiz_return_nav = return_nav
    s.nav = "퀴즈"
    ctx.render()


def build(ctx):
    s = ctx.state
    q_by_id = ctx.questions

    if not s.quiz_pool:
        controls = [
            section_title("퀴즈 연습모드"),
            ft.Text("과목을 선택하면 개념 문제를 무작위로 풀어볼 수 있어요.", size=13, color="#6B7280"),
            ft.Container(height=8),
            _subject_row(ctx),
        ]
        return controls

    if s.quiz_idx >= len(s.quiz_pool):
        rate = round(s.quiz_correct / s.quiz_seen * 100) if s.quiz_seen else 0
        return [
            section_title("연습 완료!"),
            ft.Container(height=8),
            ft.Text(f"이번 세션 정답률: {s.quiz_correct}/{s.quiz_seen} ({rate}%)", size=16),
            ft.Container(height=16),
            ft.ElevatedButton(
                content="다시 풀기",
                on_click=lambda e: start_new_pool(ctx, s.quiz_subject),
                style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"),
            ),
            ft.OutlinedButton(
                content="메뉴로 돌아가기",
                on_click=lambda e: _finish_session(ctx),
            ),
        ]

    qid = s.quiz_pool[s.quiz_idx]
    q = q_by_id[qid]
    choices = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]]

    radio_group = ft.RadioGroup(
        value=str(s.quiz_chosen) if s.quiz_chosen is not None else None,
        content=ft.Column([
            ft.Radio(value=str(i), label=f"{'①②③④'[i]} {c}") for i, c in enumerate(choices)
        ]),
        disabled=s.quiz_answered,
    )

    def on_submit(e):
        if radio_group.value is None:
            return
        chosen = int(radio_group.value)
        s.quiz_chosen = chosen
        s.quiz_answered = True
        s.quiz_seen += 1
        is_correct = (chosen + 1) == q["answer"]
        if is_correct:
            s.quiz_correct += 1
        db.record_attempt(ctx.con, ctx.user, qid, chosen + 1, is_correct)
        ctx.render()

    def on_next(e):
        s.quiz_idx += 1
        s.quiz_chosen = None
        s.quiz_answered = False
        ctx.render()

    controls = [
        ft.Row([
            pill(logic.SUBJECT_LABEL[q["subject"]]),
            pill(q["tag"], color="#9CA3AF"),
            ft.Container(expand=True),
            ft.Text(f"{s.quiz_idx + 1}/{len(s.quiz_pool)}", size=13, color="#6B7280"),
        ]),
        ft.Container(height=8),
        ft.Text(q["question"], size=17, weight=ft.FontWeight.W_600),
        ft.Container(height=8),
        radio_group,
        ft.Container(height=8),
    ]

    if not s.quiz_answered:
        controls.append(
            ft.ElevatedButton(
                content="확인",
                on_click=on_submit,
                style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"),
            )
        )
    else:
        is_correct = (s.quiz_chosen + 1) == q["answer"]
        result_color = CORRECT_COLOR if is_correct else WRONG_COLOR
        result_text = "정답이에요!" if is_correct else f"오답이에요. 정답: {'①②③④'[q['answer'] - 1]} {choices[q['answer'] - 1]}"
        controls.extend([
            ft.Container(
                content=ft.Text(result_text, color="#FFFFFF", weight=ft.FontWeight.W_600),
                bgcolor=result_color, padding=10, border_radius=8,
            ),
            ft.Container(height=6),
            ft.Text(q["explanation"], size=13, color="#374151"),
            ft.Container(height=10),
            ft.ElevatedButton(
                content="다음 문제 ▶",
                on_click=on_next,
                style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"),
            ),
        ])

    controls.append(ft.Container(height=16))
    controls.append(ft.OutlinedButton(content="세션 그만두기", on_click=lambda e: _finish_session(ctx)))
    return controls


def _finish_session(ctx):
    s = ctx.state
    s.quiz_pool = []
    s.nav = s.quiz_return_nav
    s.quiz_return_nav = "퀴즈"
    ctx.render()


def _subject_row(ctx):
    def pick(v):
        start_new_pool(ctx, v)

    from ui_common import subject_filter_row
    return subject_filter_row(ctx.state.quiz_subject, pick)
