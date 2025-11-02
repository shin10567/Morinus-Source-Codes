# -*- coding: utf-8 -*-
import wx
import math
import common
import commonwnd
import Image, ImageDraw, ImageFont
import mtexts

# -------------------------- 계산 유틸 --------------------------
def _norm360(x):
    x = math.fmod(float(x), 360.0)
    return x + 360.0 if x < 0 else x

def _build_lon(sign_idx, d, m, s):
    return float(sign_idx) * 30.0 + float(d) + float(m) / 60.0 + float(s) / 3600.0

def _lon_to_sign_dms(lon):
    """0<=lon<360 -> (sign_idx, deg(0..29), min(0..59), sec(0..59))"""
    L = _norm360(lon)
    si = int(L // 30.0)
    rest = L - si * 30.0
    d = int(rest // 1)
    mF = (rest - d) * 60.0
    m = int(mF // 1)
    s = int(round((mF - m) * 60.0))
    if s >= 60:
        s = 0; m += 1
    if m >= 60:
        m = 0; d += 1
    if d >= 30:
        d = 0; si = (si + 1) % 12
    return si, d, m, s

def _dodeka_from_sign_dms(sign_idx, d, m, s):
    """λ' = sign_start + 12 * (λ - sign_start)"""
    sign_start = float(sign_idx) * 30.0
    lam = _build_lon(sign_idx, d, m, s)
    out = sign_start + 12.0 * (lam - sign_start)
    return _norm360(out)

# -------------------------- 본문(표) --------------------------
class DodecaCalcWnd(commonwnd.CommonWnd):
    """
    CommonWnd 기반 2열 표
      헤더: Longitude | Dodecatemorion
      내용: [입력 λ] | [도데카테모리온 λ']
    숫자는 텍스트 폰트, 사인 글리프는 Morinus.ttf + options.signs(Signs1/Signs2) 사용
    """
    def __init__(self, parent, chrt, options, mainfr, id = -1, size = wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, chrt, options, id, size)
        self.parent = parent
        self.options = options
        self.mainfr = mainfr
        self.bw = self.options.bw

        # 테이블/폰트 규격: Positionswnd / DodecatemoriaWnd 패턴 준용
        self.FONT_SIZE = int(21 * self.options.tablesize)

        self.SPACE = self.FONT_SIZE / 2
        self.LINE_HEIGHT = (self.SPACE + self.FONT_SIZE + self.SPACE)
        self.SMALL_CELL_WIDTH = 0
        self.CELL_WIDTH = 8 * self.FONT_SIZE
        self.TITLE_HEIGHT = self.LINE_HEIGHT
        self.COLUMN_NUM = 2

        self.LINE_NUM = 1

        self.TABLE_HEIGHT = (self.TITLE_HEIGHT + self.LINE_NUM * (self.LINE_HEIGHT))
        self.TABLE_WIDTH = (self.COLUMN_NUM * (self.CELL_WIDTH))

        self.WIDTH = int(commonwnd.CommonWnd.BORDER + self.TABLE_WIDTH + commonwnd.CommonWnd.BORDER)
        self.HEIGHT = int(commonwnd.CommonWnd.BORDER + self.TABLE_HEIGHT + commonwnd.CommonWnd.BORDER)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        # 폰트
        self.fntMorinus = ImageFont.truetype(common.common.symbols, int(self.FONT_SIZE))
        self.fntText    = ImageFont.truetype(common.common.abc,     int(self.FONT_SIZE))
        # options.signs 에 따라 Morinus 글리프 세트 선택
        self.signs = common.common.Signs1
        if not self.options.signs:
            self.signs = common.common.Signs2
        self.deg_symbol = u'\u00b0'  # Positionswnd 규칙: '°' + ' ' + "'" + '"'

        # 입력 기본값: 양자리 0°0′0″
        self.in_sign = 0; self.in_d = 0; self.in_m = 0; self.in_s = 0

        # 최초 렌더
        self.drawBkg()

    def getExt(self):
        # 저장시 파일명 꼬리표 (기존 키 재활용)
        return mtexts.txts.get('Dodecatemorion', 'Dodecatemorion')

    # 외부에서 입력 갱신
    def set_input(self, sign_idx, d, m, s):
        self.in_sign = int(sign_idx)
        self.in_d = int(d); self.in_m = int(m); self.in_s = int(s)
        self.drawBkg()
        self.Refresh(False)

    def _fmt_cell(self, draw, x, y, cell_w, lon):
        """Positionswnd 포맷: 숫자 텍스트 + 공백 + 사인 글리프(모리누스 폰트)"""
        si, d, m, s = _lon_to_sign_dms(lon)
        wsp, hsp = draw.textsize(' ', self.fntText)
        wsg, hsg = draw.textsize(self.signs[si], self.fntMorinus)
        txt = (str(d)).rjust(2) + self.deg_symbol + (str(m)).zfill(2) + "'" + (str(s)).zfill(2) + '"'
        w, h = draw.textsize(txt, self.fntText)
        offset = (cell_w - (w + wsp + wsg)) / 2
        # 숫자
        draw.text((x + offset, y + (self.LINE_HEIGHT - h)/2), txt, fill=self._txtclr, font=self.fntText)
        # 글리프
        draw.text((x + offset + w + wsp, y + (self.LINE_HEIGHT - hsg)/2), self.signs[si], fill=self._txtclr, font=self.fntMorinus)

    def drawBkg(self):
        # 색상
        self._bkgclr = (255, 255, 255) if self.bw else self.options.clrbackground
        tableclr = (0, 0, 0) if self.bw else self.options.clrtable
        self._txtclr = (0, 0, 0) if self.bw else self.options.clrtexts
        self.SetBackgroundColour(self._bkgclr)

        # 캔버스
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self._bkgclr)
        draw = ImageDraw.Draw(img)

        BOR = commonwnd.CommonWnd.BORDER

        # 타이틀 박스(외곽선 없이 채우기만)
        draw.rectangle(((BOR, BOR),
                        (BOR + self.TABLE_WIDTH, BOR + self.TITLE_HEIGHT)),
                    fill=self._bkgclr)

        # 타이틀 텍스트
        col1 = mtexts.txts.get('Longitude', 'Longitude')
        col2 = mtexts.txts.get('Dodecatemorion', 'Dodecatemorion')
        # 헤더 텍스트 중앙 배치
        w1, h1 = draw.textsize(col1, self.fntText)
        w2, h2 = draw.textsize(col2, self.fntText)

        x1 = BOR + (self.CELL_WIDTH - w1) / 2
        x2 = BOR + self.CELL_WIDTH + (self.CELL_WIDTH - w2) / 2

        y_hdr = BOR + (self.TITLE_HEIGHT - h1) / 2
        draw.text((x1, y_hdr), col1, fill=self._txtclr, font=self.fntText)
        draw.text((x2, y_hdr), col2, fill=self._txtclr, font=self.fntText)

        # 표 외곽선 + 세로선
        top_y = BOR
        left_x = BOR
        right_x = BOR + self.TABLE_WIDTH
        bottom_y = BOR + self.TABLE_HEIGHT
        # 외곽
        draw.rectangle(((left_x, top_y), (right_x, bottom_y)), outline=tableclr)
        # 세로선들(헤더 영역 제외)
        # SMALL_CELL_WIDTH == 0이면 왼쪽 외곽선과 중복이므로 첫 줄은 스킵
        if self.SMALL_CELL_WIDTH > 0:
            draw.line((left_x + self.SMALL_CELL_WIDTH,
                    top_y + self.TITLE_HEIGHT,
                    left_x + self.SMALL_CELL_WIDTH,
                    bottom_y), fill=tableclr)

        # 컬럼 사이 구분선은 헤더 아래부터 시작 (헤더에는 보이지 않음)
        draw.line((left_x + self.SMALL_CELL_WIDTH + self.CELL_WIDTH,
                top_y + self.TITLE_HEIGHT,
                left_x + self.SMALL_CELL_WIDTH + self.CELL_WIDTH,
                bottom_y), fill=tableclr)

        # 헤더 하단 가로선
        draw.line((left_x, top_y + self.TITLE_HEIGHT, right_x, top_y + self.TITLE_HEIGHT), fill=tableclr)

        # 값 1행
        y_row = top_y + self.TITLE_HEIGHT

        # 왼쪽(입력 경도)
        L_in = _build_lon(self.in_sign, self.in_d, self.in_m, self.in_s)
        self._fmt_cell(draw, BOR, y_row, self.CELL_WIDTH, L_in)
        # 오른쪽(도데카테모리온)
        L_out = _dodeka_from_sign_dms(self.in_sign, self.in_d, self.in_m, self.in_s)
        self._fmt_cell(draw, BOR + self.CELL_WIDTH, y_row, self.CELL_WIDTH, L_out)

        # wx.Bitmap 변환
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)

    # -------------------------- 프레임 --------------------------
class DodecaCalcFrame(wx.Frame):
    def __init__(self, parent, title, chrt, options):
        wx.Frame.__init__(self, parent, -1, title)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.options = options
        self._parent_main = parent

        pnl = wx.Panel(self)
        # 상단바
        bar = wx.Panel(pnl)
        sep = wx.StaticLine(pnl, style=wx.LI_HORIZONTAL)
        sizer_bar = wx.BoxSizer(wx.HORIZONTAL)

        # ───────────────── Circumambulation과 동일한 ToolBar 방식 ─────────────────
        self.tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.tb.SetToolBitmapSize((24, 24))
        try:
            # 왼쪽 마진 12px (Circum과 동일)
            self.tb.SetMargins(12, 0)
        except Exception:
            pass

        def _tb_spacer(w):
            st = wx.StaticText(self.tb, -1, u'')
            st.SetMinSize((w, -1))
            self.tb.AddControl(st)
        def _tb_punct(ch):
            st = wx.StaticText(self.tb, -1, ch)
            # 너무 붙지 않도록 최소 폭만 아주 살짝
            st.SetMinSize((8, -1))
            self.tb.AddControl(st)

        TOPBAR_H = 30  # Circum의 버튼 높이와 동일 기준

        # 라벨들
        st_lon  = wx.StaticText(self.tb, -1, mtexts.txts.get('Longitude', 'Longitude') + ':')
        st_sign = wx.StaticText(self.tb, -1, mtexts.txts.get('TopicalSign', 'Sign') + ': ')
        st_deg  = wx.StaticText(self.tb, -1, mtexts.txts.get('Deg', 'Degree') + ': ')
        st_min  = wx.StaticText(self.tb, -1, mtexts.txts.get('Min', 'Minute') + ': ')
        st_sec  = wx.StaticText(self.tb, -1, mtexts.txts.get('Sec', 'Second') + ': ')

        # 사인 콤보/스핀 (툴바에 직접 AddControl)
        sign_labels = [mtexts.txts.get(n, n) for n in
                    ('Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces')]
        self.ch_sign = wx.Choice(self.tb, -1, choices=sign_labels)
        self.ch_sign.SetSelection(0)

        self.sp_deg = wx.SpinCtrl(self.tb, -1, min=0, max=29, initial=0)
        self.sp_deg.SetHelpText(mtexts.txts.get('HelpDegree', u'Must be between 0 and 29'))

        self.sp_min = wx.SpinCtrl(self.tb, -1, min=0, max=59, initial=0)
        self.sp_min.SetHelpText(mtexts.txts.get('HelpMin', u'Must be between 0 and 59'))

        self.sp_sec = wx.SpinCtrl(self.tb, -1, min=0, max=59, initial=0)
        self.sp_sec.SetHelpText(mtexts.txts.get('HelpMin', u'Must be between 0 and 59'))

        btn_calc = wx.Button(self.tb, -1, mtexts.txts.get('Calculate', 'Calculate'), size=(-1, TOPBAR_H))

        # 폭 축소(가로만): 기존 스펙 유지 + 높이는 OS 기본값으로 둬서 중앙 정렬 자연 발생
        # SpinCtrl 폭 강제: BestSize를 누르기 위해 Min/Max/InitialSize 모두 설정
        def _fix_width(ctrl, factor=0.35):  
            bs = ctrl.GetBestSize()
            w  = max(30, int(bs.width * factor))
            h  = bs.height
            ctrl.SetMinSize((w, h))
            ctrl.SetInitialSize((w, h))
            # 최대폭도 고정해 툴바 레이아웃 시 다시 늘리지 못하게
            try:
                ctrl.SetSizeHints(w, -1, w, -1)
            except Exception:
                pass
            ctrl.InvalidateBestSize()
            return w

        # 원하는 폭 계산(Realize 전에 1차 설정)
        _w_specs = []
        for sp in (self.sp_deg, self.sp_min, self.sp_sec):
            _w_specs.append((sp, _fix_width(sp)))

        _tb_punct('      ')  # 프레임 좌측 경계 여백 (툴바 맨 앞에 둬야 유효)
        self.tb.AddControl(st_lon); _tb_punct('   '); _tb_spacer(10)
        self.tb.AddControl(st_sign) 
        self.tb.AddControl(self.ch_sign); _tb_punct('   '); _tb_spacer(10)
        self.tb.AddControl(st_deg) 
        self.tb.AddControl(self.sp_deg); _tb_punct('   '); _tb_spacer(10)
        self.tb.AddControl(st_min)
        self.tb.AddControl(self.sp_min); _tb_punct('   '); _tb_spacer(10)
        self.tb.AddControl(st_sec)
        self.tb.AddControl(self.sp_sec); _tb_punct('   '); _tb_spacer(10)
        self.tb.AddControl(btn_calc)

        self.tb.Realize()
        # ──────────────────────────────────────────────────────────────

        # 본문
        self.body = DodecaCalcWnd(pnl, chrt, options, parent)
        self.body.mainfr = parent

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self.body, 1, wx.EXPAND)
        pnl.SetSizer(root)

        # 이벤트 (툴바 컨트롤은 프레임에서 ID로 바인딩하는 편이 안전)
        self.Bind(wx.EVT_BUTTON, self._on_calc, id=btn_calc.GetId())

        self.SetMinSize((200, 200))
        self.Layout()

        tb_h = max(30, self.GetToolBar().GetSize().height)
        client_w = self.body.WIDTH + 12
        client_h = self.body.HEIGHT + tb_h + 12
        self.SetClientSize((max(680, client_w), client_h))

    def _on_calc(self, evt):
        sidx = self.ch_sign.GetSelection()
        d = self.sp_deg.GetValue()
        m = self.sp_min.GetValue()
        s = self.sp_sec.GetValue()
        self.body.set_input(sidx, d, m, s)
