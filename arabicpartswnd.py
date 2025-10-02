# -*- coding: utf-8 -*-
import math
import sweastrology as swe
import util
import os
import wx
import astrology
from fortune import Fortune
import planets
import chart
import arabicparts
import common
import commonwnd
import Image, ImageDraw, ImageFont
import util
import mtexts
import re
# 파일 상단 import 근처
try:
	basestring
except NameError:
	basestring = str
ZODIAC_GLYPH = {'Ari':u'♈','Tau':u'♉','Gem':u'♊','Can':u'♋','Leo':u'♌','Vir':u'♍',
				'Lib':u'♎','Sco':u'♏','Sag':u'♐','Cap':u'♑','Aqu':u'♒','Pis':u'♓'}
PLANET_GLYPH = {'SU':u'☉','MO':u'☽','ME':u'☿','VE':u'♀','MA':u'♂','JU':u'♃','SA':u'♄',
				'UR':u'♅','NE':u'♆','PL':u'⯓'}
SIGN_INDEX = {'Ari':0,'Tau':1,'Gem':2,'Can':3,'Leo':4,'Vir':5,'Lib':6,'Sco':7,'Sag':8,'Cap':9,'Aqu':10,'Pis':11}
try:
	unicode
except NameError:
	unicode = str
def _ensure_re_de_tokens():
	# mtexts.txts에 키 보강
	if 'DE' not in mtexts.txts:
		mtexts.txts['DE'] = u'DE'
	if 'RE' not in mtexts.txts:
		mtexts.txts['RE'] = u'Re'

	# partstxts(콤보 표시용)에 'DE','DE!','RE','RE!'가 없으면 추가
	pts = list(mtexts.partstxts)
	for t in (mtexts.txts['DE'], mtexts.txts['DE']+u'!', mtexts.txts['RE'], mtexts.txts['RE']+u'!'):
		if t not in pts:
			pts.append(t)
	mtexts.partstxts = tuple(pts)

	# conv(라벨→상수)도 보강
	if mtexts.txts['DE'] not in mtexts.conv:
		mtexts.conv[mtexts.txts['DE']] = arabicparts.ArabicParts.DEG
	if (mtexts.txts['DE']+u'!') not in mtexts.conv:
		mtexts.conv[mtexts.txts['DE']+u'!'] = arabicparts.ArabicParts.DEGLORD
	if mtexts.txts['RE'] not in mtexts.conv:
		mtexts.conv[mtexts.txts['RE']] = arabicparts.ArabicParts.RE
	if (mtexts.txts['RE']+u'!') not in mtexts.conv:
		mtexts.conv[mtexts.txts['RE']+u'!'] = arabicparts.ArabicParts.REFLORD

	# 역매핑 캐시는 다음 조회 때 새로 만들게 비우기
	try:
		delattr(mtexts, '_conv_rev_cache')
	except:
		pass

def _to_unicode(s):
	# Py2/Win에서 바이트 문자열에 '°' 등 비ASCII가 섞이면 ascii 디폴트로 터진다.
	try:
		unicode
	except NameError:
		unicode = str
	try:
		basestring
	except NameError:
		basestring = str

	if isinstance(s, unicode):
		return s
	if isinstance(s, str):
		try:
			return s.decode('utf-8')
		except Exception:
			return s.decode('latin-1', 'replace')
	# 문자열이 아니면 안전하게 문자열화
	try:
		return unicode(s)
	except Exception:
		return u'%s' % s


