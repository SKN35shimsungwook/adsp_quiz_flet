# -*- coding: utf-8 -*-
"""quiz_data.py(정적 문제 데이터)로부터 SQLite DB를 만든다.
- questions 테이블: 문제 은행(앱 시작마다 quiz_data.py 기준으로 재생성됨). source 컬럼으로 'concept'/'cbt' 구분
- attempts 등 사용자 기록 테이블: 재실행해도 보존됨(=오답노트/통계 데이터)
"""
import os
import sqlite3

from quiz_data import CONCEPT_ROWS, CBT_ROWS
from storage import DB_PATH


def _to_row(t):
    # (id, subject, tag, question, choice1..4, answer, explanation, core_id, source)
    _id, subject, tag, question, c1, c2, c3, c4, answer, explanation, core_id, source = t
    return (subject, tag, question, c1, c2, c3, c4, answer, explanation, core_id, source)


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS questions")
    cur.execute("""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject INTEGER NOT NULL,
            tag TEXT NOT NULL,
            question TEXT NOT NULL,
            choice1 TEXT NOT NULL,
            choice2 TEXT NOT NULL,
            choice3 TEXT NOT NULL,
            choice4 TEXT NOT NULL,
            answer INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            core_id INTEGER NOT NULL,
            source TEXT NOT NULL DEFAULT 'concept'
        )
    """)

    rows = [_to_row(t) for t in CONCEPT_ROWS] + [_to_row(t) for t in CBT_ROWS]
    cur.executemany(
        "INSERT INTO questions (subject, tag, question, choice1, choice2, choice3, choice4, "
        "answer, explanation, core_id, source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            question_id INTEGER NOT NULL REFERENCES questions(id),
            chosen INTEGER NOT NULL,
            is_correct INTEGER NOT NULL,
            ts TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_attempts_q ON attempts(question_id)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            question_id INTEGER NOT NULL REFERENCES questions(id),
            ts TEXT NOT NULL,
            UNIQUE(user, question_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ox_wrong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            concept_qid INTEGER NOT NULL REFERENCES questions(id),
            ts TEXT NOT NULL,
            UNIQUE(user, concept_qid)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS card_wrong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            concept_qid INTEGER NOT NULL REFERENCES questions(id),
            ts TEXT NOT NULL,
            UNIQUE(user, concept_qid)
        )
    """)

    con.commit()
    con.close()


if __name__ == "__main__":
    main()
