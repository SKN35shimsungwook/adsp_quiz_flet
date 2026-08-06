# -*- coding: utf-8 -*-
"""개념노트: 카드(뒤집기/단어입력형/빈칸채우기) · 노트뷰 · OX퀴즈."""
import random

import flet as ft

import db
import logic
from ui_common import ACCENT, CORRECT_COLOR, WRONG_COLOR, pill, section_title, subject_filter_row


def _subjects_of(key):
    return [1, 2, 3] if key == "전체" else [int(key)]


def _rebuild_card_pool(ctx):
    s = ctx.state
    s.card_pool = logic.pick_pool(ctx.questions, _subjects_of(s.concept_subject))
    s.card_idx = 0
    s.card_flipped = False


def build(ctx):
    s = ctx.state
    controls = [section_title("개념노트")]

    def pick_view(v):
        def _click(e):
            s.concept_view = v
            ctx.render()
        return _click

    def view_btn(label, v):
        selected = s.concept_view == v
        return ft.FilledButton(
            content=label, on_click=pick_view(v),
            style=ft.ButtonStyle(bgcolor=ACCENT if selected else "#E5E7EB", color="#FFFFFF" if selected else "#374151"),
        )

    controls.append(ft.Row([view_btn("카드", "카드"), view_btn("노트", "노트"), view_btn("OX 퀴즈", "OX")], spacing=8, wrap=True))
    controls.append(ft.Container(height=6))

    def pick_subject(v):
        s.concept_subject = v
        if s.concept_view == "카드":
            _rebuild_card_pool(ctx)
        ctx.render()

    controls.append(subject_filter_row(s.concept_subject, pick_subject))
    controls.append(ft.Container(height=10))

    if s.concept_view == "카드":
        controls.extend(_build_card(ctx))
    elif s.concept_view == "노트":
        controls.extend(_build_note(ctx))
    else:
        controls.extend(_build_ox(ctx))
    return controls


# ---------- 카드 ----------

def _build_card(ctx):
    s = ctx.state
    if not s.card_pool:
        _rebuild_card_pool(ctx)

    def pick_mode(v):
        def _click(e):
            s.card_mode = v
            s.card_flipped = False
            ctx.render()
        return _click

    def mode_btn(label, v):
        selected = s.card_mode == v
        return ft.OutlinedButton(
            content=label, on_click=pick_mode(v),
            style=ft.ButtonStyle(bgcolor=ACCENT if selected else None, color="#FFFFFF" if selected else "#374151"),
        )

    header = [
        ft.Row([mode_btn("뒤집기", "뒤집기"), mode_btn("단어 입력형", "단어입력형"), mode_btn("빈칸 채우기", "빈칸채우기")], spacing=6, wrap=True),
        ft.Container(height=8),
    ]

    if not s.card_pool:
        return header + [ft.Text("표시할 개념이 없어요.", size=13, color="#6B7280")]

    qid = s.card_pool[s.card_idx]
    q = ctx.questions[qid]
    answer_text = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]][q["answer"] - 1]

    top = ft.Row([
        pill(logic.SUBJECT_LABEL[q["subject"]]), pill(q["tag"], color="#9CA3AF"),
        ft.Container(expand=True),
        ft.Text(f"{s.card_idx + 1} / {len(s.card_pool)}", size=13, color="#6B7280"),
    ])
    body = [top, ft.Container(height=8), ft.Text(q["question"], size=16, weight=ft.FontWeight.W_600), ft.Container(height=10)]

    if s.card_mode == "뒤집기":
        body.extend(_card_flip_body(ctx, q, answer_text))
    elif s.card_mode == "단어입력형":
        body.extend(_card_word_body(ctx, qid, q, answer_text))
    else:
        body.extend(_card_blank_body(ctx, qid, q, answer_text))

    def go_prev(e):
        s.card_idx = (s.card_idx - 1) % len(s.card_pool)
        s.card_flipped = False
        ctx.render()

    def go_next(e):
        s.card_idx = (s.card_idx + 1) % len(s.card_pool)
        s.card_flipped = False
        ctx.render()

    def shuffle(e):
        random.shuffle(s.card_pool)
        s.card_idx = 0
        s.card_flipped = False
        ctx.render()

    def reset_all(e):
        s.card_results = {}
        ctx.render()

    nav_row = [
        ft.Row([
            ft.OutlinedButton(content="◀ 이전", on_click=go_prev),
            ft.OutlinedButton(content="다음 ▶", on_click=go_next),
        ], spacing=8),
        ft.Container(height=8),
        ft.Row([
            ft.OutlinedButton(content="🔀 순서 섞기", on_click=shuffle),
            *([ft.OutlinedButton(content="🔄 전체 리셋 (지금까지 푼 카드)", on_click=reset_all)] if s.card_mode != "뒤집기" else []),
        ], spacing=8, wrap=True),
    ]

    wrong_ids = db.get_card_wrong_ids(ctx.con, ctx.user)
    wrong_section = _card_wrong_section(ctx, wrong_ids) if wrong_ids and s.card_mode != "뒤집기" else []

    return header + [ft.Container(content=ft.Column(body), padding=14, bgcolor="#F9FAFB", border_radius=12)] + [ft.Container(height=10)] + nav_row + wrong_section