def _token_segments_for_formula(tok, fntText, fntSymbol, signs):
	"""토큰(AC/SU/MO/RE/DE 등)을 [ (문자, 폰트), ... ] 세그먼트로 분해"""
	# Py2 호환
	try:
		basestring
	except NameError:
		basestring = str
	try:
		integer_types = (int, long)
	except NameError:
		integer_types = (int,)

	# 행성/각 라벨 → 심볼 폰트
	if isinstance(tok, integer_types):
		lab = mtexts.partstxts[tok]
		if lab in PLANET_GLYPH:
			return [(PLANET_GLYPH[lab], fntSymbol)]
		return [(lab, fntText)]

	if isinstance(tok, basestring):
		t = _to_unicode(tok).strip()
		tu = t.upper()

		# 참조 Rn
		if t.startswith(u'RE:'):
			n = t.split(u':',1)[1].strip()
			return [(u'R'+n, fntText)]
		# 돗수 DE:18°Ari / DE:18Ari / DE:18♈ 등
		if t.startswith(u'DE:'):
			val = t.split(u':',1)[1].strip()
			# 별자리 기호 → 약어
			for ab, glyph in ZODIAC_GLYPH.items():
				if glyph in val:
					val = val.replace(glyph, ab)
			# 공백/도기호 제거 후 "숫자+약어" 파싱
			v = val.replace(u'°', u'').replace(u' ', u'')
			m = re.match(u'^(\d{1,2})([A-Za-z]{3})$', v, re.U)
			if m:
				deg = int(m.group(1)) % 30
				ab  = m.group(2).title()
				si  = SIGN_INDEX.get(ab, 0)
				glyph = ZODIAC_GLYPH.get(ab, u'?')
				return [(u'%d\u00b0' % deg, fntText), (glyph, fntSymbol)]
			# 실패 시 원문 출력
			return [(val, fntText)]
		# 행성 코드 → 심볼 (소/대문자 섞여 들어와도 처리)
		if tu in PLANET_GLYPH:
			return [(PLANET_GLYPH[tu], fntSymbol)]
		# 각(AC/DC/MC/IC)은 일반 텍스트
		if tu in (u'AC', u'DC', u'MC', u'IC'):
			return [(tu, fntText)]

		# 기타 평문
		return [(t, fntText)]

	# 최후: 문자열화
	try:
		unicode
	except NameError:
		unicode = str
	return [(_to_unicode(tok), fntText)]

def _draw_formula(draw, x, y, cellw, A, B, C, swapBC, fntText, fntSymbol, signs, txtclr, line_h):
	if swapBC:
		B, C = C, B
	s = u"%s + %s - %s" % (
		_fmt_token_for_view(A),
		_fmt_token_for_view(B),
		_fmt_token_for_view(C),
	)
	w, h = draw.textsize(s, fntText)
	draw.text((x + (cellw - w)/2.0, y + (line_h - h)/2.0), s, fill=txtclr, font=fntText)

def _fmt_token_for_view(tok):
	try:
		integer_types = (int, long)
	except NameError:
		integer_types = (int,)
	if isinstance(tok, integer_types):
		return mtexts.partstxts[tok]
	if isinstance(tok, basestring):
		t = tok.strip()
		if t.upper().startswith('DE:'):
			val = t.split(':',1)[1].strip()
			# 기호 → 약어
			GLYPH_TO_ABBR = {
				u'♈':'Ari', u'♉':'Tau', u'♊':'Gem', u'♋':'Can', u'♌':'Leo', u'♍':'Vir',
				u'♎':'Lib', u'♏':'Sco', u'♐':'Sag', u'♑':'Cap', u'♒':'Aqu', u'♓':'Pis'
			}
			for g, ab in GLYPH_TO_ABBR.items():
				val = val.replace(g, ab)
			val = val.replace(u'°', u'').replace(u' ', u'')
			# 숫자+약어 3자
			i = 0
			while i < len(val) and val[i].isdigit():
				i += 1
			num = val[:i]
			ab  = val[i:i+3].title()
			try:
				deg = int(num) % 30
				return u'%d\u00b0%s' % (deg, ab)
			except:
				return _to_unicode(t)
		if t.upper().startswith('RE:'):
			return u'R' + t.split(':',1)[1].strip()
		return _to_unicode(t)
	return _to_unicode(tok) if isinstance(tok, basestring) else unicode(tok)

DEG_SYM = u'\u00b0'

def fmt_decl_deg(val):
	"""Declination 실수값(도)을 +DD°MM'SS" 형태의 문자열로 변환"""
	try:
		x = float(val)
	except:
		return u""
	sign = u"-" if x < 0 else u"+"
	d, m, s = util.decToDeg(abs(x))
	return u"%s%d%s%02d'%02d\"" % (sign, d, DEG_SYM, m, s)

def _get_jd_ut(chart):
	# chart 또는 chart.time에서 JD(UT) 찾기. 없으면 None.
	for attr in ('jd_ut', 'jd', 'jdut'):
		if hasattr(chart, attr):
			return getattr(chart, attr)
	if hasattr(chart, 'time'):
		for attr in ('jd_ut', 'jd', 'jdut'):
			if hasattr(chart.time, attr):
				return getattr(chart.time, attr)
	return None

