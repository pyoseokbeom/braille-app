import streamlit as st
import matplotlib.pyplot as plt
import ezdxf
from pathlib import Path

# ================== 점자 규격 ==================
DOT_R = 0.75        # 점 반지름 (지름 1.5mm)
COL_STEP = 2.5      # 셀 내부 가로 간격
ROW_STEP = 2.5      # 셀 내부 세로 간격
CELL_PITCH_X = 6.0  # 셀 가로 피치
CELL_PITCH_Y = 10.0 # 셀 세로 피치

dot_positions = {
    1:(0,0), 2:(0,ROW_STEP), 3:(0,ROW_STEP*2),
    4:(COL_STEP,0), 5:(COL_STEP,ROW_STEP), 6:(COL_STEP,ROW_STEP*2),
}

# ================== 점자 매핑 ==================
initial_map = {'ㄱ':[4], 'ㄴ':[1,4], 'ㄷ':[2,4], 'ㄹ':[5], 'ㅁ':[1,5], 'ㅂ':[4,5],
               'ㅅ':[6], 'ㅇ':[], 'ㅈ':[4,6], 'ㅊ':[5,6], 'ㅋ':[1,2,4], 'ㅌ':[1,2,5],
               'ㅍ':[1,4,5], 'ㅎ':[2,4,5]}
vowel_map = {'ㅏ':[1,2,6], 'ㅑ':[3,4,5], 'ㅓ':[2,3,4], 'ㅕ':[1,5,6],
             'ㅗ':[1,3,6], 'ㅛ':[3,4,6], 'ㅜ':[1,3,4], 'ㅠ':[1,4,6],
             'ㅡ':[2,4,6], 'ㅣ':[1,3,5], 'ㅔ':[1,3,4,5], 'ㅐ':[1,2,3,5],
             'ㅖ':[3,4]}
final_map = {'ㄱ':[1], 'ㄴ':[2,5], 'ㄷ':[3,5], 'ㄹ':[2], 'ㅁ':[2,6], 'ㅂ':[1,2],
             'ㅅ':[3], 'ㅇ':[2,3,5,6], 'ㅈ':[1,3], 'ㅊ':[2,3], 'ㅋ':[2,3,5],
             'ㅌ':[2,3,6], 'ㅍ':[2,5,6], 'ㅎ':[3,5,6]}

# ================== 한글 분해 ==================
S_BASE, L_COUNT, V_COUNT, T_COUNT = 0xAC00, 19, 21, 28
N_COUNT, S_COUNT = V_COUNT * T_COUNT, L_COUNT*V_COUNT*T_COUNT
compat_initials = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
compat_medials  = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ']
compat_finals   = ['', 'ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']

def decompose(ch):
    code = ord(ch)
    if S_BASE <= code < S_BASE+S_COUNT:
        s_index = code - S_BASE
        l = compat_initials[s_index // N_COUNT]
        v = compat_medials[(s_index % N_COUNT)//T_COUNT]
        t = compat_finals[s_index % T_COUNT]
        return l,v,t
    return None,None,None

def to_braille_cells(text):
    cells = []
    for ch in text:
        if ch == " ":
            cells.append(None)
            continue
        L,V,T = decompose(ch)
        if L and L!="ㅇ": cells.append(initial_map.get(L, []))
        if V: cells.append(vowel_map.get(V, []))
        if T: cells.append(final_map.get(T, []))
    return cells

# ================== DXF 생성 ==================
def make_dxf(text):
    filename = f"braille_{text}.dxf"
    cells = to_braille_cells(text)
    doc = ezdxf.new()
    msp = doc.modelspace()
    x = 0
    for cell in cells:
        if cell is None:
            x += CELL_PITCH_X
            continue
        for d in cell:
            dx,dy = dot_positions[d]
            msp.add_circle((x+dx, dy), DOT_R)  # CAD 좌표는 그대로
        x += CELL_PITCH_X
    doc.saveas(filename)
    return filename

# ================== SVG 생성 ==================
def make_svg(text):
    filename = f"braille_{text}.svg"
    cells = to_braille_cells(text)
    n = len(cells)
    width = (n-1)*CELL_PITCH_X + COL_STEP + DOT_R*2
    height = CELL_PITCH_Y
    start_x = DOT_R
    start_y = DOT_R
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">']
    x = start_x
    for cell in cells:
        if cell is None:
            x += CELL_PITCH_X
            continue
        for d in cell:
            dx,dy = dot_positions[d]
            cx = x+dx
            cy = start_y+dy
            parts.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{DOT_R}" fill="black"/>')
        x += CELL_PITCH_X
    parts.append('</svg>')
    Path(filename).write_text("\n".join(parts), encoding="utf-8")
    return filename

# ================== PNG 미리보기 (상/하 반전 수정) ==================
def plot_braille(text):
    cells = to_braille_cells(text)
    n = len(cells)
    fig, ax = plt.subplots(figsize=(n*1.2, 3))
    x = 0
    for cell in cells:
        if cell is None:
            x += CELL_PITCH_X
            continue
        for d in cell:
            dx,dy = dot_positions[d]
            cx = x+dx
            cy = CELL_PITCH_Y - dy  # 🔥 y축 반전 수정
            circle = plt.Circle((cx, cy), DOT_R, color="black")
            ax.add_patch(circle)
        x += CELL_PITCH_X
    ax.set_aspect("equal")
    ax.set_xlim(-2, x+2)
    ax.set_ylim(-2, CELL_PITCH_Y+2)
    ax.axis("off")
    return fig

# ================== Unicode 점자 변환 ==================
def to_unicode_braille(text):
    cells = to_braille_cells(text)
    result = []
    for cell in cells:
        if cell is None:
            result.append(" ")
            continue
        val = 0
        for d in cell:
            val |= (1 << (d-1))
        result.append(chr(0x2800 + val))
    return "".join(result)

# ================== Streamlit UI ==================
st.set_page_config(page_title="한글 → 점자 변환기", page_icon="🔤", layout="centered")

st.title("🔤 한글 → 점자 변환기")
st.caption("👤 제작자: 표석범")
st.caption("입력한 한글 텍스트를 **KS X 9211 점자 규격**에 맞게 변환합니다. DXF / SVG 다운로드 전 미리보기를 확인하세요.")

user_text = st.text_input("변환할 텍스트", "지폐인식기")

if st.button("미리보기 & 변환"):
    # 1) 내부 알고리즘 미리보기
    st.markdown("### 👁 **변환 결과 미리보기 (내부 알고리즘)**")
    fig = plot_braille(user_text)
    st.pyplot(fig)

    # 2) 표준 점자 폰트 비교 (크기 맞춤)
    st.markdown("### 🔎 **표준 점자 폰트 비교 (Unicode Braille)**")
    st.markdown(
        f"<p style='font-size:42px; line-height:1.5'>{to_unicode_braille(user_text)}</p>",
        unsafe_allow_html=True
    )

    # 3) 파일 다운로드
    dxf_file = make_dxf(user_text)
    svg_file = make_svg(user_text)
    st.success(f"✅ '{user_text}' 변환 완료! DXF / SVG 다운로드 가능")

    col1, col2 = st.columns(2)
    with col1:
        with open(dxf_file, "rb") as f:
            st.download_button("📥 DXF 다운로드", f, file_name=dxf_file, mime="application/dxf")
    with col2:
        with open(svg_file, "rb") as f:
            st.download_button("🎨 SVG 다운로드", f, file_name=svg_file, mime="image/svg+xml")
