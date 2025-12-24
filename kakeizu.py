import streamlit as st
import io
import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# ==========================================
# 1. 設定・データ定義
# ==========================================
FONT_NAME = "IPAMincho"
FONT_FILE = "ipam.ttf"

# 関係性マップ
RELATION_MAP = {
    'self': {'gen': 0, 'p_father': 'father', 'p_mother': 'mother', 'label': '本人', 'gender': 'm'},
    'father': {'gen': 1, 'p_father': 'ff', 'p_mother': 'fm', 'label': '父', 'gender': 'm'},
    'mother': {'gen': 1, 'p_father': 'mf', 'p_mother': 'mm', 'label': '母', 'gender': 'f'},
    'ff': {'gen': 2, 'p_father': 'fff', 'p_mother': 'ffm', 'label': '父の父', 'gender': 'm'},
    'fm': {'gen': 2, 'p_father': 'fmf', 'p_mother': 'fmm', 'label': '父の母', 'gender': 'f'},
    'mf': {'gen': 2, 'p_father': 'mff', 'p_mother': 'mfm', 'label': '母の父', 'gender': 'm'},
    'mm': {'gen': 2, 'p_father': 'mmf', 'p_mother': 'mmm', 'label': '母の母', 'gender': 'f'},
    'fff': {'gen': 3, 'p_father': 'ffff', 'p_mother': 'fffm', 'label': '父の父の父', 'gender': 'm'},
    'ffm': {'gen': 3, 'p_father': 'ffmf', 'p_mother': 'ffmm', 'label': '父の父の母', 'gender': 'f'},
    'fmf': {'gen': 3, 'p_father': 'fmff', 'p_mother': 'fmfm', 'label': '父の母の父', 'gender': 'm'},
    'fmm': {'gen': 3, 'p_father': 'fmmf', 'p_mother': 'fmmm', 'label': '父の母の母', 'gender': 'f'},
    'mff': {'gen': 3, 'p_father': 'mfff', 'p_mother': 'mffm', 'label': '母の父の父', 'gender': 'm'},
    'mfm': {'gen': 3, 'p_father': 'mfmf', 'p_mother': 'mfmm', 'label': '母の父の母', 'gender': 'f'},
    'mmf': {'gen': 3, 'p_father': 'mmff', 'p_mother': 'mmfm', 'label': '母の母の父', 'gender': 'm'},
    'mmm': {'gen': 3, 'p_father': 'mmmf', 'p_mother': 'mmmm', 'label': '母の母の母', 'gender': 'f'},
    'ffff': {'gen': 4, 'label': '父の父の父の父', 'gender': 'm'},
    'fffm': {'gen': 4, 'label': '父の父の父の母', 'gender': 'f'},
    'ffmf': {'gen': 4, 'label': '父の父の母の父', 'gender': 'm'},
    'ffmm': {'gen': 4, 'label': '父の父の母の母', 'gender': 'f'},
    'fmff': {'gen': 4, 'label': '父の母の父の父', 'gender': 'm'},
    'fmfm': {'gen': 4, 'label': '父の母の父の母', 'gender': 'f'},
    'fmmf': {'gen': 4, 'label': '父の母の母の父', 'gender': 'm'},
    'fmmm': {'gen': 4, 'label': '父の母の母の母', 'gender': 'f'},
    'mfff': {'gen': 4, 'label': '母の父の父の父', 'gender': 'm'},
    'mffm': {'gen': 4, 'label': '母の父の父の母', 'gender': 'f'},
    'mfmf': {'gen': 4, 'label': '母の父の母の父', 'gender': 'm'},
    'mfmm': {'gen': 4, 'label': '母の父の母の母', 'gender': 'f'},
    'mmff': {'gen': 4, 'label': '母の母の父の父', 'gender': 'm'},
    'mmfm': {'gen': 4, 'label': '母の母の父の母', 'gender': 'f'},
    'mmmf': {'gen': 4, 'label': '母の母の母の父', 'gender': 'm'},
    'mmmm': {'gen': 4, 'label': '母の母の母の母', 'gender': 'f'},
}