def _mean_obliquity_deg_from_jd_ut(jd_ut):
	"""
	JD(UT)로부터 평균 황도경사(ε_mean, deg) 계산.
	TT로 바꾸지 않고 UT를 바로 쓰지만, 오차는 극소(호초 단위)라 Declination에 미치는 영향도 미미.
	Laskar(1986)/Meeus 계열 근사식.
	"""
	# J2000.0 기준 세기수 (UT 기준 근사)
	T = (jd_ut - 2451545.0) / 36525.0
	# 초 단위
	eps0_arcsec = (84381.448
				   - 46.8150*T
				   - 0.00059*(T**2)
				   + 0.001813*(T**3))
	return eps0_arcsec / 3600.0  # deg

def _true_obliquity_deg_best_effort(jd_ut):
	"""
	가능한 경우엔 swe에서 진경사(ε_true)를 얻고,
	안 되면 평균경사 + (가능하면) nutation in obliquity(Δε)를 더하는 방법으로 근사.
	swe API가 버전에 따라 다르므로 단계적으로 시도.
	"""
	# 1) calc_ut(..., SE_ECL_NUT) 경로 (일부 버전만 존재)
	if hasattr(swe, 'SE_ECL_NUT'):
		try:
			ret = swe.calc_ut(jd_ut, swe.SE_ECL_NUT, 0)  # ret[0] = ε_true (deg) 인 버전들이 있음
			if ret and isinstance(ret, (list, tuple)) and len(ret) > 0:
				return float(ret[0])
		except Exception:
			pass

	# 2) obl_ecl + nutation 경로 (다른 일부 버전)
	if hasattr(swe, 'obl_ecl') and hasattr(swe, 'nutation'):
		try:
			eps_mean = swe.obl_ecl(jd_ut)[0]   # deg
			dpsi, deps = swe.nutation(jd_ut)   # deg (Δψ, Δε)
			return eps_mean + deps
		except Exception:
			pass

	# 3) 최후: 수식으로 평균경사 계산 (+ 가능하면 Δε 더함)
	eps_mean = _mean_obliquity_deg_from_jd_ut(jd_ut)
	if hasattr(swe, 'nutation'):
		try:
			dpsi, deps = swe.nutation(jd_ut)  # deg
			return eps_mean + deps
		except Exception:
			pass
	return eps_mean  # Δε도 못 얻으면 평균경사로

def _decl_from_longitude_zero_lat(lon_deg, jd_ut):
	"""
	황위=0° 가정. JD 필수.
	ε_true(가능하면)를 얻어 δ = asin( sin ε * sin λ ) 로 계산.
	"""
	if jd_ut is None:
		return None
	eps_deg = _true_obliquity_deg_best_effort(jd_ut)
	lam = math.radians(lon_deg)
	eps = math.radians(eps_deg)
	# β=0 → δ = asin( sin ε * sin λ )
	return math.degrees(math.asin(math.sin(eps) * math.sin(lam)))

def _dodecatemorion_long(lon_deg):
	"""
	12분할(도데카테모리온) 경도 계산.
	규칙: 같은 별자리(sign) 안에서 오프셋(0~30°)을 12배 → sign 시작점에 더함.
	λ' = sign*30° + 12*(λ - sign*30°)
	"""
	sign = int(lon_deg / 30.0)           # 0~11
	offset = lon_deg - sign * 30.0       # 0~30
	newlon = sign * 30.0 + 12.0 * offset
	return util.normalize(newlon)


