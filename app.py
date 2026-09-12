
import re
import streamlit as st
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

st.set_page_config(page_title="서·논술형 자동 채점기", page_icon="📝", layout="wide")

# -----------------------------
# 공통 유틸
# -----------------------------
def norm(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[“”\"'‘’·•,.:;!?()\[\]{}<>/\\_-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def has_any(text: str, terms: List[str]) -> bool:
    t = norm(text)
    return any(norm(x) in t for x in terms)

def count_groups(text: str, groups: List[List[str]]) -> int:
    return sum(1 for g in groups if has_any(text, g))

def matched_groups(text: str, groups: List[Tuple[str, List[str]]]) -> List[str]:
    return [name for name, terms in groups if has_any(text, terms)]

def contains_forbidden(text: str, forbidden: List[str]) -> List[str]:
    return [x for x in forbidden if has_any(text, [x])]

# -----------------------------
# 설명 방법 판정
# "용어"가 없어도 실제 의미 구조가 있으면 방법 사용으로 인정.
# 다만 학생이 괄호 등으로 방법명을 직접 선택한 경우, 실제 서술과 일치해야 함.
# -----------------------------
METHOD_ALIASES = {
    "정의": ["정의"],
    "예시": ["예시", "예"],
    "인과": ["인과", "원인과 결과"],
    "분석": ["분석"],
    "비교와 대조": ["비교와 대조", "비교 대조", "비교", "대조"],
    "분류와 구분": ["분류와 구분", "분류 구분", "분류", "구분"],
}

def canonical_method(label: str) -> Optional[str]:
    t = norm(label)
    for canon, aliases in METHOD_ALIASES.items():
        if any(norm(a) == t or norm(a) in t for a in aliases):
            return canon
    return None

def detect_methods(sentence: str) -> List[str]:
    """
    키워드만으로 확정하지 않고, 문장 구조를 보조적으로 판단.
    규칙 기반이라 완전한 의미 분석은 아니므로, 교사가 최종 확인할 수 있도록
    '감지된 방법'과 근거를 함께 보여 줌.
    """
    t = norm(sentence)
    detected = []

    # 정의: 대상의 뜻/개념을 규정
    if re.search(r"(이란|란|을 말한다|를 말한다|뜻은|의미는|이라고 한다|라고 한다)", t):
        detected.append("정의")

    # 예시: 일반 내용을 구체화하는 표지
    if re.search(r"(예를 들어|예로는|대표적으로|예컨대|와 같은|같은 경우)", t):
        detected.append("예시")

    # 인과: 원인 -> 결과 구조
    if re.search(r"(때문에|하므로|이므로|해서|하여|따라서|결과적으로|그 결과)", t):
        detected.append("인과")

    # 분석: 하나의 대상 안의 구성 요소/부분
    if re.search(r"(요소|부분|구성|이루어져|이루어진|담겨 있다|담겨있다)", t):
        # '담겨 있다'는 3세트 인간 예술 요소 분석에서 허용
        detected.append("분석")

    # 비교와 대조: 둘 이상의 대상 + 차이/공통 관계
    if re.search(r"(반면|하지만|그러나|와 달리|과 달리|공통점|차이점|둘 다|한편)", t):
        detected.append("비교와 대조")

    # 분류와 구분: 기준에 따라 종류를 나눔/묶음
    if re.search(r"(나뉜다|나누어|나눌 수|구분|분류|묶을 수|종류로)", t):
        detected.append("분류와 구분")

    # 중복 제거
    return list(dict.fromkeys(detected))

# -----------------------------
# 공통 데이터
# -----------------------------
COMMON_METHOD_GUIDE = {
    "정의": "대상의 뜻이나 개념을 밝힘",
    "예시": "일반적인 내용을 구체적 사례로 보여 줌",
    "인과": "원인과 결과의 관계를 설명함",
    "분석": "하나의 대상을 구성하는 요소나 부분으로 나누어 설명함",
    "비교와 대조": "둘 이상의 대상의 공통점이나 차이점을 드러냄",
    "분류와 구분": "일정한 기준에 따라 종류를 묶거나 나눔",
}

# 1~3세트 서논술형 1
FILL_RULES = {
    "1": {
        "㉠": {
            "required_groups": [
                ("쉬운 특성", ["쉬운", "비교적 쉬운", "어렵지 않은", "큰 노력이 필요하지 않은", "큰 노력을 들일 필요가 없는"]),
                ("과제/취미 대상", ["과제", "취미"]),
            ],
            "forbidden": ["어려운 과제", "도전이 필요한 과제"],
            "model": "비교적 쉬운 취미 생활이나 큰 노력을 들일 필요가 없는 과제",
            "allow_semantic": True,
        },
        "㉡": {
            "required_groups": [
                ("혼자", ["혼자", "개인적으로", "혼자서"]),
                ("집중", ["집중", "집중해서", "집중하는"]),
            ],
            "optional_groups": [
                ("연습", ["연습", "반복"]),
                ("익숙해질 때까지", ["익숙해질 때까지", "익숙해질 때"]),
                ("차분함", ["차분", "조용"]),
            ],
            "forbidden": ["다른 사람들과 함께", "공부 모임", "모임을 만들어"],
            "model": "충분히 연습하며 익숙해질 때까지 차분하게 혼자 집중함",
            "allow_semantic": True,
        },
        "㉢": {
            "required_exact": ["사회적 억제"],
            "forbidden": ["사회적 촉진"],
            "model": "사회적 억제",
            "allow_semantic": False,
        },
    },
    "2": {
        "㉠": {
            "required_groups": [
                ("높은 곳", ["높은 곳", "높은 위치", "높은 데"]),
                ("고여 있음", ["고여 있는 물", "고인 물", "머물러 있는 물", "흐르지 않는 물"]),
            ],
            "forbidden": ["흐르는 물"],
            "model": "높은 곳에 고여 있는 물",
            "allow_semantic": True,
        },
        "㉡": {
            "required_groups": [
                ("전하", ["전하"]),
                ("이동하지 않음", ["이동하지", "움직이지", "정지", "머물러"]),
            ],
            "forbidden": ["전하가 이동함", "전하가 흐름"],
            "model": "전하가 이동하지 않고 머물러 있음",
            "allow_semantic": True,
        },
        "㉢": {
            "required_groups": [
                ("위험하지 않음", ["위험하지", "위험이 없", "위험성이 없", "피해가 없", "별 피해가 없"]),
            ],
            "forbidden": ["위험하다", "감전 위험이 크"],
            "model": "위험하지 않음",
            "allow_semantic": True,
        },
    },
    "3": {
        "㉠": {
            "required_groups": [
                ("로봇", ["로봇"]),
                ("완벽한 수행", ["완벽", "실수 없이", "한 번의 실수 없이"]),
                ("감동 없음", ["마음을 울리지", "감동을 주지", "감동이 없", "울림이 없"]),
            ],
            "forbidden": [],
            "model": "한 번의 실수 없이 완벽하게 피겨 스케이팅을 하지만 사람의 마음을 울리지 못하는 로봇",
            "allow_semantic": True,
        },
        "㉡": {
            "required_groups_any": [
                ("감정 없음", ["감정이 없", "감정을 느끼지 못", "인간과 같은 감정이 없"]),
                ("철학 없음", ["독자적인 철학이 없", "자기만의 철학이 없"]),
                ("이야기 없음", ["독자적인 이야기가 없", "자기만의 이야기가 없"]),
            ],
            "required_groups": [
                ("예술로 보기 어려움", ["예술로 보기 어렵", "예술이라고 보기 어렵", "예술로 볼 수 없"]),
            ],
            "forbidden": ["기술이 부족", "가치가 전혀 없"],
            "model": "감정을 느끼지 못하고 독자적인 철학이나 이야기가 없으므로 예술로 보기 어렵다.",
            "allow_semantic": True,
        },
        "㉢": {
            "required_groups_any": [
                ("미술계 변화", ["미술계에 큰 변화", "미술계에 변화", "기존 미술계에 영향"]),
                ("예술 범주 확장", ["예술의 범주를 확장", "예술의 범위를 넓", "예술 범주를 넓"]),
            ],
            "forbidden": ["가치가 전혀 없", "아무 가치가 없"],
            "model": "기존 미술계에 큰 변화를 가져왔고 예술의 범주를 확장할 수 있다는 점에서 상징적인 가치가 있다.",
            "allow_semantic": True,
        },
    },
}

# 서논술형 2: 선택 가능한 방법별 모범 답안
METHOD_MODELS = {
    "1": {
        "비교와 대조": "비교적 쉬운 과제는 다른 사람들과 함께하는 것이 효율적이지만, 지나치게 어렵거나 도전이 필요한 과제는 차분하게 혼자 집중하는 것이 좋다.",
        "예시": "예를 들어 평소 친숙하고 좋아하는 과목이라면 공부 모임을 만들어 다른 사람들과 함께 공부할 수 있다.",
        "분류와 구분": "과제는 난이도에 따라 비교적 쉬운 과제와 지나치게 어렵거나 도전이 필요한 과제로 나누어 볼 수 있다.",
    },
    "2": {
        "정의": "정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기와 그로 인한 전기 현상을 말한다.",
        "인과": "정전기는 전압이 매우 높지만 전하가 이동하지 않고 머물러 있기 때문에 위험하지 않다.",
        "비교와 대조": "실생활에서 쓰는 전기는 전하가 이동하지만 정전기는 전하가 이동하지 않고 머물러 있다는 차이가 있다.",
    },
    "3": {
        "비교와 대조": "인간의 작품에는 작가의 감정과 철학, 경험 등이 담겨 있지만 인공 지능은 감정이나 독자적인 철학과 이야기가 없다는 차이가 있다.",
        "인과": "인공 지능이 그린 그림은 기존 미술계에 큰 변화를 가져왔고 예술의 범주를 확장할 수 있으므로 상징적인 가치가 있다.",
        "분석": "인간의 작품에는 작가의 감정과 철학, 삶의 경험, 관점, 환경 등의 여러 요소가 종합적으로 담겨 있다.",
        "예시": "예를 들어 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅하더라도 우리의 마음을 울리지는 못한다.",
    },
}

ALLOWED_METHODS = {
    "1": ["비교와 대조", "예시", "분류와 구분"],
    "2": ["정의", "인과", "비교와 대조"],
    "3": ["비교와 대조", "인과", "분석", "예시"],
}

# 세트별 지문 핵심 의미/결론 방향/오개념 금지
CONTENT_RULES_Q2 = {
    "1": {
        "positive_groups": [
            ("쉬운 과제", ["쉬운 과제", "비교적 쉬운", "큰 노력이 필요하지 않은", "친숙", "좋아하는 과목"]),
            ("함께", ["다른 사람들과 함께", "함께 공부", "공부 모임", "카페", "커피숍", "도서관"]),
            ("어려운 과제", ["어려운 과제", "지나치게 어렵", "도전이 필요한", "복잡한 과제"]),
            ("혼자 집중", ["혼자 집중", "혼자 공부", "차분하게 혼자", "익숙해질 때까지"]),
        ],
        "forbidden": [
            "어려운 과제는 다른 사람들과 함께하는 것이 더 좋다",
            "쉬운 과제는 혼자 집중하는 것이 더 좋다",
            "인지 부하", "뇌과학", "집중력이 높아진다 때문에"
        ],
        "conclusion_groups": [
            ["쉬운", "함께"],
            ["어려운", "혼자"],
        ],
    },
    "2": {
        "positive_groups": [
            ("정전기", ["정전기"]),
            ("전하 정지", ["전하가 이동하지", "전하가 정지", "전하가 머물러"]),
            ("높은 전압", ["전압이 매우 높", "전압이 높"]),
            ("위험하지 않음", ["위험하지", "위험이 없", "피해가 없"]),
            ("실생활 전기", ["실생활 전기", "우리가 쓰는 전기"]),
        ],
        "forbidden": [
            "정전기는 전하가 이동한다",
            "정전기는 위험하다",
            "전압이 높아서 위험하다",
            "전기는 정전기와 실생활 전기로 나뉜다",
        ],
        "conclusion_groups": [
            ["전하", "이동하지"],
            ["위험하지"],
        ],
    },
    "3": {
        "positive_groups": [
            ("인간 예술", ["인간의 작품", "인간의 예술", "작가"]),
            ("감정/철학/경험", ["감정", "철학", "경험", "관점", "환경"]),
            ("AI 결핍", ["감정이 없", "철학이 없", "이야기가 없", "감정을 느끼지 못"]),
            ("예술로 보기 어려움", ["예술로 보기 어렵", "예술로 볼 수 없"]),
            ("AI 가치", ["미술계에 변화", "예술의 범주를 확장", "상징적인 가치"]),
        ],
        "forbidden": [
            "인공 지능의 그림은 가치가 전혀 없다",
            "인공 지능은 기술이 부족해서 예술이 아니다",
            "인공 지능이 사람보다 창의적이다",
            "예술은 인간 예술과 인공 지능 예술로 나뉜다",
        ],
        "conclusion_groups": [
            ["예술로 보기 어렵"],
            ["가치", "변화", "확장"],
        ],
    },
}

# 서논술형3
VIDEO_RULES = {
    "1": {
        "visual": {
            "positive": [
                ("혼자/개인", ["혼자", "한 학생", "한 명"]),
                ("차분/집중", ["차분", "집중", "조용"]),
                ("연습", ["연습", "반복", "익숙해질 때까지"]),
            ],
            "forbidden": ["친구들과 떠들", "여러 명이 신나게", "활기찬 모임"],
            "model": "조용한 공간에서 한 학생이 혼자 어려운 과제를 반복해 연습하며 집중하는 모습을 보여 준다.",
        },
        "visual_effect": {
            "body_groups": [
                ("어려운 과제", ["어려운 과제", "도전이 필요한 과제"]),
                ("혼자 집중", ["혼자 집중", "차분하게 혼자", "혼자 공부"]),
                ("연습/익숙", ["연습", "익숙해질 때까지"]),
            ],
            "model": "어려운 과제는 익숙해질 때까지 차분하게 혼자 집중하는 것이 좋다는 내용을 시각적으로 드러낸다.",
        },
        "audio": {
            "positive": [
                ("조용함", ["조용", "고요", "소음을 줄", "소음을 최소", "무음", "배경음악 없음", "작은 소리"]),
            ],
            "forbidden": ["큰 대화 소리", "빠르고 신나는 음악", "시끄러운"],
            "model": "배경음악과 주변 소음을 최소화하고 책장 넘기는 작은 소리만 들려준다.",
        },
        "audio_effect": {
            "body_groups": [
                ("차분함/집중", ["차분", "집중", "고요"]),
                ("혼자", ["혼자"]),
                ("어려운 과제", ["어려운 과제", "도전이 필요한 과제"]),
            ],
            "model": "고요한 분위기를 조성하여 어려운 과제를 할 때 차분하게 혼자 집중하는 환경이 효과적임을 강조한다.",
        },
    },
    "2": {
        "visual": {
            "positive": [
                ("높은 곳", ["높은 곳", "높은 위치"]),
                ("고여 있음", ["고여", "고인", "흐르지 않", "떨어지지 않", "머물러"]),
            ],
            "forbidden": ["폭포처럼 흘러", "콸콸 흐르", "계속 이동"],
            "model": "높은 곳에 많은 물이 고여 있지만 아래로 흐르거나 떨어지지 않는 모습을 보여 준다.",
        },
        "visual_effect": {
            "body_groups": [
                ("높은 전압", ["높은 전압", "전압이 높"]),
                ("전하 정지", ["전하가 이동하지", "전하가 머물러", "전하가 정지"]),
                ("위험하지 않음", ["위험하지", "위험이 없", "피해가 없"]),
            ],
            "model": "높은 곳에 물이 고여 있지만 떨어지지 않는 모습을 통해 전압은 높지만 전하가 이동하지 않아 위험하지 않다는 특성을 드러낸다.",
        },
        "audio": {
            "positive": [
                ("흐르는 소리 없음/고요", ["물이 흐르는 소리를 사용하지", "흐르는 소리 없음", "무음", "고요", "조용"]),
            ],
            "forbidden": ["큰 폭포 소리", "물이 거세게 흐르는 소리"],
            "model": "물이 흐르거나 떨어지는 소리를 사용하지 않고 고요하게 연출한다.",
        },
        "audio_effect": {
            "body_groups": [
                ("전하 정지", ["전하가 이동하지", "전하가 머물러", "전하가 정지"]),
                ("위험하지 않음", ["위험하지", "위험이 없"]),
            ],
            "model": "물이 흐르는 소리가 들리지 않게 하여 전하가 이동하지 않고 머물러 있다는 특성을 강조한다.",
        },
    },
    "3": {
        "visual": {
            "positive": [
                ("감정/철학", ["감정", "철학"]),
                ("경험/관점/환경", ["경험", "관점", "환경"]),
                ("노력/열정", ["노력", "열정", "오랜 시간", "수정"]),
                ("창작자", ["작가", "화가"]),
            ],
            "forbidden": ["인공 지능이 그림을 만드는 모습만", "로봇이 완벽하게 그리는 모습"],
            "model": "화가가 자신의 삶의 경험과 주변 환경을 떠올리며 감정을 담아 그림을 완성해 가는 모습을 보여 준다.",
        },
        "visual_effect": {
            "body_groups": [
                ("감정/철학", ["감정", "철학"]),
                ("경험/관점/환경", ["경험", "관점", "환경"]),
                ("마음의 울림", ["마음을 울리", "감동", "울림"]),
            ],
            "model": "작가의 창작 과정을 보여 줌으로써 인간의 작품에는 작가의 감정과 경험, 관점 등이 담긴다는 점을 드러낸다.",
        },
        "audio": {
            "positive": [
                ("작가 목소리/이야기", ["작가의 목소리", "자신의 감정", "자신의 생각", "이야기"]),
                ("감정 음악", ["감정적인 음악", "감정의 변화를", "배경음악", "잔잔한 음악"]),
            ],
            "forbidden": ["기계음만", "메트로놈만"],
            "model": "작가가 자신의 감정과 생각을 이야기하는 목소리와 감정의 변화를 느낄 수 있는 배경음악을 들려준다.",
        },
        "audio_effect": {
            "body_groups": [
                ("감정/철학/이야기", ["감정", "철학", "이야기"]),
                ("마음의 울림", ["마음을 울리", "감동", "울림"]),
            ],
            "model": "작가의 목소리와 음악을 통해 인간의 작품에 고유한 감정과 이야기가 담겨 있고 그것이 감상자의 마음에 울림을 줄 수 있음을 강조한다.",
        },
    },
}

# -----------------------------
# 채점 함수
# -----------------------------
def grade_fill(set_no: str, blank: str, answer: str) -> Dict:
    rule = FILL_RULES[set_no][blank]
    reasons = []
    ok = True

    forbidden_hits = contains_forbidden(answer, rule.get("forbidden", []))
    if forbidden_hits:
        ok = False
        reasons.append(f"오개념/반대 방향 표현 감지: {', '.join(forbidden_hits)}")

    if "required_exact" in rule:
        if not has_any(answer, rule["required_exact"]):
            ok = False
            reasons.append(f"개념명 자체가 필요함: {rule['required_exact'][0]}")
    else:
        for name, terms in rule.get("required_groups", []):
            if not has_any(answer, terms):
                ok = False
                reasons.append(f"필수 의미 누락: {name}")
        any_groups = rule.get("required_groups_any", [])
        if any_groups and not any(has_any(answer, terms) for _, terms in any_groups):
            ok = False
            reasons.append("필수 의미군 중 하나 이상이 필요함: " + ", ".join(name for name, _ in any_groups))

    if ok:
        reasons.append("필수 의미와 결론 방향을 충족함.")
    return {"pass": ok, "reasons": reasons, "model": rule["model"]}

def method_structure_ok(method: str, sentence: str) -> Tuple[bool, List[str]]:
    detected = detect_methods(sentence)
    reasons = []
    if method in detected:
        return True, [f"실제 문장 구조에서 '{method}' 특성이 감지됨."]
    # 규칙 보완: 특정 세트에서 분석은 '감정/철학/경험/관점/환경' 열거로도 인정
    if method == "분석":
        parts = count_groups(sentence, [
            ["감정"], ["철학"], ["경험"], ["관점"], ["환경"]
        ])
        if parts >= 2:
            return True, ["구성 요소가 2개 이상 제시되어 '분석' 구조로 인정."]
    # 비교와 대조 보완: 대조 표지가 없더라도 둘 이상의 대상 차이가 명백한 경우
    if method == "비교와 대조":
        if (has_any(sentence, ["실생활 전기", "우리가 쓰는 전기"]) and has_any(sentence, ["정전기"])) or \
           (has_any(sentence, ["인간의 작품", "인간의 예술"]) and has_any(sentence, ["인공 지능", "AI"])) or \
           (has_any(sentence, ["쉬운 과제", "비교적 쉬운"]) and has_any(sentence, ["어려운 과제", "도전이 필요한"])):
            return True, ["둘 이상의 대상 차이가 명백하여 '비교와 대조'로 인정."]
    return False, [f"선택한 방법 '{method}'의 실제 서술 특성이 충분히 드러나지 않음. 감지된 방법: {detected or '없음'}"]

def content_grounding_ok(set_no: str, sentence: str) -> Tuple[bool, List[str]]:
    rule = CONTENT_RULES_Q2[set_no]
    reasons = []
    if not matched_groups(sentence, rule["positive_groups"]):
        return False, ["지문 핵심 내용과 대응되는 의미가 확인되지 않음."]
    forbidden_hits = contains_forbidden(sentence, rule["forbidden"])
    if forbidden_hits:
        return False, ["지문에 없는 주장 또는 오개념 감지: " + ", ".join(forbidden_hits)]
    return True, ["지문 핵심 내용과 대응되고, 금지 오개념이 감지되지 않음."]

def conclusion_direction_ok(set_no: str, s1: str, s2: str) -> Tuple[bool, List[str]]:
    combined = f"{s1} {s2}"
    reasons = []

    if set_no == "1":
        easy_together = has_any(combined, ["쉬운", "비교적 쉬운", "친숙", "좋아하는 과목"]) and \
                        has_any(combined, ["함께", "공부 모임", "카페", "커피숍", "도서관"])
        hard_alone = has_any(combined, ["어려운", "도전이 필요한", "복잡한"]) and \
                     has_any(combined, ["혼자", "차분", "익숙해질 때까지"])
        if easy_together or hard_alone:
            return True, ["과제 난이도에 따라 학습 전략이 달라진다는 방향이 드러남."]
        return False, ["요구 결론(쉬운 과제→함께 / 어려운 과제→혼자 집중) 방향이 드러나지 않음."]

    if set_no == "2":
        # 정의/비교 문장 + 인과 문장 모두 허용. 최소한 정전기 특성 결론이 있어야 함.
        if has_any(combined, ["정전기"]) and \
           (has_any(combined, ["전하가 이동하지", "전하가 정지", "전하가 머물러"]) or
            has_any(combined, ["위험하지", "위험이 없"])):
            return True, ["정전기의 핵심 특성 방향이 드러남."]
        return False, ["요구 결론(정전기는 전하가 이동하지 않고 머무는 전기이며 위험하지 않음) 방향이 부족함."]

    if set_no == "3":
        negative = has_any(combined, ["예술로 보기 어렵", "예술로 볼 수 없", "감정이 없", "철학이 없", "이야기가 없"])
        value = has_any(combined, ["미술계에 변화", "예술의 범주를 확장", "상징적인 가치"])
        # 둘 중 하나만으로도 지문의 시각 일부는 설명하지만, 전체 주제 완성도는 둘 다 있을 때 가장 높음.
        if negative or value:
            return True, ["AI 그림을 바라보는 지문의 판단 방향이 드러남."]
        return False, ["요구 결론(AI 그림의 예술성 한계 또는 상징적 가치)에 대한 판단 방향이 드러나지 않음."]

    return True, []

def grade_q2(set_no: str, s1: str, m1_label: str, s2: str, m2_label: str) -> Dict:
    reasons = []
    m1 = canonical_method(m1_label)
    m2 = canonical_method(m2_label)

    if not m1 or not m2:
        return {"pass": False, "reasons": ["설명 방법 명칭을 6개 표준 방법 중 하나로 식별할 수 없음."]}

    if m1 == m2:
        return {"pass": False, "reasons": [f"(1), (2)에 같은 설명 방법 '{m1}'을 사용함. 서로 다른 방법이어야 함."]}

    # 허용 방법 체크
    if m1 not in ALLOWED_METHODS[set_no]:
        reasons.append(f"(1)의 '{m1}'은 이 지문에서 안전하게 인정하기 어려운 방법임.")
    if m2 not in ALLOWED_METHODS[set_no]:
        reasons.append(f"(2)의 '{m2}'은 이 지문에서 안전하게 인정하기 어려운 방법임.")

    ms1, r1 = method_structure_ok(m1, s1)
    ms2, r2 = method_structure_ok(m2, s2)
    reasons.extend(["(1) " + x for x in r1])
    reasons.extend(["(2) " + x for x in r2])

    g1, gr1 = content_grounding_ok(set_no, s1)
    g2, gr2 = content_grounding_ok(set_no, s2)
    reasons.extend(["(1) " + x for x in gr1])
    reasons.extend(["(2) " + x for x in gr2])

    cd, cr = conclusion_direction_ok(set_no, s1, s2)
    reasons.extend(cr)

    # 두 문장의 실제 감지 방법이 같은 경우도 방지
    detected1 = set(detect_methods(s1))
    detected2 = set(detect_methods(s2))
    same_actual = bool(detected1 and detected2 and detected1 == detected2 and m1 != m2)
    if same_actual:
        reasons.append("괄호의 방법명은 다르지만 실제 문장 구조가 같은 방법으로 감지됨.")

    passed = (
        m1 in ALLOWED_METHODS[set_no]
        and m2 in ALLOWED_METHODS[set_no]
        and ms1 and ms2 and g1 and g2 and cd
        and not same_actual
    )

    return {
        "pass": passed,
        "reasons": reasons,
        "models": METHOD_MODELS[set_no],
    }

def overlap_link_ok(element: str, effect: str) -> bool:
    """
    요소와 효과의 연결성:
    완전한 어절 일치만 요구하지 않고, 핵심 의미군의 교집합이 있으면 인정.
    """
    e = norm(element)
    f = norm(effect)
    common_keywords = [
        "혼자", "집중", "차분", "조용", "고요", "연습", "반복",
        "높은 곳", "고여", "흐르지", "전하", "감정", "철학",
        "경험", "관점", "환경", "작가", "화가", "목소리", "음악"
    ]
    return any(k in e and k in f for k in common_keywords)

def grade_video_part(set_no: str, part: str, answer: str, related_element: str = "") -> Dict:
    rule = VIDEO_RULES[set_no][part]
    reasons = []
    ok = True

    forbidden_hits = contains_forbidden(answer, rule.get("forbidden", []))
    if forbidden_hits:
        ok = False
        reasons.append("오개념/반대 방향 표현 감지: " + ", ".join(forbidden_hits))

    if part in ("visual", "audio"):
        positives = rule["positive"]
        hits = matched_groups(answer, positives)
        if not hits:
            ok = False
            reasons.append("해당 장면에서 요구한 핵심 특성이 실제 연출로 드러나지 않음.")
        else:
            reasons.append("반영된 핵심 특성: " + ", ".join(hits))
    else:
        hits = matched_groups(answer, rule["body_groups"])
        if not hits:
            ok = False
            reasons.append("효과 설명에 본문 근거가 없음.")
        else:
            reasons.append("본문 근거로 확인된 의미: " + ", ".join(hits))

        if related_element and not overlap_link_ok(related_element, answer):
            ok = False
            reasons.append("효과가 앞서 작성한 요소와 직접 연결되지 않음.")
        elif related_element:
            reasons.append("효과가 앞서 작성한 요소와 연결됨.")

    if ok:
        reasons.append("결론 방향과 본문 근거를 충족함.")
    return {"pass": ok, "reasons": reasons, "model": rule["model"]}

# -----------------------------
# UI
# -----------------------------
st.title("📝 2회고사 대비 서·논술형 자동 채점기")
st.caption("1~3세트 · 의미 기반 허용 + 오개념 차단 + 설명 방법 일치 검증 + 결론 방향 확인")

with st.expander("공통 설명 방법 판정 기준"):
    for k, v in COMMON_METHOD_GUIDE.items():
        st.write(f"- **{k}**: {v}")

set_no = st.selectbox("세트 선택", ["1", "2", "3"], format_func=lambda x: f"{x}번 세트")
qtype = st.radio("문항 선택", ["서·논술형 1", "서·논술형 2", "서·논술형 3"], horizontal=True)

if qtype == "서·논술형 1":
    st.subheader(f"{set_no}번 세트 — 표 빈칸 채우기")
    answers = {}
    cols = st.columns(3)
    for i, blank in enumerate(["㉠", "㉡", "㉢"]):
        with cols[i]:
            answers[blank] = st.text_area(f"{blank} 답안", height=120, key=f"{set_no}-{blank}")

    if st.button("채점", type="primary"):
        total = 0
        for blank in ["㉠", "㉡", "㉢"]:
            result = grade_fill(set_no, blank, answers[blank])
            if result["pass"]:
                total += 1
                st.success(f"{blank}: 정답")
            else:
                st.error(f"{blank}: 오답")
            for r in result["reasons"]:
                st.write("•", r)
            st.info(f"모범 답안: {result['model']}")
        st.metric("정답 수", f"{total}/3")

elif qtype == "서·논술형 2":
    st.subheader(f"{set_no}번 세트 — 설명 방법 2가지 활용")
    left, right = st.columns(2)
    with left:
        m1 = st.selectbox("(1) 설명 방법", list(COMMON_METHOD_GUIDE.keys()), key="m1")
        s1 = st.text_area("(1) 답안", height=170)
    with right:
        m2 = st.selectbox("(2) 설명 방법", list(COMMON_METHOD_GUIDE.keys()), key="m2")
        s2 = st.text_area("(2) 답안", height=170)

    if st.button("채점", type="primary"):
        result = grade_q2(set_no, s1, m1, s2, m2)
        if result["pass"]:
            st.success("정답")
        else:
            st.error("오답")
        for r in result["reasons"]:
            st.write("•", r)

        st.markdown("### 선택 가능한 설명 방법별 모범 답안")
        for method, model in result["models"].items():
            st.write(f"**{method}**")
            st.write(model)

elif qtype == "서·논술형 3":
    st.subheader(f"{set_no}번 세트 — 영상 기획안")
    visual = st.text_area("Ⓐ 시각 요소", height=130)
    visual_effect = st.text_area("시각 요소의 효과", height=130)
    audio = st.text_area("Ⓑ 청각 요소", height=130)
    audio_effect = st.text_area("청각 요소의 효과", height=130)

    if st.button("채점", type="primary"):
        parts = [
            ("visual", "Ⓐ 시각 요소", visual, ""),
            ("visual_effect", "Ⓐ 효과", visual_effect, visual),
            ("audio", "Ⓑ 청각 요소", audio, ""),
            ("audio_effect", "Ⓑ 효과", audio_effect, audio),
        ]
        passed_count = 0
        for key, label, ans, rel in parts:
            result = grade_video_part(set_no, key, ans, rel)
            if result["pass"]:
                passed_count += 1
                st.success(f"{label}: 통과")
            else:
                st.error(f"{label}: 미통과")
            for r in result["reasons"]:
                st.write("•", r)
            st.info(f"모범 답안: {result['model']}")

        # 문항에 [총 6점]이 명시된 3세트 기준 부분점수 예시
        if set_no == "3":
            # 시각 요소 1, 시각 효과 2, 청각 요소 1, 청각 효과 2
            score_map = {
                "visual": 1,
                "visual_effect": 2,
                "audio": 1,
                "audio_effect": 2,
            }
            score = 0
            for key, _, ans, rel in parts:
                if grade_video_part(set_no, key, ans, rel)["pass"]:
                    score += score_map[key]
            st.metric("3세트 서·논술형 3 점수", f"{score}/6")
            st.caption("배점 기준: 시각 요소 1점 · 시각 효과 2점 · 청각 요소 1점 · 청각 효과 2점")
        else:
            st.metric("통과 항목 수", f"{passed_count}/4")

st.divider()
st.caption(
    "주의: 이 앱은 규칙 기반 자동 채점기입니다. 학생 답안의 문장 표현이 매우 자유롭거나 "
    "함축적인 경우 교사 확인이 필요할 수 있습니다. 핵심은 문자열 일치가 아니라 "
    "필수 의미군, 설명 방법 구조, 오개념, 결론 방향을 함께 확인하는 것입니다."
)