GEN_PAIRS = {
    4: [('ffff', 'fffm'), ('ffmf', 'ffmm'), ('fmff', 'fmfm'), ('fmmf', 'fmmm'),
        ('mfff', 'mffm'), ('mfmf', 'mfmm'), ('mmff', 'mmfm'), ('mmmf', 'mmmm')],
    3: [('fff', 'ffm'), ('fmf', 'fmm'), ('mff', 'mfm'), ('mmf', 'mmm')],
    2: [('ff', 'fm'), ('mf', 'mm')],
    1: [('father', 'mother')]
}

FONT_SIZE_TREE = 7.5
FONT_SIZE_QUAD_NAME = 36
FONT_SIZE_BG = 10 

# ==========================================
# 2. PDF生成クラス
# ==========================================
class GenealogyPDF:
    def __init__(self, client_data, file_object):
        self.c = canvas.Canvas(file_object, pagesize=landscape(A4))
        self.width, self.height = landscape(A4)
        self.data = client_data
        
        # フォント登録（エラーハンドリング強化）
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
        except:
            fallback = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
            if os.path.exists(fallback):
                pdfmetrics.registerFont(TTFont(FONT_NAME, fallback))
            else:
                st.error(f"フォントファイル ({FONT_FILE}) が見つかりません。")

    def check_attributes(self, label):
        clean_label = "".join(label.split())
        is_guardian = False
        for g_item in self.data['guardians']:
            if "".join(g_item.split()) == clean_label:
                is_guardian = True
                break
        is_priority = False
        for p_item in self.data['priorities']:
            if "".join(p_item.split()) == clean_label:
                is_priority = True
                break
        return is_guardian, is_priority

    def draw_vertical_text(self, text, x, y, size, is_bold=False, is_guardian=False):
        self.c.saveState()
        char_height = size * 1.05
        total_height = len(text) * char_height
        start_y = y + (total_height / 2)
        
        if is_guardian:
            line_x = x - (size * 0.8)
            line_top = start_y + (size * 0.2)
            line_bottom = start_y - total_height - (size * 0.2)
            self.c.setLineWidth(0.5)
            self.c.setStrokeColor(colors.black)
            self.c.line(line_x, line_top, line_x, line_bottom)

        for i, char in enumerate(text):
            char_y = start_y - (i * char_height) - size
            t_obj = self.c.beginText()
            t_obj.setFont(FONT_NAME, size)
            t_obj.setTextOrigin(x - (size/2), char_y)
            
            if is_bold:
                t_obj.setTextRenderMode(2)
                self.c.setLineWidth(0.5)
                self.c.setStrokeColor(colors.black)
            else:
                t_obj.setTextRenderMode(0)
                self.c.setFillColor(colors.black)
            
            t_obj.textOut(char)
            self.c.drawText(t_obj)
        self.c.restoreState()

    def create_tree_page(self):
        margin_x_base = 15 * mm 
        margin_y_top = self.height - 40 * mm 
        margin_y_bottom = 25 * mm
        box_w = 8 * mm
        box_h = 24 * mm 
        box_h_half = box_h / 2
        
        self.c.saveState()
        self.c.setFont(FONT_NAME, 10)
        self.c.setFillColor(colors.black)
        legend_x = margin_x_base
        legend_y = self.height - 15 * mm
        self.c.drawString(legend_x, legend_y, "◎ 太字 ＝ 供養の優先順位の高いご先祖様")
        self.c.drawString(legend_x, legend_y - 6*mm, "◎ 左傍線 ＝ 守護してくださるご先祖様")
        self.c.restoreState()

        layer_height = (margin_y_top - margin_y_bottom) / 4
        gen_y = {
            4: margin_y_top,
            3: margin_y_top - layer_height,
            2: margin_y_top - layer_height * 2,
            1: margin_y_top - layer_height * 3,
            0: margin_y_bottom
        }
        coords = {} 
        
        w_available = self.width - (2 * margin_x_base)
        num_couples = 8
        slot_width = w_available / num_couples
        couple_spacing_gen4 = 14 * mm 
        
        for i, (hus, wife) in enumerate(GEN_PAIRS[4]):
            slot_center_x = (self.width - margin_x_base) - (i * slot_width) - (slot_width / 2)
            coords[hus] = (slot_center_x + couple_spacing_gen4/2, gen_y[4])
            coords[wife] = (slot_center_x - couple_spacing_gen4/2, gen_y[4])
            
        for gen in [3, 2, 1]:
            for hus, wife in GEN_PAIRS[gen]:
                p_hus_f = RELATION_MAP[hus]['p_father']
                p_hus_m = RELATION_MAP[hus]['p_mother']
                p_wife_f = RELATION_MAP[wife]['p_father']
                p_wife_m = RELATION_MAP[wife]['p_mother']
                cx_hus = (coords[p_hus_f][0] + coords[p_hus_m][0]) / 2
                cx_wife = (coords[p_wife_f][0] + coords[p_wife_m][0]) / 2
                coords[hus] = (cx_hus, gen_y[gen])
                coords[wife] = (cx_wife, gen_y[gen])

        p_self_f = 'father'
        p_self_m = 'mother'
        cx_self = (coords[p_self_f][0] + coords[p_self_m][0]) / 2
        coords['self'] = (cx_self, gen_y[0])

        def draw_bracket(p_f_key, p_m_key, child_key):
            fx, fy = coords[p_f_key]
            mx, my = coords[p_m_key]
            cx, cy = coords[child_key]
            self.c.saveState()
            self.c.setLineWidth(0.6) 
            self.c.setStrokeColor(colors.black)
            self.c.setDash([]) 
            f_bottom = fy - box_h_half
            m_bottom = my - box_h_half
            c_top = cy + box_h_half
            bar_y = f_bottom - 5 * mm
            self.c.line(fx, f_bottom, fx, bar_y)
            self.c.line(mx, m_bottom, mx, bar_y)
            self.c.line(fx, bar_y, mx, bar_y)
            self.c.line(cx, bar_y, cx, c_top)
            self.c.restoreState()

        for gen in [4, 3, 2, 1]:
            pairs = GEN_PAIRS[gen]
            for hus, wife in pairs:
                children = [k for k, v in RELATION_MAP.items() if v.get('p_father') == hus and v.get('p_mother') == wife]
                for child in children:
                    if child in coords:
                        draw_bracket(hus, wife, child)
        
        for key, (x, y) in coords.items():
            self._draw_node(key, x, y, box_w, box_h)
        self.c.showPage()

    def _draw_node(self, key, x, y, box_w, box_h):
        # 名前取得ロジックの修正：シンプルに key から取得
        name = self.data['names'].get(key)
        if not name:
            # 名前がなければラベル（本人、父など）を使用
            name = RELATION_MAP[key]['label']
            
        label = RELATION_MAP[key]['label']
        gender = RELATION_MAP[key].get('gender', 'm')
        
        is_guardian, is_priority = self.check_attributes(label)

        self.c.saveState()
        self.c.setLineWidth(0.6)
        self.c.setStrokeColor(colors.black) 
        self.c.setFillColor(colors.white)
        if gender == 'f':
            self.c.ellipse(x - box_w/2, y - box_h/2, x + box_w/2, y + box_h/2, fill=1, stroke=1)
        else:
            self.c.rect(x - box_w/2, y - box_h/2, box_w, box_h, fill=1, stroke=1)
        self.c.restoreState()
        self.draw_vertical_text(name, x, y, FONT_SIZE_TREE, is_priority, is_guardian)

    def create_quad_pages(self):
        targets = []
        # 本人をリストの最初に追加
        targets.append(('self', self.data['names'].get('self', '本人')))
        
        sorted_keys = sorted(RELATION_MAP.keys(), key=lambda x: RELATION_MAP[x]['gen'])
        for key in sorted_keys:
            if key == 'self': continue
            name = self.data['names'].get(key)
            label = RELATION_MAP[key]['label']
            display_text = name if name else label
            targets.append((key, display_text))
        for i in range(0, len(targets), 4):
            batch = targets[i:i+4]
            self._draw_quad_page(batch)

    def _draw_quad_page(self, people):
        w, h = self.width, self.height
        cx, cy = w/2, h/2
        
        self.c.saveState()
        self.c.setLineWidth(1.5) 
        self.c.setStrokeColor(colors.black)
        self.c.setDash([]) 
        self.c.line(cx, 0, cx, h)
        self.c.line(0, cy, w, cy)
        self.c.restoreState()
        
        rects = [(0, cy, cx, cy), (cx, cy, cx, cy), (0, 0, cx, cy), (cx, 0, cx, cy)]
        
        for idx, (key, name) in enumerate(people):
            if idx >= 4: break
            rx, ry, rw, rh = rects[idx]
            
            self.c.saveState()
            path = self.c.beginPath()
            path.rect(rx, ry, rw, rh)
            self.c.clipPath(path, stroke=0)
            
            bg_t = self.c.beginText()
            bg_t.setFont(FONT_NAME, FONT_SIZE_BG)
            bg_t.setFillColor(colors.white) 
            bg_t.setStrokeColor(colors.white)
            bg_t.setTextRenderMode(0) 
            tx = rx
            ty = ry + rh
            while ty > ry:
                bg_t.setTextOrigin(tx, ty)
                text_line = (name + "　") * 10
                bg_t.textOut(text_line)
                ty -= 12
            self.c.drawText(bg_t)
            self.c.restoreState()
            
            self.c.saveState() 
            label = RELATION_MAP[key]['label']
            is_guardian, is_priority = self.check_attributes(label)
            center_x = rx + rw/2
            center_y = ry + rh/2
            self.c.setFillColor(colors.black)
            t_obj = self.c.beginText()
            t_obj.setFont(FONT_NAME, FONT_SIZE_QUAD_NAME)
            
            if is_priority:
                t_obj.setTextRenderMode(2) 
                self.c.setLineWidth(1.5)
                self.c.setStrokeColor(colors.black)
            else:
                t_obj.setTextRenderMode(0) 

            text_width = self.c.stringWidth(name, FONT_NAME, FONT_SIZE_QUAD_NAME)
            text_start_x = center_x - text_width/2
            t_obj.setTextOrigin(text_start_x, center_y)
            t_obj.textOut(name)
            self.c.drawText(t_obj)
            
            if is_guardian:
                self.c.setLineWidth(1.2)
                self.c.setStrokeColor(colors.black)
                underline_y = center_y - (FONT_SIZE_QUAD_NAME * 0.25)
                self.c.line(text_start_x, underline_y, text_start_x + text_width, underline_y)
            self.c.restoreState()

        self.c.showPage()

    def create_summary_page(self):
        self.c.setFont(FONT_NAME, 14)
        x_base = 30 * mm
        y = self.height - 40 * mm
        self.c.drawString(x_base, y, "■ 記録・解析")
        y -= 15 * mm
        def draw_line(text, y_pos, size=10):
            t_obj = self.c.beginText()
            t_obj.setFont(FONT_NAME, size)
            t_obj.setTextOrigin(x_base, y_pos)
            t_obj.textOut(text)
            self.c.drawText(t_obj)
        draw_line("◎ 守護", y, 12)
        y -= 8 * mm
        for item in self.data['guardians']:
            draw_line(f"・{item}", y)
            y -= 6 * mm
        y -= 10 * mm
        draw_line("◎ 癒す優先順位", y, 12)
        y -= 8 * mm
        for item in self.data['priorities']:
            draw_line(f"・{item}", y)
            y -= 6 * mm
        y -= 10 * mm
        draw_line("◎ 契約・コード", y, 12)
        y -= 8 * mm
        for item in self.data['contracts']:
            draw_line(f"・{item}", y)
            y -= 6 * mm
        self.c.showPage()

    def save(self):
        self.c.save()