class ArabicPartsWnd(commonwnd.CommonWnd):
	def _col_edges(self, x0):
		"""x0에서 시작하는 각 칼럼의 왼쪽 x좌표들과 마지막 오른쪽 경계 x좌표를 돌려줌"""
		xs = [x0]
		for w in self.COLWIDTHS:
			xs.append(xs[-1] + w)
		return xs  # 길이 = 칼럼수 + 1
	def drawDegWinner(self, draw, x, y, line_index, onlyone, degwinner, txtclr, cellw):
		# 원본 810 로직을 셀폭 매개변수로만 일반화
		aux = [[-1,-1,-1], [-1,-1,-1], [-1,-1,-1]]  # planetid, score, width
		subnum = len(degwinner[0])
		mwidth = 0
		for j in range(subnum):
			pid = degwinner[line_index][j][0]
			if pid != -1:
				pltxt = common.common.Planets[pid]
				wpl,hpl = draw.textsize(pltxt, self.fntMorinus)
				sco = degwinner[line_index][0][1]
				txt = u'(' + str(sco) + u')'
				w,h = draw.textsize(txt, self.fntText)
				wsp,hsp = draw.textsize(u' ', self.fntText)
				aux[j][0] = pid
				aux[j][1] = sco
				aux[j][2] = wpl + wsp + w
				if mwidth != 0:
					mwidth += wsp
				mwidth += wpl + wsp + w
			else:
				break

		for j in range(subnum):
			if aux[j][0] != -1:
				if self.bw:
					clr = (0,0,0)
				else:
					if self.options.useplanetcolors:
						clr = self.options.clrindividual[aux[j][0]]
					else:
						dign = self.chart.dignity(aux[j][0])
						clr = self.clrs[dign]
				pltxt = common.common.Planets[aux[j][0]]
				wpl,hpl = draw.textsize(pltxt, self.fntMorinus)
				txt = u'(' + str(aux[j][1]) + u')'
				wsp,hsp = draw.textsize(u' ', self.fntText)
				w,h = draw.textsize(txt, self.fntText)

				prev = 0
				for p in range(j):
					prev += aux[p][2] + wsp

				offs = line_index
				if onlyone:
					offs = 0

				draw.text((x + (cellw - mwidth)/2 + prev,
						y + offs*self.LINE_HEIGHT + (self.LINE_HEIGHT - h)/2),
						pltxt, fill=clr, font=self.fntMorinus)
				draw.text((x + (cellw - mwidth)/2 + prev + wpl + wsp,
						y + offs*self.LINE_HEIGHT + (self.LINE_HEIGHT - h)/2),
						txt, fill=txtclr, font=self.fntText)

	def drawDegWinner2(self, draw, x, y, degwinner, txtclr, cellw):
		aux = [[-1,-1,-1], [-1,-1,-1], [-1,-1,-1]]
		subnum = len(degwinner)
		mwidth = 0
		for j in range(subnum):
			pid = degwinner[j][0]
			if pid != -1:
				pltxt = common.common.Planets[pid]
				wpl,hpl = draw.textsize(pltxt, self.fntMorinus)
				sco = degwinner[0][1]
				txt = u'(' + str(sco) + u')'
				w,h = draw.textsize(txt, self.fntText)
				wsp,hsp = draw.textsize(u' ', self.fntText)
				aux[j][0] = pid
				aux[j][1] = sco
				aux[j][2] = wpl + wsp + w
				if mwidth != 0:
					mwidth += wsp
				mwidth += wpl + wsp + w
			else:
				break

		for j in range(subnum):
			if aux[j][0] != -1:
				if self.bw:
					clr = (0,0,0)
				else:
					if self.options.useplanetcolors:
						clr = self.options.clrindividual[aux[j][0]]
					else:
						dign = self.chart.dignity(aux[j][0])
						clr = self.clrs[dign]
				pltxt = common.common.Planets[aux[j][0]]
				wpl,hpl = draw.textsize(pltxt, self.fntMorinus)
				txt = u'(' + str(aux[j][1]) + u')'
				wsp,hsp = draw.textsize(u' ', self.fntText)
				w,h = draw.textsize(txt, self.fntText)
				prev = 0
				for p in range(j):
					prev += aux[p][2] + wsp

				draw.text((x + (cellw - mwidth)/2 + prev,
						y + (self.LINE_HEIGHT - h)/2),
						pltxt, fill=clr, font=self.fntMorinus)
				draw.text((x + (cellw - mwidth)/2 + prev + wpl + wsp,
						y + (self.LINE_HEIGHT - h)/2),
						txt, fill=txtclr, font=self.fntText)

	def _draw_col_grid(self, draw, x0, y0, height, color):
		"""세로 경계선들을 모두 그림"""
		xs = self._col_edges(x0)
		for xx in xs:
			draw.line((xx, y0, xx, y0 + height), fill=color)

	def __init__(self, parent, chrt, options, mainfr, id = -1, size = wx.DefaultSize):
		commonwnd.CommonWnd.__init__(self, parent, chrt, options, id, size)
		_ensure_re_de_tokens()
		self.mainfr = mainfr

		self.FONT_SIZE = int(21*self.options.tablesize) #Change fontsize to change the size of the table!
		self.SPACE = self.FONT_SIZE/2
		self.LINE_HEIGHT = (self.SPACE+self.FONT_SIZE+self.SPACE)
		lengthparts = 0
		if chrt.parts.parts != None:
			lengthparts = len(chrt.parts.parts)
		self.LINE_NUM = 1+lengthparts

		self.CELL_WIDTH  = 12*self.FONT_SIZE
		self.TITLE_HEIGHT = self.LINE_HEIGHT

		# 칼럼 폭: [Ref 1/4폭, Name, Formula, Longitude, Dodecatemorion, Declination, Almuten]
		self.COLWIDTHS   = [self.CELL_WIDTH//3, self.CELL_WIDTH, self.CELL_WIDTH,
							self.CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH]
		self.COLUMN_NUM  = len(self.COLWIDTHS)

		self.SPACE_TITLEY = 0
		self.TITLE_WIDTH  = sum(self.COLWIDTHS)   # ← 합계로 계산해야 오른쪽 경계가 정확히 닫힘
		self.TABLE_WIDTH  = self.TITLE_WIDTH
		self.TABLE_HEIGHT = (self.TITLE_HEIGHT + self.SPACE_TITLEY + (self.LINE_NUM)*(self.LINE_HEIGHT))
	
		self.WIDTH = int(commonwnd.CommonWnd.BORDER+self.TABLE_WIDTH+commonwnd.CommonWnd.BORDER)
		self.HEIGHT = int(commonwnd.CommonWnd.BORDER+self.TABLE_HEIGHT+commonwnd.CommonWnd.BORDER)

		self.SetVirtualSize((self.WIDTH, self.HEIGHT))

		self.fntMorinus = ImageFont.truetype(common.common.symbols, self.FONT_SIZE)
		self.fntText = ImageFont.truetype(common.common.abc, self.FONT_SIZE)
		self.signs = common.common.Signs1
		if not self.options.signs:
			self.signs = common.common.Signs2
		self.clrs = (self.options.clrdomicil, self.options.clrexal, self.options.clrperegrin, self.options.clrcasus, self.options.clrexil)	
		self.deg_symbol = u'\u00b0'

		self.drawBkg()
		# 공통 칼럼 인덱스
		self.COL_REF, self.COL_NAME, self.COL_FORM, self.COL_LONG, self.COL_DODEC, self.COL_DECL, self.COL_ALM = 0,1,2,3,4,5,6

	def getExt(self):
		return mtexts.txts['Ara']

	def drawBkg(self):
		if self.bw:
			self.bkgclr = (255,255,255)
		else:
			self.bkgclr = self.options.clrbackground

		self.SetBackgroundColour(self.bkgclr)

		tableclr = self.options.clrtable
		if self.bw:
			tableclr = (0,0,0)

		img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.bkgclr)
		draw = ImageDraw.Draw(img)

		BOR = commonwnd.CommonWnd.BORDER

		txtclr = (0,0,0)
		if not self.bw:
			txtclr = self.options.clrtexts

		# Title
		draw.rectangle(((BOR, BOR), (BOR + self.TITLE_WIDTH, BOR + self.TITLE_HEIGHT)),
					   outline=tableclr, fill=self.bkgclr)

		headers = (u"#", mtexts.txts['Name'], mtexts.txts['Formula'], mtexts.txts['Longitude'],
				mtexts.txts['Dodecatemorion'], mtexts.txts['Declination'], mtexts.txts['Almuten'])

		xcol = BOR
		for i, head in enumerate(headers):
			cellw = self.COLWIDTHS[i]
			tw, th = draw.textsize(head, self.fntText)
			draw.text((xcol + (cellw - tw)/2.0, BOR + (self.TITLE_HEIGHT - th)/2.0),
					  head, fill=txtclr, font=self.fntText)

			xcol += cellw


		#Parts
		x = BOR
		y = BOR+self.TITLE_HEIGHT+self.SPACE_TITLEY
		self.drawlinelof(draw, x, y, mtexts.txts['LotOfFortune'], self.chart.fortune.fortune, tableclr)

		if self.chart.parts.parts != None:
			num = len(self.chart.parts.parts)
			x = BOR
			for i in range(num):
				y = BOR+self.TITLE_HEIGHT+self.SPACE_TITLEY+(self.LINE_HEIGHT)*(i+1)
				self.drawline(draw, x, y, self.chart.parts.parts, tableclr, i)

		wxImg = wx.Image(img.size[0], img.size[1])
		wxImg.SetData(img.tobytes())
		self.buffer = wx.Bitmap(wxImg)

	def drawlinelof(self, draw, x, y, name, data, clr):
		#bottom horizontal line
		draw.line((x, y+self.LINE_HEIGHT, x+self.TABLE_WIDTH, y+self.LINE_HEIGHT), fill=clr)

			# 수직선/그리드 준비
		xs = self._col_edges(x)  # 각 칼럼의 왼쪽 x 좌표들 + 마지막 오른쪽 경계
		self._draw_col_grid(draw, x, y, self.LINE_HEIGHT, clr)

		txtclr = (0,0,0) if self.bw else self.options.clrtexts

		# Ref: R0(LoF)
		COL_REF, COL_NAME, COL_FORM, COL_LONG, COL_DODEC, COL_DECL = 0, 1, 2, 3, 4, 5
		ref = u'R0'
		tw, th = draw.textsize(ref, self.fntText)
		draw.text((xs[COL_REF] + (self.COLWIDTHS[COL_REF]-tw)/2.0,
				   y + (self.LINE_HEIGHT-th)/2.0),
				  ref, fill=txtclr, font=self.fntText)

		# Name
		cellw = self.COLWIDTHS[COL_NAME]
		w,h = draw.textsize(name, self.fntText)
		draw.text((xs[COL_NAME] + (cellw - w)/2.0, y + (self.LINE_HEIGHT - h)/2.0), name, fill=txtclr, font=self.fntText)

		# Formula (LoF는 AC + (MO/SU) - (SU/MO), 타입/주야 반영)
		above = self.chart.planets.planets[astrology.SE_SUN].abovehorizon
		typ = self.options.lotoffortune
		A = u'AC'
		if typ == chart.Chart.LFMOONSUN:
			B, C = u'MO', u'SU'; swapBC = False
		elif typ == chart.Chart.LFDMOONSUN:
			B, C = u'MO', u'SU'; swapBC = (not above)
		else:
			B, C = u'SU', u'MO'; swapBC = (not above)

		_draw_formula(draw, xs[COL_FORM], y, self.COLWIDTHS[COL_FORM], A, B, C, swapBC, self.fntText, self.fntMorinus, self.signs, txtclr, self.LINE_HEIGHT)

		# Longitude (LoF 경도)
		lon = data[0]  # Fortune.LON
		if self.options.ayanamsha != 0:
			lon = util.normalize(lon - self.chart.ayanamsha)
		d, m, s = util.decToDeg(lon)
		sign = int(d / chart.Chart.SIGN_DEG)
		pos  = d % chart.Chart.SIGN_DEG
		wsp,_ = draw.textsize(' ', self.fntText)
		txtsign = self.signs[sign]
		wsg,_  = draw.textsize(txtsign, self.fntMorinus)
		txt = (str(pos)).rjust(2) + self.deg_symbol + (str(m)).zfill(2) + "'" + (str(s)).zfill(2) + '"'
		w,h = draw.textsize(txt, self.fntText)
		offset = (self.COLWIDTHS[COL_LONG] - (w + wsp + wsg)) / 2.0
		draw.text((xs[COL_LONG] + offset, y + (self.LINE_HEIGHT - h)/2.0), txt, fill=txtclr, font=self.fntText)
		draw.text((xs[COL_LONG] + offset + w + wsp, y + (self.LINE_HEIGHT - h)/2.0), txtsign, fill=txtclr, font=self.fntMorinus)

		# Dodecatemorion
		dodec_lon = _dodecatemorion_long(lon)
		d, m, s = util.decToDeg(dodec_lon)
		sign = int(d / chart.Chart.SIGN_DEG)
		pos  = d % chart.Chart.SIGN_DEG
		txtsign = self.signs[sign]
		wsg,_  = draw.textsize(txtsign, self.fntMorinus)
		txt = (str(pos)).rjust(2) + self.deg_symbol + (str(m)).zfill(2) + "'" + (str(s)).zfill(2) + '"'
		w,h = draw.textsize(txt, self.fntText)
		offset = (self.COLWIDTHS[COL_DODEC] - (w + wsp + wsg)) / 2.0
		draw.text((xs[COL_DODEC] + offset, y + (self.LINE_HEIGHT - h)/2.0), txt, fill=txtclr, font=self.fntText)
		draw.text((xs[COL_DODEC] + offset + w + wsp, y + (self.LINE_HEIGHT - h)/2.0), txtsign, fill=txtclr, font=self.fntMorinus)

		# Declination (β=0 가정)
		jd_ut = _get_jd_ut(self.chart)
		dec = _decl_from_longitude_zero_lat(lon, jd_ut)
		if dec is not None:
			txt = fmt_decl_deg(dec)
			w,h = draw.textsize(txt, self.fntText)
			draw.text((xs[COL_DECL] + (self.COLWIDTHS[COL_DECL]-w)/2.0, y + (self.LINE_HEIGHT-h)/2.0), txt, fill=txtclr, font=self.fntText)
		# Almuten (원본 규칙과 동일: essentials.degwinner에서 line_index=3 사용)
		COL_REF, COL_NAME, COL_FORM, COL_LONG, COL_DODEC, COL_DECL, COL_ALM = 0,1,2,3,4,5,6
		degwinner = getattr(self.chart.almutens.essentials, 'degwinner', None)
		if degwinner:
			self.drawDegWinner(draw,
							xs[COL_ALM], y,
							3, True, degwinner, txtclr,
							self.COLWIDTHS[COL_ALM])

	def _deg_to_text(self, absdeg):
		try:
			absdeg = int(absdeg) % 360
		except:
			return u'?'
		signs = [u'Ari',u'Tau',u'Gem',u'Can',u'Leo',u'Vir',u'Lib',u'Sco',u'Sag',u'Cap',u'Aqu',u'Pis']
		sg = absdeg // 30
		dg = absdeg % 30
		return u'%d\u00B0%s' % (dg, signs[sg])

	def _render_formula_with_refs(self, part, opts):
		# part는 계산된 1개 랏 레코드이고, 옵션의 정의로부터 (f1,f2,f3)와 (refA,refB,refC)를 꺼낸다.
		try:
			name = part[arabicparts.ArabicParts.NAME]  # 네 파일 상수명에 맞춰 조정
		except:
			name = u'?'

		# 옵션에서 원 정의 찾기
		src = None
		for it in self.options.arabicparts:
			if it[0] == name:
				src = it
				break
		if not src:
			return u'?'

		f1,f2,f3 = src[1]
		refA,refB,refC = (0,0,0)
		try:
			t = src[3]
			if isinstance(t, (list,tuple)) and len(t)==3:
				refA,refB,refC = t
		except: pass

		# === 여기부터 추가 ===
		# Diurnal 플래그: 옵션 정의(src[2])가 우선, 없으면 part 레코드에서 시도
		diur = False
		try:
			diur = bool(src[2])
		except:
			try:
				diur = bool(part[arabicparts.ArabicParts.DIURNAL])
			except:
				diur = False

		# 야간차트 여부 (태양이 지평선 아래)
		try:
			above = self.chart.planets.planets[astrology.SE_SUN].abovehorizon
		except:
			above = True  # 안전값

		# 밤차트 + Diurnal이면 계산과 동일하게 B/C를 스왑해 표기
		if diur and (not above):
			f2, f3 = f3, f2
			refB, refC = refC, refB
		# === 추가 끝 ===
		def tok(code, idx):
			# code 가 partstxts "인덱스"일 수도, conv "상수값"일 수도 있음
			label = None
			try:
				label = mtexts.partstxts[code]  # 인덱스 경로
			except Exception:
				# 상수값 경로: 역매핑 캐시에서 찾기
				rev = getattr(mtexts, '_conv_rev_cache', None)
				if not isinstance(rev, dict):
					try:
						rev = dict((v, k) for (k, v) in mtexts.conv.items())
					except Exception:
						rev = {}
					mtexts._conv_rev_cache = rev
				label = rev.get(code)
				if label is None:
					# 캐시가 오래됐을 수 있으니 즉시 재구축 후 한 번 더
					try:
						rev = dict((v, k) for (k, v) in mtexts.conv.items())
					except Exception:
						rev = {}
					mtexts._conv_rev_cache = rev
					label = rev.get(code, u'?')

			txt = label
			want_lord = False
			if txt.endswith(u'!'):
				want_lord = True
				txt = txt[:-1]

			if txt == mtexts.txts['DE']:
				out = self._deg_to_text((refA, refB, refC)[idx])
				return out + (u'!' if want_lord else u'')
			if txt == mtexts.txts['RE']:
				rn = int((refA, refB, refC)[idx])
				if rn == 0:
					return u'R0' + (u'!' if want_lord else u'')
				return (u'R%d' % rn) + (u'!' if want_lord else u'')

			return label

		return u'%s + %s - %s' % (tok(f1,0), tok(f2,1), tok(f3,2))

	def drawline(self, draw, x, y, data, clr, idx):
		#bottom horizontal line
		draw.line((x, y+self.LINE_HEIGHT, x+self.TABLE_WIDTH, y+self.LINE_HEIGHT), fill=clr)
		# 수직선/그리드
		xs = self._col_edges(x)
		self._draw_col_grid(draw, x, y, self.LINE_HEIGHT, clr)
		txtclr = (0,0,0) if self.bw else self.options.clrtexts

		# [중요] 칼럼 인덱스: Ref 포함 6칸
		COL_REF, COL_NAME, COL_FORM, COL_LONG, COL_DODEC, COL_DECL = 0, 1, 2, 3, 4, 5

		# Ref: R{idx+1}
		ref = u'R%d' % (idx+1)
		tw, th = draw.textsize(ref, self.fntText)
		draw.text((xs[COL_REF] + (self.COLWIDTHS[COL_REF]-tw)/2.0, y + (self.LINE_HEIGHT-th)/2.0), ref, fill=txtclr, font=self.fntText)

		# Name
		name = data[idx][arabicparts.ArabicParts.NAME]
		w, h = draw.textsize(name, self.fntText)
		draw.text((xs[COL_NAME] + (self.COLWIDTHS[COL_NAME]-w)/2.0, y + (self.LINE_HEIGHT-h)/2.0), name, fill=txtclr, font=self.fntText)

		w,h = draw.textsize(name, self.fntText)
		draw.text((xs[COL_NAME] + (self.COLWIDTHS[COL_NAME]-w)/2.0, y + (self.LINE_HEIGHT-h)/2.0), name, fill=txtclr, font=self.fntText)

		# Formula ─ RE/DE 실제값으로 렌더
		formula = self._render_formula_with_refs(data[idx], self.options)
		tw, th = draw.textsize(formula, self.fntText)
		draw.text((xs[COL_FORM] + (self.COLWIDTHS[COL_FORM]-tw)/2.0, y + (self.LINE_HEIGHT-th)/2.0), formula, fill=txtclr, font=self.fntText)

		# Longitude
		lon = data[idx][arabicparts.ArabicParts.LONG]
		if self.options.ayanamsha != 0:
			lon = util.normalize(lon - self.chart.ayanamsha)
		d, m, s = util.decToDeg(lon)
		sign = int(d / chart.Chart.SIGN_DEG)
		pos  = d % chart.Chart.SIGN_DEG
		wsp,_ = draw.textsize(' ', self.fntText)
		txtsign = self.signs[sign]
		wsg,_  = draw.textsize(txtsign, self.fntMorinus)
		txt = (str(pos)).rjust(2) + self.deg_symbol + (str(m)).zfill(2) + "'" + (str(s)).zfill(2) + '"'
		w,h = draw.textsize(txt, self.fntText)
		offset = (self.COLWIDTHS[COL_LONG] - (w + wsp + wsg)) / 2.0
		draw.text((xs[COL_LONG] + offset, y + (self.LINE_HEIGHT - h)/2.0), txt, fill=txtclr, font=self.fntText)
		draw.text((xs[COL_LONG] + offset + w + wsp, y + (self.LINE_HEIGHT - h)/2.0), txtsign, fill=txtclr, font=self.fntMorinus)

		# Dodecatemorion
		dodec_lon = _dodecatemorion_long(lon)
		d, m, s = util.decToDeg(dodec_lon)
		sign = int(d / chart.Chart.SIGN_DEG)
		pos  = d % chart.Chart.SIGN_DEG
		txtsign = self.signs[sign]
		wsg,_  = draw.textsize(txtsign, self.fntMorinus)
		txt = (str(pos)).rjust(2) + self.deg_symbol + (str(m)).zfill(2) + "'" + (str(s)).zfill(2) + '"'
		w,h = draw.textsize(txt, self.fntText)
		offset = (self.COLWIDTHS[COL_DODEC] - (w + wsp + wsg)) / 2.0
		draw.text((xs[COL_DODEC] + offset, y + (self.LINE_HEIGHT - h)/2.0), txt, fill=txtclr, font=self.fntText)
		draw.text((xs[COL_DODEC] + offset + w + wsp, y + (self.LINE_HEIGHT - h)/2.0), txtsign, fill=txtclr, font=self.fntMorinus)

		# Declination
		jd_ut = _get_jd_ut(self.chart)
		dec = _decl_from_longitude_zero_lat(lon, jd_ut)
		if dec is not None:
			txt = fmt_decl_deg(dec)
			w,h = draw.textsize(txt, self.fntText)
			draw.text((xs[COL_DECL] + (self.COLWIDTHS[COL_DECL]-w)/2.0, y + (self.LINE_HEIGHT-h)/2.0), txt, fill=txtclr, font=self.fntText)
		# Almuten (각 파츠별 DEGWINNER 필드 사용)
		COL_REF, COL_NAME, COL_FORM, COL_LONG, COL_DODEC, COL_DECL, COL_ALM = 0,1,2,3,4,5,6
		try:
			degw = data[idx][arabicparts.ArabicParts.DEGWINNER]
		except Exception:
			degw = None
		if degw:
			self.drawDegWinner2(draw,
								xs[COL_ALM], y,
								degw, txtclr,
								self.COLWIDTHS[COL_ALM])