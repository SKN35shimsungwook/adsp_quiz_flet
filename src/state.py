# -*- coding: utf-8 -*-
"""앱 전역에서 공유되는 세션 상태. Streamlit의 st.session_state 역할을 대신한다."""


class AppState:
    def __init__(self):
        self.user = "guest"
        self.nav = "퀴즈"

        # 퀴즈 연습모드 (그리고 '자주 틀리는 개념 집중풀기'도 이 세션을 재사용한다)
        self.quiz_subject = "전체"
        self.quiz_pool = []
        self.quiz_idx = 0
        self.quiz_chosen = None
        self.quiz_answered = False
        self.quiz_correct = 0
        self.quiz_seen = 0
        self.quiz_return_nav = "퀴즈"  # 집중풀기 세션이 끝나면 어디로 돌아갈지

        # CBT 모드
        self.cbt_mode = "연습"
        self.cbt_subject = "전체"
        self.cbt_pool = []
        self.cbt_answers = {}   # qid -> chosen_idx
        self.cbt_checked = {}   # qid -> bool (연습모드 개별 '정답 확인' 눌렀는지)
        self.cbt_submitted = False

        # 개념노트
        self.concept_view = "카드"
        self.concept_subject = "전체"
        self.card_mode = "뒤집기"
        self.card_pool = []
        self.card_idx = 0
        self.card_flipped = False
        self.card_results = {}  # qid -> True/False (현재까지 푼 카드 결과, '전체 리셋'으로 지움)

        self.ox_pool = []
        self.ox_idx = 0

        # 오답노트에서 개별 항목 재시도용으로 만들어진 1문항짜리 OX (qid -> ox item dict)
        self.wrong_ox_items = {}