def _card_flip_body(ctx, q, answer_text):
    s = ctx.state
    if not s.card_flipped:
        return [ft.ElevatedButton(content="정답 보기", on_click=lambda e: _toggle_flip(ctx), style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"))]
    return [
        ft.Text(f"정답: {answer_text}", size=15, weight=ft.FontWeight.W_600, color=CORRECT_COLOR),
        ft.Text(q["explanation"], size=13, color="#374151"),
        ft.Container(height=6),
        ft.OutlinedButton(content="다시 가리기", on_click=lambda e: _toggle_flip(ctx)),
    ]


def _toggle_flip(ctx):
    ctx.state.card_flipped = not ctx.state.card_flipped
    ctx.render()


def _card_word_body(ctx, qid, q, answer_text):
    s = ctx.state
    field = ft.TextField(label="정답 입력", value="", autofocus=True)
    result = s.card_results.get(qid)

    def check(e):
        ok = logic.answer_matches(field.value, answer_text)
        s.card_results[qid] = ok
        if ok:
            db.clear_card_wrong(ctx.con, ctx.user, qid)
        else:
            db.add_card_wrong(ctx.con, ctx.user, qid)
        ctx.render()

    def dont_know(e):
        s.card_results[qid] = False
        db.add_card_wrong(ctx.con, ctx.user, qid)
        ctx.render()

    body = [field, ft.Row([
        ft.ElevatedButton(content="확인", on_click=check, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
        ft.OutlinedButton(content="모르겠어요", on_click=dont_know),
    ], spacing=8)]

    if result is not None:
        color = CORRECT_COLOR if result else WRONG_COLOR
        text = "정답이에요!" if result else f"정답: {answer_text}"
        body.append(ft.Container(content=ft.Text(text, color="#FFFFFF"), bgcolor=color, padding=8, border_radius=6))
        body.append(ft.Text(q["explanation"], size=12, color="#374151"))
    return body


def _card_blank_body(ctx, qid, q, answer_text):
    s = ctx.state
    blanked = logic.make_blank_sentence(q["explanation"], answer_text)
    choices_hint = ft.Text(
        "보기: " + "  ".join(f"{'①②③④'[i]} {c}" for i, c in enumerate([q["choice1"], q["choice2"], q["choice3"], q["choice4"]])),
        size=12, color="#6B7280",
    )
    if blanked is None:
        body = [ft.Text("(빈칸을 만들 수 없어 단어 입력형으로 대체돼요)", size=12, color="#9CA3AF"), choices_hint]
        body.extend(_card_word_body(ctx, qid, q, answer_text))
        return body

    field = ft.TextField(label="빈칸에 들어갈 답 입력", value="", autofocus=True)
    result = s.card_results.get(qid)

    def check(e):
        ok = logic.answer_matches(field.value, answer_text)
        s.card_results[qid] = ok
        if ok:
            db.clear_card_wrong(ctx.con, ctx.user, qid)
        else:
            db.add_card_wrong(ctx.con, ctx.user, qid)
        ctx.render()

    def dont_know(e):
        s.card_results[qid] = False
        db.add_card_wrong(ctx.con, ctx.user, qid)
        ctx.render()

    body = [ft.Text(blanked, size=14), choices_hint, field, ft.Row([
        ft.ElevatedButton(content="확인", on_click=check, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
        ft.OutlinedButton(content="모르겠어요", on_click=dont_know),
    ], spacing=8)]

    if result is not None:
        color = CORRECT_COLOR if result else WRONG_COLOR
        text = "정답이에요!" if result else f"정답: {answer_text}"
        body.append(ft.Container(content=ft.Text(text, color="#FFFFFF"), bgcolor=color, padding=8, border_radius=6))
    return body


def _card_wrong_section(ctx, wrong_ids):
    s = ctx.state
    groups = logic.group_ids_by_tag(ctx.questions, wrong_ids)
    items = [ft.Container(height=14), ft.Text(f"📋 카드 오답 · 개념별로 확인 ({len(wrong_ids)}개)", size=15, weight=ft.FontWeight.BOLD),
              ft.Text("과목·개념별로 묶었습니다. 바로 정답을 입력해 다시 풀어보세요. 맞히면 자동으로 목록에서 빠집니다.", size=12, color="#6B7280")]
    for (subject, tag), ids in groups.items():
        items.append(ft.Container(height=8))
        items.append(ft.Text(f"{logic.SUBJECT_LABEL[subject]} · {tag}", size=13, weight=ft.FontWeight.W_600))
        for wqid in ids:
            items.append(_wrong_retry_row(ctx, wqid))
    return items


def _wrong_retry_row(ctx, wqid):
    q = ctx.questions[wqid]
    answer_text = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]][q["answer"] - 1]
    field = ft.TextField(label="정답 입력", value="", dense=True)
    feedback = ft.Text("", size=12)

    def check(e):
        if logic.answer_matches(field.value, answer_text):
            db.clear_card_wrong(ctx.con, ctx.user, wqid)
            ctx.render()
        else:
            feedback.value = f"오답이에요. 정답: {answer_text}"
            feedback.color = WRONG_COLOR
            ctx.page.update()

    def clear_it(e):
        db.clear_card_wrong(ctx.con, ctx.user, wqid)
        ctx.render()

    return ft.Container(
        content=ft.Column([
            ft.Text(q["question"], size=13),
            ft.Row([field, ft.ElevatedButton(content="확인", on_click=check, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
                    ft.TextButton(content="목록서 지우기", on_click=clear_it)], spacing=6, wrap=True),
            feedback,
        ], spacing=4),
        padding=10, bgcolor="#FFFFFF", border=ft.Border.all(1, "#E5E7EB"), border_radius=8, margin=ft.Margin(0, 4, 0, 0),
    )


# ---------- 노트 ----------

def _build_note(ctx):
    subjects = _subjects_of(ctx.state.concept_subject)
    groups = logic.get_core_groups(ctx.questions)
    rep_ids = []
    for subj in subjects:
        for core_id, variant_ids in groups[subj].items():
            rep_ids.append(min(variant_ids))
    by_tag = logic.group_ids_by_tag(ctx.questions, rep_ids)

    total = sum(len(ids) for ids in by_tag.values())
    out = [ft.Text(f"{total}개 개념을 과목·태그별로 정리했습니다.", size=13, color="#6B7280"), ft.Container(height=8)]
    for (subject, tag), ids in by_tag.items():
        out.append(ft.Text(f"{logic.SUBJECT_LABEL[subject]} · {tag}", size=14, weight=ft.FontWeight.BOLD))
        for qid in ids:
            q = ctx.questions[qid]
            answer_text = [q["choice1"], q["choice2"], q["choice3"], q["choice4"]][q["answer"] - 1]
            out.append(ft.Container(
                content=ft.Column([
                    ft.Text(q["question"], size=13, weight=ft.FontWeight.W_600),
                    ft.Text(f"정답: {answer_text}", size=12, color=CORRECT_COLOR),
                    ft.Text(q["explanation"], size=12, color="#374151"),
                ], spacing=2),
                padding=10, bgcolor="#F9FAFB", border_radius=8, margin=ft.Margin(0, 4, 0, 8),
            ))
    return out


# ---------- OX 퀴즈 ----------

def _start_ox(ctx):
    s = ctx.state
    concepts = [ctx.questions[qid] for qid in logic.pick_pool(ctx.questions, _subjects_of(s.concept_subject))]
    s.ox_pool = logic.build_ox_pool(concepts)
    s.ox_idx = 0
    ctx.render()


def _build_ox(ctx):
    s = ctx.state
    if not s.ox_pool:
        controls = [
            ft.Text("선택한 과목의 개념으로 참/거짓 문제를 풉니다.", size=13, color="#6B7280"),
            ft.Container(height=8),
            ft.ElevatedButton(content="OX 퀴즈 시작", on_click=lambda e: _start_ox(ctx), style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
        ]
        wrong_ids = db.get_ox_wrong_ids(ctx.con, ctx.user)
        if wrong_ids:
            controls.extend(_ox_wrong_section(ctx, wrong_ids))
        return controls

    if s.ox_idx >= len(s.ox_pool):
        correct_n = sum(1 for it in s.ox_pool if it.get("_correct"))
        controls = [
            ft.Text(f"OX 퀴즈 완료! {correct_n}/{len(s.ox_pool)} 정답", size=16, weight=ft.FontWeight.W_600),
            ft.Container(height=10),
            ft.ElevatedButton(content="다시 풀기", on_click=lambda e: _start_ox(ctx), style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")),
        ]
        wrong_ids = db.get_ox_wrong_ids(ctx.con, ctx.user)
        if wrong_ids:
            controls.extend(_ox_wrong_section(ctx, wrong_ids))
        return controls

    item = s.ox_pool[s.ox_idx]
    answered = "_answered" in item

    def answer(is_true_choice):
        def _click(e):
            item["_answered"] = True
            item["_choice"] = is_true_choice
            correct = is_true_choice == item["truth"]
            item["_correct"] = correct
            if correct:
                db.clear_ox_wrong(ctx.con, ctx.user, item["qid"])
            else:
                db.add_ox_wrong(ctx.con, ctx.user, item["qid"])
            ctx.render()
        return _click

    def next_item(e):
        s.ox_idx += 1
        ctx.render()

    controls = [
        ft.Row([pill(logic.SUBJECT_LABEL[item["subject"]]), pill(item["tag"], color="#9CA3AF"),
                ft.Container(expand=True), ft.Text(f"{s.ox_idx + 1}/{len(s.ox_pool)}", size=13, color="#6B7280")]),
        ft.Container(height=8),
        ft.Text(item["stem"], size=13, color="#6B7280"),
        ft.Text(item["statement"], size=16, weight=ft.FontWeight.W_600),
        ft.Container(height=10),
    ]

    if not answered:
        controls.append(ft.Row([
            ft.ElevatedButton(content="⭕ 참", on_click=answer(True), style=ft.ButtonStyle(bgcolor=CORRECT_COLOR, color="#FFFFFF")),
            ft.ElevatedButton(content="❌ 거짓", on_click=answer(False), style=ft.ButtonStyle(bgcolor=WRONG_COLOR, color="#FFFFFF")),
        ], spacing=10))
    else:
        correct = item["_correct"]
        color = CORRECT_COLOR if correct else WRONG_COLOR
        text = "정답이에요!" if correct else f"오답이에요. 정답은 {'참' if item['truth'] else '거짓'}입니다."
        controls.append(ft.Container(content=ft.Text(text, color="#FFFFFF"), bgcolor=color, padding=8, border_radius=6))
        controls.append(ft.Text(item["explanation"], size=12, color="#374151"))
        controls.append(ft.Container(height=8))
        controls.append(ft.ElevatedButton(content="다음 ▶", on_click=next_item, style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF")))

    return controls


def _ox_wrong_section(ctx, wrong_ids):
    s = ctx.state
    groups = logic.group_ids_by_tag(ctx.questions, wrong_ids)
    out = [ft.Container(height=14), ft.Text(f"📋 OX 오답 · 개념별로 확인 ({len(wrong_ids)}개)", size=15, weight=ft.FontWeight.BOLD),
           ft.Text("바로 참/거짓을 선택해 다시 풀어보세요. 맞히면 자동으로 목록에서 빠집니다.", size=12, color="#6B7280")]
    for (subject, tag), ids in groups.items():
        out.append(ft.Container(height=8))
        out.append(ft.Text(f"{logic.SUBJECT_LABEL[subject]} · {tag}", size=13, weight=ft.FontWeight.W_600))
        for wqid in ids:
            out.append(_ox_wrong_row(ctx, wqid))
    return out


def _ox_wrong_row(ctx, wqid):
    s = ctx.state
    q = ctx.questions[wqid]
    item = s.wrong_ox_items.get(wqid)
    if item is None:
        item = logic.build_ox_pool([q])[0]
        s.wrong_ox_items[wqid] = item

    answered = item.get("_answered")

    def answer(is_true_choice):
        def _click(e):
            item["_answered"] = True
            correct = is_true_choice == item["truth"]
            if correct:
                db.clear_ox_wrong(ctx.con, ctx.user, wqid)
                del s.wrong_ox_items[wqid]
                ctx.render()
            else:
                item["_correct"] = False
                ctx.page.update()
        return _click

    def retry(e):
        del s.wrong_ox_items[wqid]
        ctx.render()

    def clear_it(e):
        db.clear_ox_wrong(ctx.con, ctx.user, wqid)
        if wqid in s.wrong_ox_items:
            del s.wrong_ox_items[wqid]
        ctx.render()

    body = [ft.Text(item["stem"], size=12, color="#6B7280"), ft.Text(item["statement"], size=14, weight=ft.FontWeight.W_600)]

    if not answered:
        body.append(ft.Row([
            ft.ElevatedButton(content="⭕ 참", on_click=answer(True), style=ft.ButtonStyle(bgcolor=CORRECT_COLOR, color="#FFFFFF")),
            ft.ElevatedButton(content="❌ 거짓", on_click=answer(False), style=ft.ButtonStyle(bgcolor=WRONG_COLOR, color="#FFFFFF")),
            ft.TextButton(content="목록서 지우기", on_click=clear_it),
        ], spacing=6, wrap=True))
    else:
        body.append(ft.Container(
            content=ft.Text(f"오답이에요. 정답은 {'참' if item['truth'] else '거짓'}입니다.", color="#FFFFFF", size=12),
            bgcolor=WRONG_COLOR, padding=6, border_radius=6,
        ))
        body.append(ft.Text(item["explanation"], size=11, color="#374151"))
        body.append(ft.OutlinedButton(content="다시 시도", on_click=retry))

    return ft.Container(content=ft.Column(body, spacing=4), padding=10, bgcolor="#FFFFFF", border=ft.Border.all(1, "#E5E7EB"), border_radius=8, margin=ft.Margin(0, 4, 0, 0))
