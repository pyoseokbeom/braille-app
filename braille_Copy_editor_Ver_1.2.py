import streamlit as st
import matplotlib.pyplot as plt
import ezdxf
from pathlib import Path
import json
from datetime import date

# ================== 메타 정보 ==================
AUTHOR = "표석범"
VERSION = "v1.0.2"
CREATED_DATE = "2025-09-15"

# ================== 점자 규격 ==================
DOT_R = 0.75        # 점 반경 (지름 1.5mm)
COL_STEP = 2.5      # 셀 내부 가로 간격 (mm)
ROW_STEP = 2.5      # 셀 내부 세로 간격 (mm)
CELL_PITCH_X = 6.0  # 셀 간 가로 피치 (mm)
CELL_PITCH_Y = 10.0 # 셀 간 세로 피치 (mm)
MARGIN_X = 2.0      # 좌우 여백 (mm)

dot_positions = {
    1:(0,0), 2:(0,ROW_STEP), 3:(0,ROW_STEP*2),
    4:(COL_STEP,0), 5:(COL_STEP,ROW_STEP), 6:(COL_STEP,ROW_STEP*2),
}

# ================== 길이 계산 ==================
def calc_length(num_cells):
    return (num_cells - 1) * CELL_PITCH_X + COL_STEP + DOT_R * 2 + (MARGIN_X * 2)

# ================== ○/● 배열 파서 ==================
def parse_circle_braille(input_text):
    lines = [line.strip() for line in input_text.strip().split("\n") if line.strip()]
    if len(lines) != 3:
        raise ValueError("○/● 방식은 반드시 3행이어야 합니다.")
    grid = [line.split() for line in lines]
    num_cells = len(grid[0]) // 2
    all_cells = []
    for c in range(num_cells):
        cell_dots = []
        if grid[0][c*2] == "●": cell_dots.append(1)
        if grid[0][c*2+1] == "●": cell_dots.append(4)
        if grid[1][c*2] == "●": cell_dots.append(2)
        if grid[1][c*2+1] == "●": cell_dots.append(5)
        if grid[2][c*2] == "●": cell_dots.append(3)
        if grid[2][c*2+1] == "●": cell_dots.append(6)
        all_cells.append(cell_dots if cell_dots else None)
    return all_cells

# ================== 유니코드 점자 파서 ==================
def parse_unicode_braille(text):
    all_cells = []
    for ch in text.strip():
        if not (0x2800 <= ord(ch) <= 0x28FF):
            continue
        code = ord(ch) - 0x2800
        cell_dots = []
        for i in range(6):
            if code & (1 << i):
                cell_dots.append(i+1)
        all_cells.append(cell_dots if cell_dots else None)
    return all_cells

# ================== 자동 판별 ==================
def parse_braille(input_text):
    if not input_text.strip():
        raise ValueError("입력 내용이 없습니다.")
    if "○" in input_text or "●" in input_text:
        return parse_circle_braille(input_text)
    if any(0x2800 <= ord(ch) <= 0x28FF for ch in input_text):
        return parse_unicode_braille(input_text)
    raise ValueError("지원하지 않는 점자 형식입니다.")

# ================== DXF / SVG / JSON ==================
def make_dxf(all_cells):
    filename = "braille_from_text.dxf"
    doc = ezdxf.new()
    msp = doc.modelspace()

    width = len(all_cells) * CELL_PITCH_X + COL_STEP + DOT_R * 2 + (MARGIN_X * 2)
    height = 10.0

    # 대지 테두리
    msp.add_lwpolyline([(0,0), (width,0), (width,height), (0,height), (0,0)],
                       dxfattribs={"lineweight": 10}, close=True)

    dot_block_height = (ROW_STEP * 2) + (DOT_R * 2)
    vertical_offset = (height - dot_block_height) / 2 + DOT_R

    x_offset = DOT_R + MARGIN_X
    for cell in all_cells:
        if cell:
            for d in cell:
                dx, dy = dot_positions[d]
                cx = x_offset + dx
                cy = vertical_offset + (ROW_STEP * 2 - dy)   # ✅ DXF는 y 위로 증가 → 반전 적용
                msp.add_circle((cx, cy), DOT_R)
        x_offset += CELL_PITCH_X

    doc.saveas(filename)
    return filename

