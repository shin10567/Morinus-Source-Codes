# circumambulationframe.py
# -*- coding: utf-8 -*-
import wx, datetime
import mtexts, util
import wx, datetime, os
import circumambulation as ca
import chart
import common, commonwnd as cw
from PIL import Image, ImageDraw, ImageFont
import astrology
from phasiswnd import PHASIS_EMPTY  # '—' 기호 그대로 사용
# ====== UI Wnd (FixStarsWnd 스타일) ======
class CircumWnd(cw.CommonWnd):

    def _planet_color(self, pid):
        # (bw면 흑백 고정)
        if getattr(self, 'bw', False):
            return (0, 0, 0)

        # pid를 숫자 인덱스로 최대한 안전하게 변환
        objidx = None
        # dict/객체 내부에서 꺼내기
        if isinstance(pid, dict):
            for k in ('pid','num','id','index','ipl','planet_pid'):
                if k in pid:
                    pid = pid[k]; break
        elif hasattr(pid, '__dict__'):
            for k in ('pid','num','id','index','ipl'):
                if hasattr(pid, k):
                    pid = getattr(pid, k); break

        # 숫자 시도
        try:
            objidx = int(pid)
        except Exception:
            objidx = None

        # 이름 → astrology 상수
        if objidx is None and isinstance(pid, (str, bytes)):
            name_map = {
                'sun': astrology.SE_SUN, 'moon': astrology.SE_MOON,
                'mercury': astrology.SE_MERCURY, 'venus': astrology.SE_VENUS,
                'mars': astrology.SE_MARS, 'jupiter': astrology.SE_JUPITER,
                'saturn': astrology.SE_SATURN, 'uranus': astrology.SE_URANUS,
                'neptune': astrology.SE_NEPTUNE, 'pluto': astrology.SE_PLUTO,
            }
            key = pid.strip().lower()
            objidx = name_map.get(key, None)

        # 최종 폴백
        if objidx is None:
            objidx = 0

        # 색 선택: 개인색 or 존비 팔레트
        if getattr(self.options, 'useplanetcolors', False) and hasattr(self.options, 'clrindividual'):
            idx = max(0, min(objidx, len(self.options.clrindividual)-1))
            clr = tuple(self.options.clrindividual[idx])
        else:
            try:
                dign = int(self.chart.dignity(objidx))
            except Exception:
                dign = 0
            pal = [self.options.clrdomicil, self.options.clrexal,
                self.options.clrperegrin, self.options.clrcasus,
                self.options.clrexil]
            i = dign if 0 <= dign < len(pal) else 0
            clr = tuple(pal[i])

        return clr

    def _aspect_color(self, glyph_or_val):
        """Aspect 글리프/값에 맞는 사용자 색을 돌려준다."""
        if getattr(self, 'bw', False):
            return self.clTxt
        # 1) 글리프로 매칭 (common.common.Aspects)
        try:
            aspects_g = getattr(common.common, 'Aspects', []) or []
            if isinstance(glyph_or_val, str) and glyph_or_val in aspects_g:
                idx = aspects_g.index(glyph_or_val)
                if 0 <= idx < len(self.options.clraspect):
                    return self.options.clraspect[idx]
        except Exception:
            pass
        # 2) 숫자(각도값)으로 매칭 (chart.Chart.Aspects)
        try:
            a = float(glyph_or_val)
            for idx, deg in enumerate(chart.Chart.Aspects):
                if abs(a - deg) < 1e-6 and 0 <= idx < len(self.options.clraspect):
                    return self.options.clraspect[idx]
        except Exception:
            pass
        return self.clTxt

    """
    헤더: Age | Asc | Term Lord | Participator | Date
    - FixStarsWnd와 동일한 폰트/행높이/선두께/색 사용
    - Asc: (기호) + dd°mm′ss″
    - Term/Participator: 조건에 따라 한쪽은 '—' (PHASIS_EMPTY)
    """
    def __init__(self, parent, horoscope, options, mainfr=None, id=-1, size=wx.DefaultSize):
        cw.CommonWnd.__init__(self, parent, horoscope, options, id, size)
        self.key = float(getattr(self.options, 'circumkey', 1.0))  # 입력창 없이 기본값 사용
        self.chart   = horoscope
        self.options = options
        self.mainfr  = mainfr
        self.bw      = self.options.bw

        # FixStarsWnd 규격 (폰트/행높이/여백)  :contentReference[oaicite:1]{index=1}
        self.FONT_SIZE    = int(21 * self.options.tablesize)
        self.SPACE        = self.FONT_SIZE / 2
        self.LINE_H       = (self.SPACE + self.FONT_SIZE + self.SPACE)
        self.HEAD_H       = self.LINE_H
        self.SPACE_TITLEY = 0

        # 폰트 (모리누스 심볼 + 텍스트)  :contentReference[oaicite:2]{index=2}
        self.f_sym  = ImageFont.truetype(common.common.symbols, self.FONT_SIZE)
        self.f_txt  = ImageFont.truetype(common.common.abc,     self.FONT_SIZE)
        # 별자리/행성 글리프 테이블
        self.signs  = common.common.Signs1 if self.options.signs else common.common.Signs2
        self.planets = common.common.Planets
        self.deg_symbol = u'\u00b0'

        FS = self.FONT_SIZE
        self.W_AGE  = int(5.0 * FS)      # Age는 유지(살짝 넓게)
        even        = int(8.0 * FS)      # ← 9.0*FS에서 “조금 더” 축소
        self.W_ASC  = even
        self.W_TRM  = even
        self.W_PAR  = even
        self.W_DATE = even
        self.COL_W  = (self.W_AGE, self.W_ASC, self.W_TRM, self.W_PAR, self.W_DATE)
        self.TITLE_W = sum(self.COL_W)
        # 색상 (FixStarsWnd와 동일 로직)  :contentReference[oaicite:3]{index=3}
        self.clBkg = (255,255,255) if self.bw else self.options.clrbackground
        self.clTbl = (0,0,0)       if self.bw else self.options.clrtable
        self.clTxt = (0,0,0)       if self.bw else self.options.clrtexts
        self.SetBackgroundColour(self.clBkg)

        # 데이터 컨테이너
        self.rows = []  # 각 행 = dict(age, asc_deg, asc_sign, term or None, part or None, date)
        # ---- 초기 버퍼(빈 표) 생성: OnPaint보다 먼저 준비 ----
        BOR = cw.CommonWnd.BORDER
        self.TABLE_H = int(self.HEAD_H + self.SPACE_TITLEY + self.LINE_H)   # ★ 최소 1행 높이로 기본값 생성
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))
        # --- 이미지 저장 폴더 보장 (commonwnd.onSaveAsBitmap에서 사용) ---
        try:
            imgdir = getattr(self.options, 'fpathimgs', None)
            if not imgdir:
                try:
                    base = util.getDocDir()
                except Exception:
                    base = os.getcwd()
                imgdir = os.path.join(base, u"images")
            if not os.path.isdir(imgdir):
                os.makedirs(imgdir)
            if self.mainfr is not None and not hasattr(self.mainfr, 'fpathimgs'):
                self.mainfr.fpathimgs = imgdir
        except Exception:
            pass
        self.drawBkg()

    # 외부에서 계산된 원본 rows를 받아, 우리 표 구조로 변환
    def set_data(self, dist_rows):
        # 출생일(그레고리안 변환)  → 나이 계산용
        jd0   = getattr(self.chart.time, 'jd', None)
        y, m, d, _ = astrology.swe_revjul(jd0, astrology.SE_GREG_CAL) if jd0 else (None, None, None, None)
        born = datetime.date(y, m, d) if (y and m and d) else None

        def _age_of(dt):
            if isinstance(dt, datetime.date) and born:
                return (dt.toordinal() - born.toordinal()) / 365.2425
            return None

        def _dms(lon):
            if lon is None: return u""
            if lon < 0: lon = lon % 360.0
            sidx = int(lon // 30.0)
            deg  = lon - 30.0 * sidx
            d = int(deg)
            m = int((deg - d) * 60.0)
            s = int(round((((deg - d) * 60.0) - m) * 60.0))
            if s == 60: s = 0; m += 1
            if m == 60: m = 0; d += 1
            return (sidx, u"%02d\u00b0%02d\u2032%02d\u2033" % (d, m, s))

        def _aspect_glyph(a):
            # fixstarsaspectswnd가 쓰는 글리프: common.common.Aspects[...]  :contentReference[oaicite:4]{index=4}
            try:
                # 1) 인덱스이면 바로
                return common.common.Aspects[int(a)]
            except:
                pass
            try:
                # 2) 각도값이면 Chart.Aspects에서 검색
                av = int(round(float(a)))
                for idx, deg in enumerate(chart.Chart.Aspects):
                    if int(round(deg)) == av:
                        return common.common.Aspects[idx]
            except:
                pass
            # 3) 문자열 키워드
            name_map = {
                'conj':'CONJUNCTIO','sext':'SEXTIL','square':'QUADRAT','trine':'TRIGON','opp':'OPPOSITIO'
            }
            try:
                key = name_map.get(unicode(a).lower(), None)
                if key and hasattr(chart.Chart, key):
                    idx = getattr(chart.Chart, key)
                    return common.common.Aspects[idx]
            except:
                pass
            return u""  # 알 수 없으면 빈칸

        disp = []
        for r in (dist_rows or []):
            # ── ① 텀 시작 행 (Term Lord가 표시되는 행)
            sidx, dms = _dms(r.get('lam_start'))
            term_pid  = r.get('term_ruler_pid', None)
            disp.append({
                'age': _age_of(r.get('date_start')),
                'asc_sign': sidx, 'asc_dms': dms,
                'term': (r.get('sign_idx', sidx), term_pid),
                'part': None,
                'date': r.get('date_start')
            })
            # ── ② Participator(hit)들은 개별 행으로
            for p in (r.get('participating') or []):
                sidx2, dms2 = _dms(p.get('lam'))

                # --- 행성 pid를 여러 키/형태에서 안전 추출 ---
                part_pid = p.get('planet_pid', None)
                if part_pid is None:
                    # 후보 키들
                    for k in ('pid', 'planet', 'pl', 'planet_id', 'planetindex', 'ipl', 'body', 'body_id'):
                        if k in p and p[k] is not None:
                            part_pid = p[k]; break
                # 딕셔너리/객체인 경우 내부 속성에서 추출
                if isinstance(part_pid, dict):
                    for k in ('pid','num','id','index','ipl'):
                        if k in part_pid:
                            part_pid = part_pid[k]; break
                elif hasattr(part_pid, '__dict__'):
                    for k in ('pid','num','id','index','ipl'):
                        if hasattr(part_pid, k):
                            part_pid = getattr(part_pid, k); break

                disp.append({
                    'age': _age_of(p.get('date')),
                    'asc_sign': sidx2, 'asc_dms': dms2,
                    'term': None,
                    'part': (_aspect_glyph(p.get('aspect')), part_pid),
                    'date': p.get('date')
                })

        self.rows = disp
        # 크기 재계산 및 다시 그리기 (FixStarsWnd 방식)  :contentReference[oaicite:5]{index=5}
        BOR = cw.CommonWnd.BORDER
        self.TABLE_H = int(self.HEAD_H + self.SPACE_TITLEY + max(1, len(self.rows)) * self.LINE_H)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))
        self.drawBkg()

    def _glyph_sign(self, sidx):
        if sidx is None: return u""
        sidx = max(0, min(sidx, len(self.signs)-1))
        return self.signs[sidx]

    # 파일 상단이 파이썬2라면 basestring 호환
    try:
        basestring
    except NameError:
        basestring = str

    def _glyph_planet(self, pid):
        """
        pid 가 무엇이 오든(정수 index, '3' 같은 문자열 숫자, 'Sun' 같은 이름,
        딕셔너리/객체, 이미 1글자 심볼) → Morinus 행성 글리프 반환
        """
        if pid is None:
            return u""

        # dict/객체면 안쪽에서 우선 추출
        if isinstance(pid, dict):
            for k in ('pid','num','id','index','ipl','planet_pid'):
                if k in pid:
                    pid = pid[k]; break
        elif hasattr(pid, '__dict__'):
            for k in ('pid','num','id','index','ipl'):
                if hasattr(pid, k):
                    pid = getattr(pid, k); break

        # 이미 1글자 심볼
        if isinstance(pid, basestring):
            s = pid.strip()
            if len(s) == 1:
                return s  # 이미 글리프
            # '3' 같은 문자열 숫자
            try:
                pid_int = int(s)
            except Exception:
                # 이름 → 상수
                name_map = {
                    'sun': astrology.SE_SUN, 'moon': astrology.SE_MOON,
                    'mercury': astrology.SE_MERCURY, 'venus': astrology.SE_VENUS,
                    'mars': astrology.SE_MARS, 'jupiter': astrology.SE_JUPITER,
                    'saturn': astrology.SE_SATURN, 'uranus': astrology.SE_URANUS,
                    'neptune': astrology.SE_NEPTUNE, 'pluto': astrology.SE_PLUTO,
                    'nn': getattr(astrology, 'SE_TRUE_NODE', getattr(astrology, 'SE_MEAN_NODE', None)),
                    'node': getattr(astrology, 'SE_TRUE_NODE', getattr(astrology, 'SE_MEAN_NODE', None)),
                }
                pid_int = name_map.get(s.lower(), None)
        else:
            try:
                pid_int = int(pid)
            except Exception:
                pid_int = None

        # 숫자 인덱스 처리
        if isinstance(pid_int, int):
            if 0 <= pid_int < len(self.planets):
                return self.planets[pid_int]
            try:
                if pid_int in (getattr(astrology, 'SE_TRUE_NODE', -999),
                            getattr(astrology, 'SE_MEAN_NODE', -998)):
                    return getattr(common.common, 'NNode', u'☊')
            except Exception:
                pass

        return u""
    def getExt(self):
        return u"Circum.bmp"

    def drawBkg(self):
        BOR = cw.CommonWnd.BORDER
        img  = Image.new('RGB', (getattr(self,'WIDTH', BOR+self.TITLE_W+BOR),
                                      getattr(self,'HEIGHT', BOR+self.HEAD_H+self.LINE_H+BOR)), self.clBkg)
        draw = ImageDraw.Draw(img)

        # ─ 헤더 박스 (FixStarsWnd 스타일)  :contentReference[oaicite:6]{index=6}
        draw.rectangle(((BOR, BOR),(BOR + self.TITLE_W, BOR + self.HEAD_H)),
                       outline=self.clTbl, fill=self.clBkg)
        heads = (u"Age", u"Degree", u"Term Lord", u"Participator", u"Date")
        x = BOR
        for i, h in enumerate(heads):
            w = self.COL_W[i]
            tw, th = draw.textsize(h, self.f_txt)
            draw.text((x + (w - tw)/2, BOR + (self.HEAD_H - th)/2), h, fill=self.clTxt, font=self.f_txt)
            x += w
        # 헤더 하단선
        y0 = BOR + self.HEAD_H
        table_h = getattr(self, 'TABLE_H', self.HEAD_H + self.SPACE_TITLEY + max(1, len(self.rows)) * self.LINE_H)
        draw.line((BOR, y0, BOR + self.TITLE_W, y0), fill=self.clTbl)

        # 세로선 (본문만: 헤더는 비우기)
        xv = BOR
        draw.line((xv, y0, xv, BOR + table_h), fill=self.clTbl)

        for w in self.COL_W:
            xv += w
            draw.line((xv, y0, xv, BOR + table_h), fill=self.clTbl)

        # ─ 본문
        y = y0
        for row in (self.rows or []):
            # 가로선
            draw.line((BOR, y + self.LINE_H, BOR + self.TITLE_W, y + self.LINE_H), fill=self.clTbl)

            # 1) Age
            age_txt = u"%.2f" % row['age'] if row.get('age') is not None else u""
            x = BOR; w = self.W_AGE
            tw, th = draw.textsize(age_txt, self.f_txt)
            draw.text((x + (w - tw)/2, y + (self.LINE_H - th)/2), age_txt, fill=self.clTxt, font=self.f_txt)
            x += w

            # 2) Asc (기호 + dms)
            sign_g = self._glyph_sign(row.get('asc_sign'))
            dms    = row.get('asc_dms', u"")
            tw1, th1 = draw.textsize(sign_g, self.f_sym)
            tw2, th2 = draw.textsize(dms,    self.f_txt)
            totw = tw1 + (self.FONT_SIZE/3) + tw2
            draw.text((x + (self.W_ASC - totw)/2, y + (self.LINE_H - th1)/2), sign_g, fill=self.clTxt, font=self.f_sym)
            draw.text((x + (self.W_ASC - totw)/2 + tw1 + (self.FONT_SIZE/3),
                       y + (self.LINE_H - th2)/2), dms, fill=self.clTxt, font=self.f_txt)
            x += self.W_ASC

            # 3) Term Lord
            if row.get('term') is not None:
                sidx, pid = row['term']
                g1 = self._glyph_sign(sidx)      # 사인 기호
                g2 = self._glyph_planet(pid)     # 행성 기호
                w  = self.W_TRM
                tw1, th1 = draw.textsize(g1, self.f_sym)
                tw2, th2 = draw.textsize(g2, self.f_sym)
                gap = int(self.FONT_SIZE/3)
                tot = tw1 + gap + tw2
                base = x + (w - tot)/2
                # 사인 글리프는 텍스트색, 행성 글리프는 사용자 행성색
                draw.text((base,                 y + (self.LINE_H-th1)/2), g1, fill=self.clTxt,               font=self.f_sym)
                draw.text((base + tw1 + gap,     y + (self.LINE_H-th2)/2), g2, fill=self._planet_color(pid),  font=self.f_sym)
            else:
                # — (phasiswnd의 빈칸 기호)
                w = self.W_TRM
                tw, th = draw.textsize(PHASIS_EMPTY, self.f_txt)
                draw.text((x + (w - tw)/2, y + (self.LINE_H-th)/2), PHASIS_EMPTY, fill=self.clTxt, font=self.f_txt)
            x += self.W_TRM

            # 4) Participator
            if row.get('part') is not None:
                asp_g, pid = row['part']        # (각 기호, 행성 ID/이름/글리프)
                g1 = asp_g or u""
                g2 = self._glyph_planet(pid)    # ← 방금 고친 변환기 사용
                w  = self.W_PAR
                tw1, th1 = draw.textsize(g1, self.f_sym)
                tw2, th2 = draw.textsize(g2, self.f_sym)
                gap = int(self.FONT_SIZE/3) if (g1 and g2) else 0
                tot = tw1 + gap + tw2
                base = x + (w - tot)/2
                if g1:
                    draw.text((base, y + (self.LINE_H-th1)/2), g1, fill=self._aspect_color(g1), font=self.f_sym)
                    base += tw1 + gap
                if g2:
                    draw.text((base, y + (self.LINE_H-th2)/2), g2, fill=self._planet_color(pid), font=self.f_sym)
            else:
                w = self.W_PAR
                tw, th = draw.textsize(PHASIS_EMPTY, self.f_txt)
                draw.text((x + (w - tw)/2, y + (self.LINE_H-th)/2), PHASIS_EMPTY, fill=self.clTxt, font=self.f_txt)
            x += self.W_PAR

            # 5) Date (YYYY.MM.DD)
            dt = row.get('date', None)
            if isinstance(dt, datetime.date):
                date_txt = u"%04d.%02d.%02d" % (dt.year, dt.month, dt.day)
            else:
                date_txt = u""
            w = self.W_DATE
            tw, th = draw.textsize(date_txt, self.f_txt)
            draw.text((x + (w - tw)/2, y + (self.LINE_H - th)/2), date_txt, fill=self.clTxt, font=self.f_txt)

            y += self.LINE_H

        # 외곽 테두리  :contentReference[oaicite:8]{index=8}
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_W, BOR + table_h)), outline=self.clTbl)

        # wx 버퍼로
        wxImg = wx.EmptyImage(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.BitmapFromImage(wxImg)
        try:
            self.Refresh(False); self.Update()
        except:
            pass


class CircumFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options, key=ca.DEFAULT_KEY_Y_PER_DEG, rows=60):
        t = u"Circumambulation"
        try:
            t = title.replace(mtexts.typeList[horoscope.htype], u"Circumambulation")
        except:
            pass
        wx.Frame.__init__(self, parent, -1, t, wx.DefaultPosition, wx.Size(900, 520))
        self.horoscope = horoscope
        self.options   = options
        self.key       = key
        self.rows_n    = rows

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.table = CircumWnd(panel, self.horoscope, self.options, mainfr=self)
        vbox.Add(self.table, 1, wx.EXPAND|wx.ALL, 8)

        panel.SetSizer(vbox)
        self.populate()

    def on_refresh(self, evt):
        try:
            self.key = float(self.key_ctrl.GetValue())
        except:
            self.key = ca.DEFAULT_KEY_Y_PER_DEG
            self.key_ctrl.SetValue(str(self.key))
        self.populate()

    def populate(self):
        try:
            rows = ca.compute_distributions(
                self.horoscope, self.options,
                key=self.key, max_rows=self.rows_n,
                include_participating=True,
                max_age_years=150
            )
        except ValueError as e:
            wx.MessageBox(unicode(e) if hasattr(e, '__unicode__') else u"%s" % e,
                        u"Circumambulation", wx.OK | wx.ICON_INFORMATION)
            try: self.Close(True)
            except: pass
            try: self.Destroy()
            except: pass
            return

        self.table.set_data(rows)

        # 창 자체의 기본 크기를 더 슬림하게
        self.SetMinSize((200, 200))   # ← 원하면 560~640로 더 줄여도 OK
        self.SetSize((660, 560))      # ← 기본 표시 크기(가로폭 축소)
        self.Layout()
        self.CentreOnScreen()


