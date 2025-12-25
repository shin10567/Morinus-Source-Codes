# -*- coding: utf-8 -*-
import wx
import os
import chart
import common
import commonwnd
import Image, ImageDraw, ImageFont
import fixstars
import util
import mtexts
import astrology


class FixStarsWnd(commonwnd.CommonWnd):

	def __init__(self, parent, chrt, options, mainfr, id = -1, size = wx.DefaultSize):
		commonwnd.CommonWnd.__init__(self, parent, chrt, options, id, size)

		self.mainfr = mainfr

		self.FONT_SIZE = int(21*self.options.tablesize) #Change fontsize to change the size of the table!
		self.SPACE = self.FONT_SIZE/2
		self.LINE_HEIGHT = (self.SPACE+self.FONT_SIZE+self.SPACE)
		self.LINE_NUM = len(self.chart.fixstars.data)
		self.SMALL_CELL_WIDTH = 3*self.FONT_SIZE
		self.BIG_CELL_WIDTH = 10*self.FONT_SIZE
		self.CELL_WIDTH = 8*self.FONT_SIZE
		self.MAG_CELL_WIDTH = self.SMALL_CELL_WIDTH

		self.COLUMN_NUM = 7
		self.TITLE_HEIGHT = self.LINE_HEIGHT
		self.TITLE_WIDTH = self.BIG_CELL_WIDTH + (self.COLUMN_NUM-2)*self.CELL_WIDTH + self.MAG_CELL_WIDTH

		self.SPACE_TITLEY = 0
		self.TABLE_HEIGHT = (self.TITLE_HEIGHT+self.SPACE_TITLEY+(self.LINE_NUM)*(self.LINE_HEIGHT))
		self.TABLE_WIDTH = (self.SMALL_CELL_WIDTH + self.BIG_CELL_WIDTH + (self.COLUMN_NUM-2)*self.CELL_WIDTH + self.MAG_CELL_WIDTH)
		self.WIDTH = int(commonwnd.CommonWnd.BORDER+self.TABLE_WIDTH+commonwnd.CommonWnd.BORDER)
		self.HEIGHT = int(commonwnd.CommonWnd.BORDER+self.TABLE_HEIGHT+commonwnd.CommonWnd.BORDER)

		self.SetVirtualSize((self.WIDTH, self.HEIGHT))

		self.fntMorinus = ImageFont.truetype(common.common.symbols, self.FONT_SIZE)
		self.fntText = ImageFont.truetype(common.common.abc, self.FONT_SIZE)
		self.signs = common.common.Signs1
		if not self.options.signs:
			self.signs = common.common.Signs2
		self.deg_symbol = u'\u00b0'

		# (추가) fixed stars apparent magnitude(Vmag) 캐시
		self._mag_cache = {}
		self._mags = self._buildMagnitudes()

		self.drawBkg()



	def getExt(self):
		return mtexts.txts['Fix']


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

		#Title
		draw.rectangle(((BOR+self.SMALL_CELL_WIDTH, BOR),(BOR+self.SMALL_CELL_WIDTH+self.TITLE_WIDTH, BOR+self.TITLE_HEIGHT)), outline=(tableclr), fill=(self.bkgclr))
		txt = (mtexts.txts['Name'], mtexts.txts['Nomencl'], mtexts.txts['MagAbbr'], mtexts.txts['Longitude'], mtexts.txts['Latitude'], mtexts.txts['Rectascension'], mtexts.txts['Declination'])

		summa = 0
		offs = (self.BIG_CELL_WIDTH, self.CELL_WIDTH, self.MAG_CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH)
		for i in range(len(txt)):
			w,h = draw.textsize(txt[i], self.fntText)
			draw.text((BOR+self.SMALL_CELL_WIDTH+summa+(offs[i]-w)/2, BOR+(self.TITLE_HEIGHT-h)/2), txt[i], fill=txtclr, font=self.fntText)
			summa += offs[i]

		x = BOR
		y = BOR+self.TITLE_HEIGHT+self.SPACE_TITLEY
		draw.line((x, y, x+self.TABLE_WIDTH, y), fill=tableclr)

		for i in range(len(self.chart.fixstars.data)):
			self.drawline(draw, x, y+i*self.LINE_HEIGHT, tableclr, i)

		wxImg = wx.Image(img.size[0], img.size[1])
		wxImg.SetData(img.tobytes())
		self.buffer = wx.Bitmap(wxImg)


	def drawline(self, draw, x, y, clr, idx):
		#bottom horizontal line
		draw.line((x, y+self.LINE_HEIGHT, x+self.TABLE_WIDTH, y+self.LINE_HEIGHT), fill=clr)

		#vertical lines
		# (추가) Mag. 칼럼 1개가 더 들어가므로 CELL_WIDTH 1개 추가
		offs = (0, self.SMALL_CELL_WIDTH, self.BIG_CELL_WIDTH, self.CELL_WIDTH, self.MAG_CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH, self.CELL_WIDTH)

		OFFS = 2
		BOR = commonwnd.CommonWnd.BORDER
		summa = 0
		txtclr = (0,0,0)
		if not self.bw:
			txtclr = self.options.clrtexts

		for i in range(self.COLUMN_NUM+OFFS):#+1 is the leftmost column
			draw.line((x+summa+offs[i], y, x+summa+offs[i], y+self.LINE_HEIGHT), fill=clr)

			d, m, s = 0, 0, 0
			# Mag. 칼럼이 추가되어 LON 이후 칼럼들의 표시 인덱스가 +1 이동
			if i >= fixstars.FixStars.LON+OFFS+1:
				datai = i-OFFS-1
				d,m,s = util.decToDeg(self.chart.fixstars.data[idx][datai])

			if i == 1:
				txt = str(idx+1)+'.'
				w,h = draw.textsize(txt, self.fntText)
				draw.text((x+summa+(offs[i]-w)/2, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)

			elif i == fixstars.FixStars.NAME+OFFS:
				# Name 열은 코드→전역 선호이름으로 표기
				code = self.chart.fixstars.data[idx][fixstars.FixStars.NOMNAME]
				fallback = self.chart.fixstars.data[idx][fixstars.FixStars.NAME] or code
				txt = astrology.display_fixstar_name(code, self.options, fallback)
				w,h = draw.textsize(txt, self.fntText)
				draw.text((x+summa+(offs[i]-w)/2, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)

			elif i == fixstars.FixStars.NOMNAME+OFFS:
				# Nomencl 열은 식별 코드 그대로
				txt = self.chart.fixstars.data[idx][fixstars.FixStars.NOMNAME]
				w,h = draw.textsize(txt, self.fntText)
				draw.text((x+summa+(offs[i]-w)/2, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)

			elif i == fixstars.FixStars.NOMNAME+OFFS+1:
				# Mag. (겉보기등급, Vmag)
				mag = self._mags[idx] if idx < len(self._mags) else None
				txt = self._fmtMag(mag)
				w,h = draw.textsize(txt, self.fntText)
				draw.text((x+summa+(offs[i]-w)/2, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)

			elif i == fixstars.FixStars.LON+OFFS+1:
				lon = self.chart.fixstars.data[idx][fixstars.FixStars.LON]
				if self.options.ayanamsha != 0:
					lon = util.normalize(lon-self.chart.ayanamsha)

				d,m,s = util.decToDeg(lon)
				sign = int(d/chart.Chart.SIGN_DEG)
				pos = d%chart.Chart.SIGN_DEG
				wsp,hsp = draw.textsize(' ', self.fntText)
				txtsign = self.signs[sign]
				wsg,hsg = draw.textsize(txtsign, self.fntMorinus)
				txt = (str(pos)).rjust(2)+self.deg_symbol+(str(m)).zfill(2)+"'"+(str(s)).zfill(2)+'"'
				w,h = draw.textsize(txt, self.fntText)
				offset = (offs[i]-(w+wsp+wsg))/2
				draw.text((x+summa+offset, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)
				draw.text((x+summa+offset+w+wsp, y+(self.LINE_HEIGHT-h)/2), txtsign, fill=txtclr, font=self.fntMorinus)

			elif i == fixstars.FixStars.LAT+OFFS+1 or i == fixstars.FixStars.DECL+OFFS+1:
				datai = i-OFFS-1
				sign = ''
				if self.chart.fixstars.data[idx][datai] < 0.0:
					sign = '-'
				txt = sign+(str(d)).rjust(2)+self.deg_symbol+(str(m)).zfill(2)+"'"+(str(s)).zfill(2)+'"'
				w,h = draw.textsize(txt, self.fntText)
				draw.text((x+summa+(offs[i]-w)/2, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)

			elif i == fixstars.FixStars.RA+OFFS+1:
				txt = str(d)+self.deg_symbol+(str(m)).zfill(2)+"'"+(str(s)).zfill(2)+'"'
				if self.options.intime:
					d,m,s = util.decToDeg(self.chart.fixstars.data[idx][fixstars.FixStars.RA]/15.0)
					txt = (str(d)).rjust(2)+':'+(str(m)).zfill(2)+":"+(str(s)).zfill(2)
				w,h = draw.textsize(txt, self.fntText)
				draw.text((x+summa+(offs[i]-w)/2, y+(self.LINE_HEIGHT-h)/2), txt, fill=txtclr, font=self.fntText)

			summa += offs[i]


	def _buildMagnitudes(self):
		# 현재 표시 중인 fixed stars 순서에 맞춰 Vmag 리스트 생성
		mags = []
		try:
			data = self.chart.fixstars.data
		except Exception:
			data = []
		for row in data:
			code = None
			name = None
			try:
				code = row[fixstars.FixStars.NOMNAME]
			except Exception:
				code = None
			try:
				name = row[fixstars.FixStars.NAME]
			except Exception:
				name = None
			mags.append(self._getStarMag(code, name))
		return mags


	def _getStarMag(self, code, fallback_name=None):
		# Swiss Ephemeris magnitude lookup (cached)
		key = (code or fallback_name or '').strip()
		if not key:
			return None
		if key in self._mag_cache:
			return self._mag_cache[key]

		mag = None
		# code 우선, 실패 시 name로 재시도
		for sid in (code, fallback_name):
			if not sid:
				continue
			try:
				ret, st, mag_val, serr = astrology.swe_fixstar_mag(',' + sid)
			except Exception:
				continue
			try:
				if isinstance(mag_val, (list, tuple)):
					raw = mag_val[0] if len(mag_val) > 0 else None
				else:
					raw = mag_val
				if raw is None:
					continue
				cand = float(raw)
				# 겉보기등급 sanity range
				if -15.0 < cand < 20.0 and cand < 998.0:
					mag = cand
					break
			except Exception:
				continue

		self._mag_cache[key] = mag
		return mag


	def _fmtMag(self, mag):
		if mag is None:
			return ''
		try:
			v = float(mag)
			neg = (v < 0.0)
			v = abs(v)

			s = '{0:.2f}'.format(v)
			s = s.rstrip('0').rstrip('.')

			if not neg:
				return s

			# 다른 각도 표기 규칙과 동일: 한자리수는 '- ' (예: - 5, - 0.3)
			if v < 10.0:
				return '- ' + s
			return '-' + s
		except Exception:
			return ''
