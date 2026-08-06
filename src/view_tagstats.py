# -*- coding: utf-8 -*-
"""자주 틀리는 개념: 태그(개념) 단위로 오답이 많은 순서를 보여주고 집중풀기로 연결한다."""
import flet as ft

import db
from ui_common import ACCENT, section_title
import logic
from view_quiz import start_focus_session


def build(ctx):
    stats = db.get_tag_stats(ctx.con, ctx.user)
    controls = [section_title("자주 틀리는 개념"), ft.Container(height=6)]

    if not stats:
        controls.append(ft.Text("아직 오답 데이터가 없어요. 문제를 더 풀어보면 여기에 취약 개념이 나타나요.", size=13, color="#6B7280"))
        return controls

    for d in stats[:20]:
        rate = round(d["wrong"] / d["seen"] * 100) if d["seen"] else 0
        qids = sorted(d["qids"])
        controls.append(ft.Container(
            content=ft.Column([
                ft.Text(f"{logic.SUBJECT_LABEL[d['subject']]} · {d['tag']}", size=14, weight=ft.FontWeight.W_600),
                ft.Text(f"오답 {d['wrong']}/{d['seen']}회 ({rate}%)", size=12, color="#6B7280"),
                ft.OutlinedButton(
                    content="이 개념 집중 풀기",
                    on_click=lambda e, ids=qids: start_focus_session(ctx, ids, "자주 틀리는 개념"),
                ),
            ], spacing=4),
            padding=10, bgcolor="#F9FAFB", border_radius=8, margin=ft.Margin(0, 0, 0, 8),
        ))
    return controls
