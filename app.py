
import re
import streamlit as st

st.set_page_config(
    page_title="국어 서·논술형 답안 작성 연습",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {max-width: 1050px; padding-top: 2rem; padding-bottom: 4rem;}
[data-testid="stSidebar"] {background:#f1f3f6;}
.hero-title {font-size:2.2rem; font-weight:800; margin-bottom:.4rem; letter-spacing:-.04em;}
.hero-desc {font-size:1rem; line-height:1.7; color:#4b5563; margin-bottom:1.5rem;}
.set-title {font-size:1.65rem; font-weight:800; margin:.6rem 0 1rem 0;}
.q-title {font-size:1.2rem; font-weight:800; margin:.8rem 0 .5rem 0;}
.passage {background:#eaf4ff; border-radius:10px; padding:1rem 1.1rem; margin:.6rem 0 1rem; line-height:1.7;}
.condition {background:#fff7e6; border-left:5px solid #f59e0b; border-radius:8px; padding:.8rem 1rem; margin:.8rem 0 1rem; line-height:1.65;}
.review-card {background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px; padding:.85rem 1rem; margin-bottom:.7rem;}
.small-muted {color:#7a8290; font-size:.92rem;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 공통 유틸
# -------------------------
def norm(text):
    return re.sub(r"\s+", " ", (text or "").lower().strip())

def has_any(text, terms):
    t = norm(text)
    return any(norm(x) in t for x in terms)

def method_ok(method, answer):
    t = norm(answer)
    if method == "정의":
        return any(x in t for x in ["이란", "란 ", "말한다", "뜻은", "의미는"])
    if method == "예시":
        return any(x in t for x in ["예를 들어", "예로", "대표적으로", "예컨대", "와 같은"])
    if method == "인과":
        return any(x in t for x in ["때문에", "하므로", "이므로", "해서", "따라서", "그 결과"])
    if method == "분석":
        groups = [["감정"], ["철학"], ["경험"], ["관점"], ["환경"], ["요소"], ["부분"], ["구성"]]
        return sum(1 for g in groups if has_any(answer, g)) >= 2 or any(x in t for x in ["이루어져", "구성되어", "요소로"])
    if method == "비교와 대조":
        explicit = any(x in t for x in ["반면", "하지만", "그러나", "와 달리", "차이", "공통점", "둘 다"])
        pair1 = has_any(answer, ["쉬운 과제", "비교적 쉬운"]) and has_any(answer, ["어려운 과제", "도전이 필요한"])
        pair2 = has_any(answer, ["실생활 전기", "우리가 쓰는 전기"]) and has_any(answer, ["정전기"])
        pair3 = has_any(answer, ["인간의 작품", "인간의 예술"]) and has_any(answer, ["인공 지능", "ai"])
        return explicit or pair1 or pair2 or pair3
    if method == "분류와 구분":
        return any(x in t for x in ["나뉜다", "나눌 수", "구분", "분류", "종류로"])
    return False

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

QUESTION_KEYS = ["1-1","1-2","1-3","2-1","2-2","2-3","3-1","3-2","3-3"]

def completed_count():
    return sum(1 for k in QUESTION_KEYS if st.session_state.get(f"submitted_{k}", False))

def set_completed(set_no):
    keys = [f"{set_no}-1", f"{set_no}-2", f"{set_no}-3"]
    return all(st.session_state.get(f"submitted_{k}", False) for k in keys)

def show_result(qkey, models=None, total=None):
    if not st.session_state.get(f"submitted_{qkey}", False):
        return
    passed = st.session_state.get(f"passed_{qkey}", False)
    if total is not None:
        score = st.session_state.get(f"score_{qkey}", 0)
        st.metric("점수", f"{score}/{total}")
    if passed:
        st.success("조건을 충족했습니다.")
    else:
        st.error("일부 조건이 충족되지 않았습니다.")
        for x in st.session_state.get(f"feedback_{qkey}", []):
            st.write("•", x)
    if models:
        with st.expander("모범 답안 보기"):
            if isinstance(models, dict):
                for k, v in models.items():
                    st.write(f"**{k}**: {v}")
            else:
                st.write(models)

# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.markdown("### 📚 자료 구성")
    st.markdown("""
- **1세트:** 사회적 촉진·사회적 억제
- **2세트:** 정전기
- **3세트:** 인공 지능과 예술
""")
    st.divider()
    st.markdown("### 📓 공통 학습 내용")
    st.markdown("""
- 설명 방법 6가지
- 영상 매체의 복합양식성
- 시각·청각 요소와 표현 효과
""")
    st.divider()
    st.caption("원자료의 구조대로 3세트 × 각 3문항으로 구성했습니다.")

# -------------------------
# Header
# -------------------------
st.markdown('<div class="hero-title">📝 [국어] 서·논술형 답안 작성 연습</div>', unsafe_allow_html=True)
st.markdown("""
<div class="hero-desc">
2회고사 대비 모의 문항의 구조를 그대로 따라 연습하는 앱입니다.
각 세트에는 서·논술형 1, 2, 3이 있으며, 답안을 입력한 뒤 조건 충족 여부를 확인할 수 있습니다.
</div>
""", unsafe_allow_html=True)

done = completed_count()
c1, c2 = st.columns([5,1])
with c1:
    st.write(f"✅ 완료한 문항: **{done} / 9**")
    st.progress(done/9)
with c2:
    st.button("🔄 처음부터", on_click=reset_all, use_container_width=True)

st.caption("탭은 원자료의 세트 수에 맞춰 1세트·2세트·3세트로 구성했습니다.")
st.divider()

tabs = st.tabs(["1세트", "2세트", "3세트", "📚 복습할 내용"])

# =========================================================
# 1세트
# =========================================================
with tabs[0]:
    st.markdown('<div class="set-title">1세트 — 사회적 촉진·사회적 억제</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="passage">
<b>[지문 핵심]</b> 비교적 쉬운 과제나 친숙한 과목은 커피숍·도서관·공부 모임처럼
다른 사람과 함께하는 환경이 효율적일 수 있다. 반면 지나치게 어렵거나 도전이 필요한 과제는
충분히 연습하며 익숙해질 때까지 차분하게 혼자 집중하는 것이 좋다.
</div>
""", unsafe_allow_html=True)

    with st.expander("서·논술형 1 — 표 빈칸 채우기", expanded=True):
        st.write("㉠~㉢에 들어갈 내용을 쓰세요.")
        a = st.text_input("㉠ 과제의 특성", key="s1q1_a")
        b = st.text_input("㉡ 효율적인 환경 및 방법", key="s1q1_b")
        c = st.text_input("㉢ 관련된 심리 현상", key="s1q1_c")
        if st.button("서·논술형 1 제출", key="s1q1_submit", type="primary"):
            checks = {
                "㉠": has_any(a, ["쉬운", "비교적 쉬운", "어렵지 않은", "큰 노력이 필요하지 않은", "큰 노력을 들일 필요가 없는"]),
                "㉡": has_any(b, ["혼자"]) and has_any(b, ["집중"]),
                "㉢": has_any(c, ["사회적 억제"]) and not has_any(c, ["사회적 촉진"]),
            }
            fb = []
            if not checks["㉠"]: fb.append("㉠에는 쉬운 과제라는 특성이 드러나야 합니다.")
            if not checks["㉡"]: fb.append("㉡에는 '혼자'와 '집중'의 의미가 모두 필요합니다.")
            if not checks["㉢"]: fb.append("㉢은 개념명 '사회적 억제'가 필요합니다.")
            mark("1-1", all(checks.values()), sum(checks.values()), fb)
        show_result("1-1", {
            "㉠": "비교적 쉬운 취미 생활이나 큰 노력을 들일 필요가 없는 과제",
            "㉡": "충분히 연습하며 익숙해질 때까지 차분하게 혼자 집중함",
            "㉢": "사회적 억제",
        })

    with st.expander("서·논술형 2 — 설명 방법 2가지 활용"):
        st.markdown("""
<div class="condition">
① 서로 다른 설명 방법을 사용할 것.<br>
② 지문 내용만 활용할 것.<br>
③ 선택한 설명 방법의 특성이 실제 문장에 드러날 것.
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
            misconception = has_any(s1+s2, ["인지 부하","뇌과학","어려운 과제는 다른 사람들과 함께하는 것이 더 좋다"])
            passed = distinct and st1 and st2 and content and conclusion and not misconception
            fb=[]
            if not distinct: fb.append("두 문장에 서로 다른 설명 방법을 사용해야 합니다.")
            if not st1: fb.append(f"(1)에서 선택한 '{m1}'의 특성이 문장에 드러나지 않습니다.")
            if not st2: fb.append(f"(2)에서 선택한 '{m2}'의 특성이 문장에 드러나지 않습니다.")
            if not content: fb.append("지문 핵심 내용이 부족합니다.")
            if not conclusion: fb.append("과제 난이도에 따라 학습 전략이 달라진다는 방향이 드러나야 합니다.")
            if misconception: fb.append("지문 밖의 개념 또는 반대 방향 설명이 포함되어 있습니다.")
            mark("1-2", passed, None, fb)
        show_result("1-2", {
            "비교와 대조": "비교적 쉬운 과제는 다른 사람들과 함께하는 것이 효율적이지만, 지나치게 어렵거나 도전이 필요한 과제는 차분하게 혼자 집중하는 것이 좋다.",
            "예시": "예를 들어 평소 친숙하고 좋아하는 과목이라면 공부 모임을 만들어 다른 사람들과 함께 공부할 수 있다.",
            "분류와 구분": "과제는 난이도에 따라 비교적 쉬운 과제와 지나치게 어렵거나 도전이 필요한 과제로 나누어 볼 수 있다.",
        })

    with st.expander("서·논술형 3 — 영상 기획안"):
        st.markdown("""
<div class="condition">
어려운 과제를 할 때 필요한 환경의 특성이 드러나도록 시각·청각 요소를 계획하고,
각 요소의 효과를 지문 근거와 연결해 쓰세요.
</div>
""", unsafe_allow_html=True)
        v = st.text_area("Ⓐ 시각 요소", key="s1q3_v")
        ve = st.text_area("시각 요소의 효과", key="s1q3_ve")
        a = st.text_area("Ⓑ 청각 요소", key="s1q3_a")
        ae = st.text_area("청각 요소의 효과", key="s1q3_ae")
        if st.button("서·논술형 3 제출", key="s1q3_submit", type="primary"):
            v_ok = has_any(v, ["혼자","한 학생","차분","집중","연습","반복"])
            a_ok = has_any(a, ["조용","고요","소음을 줄","소음을 최소","무음","작은 소리"])
            ve_ok = has_any(ve, ["어려운 과제","도전이 필요한","혼자","집중","차분","연습","익숙해질 때까지"])
            ae_ok = has_any(ae, ["어려운 과제","혼자","집중","차분","고요"])
            bad = has_any(v+a+ve+ae, ["친구들과 떠들","빠르고 신나는 음악","시끄러운"])
            passed = v_ok and a_ok and ve_ok and ae_ok and not bad
            fb=[]
            if not v_ok: fb.append("시각 요소에 어려운 과제에 필요한 환경 특성이 드러나지 않습니다.")
            if not ve_ok: fb.append("시각 효과에 지문 근거가 필요합니다.")
            if not a_ok: fb.append("청각 요소에 차분하고 집중되는 환경이 드러나지 않습니다.")
            if not ae_ok: fb.append("청각 효과에 지문 근거가 필요합니다.")
            if bad: fb.append("쉬운 과제의 환경 특성을 어려운 과제에 적용한 오개념이 있습니다.")
            mark("1-3", passed, sum([v_ok,ve_ok,a_ok,ae_ok]), fb)
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
<div class="passage">
<b>[지문 핵심]</b> 정전기는 전하가 이동하지 않고 머물러 있는 전기 현상이다.
실생활 전기가 '흐르는 물'이라면 정전기는 '높은 곳에 고여 있는 물'에 비유할 수 있다.
정전기는 전압은 높지만 전하가 이동하지 않아 위험하지 않다.
</div>
""", unsafe_allow_html=True)

    with st.expander("서·논술형 1 — 표 빈칸 채우기", expanded=True):
        a = st.text_input("㉠ 물의 상태에 비유", key="s2q1_a")
        b = st.text_input("㉡ 전하의 상태", key="s2q1_b")
        c = st.text_input("㉢ 위험성", key="s2q1_c")
        if st.button("서·논술형 1 제출", key="s2q1_submit", type="primary"):
            checks = {
                "㉠": has_any(a, ["높은 곳","높은 위치"]) and has_any(a, ["고여","고인","머물러","흐르지"]),
                "㉡": has_any(b, ["전하"]) and has_any(b, ["이동하지","정지","머물러","움직이지"]),
                "㉢": has_any(c, ["위험하지","위험이 없","피해가 없"]),
            }
            fb=[]
            if not checks["㉠"]: fb.append("㉠에는 '높은 곳'과 '고여 있음'이 함께 드러나야 합니다.")
            if not checks["㉡"]: fb.append("㉡에는 전하가 이동하지 않고 머문다는 의미가 필요합니다.")
            if not checks["㉢"]: fb.append("㉢에는 위험하지 않다는 결론이 필요합니다.")
            mark("2-1", all(checks.values()), sum(checks.values()), fb)
        show_result("2-1", {
            "㉠": "높은 곳에 고여 있는 물",
            "㉡": "전하가 이동하지 않고 머물러 있음",
            "㉢": "위험하지 않음",
        })

    with st.expander("서·논술형 2 — 설명 방법 2가지 활용"):
        m1 = st.selectbox("(1) 설명 방법", ["정의","인과","비교와 대조"], key="s2q2_m1")
        s1 = st.text_area("(1) 문장", key="s2q2_s1")
        m2 = st.selectbox("(2) 설명 방법", ["인과","비교와 대조","정의"], key="s2q2_m2")
        s2 = st.text_area("(2) 문장", key="s2q2_s2")
        if st.button("서·논술형 2 제출", key="s2q2_submit", type="primary"):
            distinct = m1 != m2
            st1, st2 = method_ok(m1,s1), method_ok(m2,s2)
            content = has_any(s1+s2, ["정전기"]) and has_any(s1+s2, ["전하가 이동하지","전하가 정지","전하가 머물러","위험하지","실생활 전기"])
            bad = has_any(s1+s2, ["정전기는 전하가 이동한다","정전기는 위험하다","전압이 높아서 위험하다","전기는 정전기와 실생활 전기로 나뉜다"])
            conclusion = has_any(s1+s2, ["전하가 이동하지","전하가 정지","전하가 머물러","위험하지"])
            passed = distinct and st1 and st2 and content and conclusion and not bad
            fb=[]
            if not distinct: fb.append("두 문장에 서로 다른 설명 방법을 사용해야 합니다.")
            if not st1: fb.append(f"(1)에서 선택한 '{m1}'의 특성이 드러나지 않습니다.")
            if not st2: fb.append(f"(2)에서 선택한 '{m2}'의 특성이 드러나지 않습니다.")
            if not content: fb.append("정전기의 핵심 내용이 부족합니다.")
            if not conclusion: fb.append("정전기의 핵심 특성에 대한 결론이 분명해야 합니다.")
            if bad: fb.append("정전기의 특성을 반대로 설명한 오개념이 있습니다.")
            mark("2-2", passed, None, fb)
        show_result("2-2", {
            "정의": "정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기와 그로 인한 전기 현상을 말한다.",
            "인과": "정전기는 전압이 매우 높지만 전하가 이동하지 않고 머물러 있기 때문에 위험하지 않다.",
            "비교와 대조": "실생활에서 쓰는 전기는 전하가 이동하지만 정전기는 전하가 이동하지 않고 머물러 있다는 차이가 있다.",
        })

    with st.expander("서·논술형 3 — 영상 기획안"):
        v = st.text_area("Ⓐ 시각 요소", key="s2q3_v")
        ve = st.text_area("시각 요소의 효과", key="s2q3_ve")
        a = st.text_area("Ⓑ 청각 요소", key="s2q3_a")
        ae = st.text_area("청각 요소의 효과", key="s2q3_ae")
        if st.button("서·논술형 3 제출", key="s2q3_submit", type="primary"):
            v_ok = has_any(v, ["높은 곳","높은 위치"]) and has_any(v, ["고여","고인","흐르지","떨어지지","머물러"])
            a_ok = has_any(a, ["흐르는 소리를 사용하지","흐르는 소리 없음","무음","고요","조용"])
            ve_ok = has_any(ve, ["전압이 높","높은 전압","전하가 이동하지","전하가 머물러","위험하지"])
            ae_ok = has_any(ae, ["전하가 이동하지","전하가 머물러","전하가 정지","위험하지"])
            bad = has_any(v+a+ve+ae, ["큰 폭포 소리","콸콸 흐르","정전기는 위험하다"])
            passed = v_ok and a_ok and ve_ok and ae_ok and not bad
            fb=[]
            if not v_ok: fb.append("시각 요소에 '높은 곳'과 '고여 있음/흐르지 않음'이 드러나야 합니다.")
            if not ve_ok: fb.append("시각 효과에 정전기의 본문 근거가 필요합니다.")
            if not a_ok: fb.append("청각 요소는 흐르지 않는 정적인 상태를 표현해야 합니다.")
            if not ae_ok: fb.append("청각 효과에 전하가 이동하지 않는다는 본문 근거가 필요합니다.")
            if bad: fb.append("실생활 전기의 특성을 정전기에 적용한 오개념이 있습니다.")
            mark("2-3", passed, sum([v_ok,ve_ok,a_ok,ae_ok]), fb)
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
<div class="passage">
<b>[지문 핵심]</b> 인간의 작품에는 작가의 감정·철학·삶의 경험·관점·환경 등이 담긴다.
인공 지능은 인간과 같은 감정이나 독자적인 철학·이야기가 없기 때문에 그 그림을 인간의 예술과
동일하게 보기는 어렵다. 그러나 미술계에 변화를 가져오고 예술의 범주를 확장할 수 있다는 점에서는
상징적인 가치가 있다.
</div>
""", unsafe_allow_html=True)

    with st.expander("서·논술형 1 — 표 빈칸 채우기", expanded=True):
        a = st.text_area("㉠ 올림픽 경기에 비유", key="s3q1_a")
        b = st.text_area("㉡ 예술로 볼 수 있는가(근거 포함)", key="s3q1_b")
        c = st.text_area("㉢ 예술로서의 가치", key="s3q1_c")
        if st.button("서·논술형 1 제출", key="s3q1_submit", type="primary"):
            checks = {
                "㉠": has_any(a, ["로봇"]) and has_any(a, ["완벽","실수 없이"]) and has_any(a, ["마음을 울리지","감동을 주지","감동이 없","울림이 없"]),
                "㉡": has_any(b, ["감정이 없","감정을 느끼지 못","철학이 없","이야기가 없"]) and has_any(b, ["예술로 보기 어렵","예술로 볼 수 없"]),
                "㉢": has_any(c, ["미술계에 변화","미술계에 큰 변화","예술의 범주를 확장","예술의 범위를 넓","상징적인 가치"]),
            }
            fb=[]
            if not checks["㉠"]: fb.append("㉠에는 로봇의 완벽한 수행과 감동 없음이 모두 필요합니다.")
            if not checks["㉡"]: fb.append("㉡에는 AI의 감정·철학·이야기 부재와 '예술로 보기 어려움'의 결론이 필요합니다.")
            if not checks["㉢"]: fb.append("㉢에는 미술계 변화 또는 예술 범주 확장이라는 가치가 필요합니다.")
            mark("3-1", all(checks.values()), sum(checks.values()), fb)
        show_result("3-1", {
            "㉠": "한 번의 실수 없이 완벽하게 피겨 스케이팅하지만 사람의 마음을 울리지 못하는 로봇",
            "㉡": "감정을 느끼지 못하고 독자적인 철학이나 이야기가 없으므로 예술로 보기 어렵다.",
            "㉢": "기존 미술계에 큰 변화를 가져왔고 예술의 범주를 확장할 수 있다는 점에서 상징적인 가치가 있다.",
        })

    with st.expander("서·논술형 2 — 설명 방법 2가지 활용"):
        m1 = st.selectbox("(1) 설명 방법", ["비교와 대조","인과","분석","예시"], key="s3q2_m1")
        s1 = st.text_area("(1) 문장", key="s3q2_s1")
        m2 = st.selectbox("(2) 설명 방법", ["인과","분석","예시","비교와 대조"], key="s3q2_m2")
        s2 = st.text_area("(2) 문장", key="s3q2_s2")
        if st.button("서·논술형 2 제출", key="s3q2_submit", type="primary"):
            distinct = m1 != m2
            st1, st2 = method_ok(m1,s1), method_ok(m2,s2)
            content = has_any(s1+s2, ["감정","철학","경험","관점","환경","예술로 보기 어렵","미술계에 변화","예술의 범주"])
            bad = has_any(s1+s2, ["가치가 전혀 없다","기술이 부족해서 예술이 아니다","사람보다 창의적이다","예술은 인간 예술과 인공 지능 예술로 나뉜다"])
            conclusion = has_any(s1+s2, ["예술로 보기 어렵","예술로 볼 수 없","미술계에 변화","예술의 범주","상징적인 가치"])
            passed = distinct and st1 and st2 and content and conclusion and not bad
            fb=[]
            if not distinct: fb.append("두 문장에 서로 다른 설명 방법을 사용해야 합니다.")
            if not st1: fb.append(f"(1)에서 선택한 '{m1}'의 특성이 드러나지 않습니다.")
            if not st2: fb.append(f"(2)에서 선택한 '{m2}'의 특성이 드러나지 않습니다.")
            if not content: fb.append("인간 예술 또는 AI 그림의 핵심 내용이 부족합니다.")
            if not conclusion: fb.append("AI 그림의 예술성 한계 또는 상징적 가치에 대한 결론이 필요합니다.")
            if bad: fb.append("지문에 없는 평가나 잘못된 분류가 포함되어 있습니다.")
            mark("3-2", passed, None, fb)
        show_result("3-2", {
            "비교와 대조": "인간의 작품에는 작가의 감정과 철학, 경험 등이 담겨 있지만 인공 지능은 감정이나 독자적인 철학과 이야기가 없다는 차이가 있다.",
            "인과": "인공 지능이 그린 그림은 기존 미술계에 큰 변화를 가져왔고 예술의 범주를 확장할 수 있으므로 상징적인 가치가 있다.",
            "분석": "인간의 작품에는 작가의 감정과 철학, 삶의 경험, 관점, 환경 등의 여러 요소가 종합적으로 담겨 있다.",
            "예시": "예를 들어 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅하더라도 우리의 마음을 울리지는 못한다.",
        })

    with st.expander("서·논술형 3 — 영상 기획안 [총 6점]"):
        v = st.text_area("Ⓐ 시각 요소", key="s3q3_v")
        ve = st.text_area("시각 요소의 효과", key="s3q3_ve")
        a = st.text_area("Ⓑ 청각 요소", key="s3q3_a")
        ae = st.text_area("청각 요소의 효과", key="s3q3_ae")
        if st.button("서·논술형 3 제출", key="s3q3_submit", type="primary"):
            v_ok = has_any(v, ["작가","화가","감정","철학","경험","관점","환경","노력","열정"])
            a_ok = has_any(a, ["작가의 목소리","감정","생각","이야기","배경음악","음악"])
            ve_ok = has_any(ve, ["감정","철학","경험","관점","환경","마음을 울리","감동","울림"])
            ae_ok = has_any(ae, ["감정","철학","이야기","마음을 울리","감동","울림"])
            bad = has_any(v+a+ve+ae, ["기계음만","메트로놈만","인공 지능 그림의 상징적 가치만"])
            score = (1 if v_ok else 0)+(2 if ve_ok else 0)+(1 if a_ok else 0)+(2 if ae_ok else 0)
            passed = score == 6 and not bad
            fb=[]
            if not v_ok: fb.append("시각 요소에 인간 예술의 특성이 드러나지 않습니다.")
            if not ve_ok: fb.append("시각 효과에 인간 예술의 본문 근거가 필요합니다.")
            if not a_ok: fb.append("청각 요소에 인간의 감정·생각·이야기를 표현하는 요소가 필요합니다.")
            if not ae_ok: fb.append("청각 효과에 인간 예술의 본문 근거가 필요합니다.")
            if bad: fb.append("장면 1의 기계적 특성 또는 AI의 가치만을 장면 2에 적용한 오개념이 있습니다.")
            mark("3-3", passed, score, fb)
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

    wrong = [k for k in QUESTION_KEYS if st.session_state.get(f"submitted_{k}") and not st.session_state.get(f"passed_{k}")]
    if not wrong and done < 9:
        st.info("아직 모든 문항을 제출하지 않았습니다. 제출한 문항 중 틀린 내용이 있으면 여기에 표시됩니다.")
    elif not wrong and done == 9:
        st.success("9개 문항을 모두 통과했습니다.")

    review = {
        "1-1":"쉬운 과제와 어려운 과제의 학습 환경을 구분하세요.",
        "1-2":"설명 방법은 이름보다 실제 문장 구조가 중요합니다.",
        "1-3":"영상 요소와 효과를 지문 근거로 연결하세요.",
        "2-1":"정전기는 높은 곳에 고인 물처럼 전하가 이동하지 않고 머뭅니다.",
        "2-2":"정전기의 정의·인과·비교와 대조를 구분하세요.",
        "2-3":"실생활 전기의 '흐름'과 정전기의 '정지'를 뒤바꾸지 마세요.",
        "3-1":"AI 그림의 예술성 한계와 상징적 가치를 구분하세요.",
        "3-2":"인간 예술과 AI 그림의 차이를 지문 내용 안에서 설명하세요.",
        "3-3":"인간 예술의 감정·철학·경험·관점·환경과 마음의 울림을 연결하세요.",
    }
    for k in wrong:
        st.markdown(f'<div class="review-card"><b>{k} 문항</b><br>{review[k]}</div>', unsafe_allow_html=True)

    st.divider()
    st.write("**세트 완료 현황**")
    for s in [1,2,3]:
        st.write(f"- {s}세트: {'✅ 완료' if set_completed(s) else '⬜ 미완료'}")