# ==========================================
# 3. テキスト解析処理（強化版）
# ==========================================
def parse_text_data(text):
    data = {'names': {}, 'guardians': [], 'priorities': [], 'contracts': []}
    current_section = 'names'
    label_map = {v['label']: k for k, v in RELATION_MAP.items()}
    # ラベルマップに「本人」を明示的に追加
    label_map['本人'] = 'self' 
    
    lines = text.split('\n')
    for line in lines:
        # 全角スペースや全角イコールなどの揺らぎを吸収
        line = line.replace('　', ' ').strip()
        if not line: continue
        
        if line.startswith('◎守護'):
            current_section = 'guardians'
            continue
        elif line.startswith('◎優先順位'):
            current_section = 'priorities'
            continue
        elif line.startswith('◎契約'):
            current_section = 'contracts'
            continue
        
        if current_section == 'names':
            # 全角イコール対応
            clean_line = line.replace('＝', '=')
            if '=' in clean_line:
                key_str, val = clean_line.split('=', 1)
                key_str = key_str.strip()
                val = val.strip()
                
                # 「本人」と書かれていたら強制的に key='self' として保存
                if key_str == '本人':
                    data['names']['self'] = val
                # その他のキー処理
                elif key_str in label_map:
                    sys_key = label_map[key_str]
                    data['names'][sys_key] = val
                elif key_str in RELATION_MAP:
                    data['names'][key_str] = val
                else:
                    data['names'][key_str] = val

        elif current_section == 'guardians':
            if line.startswith('・'): line = line[1:]
            data['guardians'].append(line)
        elif current_section == 'priorities':
            if line.startswith('・'): line = line[1:]
            data['priorities'].append(line)
        elif current_section == 'contracts':
            if line.startswith('・'): line = line[1:]
            data['contracts'].append(line)
    return data

