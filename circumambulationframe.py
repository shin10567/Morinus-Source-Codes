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
import mtexts
import chart
import intvalidator
import rangechecker
import datetime, math
import primdirs
def _circum_years_per_deg_from_options(options):
    """
    Circumambulations는 'years per OA degree' 형태의 정적 키를 기대한다.
    - options.circumkey가 있으면 그 값을 최우선으로 사용
    - 없으면 PrimDirs 정적 키(pdboid/cardan/ptolemy/customer)를 따라간다
    """
    # 0) 명시 오버라이드(있으면 그대로)
    v = getattr(options, 'circumkey', None)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass

    # 1) PrimDirs 정적 키 사용 (Morinus 기본 pdkeys=Naibod)
    try:
        # Customer key: deg/year -> years/deg로 뒤집기
        if getattr(options, 'pdkeys', None) == primdirs.PrimDirs.CUSTOMER:
            deg  = float(getattr(options, 'pdkeydeg', 0.0))
            minu = float(getattr(options, 'pdkeymin', 0.0))
            sec  = float(getattr(options, 'pdkeysec', 0.0))
            deg_per_year = deg + minu/60.0 + sec/3600.0
            return (1.0/deg_per_year) if deg_per_year else 1.0

        pdkeys = getattr(options, 'pdkeys', None)
        if pdkeys is not None:
            return float(primdirs.PrimDirs.staticData[pdkeys][primdirs.PrimDirs.COEFF])
    except Exception:
        pass

    # 2) 폴백: Ptolemy
    return 1.0
