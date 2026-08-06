# -*- coding: utf-8 -*-
"""문항 선택/채점 관련 순수 로직. adsp_quiz(Streamlit)의 app.py 로직을 그대로 포팅했다."""
import random
import re

SUBJECT_LABEL = {1: "1과목 데이터 이해", 2: "2과목 데이터 분석 기획", 3: "3과목 데이터 분석"}
EXAM_SUBJECT_COUNTS = {1: 10, 2: 10, 3: 30}
EXAM_MIN_CORRECT = {1: 4, 2: 4, 3: 12}
EXAM_TOTAL_PASS = 30
POINTS_PER_Q = 2


def build_questions_index(rows):
    """db.get_all_questions() 결과(sqlite3.Row 목록)를 id -> dict로 변환."""
    return {r["id"]: dict(r) for r in rows}


def get_core_groups(questions):
    """subject -> {core_id: [qid, ...]} : 같은 개념(core_id)의 문항 변형들을 묶는다(개념형 문제 전용)."""
    groups = {1: {}, 2: {}, 3: {}}
    for qid, q in questions.items():
        if q["source"] != "concept":
            continue
        groups[q["subject"]].setdefault(q["core_id"], []).append(qid)
    return groups


def pick_pool(questions, subjects, limit=None):
    """subjects에 속한 개념형 문항을 core_id(개념) 기준으로 중복 없이 하나씩 무작위로 뽑는다."""
    groups = get_core_groups(questions)
    pool = []
    for s in subjects:
        for variant_ids in groups[s].values():
            pool.append(random.choice(variant_ids))
    random.shuffle(pool)
    if limit:
        pool = pool[:limit]
    return pool


def pick_exam_pool(questions):
    """실전 시험 모드: 과목별 공식 문항 수(10/10/30)만큼 개념 중복 없이 무작위로 뽑되,
    실제 시험지처럼 1->2->3과목 순서로 정렬해 반환한다(과목 내부만 무작위)."""
    groups = get_core_groups(questions)
    ids = []
    for s, n in EXAM_SUBJECT_COUNTS.items():
        core_ids = list(groups[s].keys())
        random.shuffle(core_ids)
        subj_ids = [random.choice(groups[s][c]) for c in core_ids[:n]]
        ids.extend(subj_ids)
    return ids


def pick_cbt_pool(questions, cbt_ids, subjects, limit=None):
    """CBT 연습 모드: 선택한 과목의 기출문제 중 무작위로 뽑는다."""
    ids = [qid for qid in cbt_ids if questions[qid]["subject"] in subjects]
    random.shuffle(ids)
    if limit:
        ids = ids[:limit]
    return ids


def pick_cbt_exam_pool(questions, cbt_ids):
    """CBT 실전 모드: 실제 ADsP 출제 기준과 동일한 비율로 기출문제 풀에서 무작위로 뽑되,
    1->2->3과목 순서로 정렬해 반환한다(과목 내부만 무작위)."""
    ids = []
    for s, n in EXAM_SUBJECT_COUNTS.items():
        subj_ids = [qid for qid in cbt_ids if questions[qid]["subject"] == s]
        random.shuffle(subj_ids)
        ids.extend(subj_ids[:n])
    return ids


def _normalize_answer(s):
    return re.sub(r"\s+", "", s.strip().lower())


def answer_matches(user_input, correct_text):
    """개념 카드 입력형 채점: 괄호 안 영문 약어/원어 표기도 정답으로 인정한다."""
    if not user_input or not user_input.strip():
        return False
    variants = {correct_text}
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", correct_text)
    if m:
        variants.add(m.group(1).strip())
        variants.add(m.group(2).strip())
    u = _normalize_answer(user_input)
    return any(u == _normalize_answer(v) for v in variants if v)


def make_blank_sentence(explanation, answer_text):
    """해설 문장 안에서 정답 텍스트(또는 괄호 앞부분)를 찾아 빈칸으로 치환한다.
    찾지 못하면 None을 반환해 호출부가 단어 입력형으로 대체하도록 한다."""
    candidates = [answer_text]
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", answer_text)
    if m:
        candidates = [answer_text, m.group(1).strip()]
    for cand in candidates:
        if cand and cand in explanation:
            return explanation.replace(cand, "〔　　　　〕", 1)
    return None


def group_ids_by_tag(questions, ids):
    """qid 목록을 (과목, 태그) 기준으로 묶어 과목·태그 순으로 정렬해 반환한다."""
    groups = {}
    for qid in ids:
        q = questions.get(qid)
        if q is None:
            continue
        key = (q["subject"], q["tag"])
        groups.setdefault(key, []).append(qid)
    return dict(sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])))


def build_ox_pool(concepts):
    """개념 목록으로부터 OX 퀴즈 문제 풀을 만든다(참/거짓 문장을 무작위로 섞어 생성)."""
    pool = []
    for c in concepts:
        choices = [c["choice1"], c["choice2"], c["choice3"], c["choice4"]]
        correct_idx = c["answer"] - 1
        is_true = random.random() < 0.5
        if is_true:
            statement = choices[correct_idx]
        else:
            wrong_idx = random.choice([i for i in range(4) if i != correct_idx])
            statement = choices[wrong_idx]
        pool.append({
            "qid": c["id"], "subject": c["subject"], "tag": c["tag"], "stem": c["question"],
            "statement": statement, "truth": is_true, "explanation": c["explanation"],
        })
    random.shuffle(pool)
    return pool
