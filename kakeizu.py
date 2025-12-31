import streamlit as st
import os
import datetime
import io
import requests
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# ==========================================
# 1. 設定・フォント準備 (修正箇所)
# ==========================================
FONT_URL = "https://github.com/ixkaito/IPAexfont/raw/master/ipaexm.ttf"
FONT_FILE = "ipaexm.ttf"
FONT_NAME = "IPAexMincho"

# Streamlitのキャッシュ機能を使って、再起動してもフォント設定を保持・確実化します
@st.cache_resource
def setup_font():
    """フォントファイルをダウンロードして登録する"""
    # 1. ファイルがなければダウンロード
    if not os.path.exists(FONT_FILE):
        try:
            response = requests.get(FONT_URL)
            response.raise_for_status() # 通信エラーがあればここで例外発生
            with open(FONT_FILE, "wb") as f:
                f.write(response.content)
        except Exception as e:
            st.error(f"フォントのダウンロードに失敗しました: {e}")
            return False

    # 2. フォントをReportLabに登録
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
        return True
    except Exception as e:
        # すでに登録済みの場合のエラーは無視、それ以外は表示
        if "is already registered" not in str(e):
            st.error(f"フォントの登録に失敗しました: {e}")
            return False
        return True

# 設定定数
FONT_SIZE_TREE = 7.5
FONT_SIZE_QUAD_NAME = 36
FONT_SIZE_BG = 10 

# ==========================================
# 2. デフォルト入力データ
# ==========================================
client_txt_content = """
本人 = 山田光
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
母の母の母の母 = 母の母の母の母
母の母の母の父 = 母の母の母の父
母の母の父の母 = 母の母の父の母
母の母の父の父 = 母の母の父の父
母の父の母の母 = 母の父の母の母
母の父の母の父 = 母の父の母の父
母の父の父の母 = 母の父の父の母
母の父の父の父 = 母の父の父の父
父の母の母の母 = 父の母の母の母
父の母の母の父 = 父の母の母の父
父の母の父の母 = 父の母の父の母
父の母の父の父 = 父の母の父の父
父の父の母の母 = 父の父の母の母
父の父の母の父 = 父の父の母の父
父の父の父の母 = 父の父の父の母
父の父の父の父 = 父の父の父の父

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
・感情未消化
"""

# ==========================================
# 3. 定義データ
# ==========================================
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

