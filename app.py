
import re
import streamlit as st

st.set_page_config(
    page_title="국어 서·논술형 답안 작성 연습",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 스타일
# =========================================================
st.markdown("""
<style>
.block-container {
    max-width: 1120px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
[data-testid="stSidebar"] {
    background: #f2f4f7;
}
.hero-title {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin-bottom: .4rem;
}
.hero-desc {
    color: #4b5563;
    line-height: 1.8;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}
.set-title {
    font-size: 1.85rem;
    font-weight: 800;
    letter-spacing: -0.035em;
    margin: .4rem 0 1rem 0;
}
.source-box {
    background: #eaf4ff;
    border-radius: 12px;
    padding: 1.15rem 1.25rem;
    margin: .7rem 0 1.4rem 0;
    line-height: 1.85;
}
.prompt-box {
    background: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin: .6rem 0 1rem 0;
    line-height: 1.75;
}
.condition-box {
    background: #fff7e6;
    border-left: 5px solid #f59e0b;
    border-radius: 8px;
    padding: .9rem 1rem;
    margin: .8rem 0 1rem 0;
    line-height: 1.7;
}
.plan-box {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin: .7rem 0 1rem 0;
    line-height: 1.75;
}
.review-card {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: .85rem 1rem;
    margin-bottom: .7rem;
}
.small-muted {
    color: #7a8290;
    font-size: .92rem;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 공통 유틸
# =========================================================
def norm(text):
    return re.sub(r"\s+", " ", (text or "").lower().strip())

def has_any(text, terms):
    t = norm(text)
    return any(norm(x) in t for x in terms)

def method_ok(method, answer):
    """학생이 선택한 설명 방법의 실제 특성이 문장에 드러나는지 규칙 기반 확인."""
    t = norm(answer)

    if method == "정의":
        return any(x in t for x in ["이란", "란 ", "말한다", "뜻은", "의미는"])
    if method == "예시":
        return any(x in t for x in ["예를 들어", "예로", "대표적으로", "예컨대", "와 같은"])
    if method == "인과":
        return any(x in t for x in ["때문에", "하므로", "이므로", "해서", "따라서", "그 결과"])
    if method == "분석":
        groups = [["감정"], ["철학"], ["경험"], ["관점"], ["환경"], ["요소"], ["부분"], ["구성"]]
        return sum(1 for g in groups if has_any(answer, g)) >= 2 or any(
            x in t for x in ["이루어져", "구성되어", "요소로"]
        )
    if method == "비교와 대조":
        explicit = any(x in t for x in ["반면", "하지만", "그러나", "와 달리", "차이", "공통점", "둘 다"])
        pair1 = has_any(answer, ["쉬운 과제", "비교적 쉬운"]) and has_any(answer, ["어려운 과제", "도전이 필요한"])
        pair2 = has_any(answer, ["실생활 전기", "우리가 쓰는 전기"]) and has_any(answer, ["정전기"])
        pair3 = has_any(answer, ["인간의 작품", "인간의 예술"]) and has_any(answer, ["인공 지능", "ai"])
        return explicit or pair1 or pair2 or pair3
    if method == "분류와 구분":
        return any(x in t for x in ["나뉜다", "나눌 수", "구분", "분류", "종류로"])
    return False

QUESTION_KEYS = [
    "1-1", "1-2", "1-3",
    "2-1", "2-2", "2-3",
    "3-1", "3-2", "3-3"
]

def mark(qkey, passed, score=None, feedback=None):
    st.session_state[f"submitted_{qkey}"] = True
    st.session_state[f"passed_{qkey}"] = passed
    if score is not None:
        st.session_state[f"score_{qkey}"] = score
    st.session_state[f"feedback_{qkey}"] = feedback or []

def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

def completed_count():
    return sum(1 for k in QUESTION_KEYS if st.session_state.get(f"submitted_{k}", False))

def show_result(qkey, models=None, total=None):
    if not st.session_state.get(f"submitted_{qkey}", False):
        return
    passed = st.session_state.get(f"passed_{qkey}", False)
    if total is not None:
        st.metric("점수", f"{st.session_state.get(f'score_{qkey}', 0)}/{total}")
    if passed:
        st.success("조건을 충족했습니다.")
    else:
        st.error("일부 조건이 충족되지 않았습니다.")
        for msg in st.session_state.get(f"feedback_{qkey}", []):
            st.write("•", msg)
    if models:
        with st.expander("모범 답안 보기"):
            for k, v in models.items():
                st.write(f"**{k}**: {v}")

# =========================================================
# 사이드바: 1쪽 학습 내용
# =========================================================
with st.sidebar:
    st.markdown("### 📘 학습 내용")
    st.markdown("""
**설명 방법 6가지**
- 정의
- 예시
- 인과
- 분석
- 비교와 대조
- 분류와 구분
""")
    st.divider()
    st.markdown("""
**영상 매체 자료**
- 복합양식성
- 주제·목적·예상 시청자 고려
- 스토리보드: 화면·자막·소리
""")
    st.divider()
    st.markdown("### 📄 자료 구성")
    st.markdown("""
- **1세트:** 2~3쪽
- **2세트:** 4~5쪽
- **3세트:** 6~7쪽
""")
    st.caption("원문 지문과 문항 문구를 그대로 제시하고, 답안 입력·채점 기능만 추가했습니다.")

# =========================================================
# 상단
# =========================================================
st.markdown('<div class="hero-title">📝 [국어] 서·논술형 답안 작성 연습</div>', unsafe_allow_html=True)
st.markdown("""
<div class="hero-desc">
2회고사 대비 모의 문항을 화면에서 그대로 읽고 답안을 작성할 수 있도록 구성한 연습 앱입니다.
각 세트의 원문 지문을 먼저 읽은 뒤 서·논술형 1~3을 풀어 보세요.
자동 채점 결과는 연습용 참고 자료입니다.
</div>
""", unsafe_allow_html=True)

done = completed_count()
c1, c2 = st.columns([5,1])
with c1:
    st.write(f"✅ 완료한 문항: **{done} / 9**")
    st.progress(done / 9)
with c2:
    st.button("🔄 처음부터", on_click=reset_all, use_container_width=True)

st.divider()
tabs = st.tabs(["1세트", "2세트", "3세트", "📚 복습할 내용"])

# =========================================================
# 1세트
# =========================================================
with tabs[0]:
    st.markdown('<div class="set-title">1세트 — 사회적 촉진·사회적 억제</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="source-box">
<b>기자:</b> 심리학 용어인 ‘사회적 촉진’과 ‘사회적 억제’를 일상생활, 특히 우리의 학습에 어떻게 적용할 수 있을까요?<br><br>
<b>전문가:</b> 이 두 가지 개념을 알면 상황에 맞춰 유용하게 활용할 수 있습니다. 예를 들어, 비교적 쉬운 취미 생활이나 큰 노력을 들일 필요가 없는 과제를 할 때는 어떨까요?<br><br>
<b>기자:</b> 음, 그냥 집에서 편하게 혼자 하는 게 집중이 잘되지 않을까요?<br><br>
<b>전문가:</b> 그렇지 않습니다. 오히려 집에서 혼자 하는 것보다는 커피숍이나 도서관에서 하는 것이 더 효율적일 수 있습니다. 평소 친숙하고 좋아하는 과목이라면 공부 모임을 만들어서 다른 사람들과 함께 공부하는 것도 좋은 방법이죠.<br><br>
<b>기자:</b> 그렇다면 어렵고 복잡한 과제를 할 때는 어떻게 해야 하나요?<br><br>
<b>전문가:</b> 그럴 때는 반대입니다. 지나치게 어렵거나 도전이 필요한 과제는 충분히 연습하며 익숙해질 때까지 차분하게 혼자 집중하는 시간을 가지는 것이 좋습니다.
</div>
""", unsafe_allow_html=True)

    # 1-1
    with st.expander("서·논술형 1", expanded=True):
        st.markdown("""
<div class="prompt-box">
윗글을 요약하여 표로 정리하였다. ㉠~㉢에 들어갈 내용을 찾아 쓰시오.
</div>
""", unsafe_allow_html=True)

        st.markdown("""
| 과제의 특성 | 효율적인 환경 및 방법 | 관련된 심리 현상 |
|---|---|---|
| (㉠) | 커피숍, 도서관 등에서 하거나 모임을 만들어 다른 사람들과 함께 함 | 사회적 촉진 |
| 지나치게 어렵거나 도전이 필요한 과제 | (㉡) | (㉢) |
""")

        a = st.text_input("㉠", key="s1q1_a")
        b = st.text_input("㉡", key="s1q1_b")
        c = st.text_input("㉢", key="s1q1_c")

        if st.button("서·논술형 1 제출", key="s1q1_submit", type="primary"):
            c1 = has_any(a, ["쉬운", "비교적 쉬운", "어렵지 않은", "큰 노력이 필요하지 않은", "큰 노력을 들일 필요가 없는"])
            c2 = has_any(b, ["혼자"]) and has_any(b, ["집중"])
            c3 = has_any(c, ["사회적 억제"]) and not has_any(c, ["사회적 촉진"])
            fb = []
            if not c1: fb.append("㉠에는 비교적 쉬운 과제라는 특성이 드러나야 합니다.")
            if not c2: fb.append("㉡에는 '혼자'와 '집중'의 의미가 모두 필요합니다.")
            if not c3: fb.append("㉢에는 개념명 '사회적 억제'가 필요합니다.")
            mark("1-1", c1 and c2 and c3, sum([c1,c2,c3]), fb)

        show_result("1-1", {
            "㉠": "비교적 쉬운 취미 생활이나 큰 노력을 들일 필요가 없는 과제",
            "㉡": "충분히 연습하며 익숙해질 때까지 차분하게 혼자 집중함",
            "㉢": "사회적 억제",
        })

    # 1-2
    with st.expander("서·논술형 2"):
        st.markdown("""
<div class="prompt-box">
윗글을 활용하여 ‘과제 난이도에 따른 효율적인 학습 전략’에 대한 설명문을 작성하려 한다.
주어진 첫 문장에 이어지는 내용인 ㉮를 &lt;조건&gt;에 맞추어 작성하시오.<br><br>
<b>과제의 특성과 난이도에 따라 우리의 학습 효율을 높이는 방법은 다르게 적용되어야 한다. (㉮)</b>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="condition-box">
<b>&lt;조건&gt;</b><br>
• 서로 다른 2가지의 설명 방법을 사용하여, 주어진 문장에 이어지는 문장을 (1), (2)에 각각 하나씩 작성할 것.<br>
• 윗글에 제시된 내용만을 활용하여 문장을 구성할 것. (지문에 없는 외부 배경지식을 활용할 경우 인정하지 않음.)<br>
• 각 문장의 끝에 자신이 사용한 설명 방법의 명칭을 괄호에 넣어 표기할 것.
</div>
""", unsafe_allow_html=True)

        m1 = st.selectbox("(1) 설명 방법", ["비교와 대조","예시","분류와 구분"], key="s1q2_m1")
        s1 = st.text_area("(1) 문장", key="s1q2_s1")
        m2 = st.selectbox("(2) 설명 방법", ["예시","비교와 대조","분류와 구분"], key="s1q2_m2")
        s2 = st.text_area("(2) 문장", key="s1q2_s2")

        if st.button("서·논술형 2 제출", key="s1q2_submit", type="primary"):
            distinct = m1 != m2
            st1, st2 = method_ok(m1,s1), method_ok(m2,s2)
            content = has_any(s1+s2, ["쉬운","친숙","좋아하는 과목","어려운","도전이 필요한"])
            conclusion = (
                (has_any(s1+s2, ["쉬운","친숙"]) and has_any(s1+s2, ["함께","공부 모임","도서관","커피숍"]))
                or
                (has_any(s1+s2, ["어려운","도전이 필요한"]) and has_any(s1+s2, ["혼자","집중","차분"]))
            )
            bad = has_any(s1+s2, ["인지 부하","뇌과학","어려운 과제는 다른 사람들과 함께하는 것이 더 좋다"])
            fb = []
            if not distinct: fb.append("두 문장에 서로 다른 설명 방법을 사용해야 합니다.")
            if not st1: fb.append(f"(1)에서 선택한 '{m1}'의 특성이 문장에 드러나지 않습니다.")
            if not st2: fb.append(f"(2)에서 선택한 '{m2}'의 특성이 문장에 드러나지 않습니다.")
            if not content: fb.append("지문에 제시된 핵심 내용이 부족합니다.")
            if not conclusion: fb.append("과제 난이도에 따라 학습 전략이 달라진다는 방향이 드러나야 합니다.")
            if bad: fb.append("지문 밖의 개념 또는 반대 방향 설명이 포함되어 있습니다.")
            mark("1-2", distinct and st1 and st2 and content and conclusion and not bad, None, fb)

        show_result("1-2", {
            "비교와 대조": "비교적 쉬운 과제는 다른 사람들과 함께하는 것이 효율적이지만, 지나치게 어렵거나 도전이 필요한 과제는 차분하게 혼자 집중하는 것이 좋다.",
            "예시": "예를 들어 평소 친숙하고 좋아하는 과목이라면 공부 모임을 만들어 다른 사람들과 함께 공부할 수 있다.",
            "분류와 구분": "과제는 난이도에 따라 비교적 쉬운 과제와 지나치게 어렵거나 도전이 필요한 과제로 나누어 볼 수 있다.",
        })

    # 1-3
    with st.expander("서·논술형 3"):
        st.markdown("""
<div class="prompt-box">
윗글을 바탕으로 ‘상황에 맞는 학습 공간 선택법’을 설명하는 영상을 제작하려 한다.
다음 기획안을 보고 물음에 답하시오.
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="plan-box">
<b>[영상 기획안]</b><br>
• 주제: 사회적 촉진과 억제를 활용한 스마트한 공부법<br><br>
<b>[장면 1] 쉬운 과제를 할 때</b><br>
• 시각 요소: 백색소음이 있는 밝은 도서관에서 친구들과 가볍게 미소 지으며 공부하는 학생들의 모습을 넓은 화면(풀샷)으로 보여줌.<br>
• 청각 요소: 경쾌하고 리듬감 있는 배경음악과 함께 사람들의 가벼운 발소리와 책장 넘기는 소리를 깔아줌.<br><br>
<b>[장면 2] 어려운 과제를 할 때</b><br>
• 시각 요소: (Ⓐ)<br>
• 청각 요소: (Ⓑ)
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="condition-box">
<b>&lt;조건&gt;</b><br>
• 윗글을 참고하여 어려운 과제를 할 때 필요한 환경의 특성이 잘 드러나도록 Ⓐ와 Ⓑ에 들어갈 연출 계획을 세울 것.<br>
• 자신이 설정한 시각/청각 요소가 글의 내용을 전달하는 데 어떤 효과가 있는지 각각 서술할 것.
</div>
""", unsafe_allow_html=True)

        v = st.text_area("시각 요소(Ⓐ)", key="s1q3_v")
        ve = st.text_area("시각 요소(Ⓐ)의 효과", key="s1q3_ve")
        a = st.text_area("청각 요소(Ⓑ)", key="s1q3_a")
        ae = st.text_area("청각 요소(Ⓑ)의 효과", key="s1q3_ae")

        if st.button("서·논술형 3 제출", key="s1q3_submit", type="primary"):
            v_ok = has_any(v, ["혼자","한 학생","차분","집중","연습","반복"])
            a_ok = has_any(a, ["조용","고요","소음을 줄","소음을 최소","무음","작은 소리"])
            ve_ok = has_any(ve, ["어려운 과제","도전이 필요한","혼자","집중","차분","연습","익숙해질 때까지"])
            ae_ok = has_any(ae, ["어려운 과제","혼자","집중","차분","고요"])
            bad = has_any(v+a+ve+ae, ["친구들과 떠들","빠르고 신나는 음악","시끄러운"])
            fb=[]
            if not v_ok: fb.append("시각 요소에 어려운 과제에 필요한 환경 특성이 드러나지 않습니다.")
            if not ve_ok: fb.append("시각 효과에 지문 근거가 필요합니다.")
            if not a_ok: fb.append("청각 요소에 차분하고 집중되는 환경이 드러나지 않습니다.")
            if not ae_ok: fb.append("청각 효과에 지문 근거가 필요합니다.")
            if bad: fb.append("쉬운 과제의 환경 특성을 어려운 과제에 적용한 오개념이 있습니다.")
            mark("1-3", v_ok and a_ok and ve_ok and ae_ok and not bad, sum([v_ok,ve_ok,a_ok,ae_ok]), fb)

        show_result("1-3", {
            "시각 요소": "조용한 공간에서 한 학생이 혼자 어려운 과제를 반복해 연습하며 집중하는 모습을 보여 준다.",
            "시각 효과": "어려운 과제는 익숙해질 때까지 차분하게 혼자 집중하는 것이 좋다는 내용을 시각적으로 드러낸다.",
            "청각 요소": "배경음악과 주변 소음을 최소화하고 책장 넘기는 작은 소리만 들려준다.",
            "청각 효과": "고요한 분위기를 조성하여 어려운 과제를 할 때 차분하게 혼자 집중하는 환경이 효과적임을 강조한다.",
        })

# =========================================================
# 2세트
# =========================================================
with tabs[1]:
    st.markdown('<div class="set-title">2세트 — 정전기</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="source-box">
<b>기자:</b> 겨울철 불청객인 ‘정전기’란 정확히 무엇인지 설명 부탁드립니다.<br><br>
<b>전문가:</b> 정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기, 그리고 그로 인한 전기 현상을 말합니다. 쉽게 설명하면 흐르지 않고 머물러 있는 전기라고 해서 “움직이지 아니하여 조용하다.”는 뜻을 가진 한자 ‘정(靜)’을 써서 정전기라고 부르는 것이죠.<br><br>
<b>기자:</b> 우리가 실생활에서 쓰는 전기와는 어떻게 다른가요? 물에 비유해서 설명해 주시면 이해가 쉬울 것 같습니다.<br><br>
<b>전문가:</b> 아주 좋은 비유가 될 수 있습니다. 우리가 실생활에서 쓰는 전기가 ‘흐르는 물’이라면, 정전기는 ‘높은 곳에 고여 있는 물’이라고 할 수 있습니다.<br><br>
<b>기자:</b> 정전기가 일어날 때 찌릿한 느낌이 드는데, 혹시 위험하지는 않은가요?<br><br>
<b>전문가:</b> 정전기의 전압은 매우 높지만, 우리가 실생활에서 쓰는 전기와는 다르게 전하가 이동하지 않고 머물러 있어 위험하지는 않습니다. 어마어마하게 높은 곳에 고여 있는 물이지만 떨어지지 않고 있어서 별 피해가 없는 것과 같다고 이해하시면 됩니다.
</div>
""", unsafe_allow_html=True)

    # 2-1
    with st.expander("서·논술형 1", expanded=True):
        st.markdown("""
<div class="prompt-box">
윗글을 요약하여 표로 정리하였다. ㉠~㉢에 들어갈 내용을 찾아 쓰시오.
</div>
""", unsafe_allow_html=True)

        st.markdown("""
| 대상 | 물의 상태에 비유 | 전하의 상태 | 위험성 |
|---|---|---|---|
| 실생활 전기 | 흐르는 물 | 전하가 이동함 | 감전 등의 위험이 있음 |
| 정전기 | (㉠) | (㉡) | (㉢) |
""")

        a = st.text_input("㉠", key="s2q1_a")
        b = st.text_input("㉡", key="s2q1_b")
        c = st.text_input("㉢", key="s2q1_c")

        if st.button("서·논술형 1 제출", key="s2q1_submit", type="primary"):
            c1 = has_any(a, ["높은 곳","높은 위치"]) and has_any(a, ["고여","고인","머물러","흐르지"])
            c2 = has_any(b, ["전하"]) and has_any(b, ["이동하지","정지","머물러","움직이지"])
            c3 = has_any(c, ["위험하지","위험이 없","피해가 없"])
            fb=[]
            if not c1: fb.append("㉠에는 '높은 곳'과 '고여 있음'이 함께 드러나야 합니다.")
            if not c2: fb.append("㉡에는 전하가 이동하지 않고 머문다는 의미가 필요합니다.")
            if not c3: fb.append("㉢에는 위험하지 않다는 결론이 필요합니다.")
            mark("2-1", c1 and c2 and c3, sum([c1,c2,c3]), fb)

        show_result("2-1", {
            "㉠": "높은 곳에 고여 있는 물",
            "㉡": "전하가 이동하지 않고 머물러 있음",
            "㉢": "위험하지 않음",
        })

    # 2-2
    with st.expander("서·논술형 2"):
        st.markdown("""
<div class="prompt-box">
윗글을 활용하여 ‘정전기의 특징’에 대한 설명문을 작성하려 한다.
주어진 첫 문장에 이어지는 내용인 ㉮를 &lt;조건&gt;에 맞추어 작성하시오.<br><br>
<b>겨울철에 흔히 겪는 정전기는 우리가 평소 집에서 사용하는 전기와는 다른 뚜렷한 특징이 있다. (㉮)</b>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="condition-box">
<b>&lt;조건&gt;</b><br>
• 주어진 문장에 이어지는 문장을 (1), (2)에 각각 하나씩 작성할 것. (1)과 (2)에는 서로 다른 설명 방법이 1가지 이상 활용되어야 하며, 각 문장에 사용된 설명 방법의 명칭을 괄호에 넣어 문장 끝에 기재할 것.<br>
• 윗글에 제시된 내용만을 활용하여 문장을 구성할 것.<br>
• (1)과 (2)가 논리적 흐름을 갖고 이어지도록 할 것.
</div>
""", unsafe_allow_html=True)

        m1 = st.selectbox("(1) 설명 방법", ["정의","인과","비교와 대조"], key="s2q2_m1")
        s1 = st.text_area("(1) 문장", key="s2q2_s1")
        m2 = st.selectbox("(2) 설명 방법", ["인과","비교와 대조","정의"], key="s2q2_m2")
        s2 = st.text_area("(2) 문장", key="s2q2_s2")

        if st.button("서·논술형 2 제출", key="s2q2_submit", type="primary"):
            distinct = m1 != m2
            st1, st2 = method_ok(m1,s1), method_ok(m2,s2)
            content = has_any(s1+s2, ["정전기"]) and has_any(
                s1+s2,
                ["전하가 이동하지","전하가 정지","전하가 머물러","위험하지","실생활 전기"]
            )
            bad = has_any(s1+s2, [
                "정전기는 전하가 이동한다",
                "정전기는 위험하다",
                "전압이 높아서 위험하다",
                "전기는 정전기와 실생활 전기로 나뉜다",
            ])
            conclusion = has_any(s1+s2, ["전하가 이동하지","전하가 정지","전하가 머물러","위험하지"])
            fb=[]
            if not distinct: fb.append("두 문장에 서로 다른 설명 방법을 사용해야 합니다.")
            if not st1: fb.append(f"(1)에서 선택한 '{m1}'의 특성이 드러나지 않습니다.")
            if not st2: fb.append(f"(2)에서 선택한 '{m2}'의 특성이 드러나지 않습니다.")
            if not content: fb.append("정전기의 핵심 내용이 부족합니다.")
            if not conclusion: fb.append("정전기의 핵심 특성에 대한 결론이 분명해야 합니다.")
            if bad: fb.append("정전기의 특성을 반대로 설명한 오개념이 있습니다.")
            mark("2-2", distinct and st1 and st2 and content and conclusion and not bad, None, fb)

        show_result("2-2", {
            "정의": "정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기와 그로 인한 전기 현상을 말한다.",
            "인과": "정전기는 전압이 매우 높지만 전하가 이동하지 않고 머물러 있기 때문에 위험하지 않다.",
            "비교와 대조": "실생활에서 쓰는 전기는 전하가 이동하지만 정전기는 전하가 이동하지 않고 머물러 있다는 차이가 있다.",
        })

    # 2-3
    with st.expander("서·논술형 3"):
        st.markdown("""
<div class="prompt-box">
윗글을 바탕으로 ‘정전기의 특징’을 설명하는 영상을 제작하려 한다.
다음 기획안을 보고 물음에 답하시오.
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="plan-box">
<b>[영상 기획안]</b><br>
• 주제: 전압은 높지만 위험하지 않은 정전기의 비밀<br><br>
<b>[장면 1] 실생활 전기 (흐르는 물)</b><br>
• 시각 요소: 거대한 폭포수가 콸콸 쏟아져 내려오며 물레방아를 힘차게 돌리는 역동적인 그래픽을 보여줌.<br>
• 청각 요소: 물이 거세게 부딪히는 웅장하고 큰 소리를 배경음으로 사용함.<br><br>
<b>[장면 2] 정전기 (고여 있는 물)</b><br>
• 시각 요소: (Ⓐ)<br>
• 청각 요소: (Ⓑ)
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="condition-box">
<b>&lt;조건&gt;</b><br>
• 윗글을 바탕으로 정전기의 특성이 잘 드러나도록 Ⓐ와 Ⓑ에 들어갈 연출 계획을 세울 것.<br>
• 설정한 시각 및 청각 요소의 연출 효과를 각각 서술하되, 반드시 윗글의 내용을 근거로 포함할 것.
</div>
""", unsafe_allow_html=True)

        v = st.text_area("시각 요소(Ⓐ)", key="s2q3_v")
        ve = st.text_area("시각 요소(Ⓐ)의 효과", key="s2q3_ve")
        a = st.text_area("청각 요소(Ⓑ)", key="s2q3_a")
        ae = st.text_area("청각 요소(Ⓑ)의 효과", key="s2q3_ae")

        if st.button("서·논술형 3 제출", key="s2q3_submit", type="primary"):
            v_ok = has_any(v, ["높은 곳","높은 위치"]) and has_any(v, ["고여","고인","흐르지","떨어지지","머물러"])
            a_ok = has_any(a, ["흐르는 소리를 사용하지","흐르는 소리 없음","무음","고요","조용"])
            ve_ok = has_any(ve, ["전압이 높","높은 전압","전하가 이동하지","전하가 머물러","위험하지"])
            ae_ok = has_any(ae, ["전하가 이동하지","전하가 머물러","전하가 정지","위험하지"])
            bad = has_any(v+a+ve+ae, ["큰 폭포 소리","콸콸 흐르","정전기는 위험하다"])
            fb=[]
            if not v_ok: fb.append("시각 요소에 '높은 곳'과 '고여 있음/흐르지 않음'이 드러나야 합니다.")
            if not ve_ok: fb.append("시각 효과에 정전기의 본문 근거가 필요합니다.")
            if not a_ok: fb.append("청각 요소는 흐르지 않는 정적인 상태를 표현해야 합니다.")
            if not ae_ok: fb.append("청각 효과에 전하가 이동하지 않는다는 본문 근거가 필요합니다.")
            if bad: fb.append("실생활 전기의 특성을 정전기에 적용한 오개념이 있습니다.")
            mark("2-3", v_ok and a_ok and ve_ok and ae_ok and not bad, sum([v_ok,ve_ok,a_ok,ae_ok]), fb)

        show_result("2-3", {
            "시각 요소": "높은 곳에 많은 물이 고여 있지만 아래로 흐르거나 떨어지지 않는 모습을 보여 준다.",
            "시각 효과": "높은 곳에 물이 고여 있지만 떨어지지 않는 모습을 통해 전압은 높지만 전하가 이동하지 않아 위험하지 않다는 특성을 드러낸다.",
            "청각 요소": "물이 흐르거나 떨어지는 소리를 사용하지 않고 고요하게 연출한다.",
            "청각 효과": "물이 흐르는 소리가 들리지 않게 하여 전하가 이동하지 않고 머물러 있다는 특성을 강조한다.",
        })

# =========================================================
# 3세트
# =========================================================
with tabs[2]:
    st.markdown('<div class="set-title">3세트 — 인공 지능과 예술</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="source-box">
<b>기자:</b> 최근 생성형 인공 지능이 그린 그림이 미술계에서 큰 화제를 모으고 있습니다. 어떤 작품인지 소개해 주실 수 있을까요?<br><br>
<b>전문가:</b> 네, 대표적으로 「에드몽 드 벨라미」라는 작품이 있습니다. 이 작품은 14~20세기에 그려진 초상화 1만 5,000점을 토대로 알고리즘과 데이터를 사용해 그려졌습니다. 뉴욕 크리스티 경매에서 최종 낙찰가 43만 2,000달러에 판매되어 큰 놀라움을 주었죠.<br><br>
<b>기자:</b> 그렇다면 이 그림을 인간이 만든 예술 작품과 같다고 볼 수 있을까요?<br><br>
<b>전문가:</b> 올림픽 경기를 예로 들어 볼게요. 우리가 올림픽에 열광하는 이유는 선수들이 경기를 위해 기울인 노력이나 열정을 알기 때문입니다. 반면 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅을 해내더라도 우리의 마음을 울리지는 못하지요. 이처럼 인간의 작품에는 작가의 고유한 감정이나 철학, 그리고 작가가 살아온 삶의 경험, 세상을 바라보는 관점, 그를 둘러싼 환경 같은 내외부적인 요소가 종합적으로 담겨 있으므로 예술로 볼 수 있습니다. 하지만 인공 지능은 감정도 느끼지 못하고 독자적인 철학이나 이야기가 없기 때문에 이를 예술로 보기는 어렵습니다.<br><br>
<b>기자:</b> 그렇다면 인공 지능이 그린 그림은 가치가 전혀 없는 것인가요?<br><br>
<b>전문가:</b> 그렇지는 않습니다. 비록 인간과 같은 감정은 없더라도, 기존 미술계에 큰 변화를 가져왔다는 점에서 분명한 의미가 있습니다. 또한 앞으로 우리가 알고 있던 예술의 범주를 확장할 수 있다는 점에서 상징적인 가치를 지닙니다.
</div>
""", unsafe_allow_html=True)

    # 3-1
    with st.expander("서·논술형 1", expanded=True):
        st.markdown("""
<div class="prompt-box">
윗글을 요약하여 표로 정리하였다. ㉠~㉢에 들어갈 내용을 찾아 쓰시오.
</div>
""", unsafe_allow_html=True)

        st.markdown("""
| 대상 | 올림픽 경기에 비유 | 예술로 볼 수 있는가 (근거 포함하여 쓰기) | 예술로서의 가치 |
|---|---|---|---|
| 인간의 예술 | 인간 선수의 노력과 열정이 담긴 올림픽 경기 | 작가의 경험, 관점, 환경이 담겨 있으므로 예술이다. | 감상자에게 남다른 감동을 줌 |
| 인공 지능의 예술 | (㉠) | (㉡) | (㉢) |
""")

        a = st.text_area("㉠", key="s3q1_a")
        b = st.text_area("㉡", key="s3q1_b")
        c = st.text_area("㉢", key="s3q1_c")

        if st.button("서·논술형 1 제출", key="s3q1_submit", type="primary"):
            c1 = has_any(a, ["로봇"]) and has_any(a, ["완벽","실수 없이"]) and has_any(
                a, ["마음을 울리지","감동을 주지","감동이 없","울림이 없"]
            )
            c2 = has_any(b, ["감정이 없","감정을 느끼지 못","철학이 없","이야기가 없"]) and has_any(
                b, ["예술로 보기 어렵","예술로 볼 수 없"]
            )
            c3 = has_any(c, ["미술계에 변화","미술계에 큰 변화","예술의 범주를 확장","예술의 범위를 넓","상징적인 가치"])
            fb=[]
            if not c1: fb.append("㉠에는 로봇의 완벽한 수행과 감동 없음이 모두 필요합니다.")
            if not c2: fb.append("㉡에는 AI의 감정·철학·이야기 부재와 '예술로 보기 어려움'의 결론이 필요합니다.")
            if not c3: fb.append("㉢에는 미술계 변화 또는 예술 범주 확장이라는 가치가 필요합니다.")
            mark("3-1", c1 and c2 and c3, sum([c1,c2,c3]), fb)

        show_result("3-1", {
            "㉠": "한 번의 실수 없이 완벽하게 피겨 스케이팅하지만 사람의 마음을 울리지 못하는 로봇",
            "㉡": "감정을 느끼지 못하고 독자적인 철학이나 이야기가 없으므로 예술로 보기 어렵다.",
            "㉢": "기존 미술계에 큰 변화를 가져왔고 예술의 범주를 확장할 수 있다는 점에서 상징적인 가치가 있다.",
        })

    # 3-2
    with st.expander("서·논술형 2"):
        st.markdown("""
<div class="prompt-box">
윗글을 활용하여 ‘인공 지능이 그린 그림을 바라보는 시각’에 대한 설명문을 작성하려 한다.
주어진 첫 문장에 이어지는 내용인 ㉮를 &lt;조건&gt;에 맞추어 작성하시오.<br><br>
<b>인공 지능이 그린 그림이 늘어나는 요즘, 우리는 이 작품들을 어떤 눈으로 바라봐야 할지 올바르게 생각해야 한다. (㉮)</b>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="condition-box">
<b>&lt;조건&gt;</b><br>
• 주어진 문장에 이어지는 문장을 (1), (2)에 각각 하나씩 작성할 것. (1)과 (2)에는 서로 다른 설명 방법이 1가지 이상 활용되어야 하며, 각 문장에 사용된 설명 방법의 명칭을 괄호에 넣어 문장 끝에 기재할 것.<br>
• 윗글에 제시된 내용만을 활용하여 문장을 구성할 것.<br>
• (1)과 (2)가 논리적 흐름을 갖고 이어지도록 할 것.
</div>
""", unsafe_allow_html=True)

        m1 = st.selectbox("(1) 설명 방법", ["비교와 대조","인과","분석","예시"], key="s3q2_m1")
        s1 = st.text_area("(1) 문장", key="s3q2_s1")
        m2 = st.selectbox("(2) 설명 방법", ["인과","분석","예시","비교와 대조"], key="s3q2_m2")
        s2 = st.text_area("(2) 문장", key="s3q2_s2")

        if st.button("서·논술형 2 제출", key="s3q2_submit", type="primary"):
            distinct = m1 != m2
            st1, st2 = method_ok(m1,s1), method_ok(m2,s2)
            content = has_any(s1+s2, ["감정","철학","경험","관점","환경","예술로 보기 어렵","미술계에 변화","예술의 범주"])
            bad = has_any(s1+s2, [
                "가치가 전혀 없다",
                "기술이 부족해서 예술이 아니다",
                "사람보다 창의적이다",
                "예술은 인간 예술과 인공 지능 예술로 나뉜다",
            ])
            conclusion = has_any(s1+s2, ["예술로 보기 어렵","예술로 볼 수 없","미술계에 변화","예술의 범주","상징적인 가치"])
            fb=[]
            if not distinct: fb.append("두 문장에 서로 다른 설명 방법을 사용해야 합니다.")
            if not st1: fb.append(f"(1)에서 선택한 '{m1}'의 특성이 드러나지 않습니다.")
            if not st2: fb.append(f"(2)에서 선택한 '{m2}'의 특성이 드러나지 않습니다.")
            if not content: fb.append("인간 예술 또는 AI 그림의 핵심 내용이 부족합니다.")
            if not conclusion: fb.append("AI 그림의 예술성 한계 또는 상징적 가치에 대한 결론이 필요합니다.")
            if bad: fb.append("지문에 없는 평가나 잘못된 분류가 포함되어 있습니다.")
            mark("3-2", distinct and st1 and st2 and content and conclusion and not bad, None, fb)

        show_result("3-2", {
            "비교와 대조": "인간의 작품에는 작가의 감정과 철학, 경험 등이 담겨 있지만 인공 지능은 감정이나 독자적인 철학과 이야기가 없다는 차이가 있다.",
            "인과": "인공 지능이 그린 그림은 기존 미술계에 큰 변화를 가져왔고 예술의 범주를 확장할 수 있으므로 상징적인 가치가 있다.",
            "분석": "인간의 작품에는 작가의 감정과 철학, 삶의 경험, 관점, 환경 등의 여러 요소가 종합적으로 담겨 있다.",
            "예시": "예를 들어 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅하더라도 우리의 마음을 울리지는 못한다.",
        })

    # 3-3
    with st.expander("서·논술형 3 [총 6점]"):
        st.markdown("""
<div class="prompt-box">
윗글을 바탕으로 ‘인공 지능이 그린 그림을 바라보는 시각’을 설명하는 영상을 제작하려 한다.
다음 기획안을 보고 물음에 답하시오. <b>[총 6점]</b>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="plan-box">
<b>[영상 기획안]</b><br>
• 주제: 인간의 감정이 담긴 진정한 예술의 가치<br><br>
<b>[장면 1] 감정이 없는 완벽한 기술</b><br>
• 시각 요소: 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅을 해내지만 우리의 마음을 울리지는 못하는 동영상을 보여줌.<br>
• 청각 요소: 기계음이나 일정한 박자의 메트로놈 소리를 깔아 차갑고 정형화된 분위기를 조성함.<br><br>
<b>[장면 2] 마음에 울림을 주는 진정한 예술</b><br>
• 시각 요소: (Ⓐ)<br>
• 청각 요소: (Ⓑ)
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="condition-box">
<b>&lt;조건&gt;</b><br>
• 윗글을 바탕으로 인간이 만들어내는 예술의 특성이 잘 드러나도록 Ⓐ와 Ⓑ에 들어갈 연출 계획을 세울 것.<br>
• 설정한 시각 및 청각 요소의 연출 효과를 각각 서술하되, 반드시 윗글의 내용을 근거로 포함할 것.
</div>
""", unsafe_allow_html=True)

        v = st.text_area("시각 요소(Ⓐ)", key="s3q3_v")
        ve = st.text_area("시각 요소(Ⓐ)의 효과", key="s3q3_ve")
        a = st.text_area("청각 요소(Ⓑ)", key="s3q3_a")
        ae = st.text_area("청각 요소(Ⓑ)의 효과", key="s3q3_ae")

        if st.button("서·논술형 3 제출", key="s3q3_submit", type="primary"):
            v_ok = has_any(v, ["작가","화가","감정","철학","경험","관점","환경","노력","열정"])
            a_ok = has_any(a, ["작가의 목소리","감정","생각","이야기","배경음악","음악"])
            ve_ok = has_any(ve, ["감정","철학","경험","관점","환경","마음을 울리","감동","울림"])
            ae_ok = has_any(ae, ["감정","철학","이야기","마음을 울리","감동","울림"])
            bad = has_any(v+a+ve+ae, ["기계음만","메트로놈만","인공 지능 그림의 상징적 가치만"])
            score = (1 if v_ok else 0) + (2 if ve_ok else 0) + (1 if a_ok else 0) + (2 if ae_ok else 0)
            fb=[]
            if not v_ok: fb.append("시각 요소에 인간 예술의 특성이 드러나지 않습니다.")
            if not ve_ok: fb.append("시각 효과에 인간 예술의 본문 근거가 필요합니다.")
            if not a_ok: fb.append("청각 요소에 인간의 감정·생각·이야기를 표현하는 요소가 필요합니다.")
            if not ae_ok: fb.append("청각 효과에 인간 예술의 본문 근거가 필요합니다.")
            if bad: fb.append("장면 1의 기계적 특성 또는 AI의 가치만을 장면 2에 적용한 오개념이 있습니다.")
            mark("3-3", score == 6 and not bad, score, fb)

        show_result("3-3", {
            "시각 요소": "화가가 자신의 삶의 경험과 주변 환경을 떠올리며 감정을 담아 그림을 완성해 가는 모습을 보여 준다.",
            "시각 효과": "작가의 창작 과정을 보여 줌으로써 인간의 작품에는 작가의 감정과 경험, 관점 등이 담긴다는 점을 드러낸다.",
            "청각 요소": "작가가 자신의 감정과 생각을 이야기하는 목소리와 감정의 변화를 느낄 수 있는 배경음악을 들려준다.",
            "청각 효과": "작가의 목소리와 음악을 통해 인간의 작품에 고유한 감정과 이야기가 담겨 있고 그것이 감상자의 마음에 울림을 줄 수 있음을 강조한다.",
        }, total=6)

# =========================================================
# 복습
# =========================================================
with tabs[3]:
    st.markdown('<div class="set-title">📚 복습할 내용</div>', unsafe_allow_html=True)

    wrong = [
        k for k in QUESTION_KEYS
        if st.session_state.get(f"submitted_{k}") and not st.session_state.get(f"passed_{k}")
    ]

    review = {
        "1-1":"쉬운 과제와 어려운 과제의 학습 환경을 구분하세요.",
        "1-2":"설명 방법의 명칭과 실제 문장 구조가 일치하는지 확인하세요.",
        "1-3":"영상 요소와 효과를 지문 근거로 연결하세요.",
        "2-1":"정전기는 높은 곳에 고인 물처럼 전하가 이동하지 않고 머뭅니다.",
        "2-2":"정전기의 정의·인과·비교와 대조를 구분하세요.",
        "2-3":"실생활 전기의 '흐름'과 정전기의 '정지'를 뒤바꾸지 마세요.",
        "3-1":"AI 그림의 예술성 한계와 상징적 가치를 구분하세요.",
        "3-2":"인간 예술과 AI 그림의 차이를 지문 내용 안에서 설명하세요.",
        "3-3":"인간 예술의 감정·철학·경험·관점·환경과 마음의 울림을 연결하세요.",
    }

    if not wrong and done < 9:
        st.info("제출한 문항 중 틀린 내용이 있으면 이곳에 표시됩니다.")
    elif not wrong and done == 9:
        st.success("9개 문항을 모두 통과했습니다.")

    for k in wrong:
        st.markdown(
            f'<div class="review-card"><b>{k} 문항</b><br>{review[k]}</div>',
            unsafe_allow_html=True
        )

    st.caption("자동 채점은 답안 작성 연습을 위한 참고 자료입니다. 실제 평가에서는 교사의 채점 기준이 우선합니다.")
