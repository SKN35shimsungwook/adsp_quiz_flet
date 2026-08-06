# -*- coding: utf-8 -*-
"""앱의 쓰기 가능한 데이터 디렉터리를 결정한다.

Flet 런타임은 모바일/데스크톱에서 앱을 실행할 때 FLET_APP_STORAGE_DATA 환경변수에
플랫폼별 쓰기 가능한 앱 데이터 디렉터리를 동기적으로 넣어준다(공식 문서 권장 방식).
`flet run --web` 등 웹 프리뷰로 개발/테스트할 때는 이 변수가 없으므로 프로젝트 폴더
아래 _devdata를 대신 사용한다.
"""
import os

_env_dir = os.environ.get("FLET_APP_STORAGE_DATA")
if _env_dir:
    DATA_DIR = _env_dir
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "_devdata")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "quiz.db")