# ==========================================
# 4. Streamlitアプリのメイン処理
# ==========================================
def main():
    st.set_page_config(page_title="家系図PDFジェネレーター", layout="wide")
    st.title("家系図PDFジェネレーター")
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. データ入力")
        default_input = """本人 = 山田光
母 = 母
父 = 父
母の母 = 母の母
母の父 = 母の父
父の母 = 父の母
父の父 = 父の父
母の母の母 = 母の母の母
母の母の父 = 母の母の父
母の父の母 = 母の父の母
母の父の父 = 母の父の父
父の母の母 = 父の母の母
父の母の父 = 父の母の父
父の父の母 = 父の父の母
父の父の父 = 父の父の父

◎守護
・父の父の父
・父の父の父の父
・父の父の母の母

◎優先順位
・母の母の母の母
・父の母の父
・父の父の母の母

◎契約・コード
・自己犠牲
・役割
・感情未消化"""
        input_text = st.text_area("入力欄", value=default_input, height=500)

    with col2:
        st.subheader("2. 生成・ダウンロード")
        st.write("左側のデータを編集して「PDF生成」を押してください。")
        
        if st.button("PDFを生成する", type="primary"):
            if not input_text:
                st.error("入力データが空です。")
            else:
                try:
                    # 解析
                    client_data = parse_text_data(input_text)
                    
                    # クライアント名（ファイル名用）の取得をより堅牢に
                    # 'self' が無ければ '本人' を探し、それでもなければ 'Client'
                    client_name = client_data['names'].get('self', 
                                  client_data['names'].get('本人', 'Client'))
                    
                    # メモリ上にPDF作成
                    buffer = io.BytesIO()
                    gen = GenealogyPDF(client_data, buffer)
                    gen.create_tree_page()
                    gen.create_quad_pages()
                    gen.create_summary_page()
                    gen.save()
                    
                    buffer.seek(0)
                    
                    st.success(f"「{client_name}」様のPDF生成に成功しました！")
                    
                    # ダウンロードボタン
                    file_name = f"{client_name}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
                    st.download_button(
                        label="PDFをダウンロード",
                        data=buffer,
                        file_name=file_name,
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
                    if "IPAMincho" in str(e) or "Can't find font" in str(e):
                        st.warning("⚠️ ヒント: フォントファイル(ipam.ttf)が同じフォルダに存在するか確認してください。")

if __name__ == "__main__":
    main()