# ==========================================
# 4. PDF生成クラス (Streamlit向け)
# ==========================================
class GenealogyPDF:
    def __init__(self, client_data, buffer):
        self.c = canvas.Canvas(buffer, pagesize=landscape(A4))
        self.width, self.height = landscape(A4)
        self.data = client_data
        # コンストラクタでのフォント登録処理は削除し、setup_font()に一任

    def check_attributes(self, label):
        """属性判定（完全一致ロジック）"""
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
        box_h = 24 * mm # 短縮版
        box_h_half = box_h / 2
        
        # 凡例
        self.c.saveState()
        self.c.setFont(FONT_NAME, 10)
        self.c.setFillColor(colors.black)
        legend_x = 20 * mm
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
        name = self.data['names'].get(key, RELATION_MAP[key]['label'])
        label = RELATION_MAP[key]['label']
        gender = RELATION_MAP[key].get('gender', 'm')
        if key == 'self': name = self.data['names'].get('本人', name)
        
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
        self.draw_vertical_text(name if name else label, x, y, FONT_SIZE_TREE, is_priority, is_guardian)

    def create_quad_pages(self):
        targets = []
        targets.append(('self', self.data['names'].get('本人', '本人')))
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
        self.c.setLineWidth(2.0) 
        self.c.setStrokeColor(colors.black)
        self.c.setDash([]) 
        self.c.line(cx, 0, cx, h)
        self.c.line(0, cy, w, cy)
        self.c.restoreState()
        
        rects = [(0, cy, cx, cy), (cx, cy, cx, cy), (0, 0, cx, cy), (cx, 0, cx, cy)]
        
        for idx, (key, name) in enumerate(people):
            if idx >= 4: break
            rx, ry, rw, rh = rects[idx]
            
            # 背景転写
            self.c.saveState()
            path = self.c.beginPath()
            path.rect(rx, ry, rw, rh)
            self.c.clipPath(path, stroke=0)
            self.c.setFillColor(colors.white)
            self.c.setStrokeColor(colors.white)
            bg_t = self.c.beginText()
            bg_t.setFont(FONT_NAME, FONT_SIZE_BG)
            bg_t.setFillColor(colors.white) 
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

        self.c.showPage()

    def create_summary_page(self):
        self.c.setFont(FONT_NAME, 14)
        x_base = 30 * mm
        y = self.height - 40 * mm
        self.c.drawString(x_base, y, "■ 記録・解析")
        y -= 15 * mm
        
        def draw_section_multicolumn(title, data_list, start_y):
            t_obj = self.c.beginText()
            t_obj.setFont(FONT_NAME, 12)
            t_obj.setTextOrigin(x_base, start_y)
            t_obj.textOut(title)
            self.c.drawText(t_obj)
            
            item_y_start = start_y - 8 * mm
            line_height = 6 * mm
            col_width = 60 * mm
            limit_per_col = 12
            
            current_x = x_base + 10 * mm
            current_y = item_y_start
            
            if not data_list:
                return start_y - 15 * mm

            for i, item in enumerate(data_list):
                if i > 0 and i % limit_per_col == 0:
                    current_x += col_width
                    current_y = item_y_start
                
                t_obj = self.c.beginText()
                t_obj.setFont(FONT_NAME, 10)
                t_obj.setTextOrigin(current_x, current_y)
                t_obj.textOut(f"・{item}")
                self.c.drawText(t_obj)
                current_y -= line_height
            
            rows_used = min(len(data_list), limit_per_col)
            section_height = (rows_used * line_height) + 8 * mm
            return start_y - section_height - 10 * mm

        y = draw_section_multicolumn("◎ 守護", self.data['guardians'], y)
        y = draw_section_multicolumn("◎ 癒す優先順位", self.data['priorities'], y)
        y = draw_section_multicolumn("◎ 契約・コード", self.data['contracts'], y)
        self.c.showPage()

    def save(self):
        self.c.save()

# ==========================================
# 5. Streamlit UI
# ==========================================
def parse_client_data(text_content):
    """テキストボックスの内容をパースする関数"""
    data = {'names': {}, 'guardians': [], 'priorities': [], 'contracts': []}
    current_section = 'names'
    label_map = {v['label']: k for k, v in RELATION_MAP.items()}
    label_map['本人'] = 'self' 
    
    # 行ごとに処理
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
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
            if '=' in line:
                parts = line.split('=', 1)
                key_str = parts[0].strip()
                val = parts[1].strip()
                sys_key = label_map.get(key_str)
                if key_str in RELATION_MAP: data['names'][key_str] = val
                elif sys_key: data['names'][sys_key] = val
                else: data['names'][key_str] = val
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

# Streamlitメイン処理
def main():
    st.title("家系図PDFジェネレーター (Final v8.2)")
    
    # フォント確認・ダウンロード
    if not setup_font():
        return

    # 入力エリア
    user_input = st.text_area("クライアント情報入力", value=client_txt_content, height=400)
    
    if st.button("PDFを生成"):
        try:
            # データのパース
            client_data = parse_client_data(user_input)
            client_name = client_data['names'].get('self', 'Client')
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            filename = f"{client_name}_{date_str}.pdf"
            
            # バッファにPDF生成
            buffer = io.BytesIO()
            gen = GenealogyPDF(client_data, buffer)
            gen.create_tree_page()
            gen.create_quad_pages()
            gen.create_summary_page()
            gen.save()
            buffer.seek(0)
            
            # ダウンロードボタン表示
            st.success(f"PDF生成完了: {filename}")
            st.download_button(
                label="PDFをダウンロード",
                data=buffer,
                file_name=filename,
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()