# -*- coding: utf-8 -*-
# ZR: CommonWnd + PIL (fixedstars 스타일)
# - 상단 info: "Start sign: <기호>" (세로줄 없음, 클릭하면 Start 팝업)
# - 본문 표: Level | Sign | Start | Length (중앙 정렬)
# - L1은 배경 동일(하이라이트 배경 없음), 글자만 Bold+약간 크게
# - L2 셀 클릭 → L3/L4 팝업(표 하나, 저장 가능, 메인과 동일 톤)
import wx, datetime
import Image, ImageDraw, ImageFont
import common, commonwnd
import zodiacalreleasing as zr
import mtexts
# ───────────────────────────── ZR 메인 Wnd ─────────────────────────────
class ZRWnd(commonwnd.CommonWnd):
    def __init__(self, parent, horoscope, options, mainfr, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, horoscope, options, id, size)
        self.mainfr  = mainfr
        self.chart   = horoscope
        self.options = options
        self.bw      = self.options.bw

        # [폰트/사이즈] fixedstars 규칙
        self.FONT_SIZE   = int(21 * self.options.tablesize)
        self.SPACE       = self.FONT_SIZE / 2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE
        self.HEAD_H      = self.LINE_HEIGHT
        self.INFO_H      = self.LINE_HEIGHT

        # [폰트] 텍스트/심볼 모두 Morinus TTF 사용 (antisciawnd.py와 동일)
        self.fntText   = ImageFont.truetype(common.common.abc,      self.FONT_SIZE)
        self.fntTextBold = ImageFont.truetype(common.common.abc_bold, self.FONT_SIZE)
        self.fntMor    = ImageFont.truetype(common.common.symbols,  self.FONT_SIZE)

        # [사인 글리프 테이블] antisciawnd.py와 동일 규칙
        #   기본은 Signs1, 옵션에서 Signs 비활성 시 Signs2 사용
        self.signs = common.common.Signs1
        try:
            if not self.options.signs:
                self.signs = common.common.Signs2
        except:
            pass  # 옵션 없으면 기본 Signs1

        # [컬럼 폭] 요청대로 Level/Length를 '조끔' 넓힘
        self.W_LEVEL = int(2.8 * self.FONT_SIZE)   # ← 기존 2.2에서 확장
        self.W_SIGN  = int(3.0 * self.FONT_SIZE)   # 기호 칸 (좁게 유지)
        self.W_START = int(7.0 * self.FONT_SIZE)
        self.W_LEN   = int(7.0 * self.FONT_SIZE)   # ← 기존 6.0에서 확장
        self.COL_W   = (self.W_LEVEL, self.W_SIGN, self.W_START, self.W_LEN)
        self.TITLE_W = sum(self.COL_W)

        # 데이터
        self.rows = []      # [{level:1/2, sign:0..11, start:dt, end:dt, ...}, ...]
        self.row_lv = []    # [1 or 2] 히트테스트용
        self.start_sign_idx = 0

        # 마우스
        self.Bind(wx.EVT_LEFT_DOWN, self._onLeftDown)
        self.Bind(wx.EVT_MOTION,    self._onMotion)

        # 초기 크기
        self._recalc_sizes(0)
        self.drawBkg()

    def getExt(self):
        return u"ZR.bmp"

    # 외부 인터페이스
    def set_start_sign(self, idx):
        self.start_sign_idx = int(idx)

    def compute_and_draw(self):
        self.rows = zr.build_main(self._chart_dt(), self.start_sign_idx, years_horizon=120)
        self.row_lv = [int(r.get('level', 2)) for r in self.rows]
        self._recalc_sizes(len(self.rows))
        self.drawBkg()

    def get_sign_names_for_popup(self):
        # Start 팝업에 보일 이름(텍스트). 없어도 동작하게 안전 폴백.
        try:
            import mtexts
            return [mtexts.txts['zodiac'][i] for i in range(12)]
        except:
            return [[mtexts.txts["Aries"], mtexts.txts["Taurus"], mtexts.txts["Gemini"], mtexts.txts["Cancer"], mtexts.txts["Leo"], mtexts.txts["Virgo"],
                          mtexts.txts["Libra"], mtexts.txts["Scorpio"], mtexts.txts["Sagittarius"], mtexts.txts["Capricornus"], mtexts.txts["Aquarius"], mtexts.txts["Pisces"]]]

    # 내부
    def _chart_dt(self):
        try:
            return self.chart.time.getDatetime()
        except:
            t = self.chart.time
            return datetime.datetime(int(t.year), int(t.month), int(t.day),
                                     int(t.hour), int(t.minute), int(getattr(t,'second',0)))

    def _recalc_sizes(self, nlines):
        BOR = commonwnd.CommonWnd.BORDER
        self.TABLE_H = int(self.INFO_H + self.HEAD_H + max(1, nlines)*self.LINE_HEIGHT)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

    # ── 렌더 ──
    def drawBkg(self):
        BOR = commonwnd.CommonWnd.BORDER
        bkg = (255,255,255) if self.bw else self.options.clrbackground
        tbl = (0,0,0)       if self.bw else self.options.clrtable
        txt = (0,0,0)       if self.bw else self.options.clrtexts
        self.SetBackgroundColour(bkg)

        img  = Image.new('RGB', (self.WIDTH, self.HEIGHT), bkg)
        draw = ImageDraw.Draw(img)

        # [A] info (세로줄 없음): "Start sign: <기호>" → <기호> 클릭으로 팝업
        label  = mtexts.txts["StartSign"]
        glyph  = self.signs[self.start_sign_idx]  # ← antisciawnd와 같은 소스
        lw, lh = draw.textsize(label, self.fntText)
        gw, gh = draw.textsize(glyph, self.fntMor)
        gap    = int(self.FONT_SIZE*0.5)
        base_x = BOR + (self.TITLE_W - (lw+gap+gw))/2
        y_info = BOR + (self.INFO_H - lh)/2
        draw.text((base_x, y_info), label, fill=txt, font=self.fntText)
        sign_x = base_x + lw + gap
        sign_y = BOR + (self.INFO_H - gh)/2
        draw.text((sign_x, sign_y), glyph, fill=txt, font=self.fntMor)
        # 클릭 영역 저장
        self._bbox_start = (sign_x, sign_y, sign_x+gw, sign_y+gh)

        # [B] 헤더
        head_y = BOR + self.INFO_H
        draw.rectangle(((BOR, head_y), (BOR+self.TITLE_W, head_y+self.HEAD_H)),
                       fill=bkg)
        heads = (u"Lv.", mtexts.txts["Signs"], mtexts.txts["Start"], mtexts.txts["Length"])
        x = BOR
        for i,h in enumerate(heads):
            tw, th = draw.textsize(h, self.fntText)
            draw.text((x + (self.COL_W[i]-tw)/2, head_y + (self.HEAD_H-th)/2), h, fill=txt, font=self.fntText)
            x += self.COL_W[i]
        # 헤더 하단
        x0 = BOR; y0 = head_y + self.HEAD_H
        draw.line((x0, y0, x0 + self.TITLE_W, y0), fill=tbl)

        # [C] 세로선 
        top = y0
        bot = BOR + self.TABLE_H
        xv  = x0
        draw.line((xv, top, xv, bot), fill=tbl)
        for w in self.COL_W:
            xv += w
            draw.line((xv, top, xv, bot), fill=tbl)

        # [D] 데이터
        y = y0
        for r in self.rows:
            lvl  = int(r.get('level',2))
            sign = int(r['sign'])
            start_s = zr.fmt_date(r['start'])
            len_s   = zr.fmt_length(r)
            cells = (u"L%d"%lvl, self.signs[sign], start_s, len_s)

            # L1 강조: 배경은 동일(흰칸 금지), 글자만 Bold + 약간 크게
            isL1  = (lvl == 1)
            fTxt  = self.fntText
            fTxtB = self.fntTextBold
            fZod  = self.fntMor
            if isL1:
                def draw_L1(val, xx, ww, yy):
                    # 사인 칼럼(W_SIGN)은 morinus 기호 → 두 번 찍기(가짜 Bold)
                    if ww == self.W_SIGN:
                        tw, th = draw.textsize(val, fZod)
                        cx = xx + (ww - tw)/2; cy = yy + (self.LINE_HEIGHT - th)/2
                        draw.text((cx,   cy), val, fill=txt, font=fZod)
                        draw.text((cx-1, cy), val, fill=txt, font=fZod)
                    else:
                        # 나머지는 진짜 Bold 폰트로 한 번만
                        tw, th = draw.textsize(val, fTxtB)
                        cx = xx + (ww - tw)/2; cy = yy + (self.LINE_HEIGHT - th)/2
                        draw.text((cx, cy), val, fill=txt, font=fTxtB)

                xx = x0
                vals = (cells[0], cells[1], cells[2], cells[3])
                wss  = (self.W_LEVEL, self.W_SIGN, self.W_START, self.W_LEN)
                for vi in range(4):
                    draw_L1(vals[vi], xx, wss[vi], y)
                    xx += wss[vi]
            else:
                # 일반 행: 기존 그대로(기호는 fZod, 텍스트는 fTxt)
                xx = x0
                for ci,w in enumerate(self.COL_W):
                    val = cells[ci]
                    fnt = fZod if ci==1 else fTxt
                    tw, th = draw.textsize(val, fnt)
                    draw.text((xx + (w - tw)/2, y + (self.LINE_HEIGHT - th)/2), val, fill=txt, font=fnt)
                    xx += w


            # 행 하단선
            draw.line((x0, y + self.LINE_HEIGHT, x0 + self.TITLE_W, y + self.LINE_HEIGHT), fill=tbl)
            y += self.LINE_HEIGHT

        # [E] 외곽
        draw.rectangle(((BOR, BOR), (BOR+self.TITLE_W, BOR+self.TABLE_H)), outline=tbl)

        # wx 비트맵
        wxImg = wx.Image(img.size[0], img.size[1]); wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        self.Refresh()

    # ── 마우스 ──
    def _calc_unscrolled(self, pt):
        try:  return self.CalcUnscrolledPosition(pt[0], pt[1])
        except:
            vx,vy = self.GetViewStart(); px,py = self.GetScrollPixelsPerUnit()
            return (pt[0]+vx*px, pt[1]+vy*py)

    def _onLeftDown(self, evt):
        #ux, uy = self._calc_unscrolled(evt.GetPositionTuple())
        ux, uy = self._calc_unscrolled(tuple(evt.GetPosition()))
        # Start sign 클릭?
        if hasattr(self, "_bbox_start"):
            x1,y1,x2,y2 = self._bbox_start
            if x1 <= ux <= x2 and y1 <= uy <= y2:
                dlg = ZRStartDlg(self, self.get_sign_names_for_popup())
                dlg.CentreOnScreen()
                if dlg.ShowModal()==wx.ID_OK:
                    self.start_sign_idx = dlg.get_sign_index()
                    self.compute_and_draw()
                dlg.Destroy()
                return

        # 본문 클릭 → L2만 팝업
        BOR = commonwnd.CommonWnd.BORDER
        x = ux - BOR; y = uy - BOR
        if x < 0 or x > self.TITLE_W or y < self.INFO_H + self.HEAD_H:
            return
        row = int((y - (self.INFO_H + self.HEAD_H)) // self.LINE_HEIGHT)
        if row < 0 or row >= len(self.row_lv): return
        l2row = self.rows[row]
        # 부모는 반드시 프레임(self.mainfr)로 지정 (부모 닫을 때 함께 정리)
        dlg = ZRDrillDlg(self.mainfr, l2row, self.signs, self.fntText, self.fntMor, mainfr=self.mainfr)

        # 프레임에 등록(부모 닫힐 때 함께 정리)
        if hasattr(self.mainfr, "_register_drill"):
            self.mainfr._register_drill(dlg)

        # 모델리스로 띄우고, 닫기(X) 시 파괴되게 연결
        dlg.Bind(wx.EVT_CLOSE, lambda e: dlg.Destroy())
        dlg.Show()          # ← 모델리스
        dlg.Raise()
        try:
            dlg.SetFocus()
        except Exception:
            pass

    def _onMotion(self, evt):
        #ux, uy = tuple(self._calc_unscrolled(evt.GetPositionTuple()))
        ux, uy = tuple(self._calc_unscrolled(evt.GetPosition()))
        hand = False
        if hasattr(self, "_bbox_start"):
            x1,y1,x2,y2 = self._bbox_start
            if x1 <= ux <= x2 and y1 <= uy <= y2:
                hand = True
        if not hand:
            BOR = commonwnd.CommonWnd.BORDER
            x = ux - BOR; y = uy - BOR
            if 0 <= x <= self.TITLE_W and y >= self.INFO_H + self.HEAD_H:
                row = int((y - (self.INFO_H + self.HEAD_H)) // self.LINE_HEIGHT)
                if 0 <= row < len(self.row_lv) and self.row_lv[row]==2:
                    hand = True

        self.SetCursor(wx.Cursor(wx.CURSOR_HAND) if hand else wx.NullCursor)
        evt.Skip()

# ───────────────────────────── Start 팝업 ─────────────────────────────
class ZRStartDlg(wx.Dialog):
    def __init__(self, parent, sign_names):
        wx.Dialog.__init__(self, parent, title= mtexts.txts["StartSign"])
        v = wx.BoxSizer(wx.VERTICAL)
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, mtexts.txts["StartSign"]), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.cmb = wx.ComboBox(self, -1, choices=sign_names, style=wx.CB_READONLY)
        self.cmb.SetSelection(0)
        row.Add(self.cmb, 0)
        v.Add(row, 0, wx.ALL, 10)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(wx.Button(self, wx.ID_OK, mtexts.txts["Compute"]))
        btns.AddButton(wx.Button(self, wx.ID_CANCEL, mtexts.txts["Cancel"])) 
        btns.Realize()
        v.Add(btns, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
        self.SetSizerAndFit(v)

    def get_sign_index(self):
        return int(self.cmb.GetSelection())

# ───────────────────────────── L3/L4 팝업 ─────────────────────────────
class ZRDrillDlg(wx.Dialog):
    """선택한 L2의 L3/L4 표를 그리는 팝업(저장 가능)."""
    def __init__(self, parent, l2row, signs, fntText, fntMor, mainfr):
        wx.Dialog.__init__(self, parent, title=mtexts.txts['ZodiacalReleasing'],
                        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        # 메인 패널(그림 렌더; CommonWnd 상속)
        self.panel = ZRDrillWnd(self, l2row, signs, fntText, fntMor, mainfr=mainfr)

        # ⬇️ OK 버튼/버튼영역 완전히 제거: 패널만 넣고 끝
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self.panel, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizerAndFit(s)

        # 너가 요청한 작은 가로폭 + 리사이즈 가능/최소 크기
        self.SetInitialSize((400, 560))
        self.SetMinSize((200, 200))
        pos = self.GetPosition()
        self.SetPosition((pos[0] +300, pos[1]-75))

    def _onChar(self, evt):
        code = evt.GetKeyCode()
        if code == wx.WXK_ESCAPE:
            self.Close()
            return
        evt.Skip()

class ZRDrillWnd(commonwnd.CommonWnd):
    def __init__(self, parent, l2row, signs, fntText, fntMor, mainfr, id=-1, size=wx.DefaultSize):

        commonwnd.CommonWnd.__init__(self, parent, mainfr.horoscope, mainfr.options, id, size)
        self.mainfr  = mainfr
        self.chart   = mainfr.horoscope
        self.options = mainfr.options
        self.bw      = self.options.bw

        # 폰트/사인
        self.fntText = fntText
        self.fntMor  = fntMor
        self.signs   = signs
        try:
            # 메인 폰트 크기와 동일 크기의 Bold 로드
            self.fntTextBold = ImageFont.truetype(common.common.abc_bold, self.fntText.size)
        except:
            self.fntTextBold = self.fntText

        # 데이터 조합
        L3, L4 = zr.build_drill(l2row)
        self.rows = []  # [(lvl, sign, start, end), ...]
        k = 0
        for r3 in L3:
            self.rows.append((3, r3['sign'], r3['start'], r3['end']))
            while k < len(L4) and (L4[k]['start'] >= r3['start']) and (L4[k]['end'] <= r3['end']):
                r4 = L4[k]
                self.rows.append((4, r4['sign'], r4['start'], r4['end']))
                k += 1

        # 치수: 메인과 동일 규칙 사용
        self.FONT_SIZE   = self.fntText.size
        self.SPACE       = self.FONT_SIZE/2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE
        self.HEAD_H      = self.LINE_HEIGHT
        self.W_LEVEL = int(2.8 * self.FONT_SIZE)
        self.W_SIGN  = int(3.0 * self.FONT_SIZE)
        self.W_START = int(7.0 * self.FONT_SIZE)
        self.W_LEN   = int(7.0 * self.FONT_SIZE)
        self.COL_W   = (self.W_LEVEL, self.W_SIGN, self.W_START, self.W_LEN)
        self.TITLE_W = sum(self.COL_W)

        # 높이/폭
        BOR = commonwnd.CommonWnd.BORDER
        n = len(self.rows)
        self.TABLE_H = int(self.HEAD_H + max(1, n)*self.LINE_HEIGHT)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        self.drawBkg()
#        pos = self.GetPosition()
#        self.SetPosition((pos[0] +300, pos[1]-75));

    def getExt(self):
        return u"ZR.bmp"

    def _len_d_first(self, start, end):
        try:
            td = end - start
            days_dec = float(td.days) + (td.seconds + getattr(td, 'microseconds', 0)/1e6) / 86400.0
            if days_dec < 0:
                return u"-"
            unit = mtexts.txts['Day'] if abs(days_dec) == 1 else mtexts.txts['Days']
            return u"%.2f %s" % (days_dec, unit)
        except:
            return u"-"

    def drawBkg(self):
        BOR = commonwnd.CommonWnd.BORDER
        bkg = (255,255,255) if self.bw else self.options.clrbackground
        tbl = (0,0,0)       if self.bw else self.options.clrtable
        txt = (0,0,0)       if self.bw else self.options.clrtexts
        self.SetBackgroundColour(bkg)

        img = Image.new('RGB',(self.WIDTH,self.HEIGHT),bkg)
        draw= ImageDraw.Draw(img)

        # 헤더
        head_y = BOR
        draw.rectangle(((BOR, head_y),(BOR+self.TITLE_W, head_y+self.HEAD_H)), outline=tbl, fill=bkg)
        heads = (u"Lv.", mtexts.txts["Signs"], mtexts.txts["Start"], mtexts.txts["Length"])
        x = BOR
        for i,h in enumerate(heads):
            tw, th = draw.textsize(h, self.fntText)
            draw.text((x + (self.COL_W[i]-tw)/2, head_y + (self.HEAD_H-th)/2), h, fill=txt, font=self.fntText)
            x += self.COL_W[i]
        x0 = BOR; y0 = head_y + self.HEAD_H
        draw.line((x0, y0, x0+self.TITLE_W, y0), fill=tbl)

        # 세로선(헤더부터 표 끝) → 헤더 '아래'부터 표 끝
        top = BOR + self.HEAD_H
        bot = BOR + self.TABLE_H
        xv  = x0
        draw.line((xv, top, xv, bot), fill=tbl)
        for w in self.COL_W:
            xv += w
            draw.line((xv, top, xv, bot), fill=tbl)

        # 데이터 (L3 강조: 글자 Bold+약간 크게, 배경은 동일)
        y = y0
        for (lvl, sign, start, end) in self.rows:
            length_s = self._len_d_first(start, end)
            cells = (u"L%d" % lvl, self.signs[int(sign)], zr.fmt_date(start), length_s)
            isL3  = (lvl == 3)

            if isL3:
                xx = x0
                for ci, w in enumerate(self.COL_W):
                    val = cells[ci]
                    if ci == 1:
                        # 사인 칸: morinus 기호 → 가짜 볼드(두 번 찍기)
                        fnt = self.fntMor
                        tw, th = draw.textsize(val, fnt)
                        cx = xx + (w - tw)/2; cy = y + (self.LINE_HEIGHT - th)/2
                        draw.text((cx,   cy), val, fill=txt, font=fnt)
                        draw.text((cx-1, cy), val, fill=txt, font=fnt)
                    else:
                        # 나머지 칸: 진짜 Bold
                        fntB = self.fntTextBold
                        tw, th = draw.textsize(val, fntB)
                        cx = xx + (w - tw)/2; cy = y + (self.LINE_HEIGHT - th)/2
                        draw.text((cx, cy), val, fill=txt, font=fntB)
                    xx += w
            else:

                xx = x0
                for ci, w in enumerate(self.COL_W):
                    val = cells[ci]
                    fnt = self.fntMor if ci == 1 else self.fntText
                    tw, th = draw.textsize(val, fnt)
                    draw.text((xx + (w - tw)/2, y + (self.LINE_HEIGHT - th)/2), val, fill=txt, font=fnt)
                    xx += w

            draw.line((x0, y + self.LINE_HEIGHT, x0 + self.TITLE_W, y + self.LINE_HEIGHT), fill=tbl)
            y += self.LINE_HEIGHT

        # 외곽
        draw.rectangle(((BOR,BOR),(BOR+self.TITLE_W,BOR+self.TABLE_H)), outline=tbl)

        wxImg = wx.Image(img.size[0], img.size[1]); wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        self.Refresh()