def make_svg(all_cells):
    filename = "braille_from_text.svg"
    width = len(all_cells) * CELL_PITCH_X + COL_STEP + DOT_R * 2 + (MARGIN_X * 2)
    height = 10.0

    dot_block_height = (ROW_STEP * 2) + (DOT_R * 2)
    vertical_offset = (height - dot_block_height) / 2 + DOT_R

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{width}mm" height="{height}mm" '
             f'viewBox="0 0 {width} {height}">']

    # 대지 테두리
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" '
                 f'stroke="black" fill="white" stroke-width="0.1"/>')

    x_offset = DOT_R + MARGIN_X
    for cell in all_cells:
        if cell:
            for d in cell:
                dx,dy = dot_positions[d]
                cx = x_offset + dx
                cy = vertical_offset + dy   # ✅ SVG는 y 아래로 증가 → 그대로
                parts.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{DOT_R}" fill="black"/>')
        x_offset += CELL_PITCH_X

    parts.append('</svg>')
    Path(filename).write_text("\n".join(parts), encoding="utf-8")
    return filename

def save_json(all_cells):
    filename = "braille_from_text.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_cells, f, ensure_ascii=False, indent=2)
    return filename

# ================== Streamlit UI ==================
st.set_page_config(page_title="점자 변환기 + 점자로 연동", page_icon="🟡", layout="wide")

st.title("🟡 점자 붙여넣기 변환기 (○/● & ⠁⠟⠬ 지원 + 대지 출력)")
st.caption(f"👤 제작자: {AUTHOR}")
st.caption(f"📅 제작일: {CREATED_DATE}")
st.caption(f"🔖 버전: {VERSION}")

# iframe
st.components.v1.html(
    '''
    <iframe src="https://jumjaro.org/"
            width="100%" height="600"
            style="border:none; overflow:hidden;"
            scrolling="no">
    </iframe>
    ''',
    height=600
)

st.markdown("---")
st.markdown("### 📥 변환된 점자 붙여넣기")

input_braille = st.text_area("점자 붙여넣기 (○/● 또는 ⠁⠟⠬)", height=150)

if st.button("변환 실행"):
    try:
        all_cells = parse_braille(input_braille)
        st.success(f"✅ 점자 {len(all_cells)}셀 변환 완료!")

        # 미리보기
        st.markdown("### 👁 점자 미리보기")
        fig, ax = plt.subplots(figsize=(len(all_cells) * 0.6, 2))
        width = len(all_cells) * CELL_PITCH_X + COL_STEP + DOT_R * 2 + (MARGIN_X * 2)
        height = 10.0
        ax.add_patch(plt.Rectangle((0,0), width, height, fill=False, edgecolor="black", linewidth=0.5))

        x_offset = DOT_R + MARGIN_X
        dot_block_height = (ROW_STEP * 2) + (DOT_R * 2)
        vertical_offset = (height - dot_block_height) / 2 + DOT_R

        for cell in all_cells:
            if cell:
                for d in cell:
                    dx, dy = dot_positions[d]
                    cx = x_offset + dx
                    cy = vertical_offset + (ROW_STEP * 2 - dy)   # ✅ 미리보기 = DXF와 동일
                    circle = plt.Circle((cx, cy), DOT_R, color="black")
                    ax.add_patch(circle)
            x_offset += CELL_PITCH_X

        ax.set_aspect("equal")
        ax.set_xlim(-2, width+2)
        ax.set_ylim(-2, height+2)
        ax.axis("off")
        st.pyplot(fig)

        # 전체 길이
        length_mm = calc_length(len(all_cells))
        st.info(f"📏 점자 전체 길이: {length_mm:.2f} mm")

        # 다운로드
        dxf_file = make_dxf(all_cells)
        svg_file = make_svg(all_cells)
        json_file = save_json(all_cells)

        col1, col2, col3 = st.columns(3)
        with col1:
            with open(dxf_file, "rb") as f:
                st.download_button("📥 DXF 다운로드", f, file_name=dxf_file, mime="application/dxf")
        with col2:
            with open(svg_file, "rb") as f:
                st.download_button("🎨 SVG 다운로드", f, file_name=svg_file, mime="image/svg+xml")
        with col3:
            with open(json_file, "rb") as f:
                st.download_button("💾 JSON 저장", f, file_name=json_file, mime="application/json")

    except Exception as e:
        st.error(f"입력 오류: {e}")
