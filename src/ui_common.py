# -*- coding: utf-8 -*-
"""여러 화면에서 공용으로 쓰는 작은 UI 헬퍼들."""
import flet as ft

ACCENT = "#7C3AED"
CORRECT_COLOR = "#16A34A"
WRONG_COLOR = "#DC2626"
CARD_BG = "#F5F3FF"


def pill(text, color=ACCENT):
    return ft.Container(
        content=ft.Text(text, size=12, color="#FFFFFF", weight=ft.FontWeight.W_600),
        bgcolor=color,
        padding=ft.Padding(8, 3, 8, 3),
        border_radius=999,
    )


def section_title(text):
    return ft.Text(text, size=18, weight=ft.FontWeight.BOLD)


def subject_filter_row(current, on_pick, options=("전체", "1", "2", "3")):
    """전체/1/2/3과목 토글 버튼 행. on_pick(value) 콜백으로 선택값을 알려준다."""
    label = {"전체": "전체", "1": "1과목", "2": "2과목", "3": "3과목"}
    btns = []
    for opt in options:
        selected = opt == current

        def make_click(v):
            def _click(e):
                on_pick(v)
            return _click

        btns.append(
            ft.FilledButton(
                content=label.get(opt, opt),
                on_click=make_click(opt),
                style=ft.ButtonStyle(
                    bgcolor=ACCENT if selected else "#E5E7EB",
                    color="#FFFFFF" if selected else "#374151",
                ),
            )
        )
    return ft.Row(btns, spacing=8, wrap=True)


def empty_state(text):
    return ft.Container(
        content=ft.Text(text, size=14, color="#6B7280"),
        padding=20,
        alignment=ft.Alignment.CENTER,
    )


def question_card(stem, subject_label, tag):
    return ft.Column([
        ft.Row([pill(subject_label), pill(tag, color="#9CA3AF")], spacing=6, wrap=True),
        ft.Container(height=6),
        ft.Text(stem, size=16, weight=ft.FontWeight.W_600),
    ], spacing=4)
