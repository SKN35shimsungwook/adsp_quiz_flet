# -*- coding: utf-8 -*-
import flet as ft

import build_db
import db
from state import AppState

import view_quiz
import view_cbt
import view_concept
import view_wrong
import view_tagstats

NAV_ITEMS = ["퀴즈", "CBT", "개념노트", "오답노트", "자주 틀리는 개념"]
NAV_ICONS = [ft.Icons.QUIZ, ft.Icons.FACT_CHECK, ft.Icons.STYLE, ft.Icons.ASSIGNMENT_LATE, ft.Icons.TRENDING_DOWN]


class Ctx:
    """각 화면 빌더 함수에 전달되는 공용 컨텍스트."""

    def __init__(self, page, state, con, questions, cbt_ids, user, render):
        self.page = page
        self.state = state
        self.con = con
        self.questions = questions
        self.cbt_ids = cbt_ids
        self.user = user
        self.render = render


def main(page: ft.Page):
    build_db.main()
    con = db.get_connection()
    questions = {r["id"]: dict(r) for r in db.get_all_questions(con)}
    cbt_ids = [qid for qid, q in questions.items() if q["source"] == "cbt"]

    page.title = "ADsP 핵심요약 퀴즈"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#FFFFFF"
    page.padding = 0

    state = AppState()
    body = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
    content_area = ft.Container(content=body, padding=16, expand=True)

    nav_bar = ft.NavigationBar(
        selected_index=0,
        destinations=[ft.NavigationBarDestination(icon=NAV_ICONS[i], label=NAV_ITEMS[i]) for i in range(len(NAV_ITEMS))],
    )

    def render():
        body.controls.clear()
        if state.nav == "퀴즈":
            body.controls.extend(view_quiz.build(ctx))
        elif state.nav == "CBT":
            body.controls.extend(view_cbt.build(ctx))
        elif state.nav == "개념노트":
            body.controls.extend(view_concept.build(ctx))
        elif state.nav == "오답노트":
            body.controls.extend(view_wrong.build(ctx))
        else:
            body.controls.extend(view_tagstats.build(ctx))
        nav_bar.selected_index = NAV_ITEMS.index(state.nav)
        page.update()

    ctx = Ctx(page, state, con, questions, cbt_ids, state.user, render)

    def on_nav_change(e):
        state.nav = NAV_ITEMS[e.control.selected_index]
        render()

    nav_bar.on_change = on_nav_change
    page.navigation_bar = nav_bar

    page.add(ft.SafeArea(expand=True, content=content_area))
    render()


if __name__ == "__main__":
    ft.run(main)