# ====== UI Wnd (FixStarsWnd 스타일) ======
class CircumWnd(cw.CommonWnd):

    def _planet_color(self, pid):
        """사용자 설정 '행성별 색' 팔레트를 최우선으로 사용하고, 없으면 존비 팔레트로 폴백."""
        # 흑백 모드면 텍스트색(또는 검정)으로
        if getattr(self, 'bw', False):
            return self.clTxt

        # 0) pid → 내부 인덱스 해석 (숫자/이름/객체/딕셔너리 모두 허용)
        objidx = None
        # a) dict/객체에서 꺼내기
        if isinstance(pid, dict):
            for k in ('pid','num','id','index','ipl','planet_pid'):
                if k in pid:
                    pid = pid[k]; break
        elif hasattr(pid, '__dict__'):
            for k in ('pid','num','id','index','ipl'):
                if hasattr(pid, k):
                    pid = getattr(pid, k); break
        # b) 숫자 시도
        try:
            objidx = int(pid)
        except Exception:
            objidx = None
        # c) 이름 → 인덱스 (영문/다국어 라벨 모두)
        if objidx is None and isinstance(pid, (str, bytes)):
            if isinstance(pid, bytes):
                pid = pid.decode('utf-8','ignore')
            key = pid.strip().lower()
            name_map = {
                mtexts.txts.get('Sun','Sun').lower():      astrology.SE_SUN,
                mtexts.txts.get('Moon','Moon').lower():    astrology.SE_MOON,
                mtexts.txts.get('Mercury','Mercury').lower(): astrology.SE_MERCURY,
                mtexts.txts.get('Venus','Venus').lower():  astrology.SE_VENUS,
                mtexts.txts.get('Mars','Mars').lower():    astrology.SE_MARS,
                mtexts.txts.get('Jupiter','Jupiter').lower(): astrology.SE_JUPITER,
                mtexts.txts.get('Saturn','Saturn').lower():   astrology.SE_SATURN,
                mtexts.txts.get('Uranus','Uranus').lower():   astrology.SE_URANUS,
                mtexts.txts.get('Neptune','Neptune').lower(): astrology.SE_NEPTUNE,
                mtexts.txts.get('Pluto','Pluto').lower():     astrology.SE_PLUTO,
                'sun': astrology.SE_SUN, 'moon': astrology.SE_MOON, 'mercury': astrology.SE_MERCURY,
                'venus': astrology.SE_VENUS, 'mars': astrology.SE_MARS, 'jupiter': astrology.SE_JUPITER,
                'saturn': astrology.SE_SATURN, 'uranus': astrology.SE_URANUS,
                'neptune': astrology.SE_NEPTUNE, 'pluto': astrology.SE_PLUTO,
            }
            objidx = name_map.get(key, None)
        if objidx is None:
            objidx = astrology.SE_SUN  # 안전 폴백

        # 1) 사용자 행성 팔레트(개별색) ― 옵션(useplanetcolors) 켜진 경우에만 사용
        if bool(getattr(self.options, 'useplanetcolors', False)):
            # 프로젝트마다 속성명이 다를 수 있어 폭넓게 탐색
            palettes = []
            for attr in ('clrplanets','clrindividual','pcolors','planet_colors'):
                if hasattr(self.options, attr):
                    palettes.append(getattr(self.options, attr))
            # common 쪽에 전역 팔레트가 있으면 후보에 추가
            try:
                if hasattr(common, 'common'):
                    for attr in ('PLANET_COLORS','planet_colors','clrPlanets'):
                        if hasattr(common.common, attr):
                            palettes.append(getattr(common.common, attr))
            except Exception:
                pass

            for pal in palettes:
                try:
                    if pal is None:
                        continue
                    # 리스트/튜플 형태
                    if isinstance(pal, (list, tuple)) and 0 <= objidx < len(pal):
                        c = pal[objidx]
                        if isinstance(c, (list, tuple)) and len(c) >= 3:
                            return (int(c[0]), int(c[1]), int(c[2]))
                    # 딕셔너리 형태 (키가 인덱스/이름 둘 다일 수 있음)
                    if isinstance(pal, dict):
                        key_try = objidx
                        if key_try in pal and isinstance(pal[key_try], (list, tuple)) and len(pal[key_try]) >= 3:
                            c = pal[key_try]
                            return (int(c[0]), int(c[1]), int(c[2]))
                except Exception:
                    continue

        # 2) 위 팔레트가 없으면: 존비/엑잘트/페레그린/카수스/엑실 팔레트로 폴백
        try:
            dign = int(self.chart.dignity(objidx))
        except Exception:
            dign = 0
        pal2 = [self.options.clrdomicil, self.options.clrexal,
                self.options.clrperegrin, self.options.clrcasus,
                self.options.clrexil]
        i = dign if 0 <= dign < len(pal2) else 0
        c = pal2[i]
        return (int(c[0]), int(c[1]), int(c[2]))


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
        self.key = _circum_years_per_deg_from_options(self.options)
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
        born = ca._gregorian_date_in_radix_zone(jd0, self.chart) if jd0 else None

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
            return (sidx, u"%02d\u00b0%02d\'%02d\"" % (d, m, s))

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
                key = name_map.get(str(a).lower(), None)
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
    def getExt(self):
        return u"Circum.bmp"

    def drawBkg(self):
        BOR = cw.CommonWnd.BORDER
        img  = Image.new('RGB',
                         (getattr(self,'WIDTH', BOR+self.TITLE_W+BOR),
                          getattr(self,'HEIGHT', BOR+self.HEAD_H+self.LINE_H+BOR)),
                         self.clBkg)
        draw = ImageDraw.Draw(img)

        # ─ 헤더 박스
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_W, BOR + self.HEAD_H)),
                       outline=self.clTbl, fill=self.clBkg)

        heads = (mtexts.txts["Age"], mtexts.txts["Degree"],
                 mtexts.txts["TermLord"], mtexts.txts["Participator"], mtexts.txts["Date"])

        x = BOR
        for i, h in enumerate(heads):
            w = self.COL_W[i]
            tw, th = draw.textsize(h, self.f_txt)
            draw.text((x + (w - tw)/2, BOR + (self.HEAD_H - th)/2), h, fill=self.clTxt, font=self.f_txt)
            x += w

        # 표 본문
        y = BOR + self.HEAD_H + self.SPACE_TITLEY
        table_h = self.HEAD_H + self.SPACE_TITLEY + max(1, len(self.rows)) * self.LINE_H

        for row in self.rows if self.rows else [{}]:
            x = BOR

            # 1) Age
            age_txt = row.get('age', u"")
            w  = self.W_AGE
            tw, th = draw.textsize(age_txt, self.f_txt)
            draw.text((x + (w - tw)/2, y + (self.LINE_H - th)/2), age_txt, fill=self.clTxt, font=self.f_txt)
            x += w

            # 2) Asc (기호 + dms)
            sign_g = self._glyph_sign(row.get('asc_sign'))
            dms    = row.get('asc_dms', u"")
            tw1, th1 = draw.textsize(sign_g, self.f_sym)
            tw2, th2 = draw.textsize(dms,    self.f_txt)
            totw = tw1 + (self.FONT_SIZE//3) + tw2
            draw.text((x + (self.W_ASC - totw)/2, y + (self.LINE_H - th1)/2),
                      sign_g, fill=self.clTxt, font=self.f_sym)
            draw.text((x + (self.W_ASC - totw)/2 + tw1 + (self.FONT_SIZE//3),
                       y + (self.LINE_H - th2)/2),
                      dms, fill=self.clTxt, font=self.f_txt)
            x += self.W_ASC

            # 3) Term Lord
            pid = row.get('term_pid', None)
            g2  = self._glyph_planet(pid) if hasattr(self, '_glyph_planet') else u""
            tw2, th2 = draw.textsize(g2, self.f_sym)
            draw.text((x + (self.W_TRM - tw2)/2, y + (self.LINE_H - th2)/2),
                      g2, fill=self._planet_color(pid), font=self.f_sym)
            x += self.W_TRM

            # 4) Participator (aspect glyph + planet glyph)
            part = row.get('part', None)
            if part:
                g1 = part.get('aspect_g', u"")
                pid = part.get('pid', None)
                g2 = self._glyph_planet(pid) if hasattr(self, '_glyph_planet') else u""
                w  = self.W_PAR
                tw1, th1 = draw.textsize(g1, self.f_sym)
                tw2, th2 = draw.textsize(g2, self.f_sym)
                gap = (self.FONT_SIZE//3) if (g1 and g2) else 0
                tot = tw1 + gap + tw2
                base = x + (w - tot)/2
                if g1:
                    draw.text((base, y + (self.LINE_H - th1)/2),
                              g1, fill=self._aspect_color(g1), font=self.f_sym)
                    base += tw1 + gap
                if g2:
                    draw.text((base, y + (self.LINE_H - th2)/2),
                              g2, fill=self._planet_color(pid), font=self.f_sym)
            else:
                w = self.W_PAR
                tw, th = draw.textsize(PHASIS_EMPTY, self.f_txt)
                draw.text((x + (w - tw)/2, y + (self.LINE_H - th)/2),
                          PHASIS_EMPTY, fill=self.clTxt, font=self.f_txt)
            x += self.W_PAR

            # 5) Date
            dt = row.get('date', None)
            if isinstance(dt, datetime.date):
                date_txt = u"%d.%02d.%02d" % (dt.year, dt.month, dt.day)
            else:
                date_txt = u""
            w = self.W_DATE
            tw, th = draw.textsize(date_txt, self.f_txt)
            draw.text((x + (w - tw)/2, y + (self.LINE_H - th)/2),
                      date_txt, fill=self.clTxt, font=self.f_txt)

            y += self.LINE_H

        # 외곽 테두리
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_W, BOR + table_h)),
                       outline=self.clTbl)

        # wx 버퍼로
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        try:
            self.Refresh(False); self.Update()
        except:
            pass

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
        # --- [추가] 다국어 행성 이름 문자열 → 글리프 매핑 ---
        if isinstance(pid, (str, bytes)):
            if isinstance(pid, bytes):
                pid = pid.decode('utf-8', 'ignore')

            name = pid.strip().lower()

            # 현재 UI 언어의 라벨을 전부 수집(영/한/중 ... 어떤 문자열로 와도 매칭되게)
            name_map = {
                mtexts.txts.get('Sun','Sun').lower():      0,
                mtexts.txts.get('Moon','Moon').lower():    1,
                mtexts.txts.get('Mercury','Mercury').lower(): 2,
                mtexts.txts.get('Venus','Venus').lower():  3,
                mtexts.txts.get('Mars','Mars').lower():    4,
                mtexts.txts.get('Jupiter','Jupiter').lower(): 5,
                mtexts.txts.get('Saturn','Saturn').lower():   6,
                mtexts.txts.get('Uranus','Uranus').lower():   7,
                mtexts.txts.get('Neptune','Neptune').lower(): 8,
                mtexts.txts.get('Pluto','Pluto').lower():     9,
            }
            idx = name_map.get(name, None)
            if idx is not None and 0 <= idx < len(self.planets):
                return self.planets[idx]

            # 이미 1글자 심볼이면 그대로 사용(예방용)
            if len(pid) == 1:
                return pid
        # --- [추가 끝] ---

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
        heads = (mtexts.txts["Age"], mtexts.txts["Degree"], mtexts.txts["TermLord"], mtexts.txts["Participator"], mtexts.txts["Date"])
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
                date_txt = u"%d.%02d.%02d" % (dt.year, dt.month, dt.day)
            else:
                date_txt = u""
            w = self.W_DATE
            tw, th = draw.textsize(date_txt, self.f_txt)
            draw.text((x + (w - tw)/2, y + (self.LINE_H - th)/2), date_txt, fill=self.clTxt, font=self.f_txt)

            y += self.LINE_H

        # 외곽 테두리  :contentReference[oaicite:8]{index=8}
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_W, BOR + table_h)), outline=self.clTbl)

        # wx 버퍼로
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        try:
            self.Refresh(False); self.Update()
        except:
            pass


class CircumFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options, key=ca.DEFAULT_KEY_Y_PER_DEG, rows=60):
        t = mtexts.txts['Circumambulation']
        try:
            t = title.replace(mtexts.typeList[horoscope.htype], mtexts.txts['Circumambulation'])
        except:
            pass
        wx.Frame.__init__(self, parent, -1, t, wx.DefaultPosition, wx.Size(850, 520))
        self.horoscope = horoscope
        self.options   = options
        self.key       = _circum_years_per_deg_from_options(self.options)
        self.rows_n    = rows

        panel = wx.Panel(self)
        # ---- 상단 툴바: PD와 동일한 컨트롤만(아이콘 없음) ----
        self.tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.tb.SetToolBitmapSize((24,24))
        # 툴바 전체 왼쪽 마진(픽셀) — 10~14 사이가 무난
        try:
            self.tb.SetMargins(12, 0)   # (left=12px, top=0px)
        except Exception:
            pass
        self.tb.AddControl(wx.StaticText(self.tb, -1, u'   '))

        # 픽셀 간격 유틸(툴바 컨트롤 사이 간격을 PD와 유사하게 고정)
        def _tb_spacer(w):
            st = wx.StaticText(self.tb, -1, u'')
            st.SetMinSize((w, -1))
            self.tb.AddControl(st)

        # 연도 범위(확장 모드면 5000년)
        rnge = 3000
        try:
            checker = rangechecker.RangeChecker()
            if checker.isExtended():
                rnge = 5000
        except Exception:
            pass
        _tb_spacer(12)  # 툴바 맨 왼쪽과 첫 필드 사이 여백 12px

        t = self.horoscope.time  # 원 시각

        # 날짜(YYYY MM DD)
        self.year = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, rnge),
                                size=(50,-1), style=wx.TE_READONLY)
        self.year.SetMaxLength(4)
        self.year.SetValue(str(getattr(t, 'origyear', getattr(t, 'year', 0))))
        self.tb.AddControl(self.year); self.tb.AddControl(wx.StaticText(self.tb, -1, u'.'))

        self.month = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(1, 12),
                                size=(30,-1), style=wx.TE_READONLY)
        self.month.SetMaxLength(2)
        self.month.SetValue(str(getattr(t, 'origmonth', getattr(t, 'month', 1))).zfill(2))
        self.tb.AddControl(self.month); self.tb.AddControl(wx.StaticText(self.tb, -1, u'.'))

        self.day = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(1, 31),
                            size=(30,-1), style=wx.TE_READONLY)
        self.day.SetMaxLength(2)
        self.day.SetValue(str(getattr(t, 'origday', getattr(t, 'day', 1))).zfill(2))
        self.tb.AddControl(self.day)

        # 날짜-시간 사이 간격
        self.tb.AddControl(wx.StaticText(self.tb, -1, '     '))

        # 시간(hh:mm:ss)
        self.hour = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, 23),
                                size=(30,-1), style=wx.TE_READONLY)
        self.hour.SetMaxLength(2)
        self.hour.SetValue(str(getattr(t, 'hour', 0)))
        self.tb.AddControl(self.hour)
        self.tb.AddControl(wx.StaticText(self.tb, -1, ':'))

        self.minute = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, 59),
                                size=(30,-1), style=wx.TE_READONLY)
        self.minute.SetMaxLength(2)
        self.minute.SetValue(str(getattr(t, 'minute', 0)).zfill(2))
        self.tb.AddControl(self.minute)
        self.tb.AddControl(wx.StaticText(self.tb, -1, ':'))

        self.sec = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, 59),
                            size=(30,-1), style=wx.TE_READONLY)
        self.sec.SetMaxLength(2)
        self.sec.SetValue(str(getattr(t, 'second', 0)).zfill(2))
        self.tb.AddControl(self.sec)

        # 시간-라벨 사이 간격
        self.tb.AddControl(wx.StaticText(self.tb, -1, '     '))

        # '생시보정:' (다국어)
        self.tb.AddControl(wx.StaticText(self.tb, -1, mtexts.txts.get('Rectification', u'Rectification')))
        self.tb.AddControl(wx.StaticText(self.tb, -1, ': '))

        # 보정 콤보
        self.recttypes = ('1s', '5s', '10s', '1m', '5m', '10m')
        self.rectcb = wx.ComboBox(self.tb, -1, self.recttypes[0], size=(70,-1),
                                choices=self.recttypes, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.rectcb.SetSelection(0)
        self.tb.AddControl(self.rectcb)

        # 콤보-± 간격
        self.tb.AddControl(wx.StaticText(self.tb, -1, ' '))

        # + / -
        self.btnIncr = wx.Button(self.tb, -1, '+', size=(40,30))
        self.tb.AddControl(self.btnIncr)
        self.btnDecr = wx.Button(self.tb, -1, '-', size=(40,30))
        self.tb.AddControl(self.btnDecr)

        # ± - 계산 간격
        self.tb.AddControl(wx.StaticText(self.tb, -1, '  '))

        # 계산(다국어)
        self.btnCalc = wx.Button(self.tb, -1, mtexts.txts.get('Calculate', u'Calculate'), size=(-1,30))
        self.tb.AddControl(self.btnCalc)

        # 이벤트
        self.Bind(wx.EVT_BUTTON, self.onIncr, id=self.btnIncr.GetId())
        self.Bind(wx.EVT_BUTTON, self.onDecr, id=self.btnDecr.GetId())
        self.Bind(wx.EVT_BUTTON, self.onCalc, id=self.btnCalc.GetId())

        self.tb.Realize()

        self.table = CircumWnd(panel, self.horoscope, self.options, mainfr=self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.table, 1, wx.EXPAND, 0)

        panel.SetSizer(vbox)
        self.table.SetFocus()

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
                        mtexts.txts['Circumambulation'], wx.OK | wx.ICON_INFORMATION)
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
    # ----- 시간 필드/보정 유틸 -----
    def _get_fields(self):
        return (int(self.year.GetValue()), int(self.month.GetValue()), int(self.day.GetValue()),
                int(self.hour.GetValue()), int(self.minute.GetValue()), int(self.sec.GetValue()))

    def _set_fields(self, y, m, d, h, mi, s):
        self.year.SetValue(str(y))
        self.month.SetValue(str(m).zfill(2))
        self.day.SetValue(str(d).zfill(2))
        self.hour.SetValue(str(h))
        self.minute.SetValue(str(mi).zfill(2))
        self.sec.SetValue(str(s).zfill(2))

    def _adjust_time(self, seconds):
        y, m, d, h, mi, s = self._get_fields()
        try:
            base = datetime.datetime(y, m, d, h, mi, s)
            base = base + datetime.timedelta(seconds=seconds)
            self._set_fields(base.year, base.month, base.day, base.hour, base.minute, base.second)
        except Exception:
            pass

    def onIncr(self, evt=None):
        idx = self.rectcb.GetCurrentSelection()
        step = (1, 5, 10, 60, 300, 600)[idx if 0 <= idx < 6 else 0]
        self._adjust_time(step)

    def onDecr(self, evt=None):
        idx = self.rectcb.GetCurrentSelection()
        step = (1, 5, 10, 60, 300, 600)[idx if 0 <= idx < 6 else 0]
        self._adjust_time(-step)

    def onCalc(self, evt=None):
        # 필드 → Time/Chart 갱신
        y, m, d, h, mi, s = self._get_fields()
        ot = self.horoscope.time
        new_time = chart.Time(y, m, d, h, mi, s,
                            ot.bc, ot.cal, ot.zt, ot.plus, ot.zh, ot.zm,
                            ot.daylightsaving, self.horoscope.place)
        self.horoscope = chart.Chart(self.horoscope.name, self.horoscope.male,
                                    new_time, self.horoscope.place, self.horoscope.htype,
                                    self.horoscope.notes, self.horoscope.options)
        # 테이블 재계산/표시
        self.populate()

