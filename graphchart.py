# -*- coding: utf-8 -*-
import wx
import Image, ImageDraw, ImageFont
import math
import astrology
import chart, houses, planets, fortune
import fixstars
import options
import common
import util
import mtexts
import arabicparts
import fortune
import mtexts
import hours

class GraphChart:

	DEG1 = math.pi/180
	DEG5 = math.pi/36
	DEG10 = math.pi/18
	DEG30 = math.pi/6

	SMALL_SIZE = 400
	MEDIUM_SIZE = 600

	def __init__(self, chrt, size, opts, bw, planetaryday=True, chrt2 = None):
		self.chart = chrt
		self.chart2 = chrt2
		self.w, self.h = size
		self.options = opts
		self.bw = bw
		self.planetaryday = planetaryday
		self.buffer = wx.Bitmap(self.w, self.h)
		self.bdc = wx.BufferedDC(None, self.buffer)
		self.chartsize = min(self.w, self.h)
		self.maxradius = self.chartsize/2
		self.center = wx.Point(self.w/2, self.h/2)

		self.arrowlen = 0.04
		self.deg01510len = 0.01
		self.retrdiff = 0.01
		if self.chart2 == None:
			#if self.planetaryday and self.options.showfixstars != options.Options.NONE: #If planetaryday is True => radix chart
			if self.options.showfixstars != options.Options.NONE:
				self.symbolSize = self.maxradius/16
				self.signSize = self.maxradius/20
				self.planetsectorlen = 0.15
				self.signsectorlen = self.planetsectorlen
				self.signoffs = (self.signsectorlen/2.0)*self.maxradius
				self.planetoffs = (self.planetsectorlen/2.0)*self.maxradius
				self.planetlinelen = 0.03
				self.rHousesectorlen = 0.06
				self.rAntis = self.maxradius*0.90
				self.rAntisLines = self.maxradius*0.86
				self.rFixstars = self.maxradius*0.88#84
				self.r30 = self.maxradius*0.83

				self.rOuterLine = self.maxradius*0.86
				self.rOuter0 = self.r30
				self.rOuter1 = self.rOuter0-self.deg01510len*self.maxradius
				self.rOuter5 = self.rOuter1-self.deg01510len*self.maxradius
				self.rOuter10 = self.rOuter5-self.deg01510len*self.maxradius
				self.rOuterMin = self.maxradius*0.82
				self.rSign = self.r30-self.signoffs
				self.r0 = self.r30-self.signsectorlen*self.maxradius
				self.r1 = self.r0+self.deg01510len*self.maxradius
				self.r5 = self.r1+self.deg01510len*self.maxradius
				self.r10 = self.r5+self.deg01510len*self.maxradius
				self.rASCMC = self.rSign
				self.rArrow = self.rASCMC+self.arrowlen*self.maxradius

				self.rTerms = self.r0
				self.termssectorlen = 0.0
				if self.options.showterms:
					self.termssectorlen = 0.08
				self.termsoffs = (self.termssectorlen/2.0)*self.maxradius
				self.rTermsPlanet = self.r0-self.termsoffs#
				self.rDecans = self.rTerms-self.termssectorlen*self.maxradius
				self.decanssectorlen = 0.0
				if self.options.showdecans:
					self.decanssectorlen = 0.08
				self.decansoffs = (self.decanssectorlen/2.0)*self.maxradius
				self.rInner = self.rDecans-self.decanssectorlen*self.maxradius
				self.rDecansPlanet = self.rInner+self.decansoffs#

				self.rLLine = self.rInner-self.planetlinelen*self.maxradius #line between zodiacpos & planet
				self.rPlanet = self.rInner-self.planetoffs
				self.rAsp = self.rInner-self.planetsectorlen*self.maxradius
				self.rLLine2 = self.rAsp+self.planetlinelen*self.maxradius
				self.rRetr = self.rLLine2+self.maxradius*self.retrdiff

				pos = 0.48
				aspascmc = 0.43
				posascmc = 0.41
				poshouses = 0.32				
				if self.options.showdecans and self.options.showterms:
					pos = 0.32
					aspascmc = 0.28
					posascmc = 0.27
					poshouses = 0.21				
				elif self.options.showdecans or self.options.showterms:
					pos = 0.40
					aspascmc = 0.36
					posascmc = 0.34
					poshouses = 0.25				

				self.rPos = self.maxradius*pos
				self.rAspAscMC = self.maxradius*aspascmc
				self.rPosAscMC = self.maxradius*posascmc
				self.rPosHouses = self.maxradius*poshouses
				self.rBase = self.maxradius*0.11
				self.rHouse = self.rBase+self.rHousesectorlen*self.maxradius
				self.rHouseName = self.maxradius*0.14
			else:
				self.symbolSize = self.maxradius/12
				self.signSize = self.maxradius/12
				self.signsectorlen = 0.16
				self.planetsectorlen = 0.18
				self.planetoffs = (self.planetsectorlen/2.0)*self.maxradius
				self.planetlinelen = 0.03
				self.rHousesectorlen = 0.08
				self.r30 = self.maxradius*0.96
				self.signoffs = (self.signsectorlen/2.0-0.01)*self.maxradius
				self.rSign = self.r30-self.signoffs
				self.rASCMC = self.maxradius*0.88
				self.rArrow = self.rASCMC+self.arrowlen*self.maxradius
				self.r0 = self.r30-self.signsectorlen*self.maxradius
				self.r1 = self.r0+self.deg01510len*self.maxradius
				self.r5 = self.r1+self.deg01510len*self.maxradius
				self.r10 = self.r5+self.deg01510len*self.maxradius

				self.rTerms = self.r0
				self.termssectorlen = 0.0
				if self.options.showterms:
					self.termssectorlen = 0.08
				self.termsoffs = (self.termssectorlen/2.0)*self.maxradius
				self.rTermsPlanet = self.r0-self.termsoffs#
				self.rDecans = self.rTerms-self.termssectorlen*self.maxradius
				self.decanssectorlen = 0.0
				if self.options.showdecans:
					self.decanssectorlen = 0.08
				self.decansoffs = (self.decanssectorlen/2.0)*self.maxradius
				self.rInner = self.rDecans-self.decanssectorlen*self.maxradius
				self.rDecansPlanet = self.rInner+self.decansoffs#

				self.rLLine = self.rInner-self.planetlinelen*self.maxradius #line between zodiacpos & planet
				self.rPlanet = self.rInner-self.planetoffs
				self.rAsp = self.rInner-self.planetsectorlen*self.maxradius
				self.rLLine2 = self.rAsp+self.planetlinelen*self.maxradius
				self.rRetr = self.rLLine2+self.maxradius*self.retrdiff

				pos = 0.55
				aspascmc = 0.50
				posascmc = 0.50
				poshouses = 0.40				
				if self.options.showdecans and self.options.showterms:
					pos = 0.40
					aspascmc = 0.37
					posascmc = 0.35
					poshouses = 0.26				
				elif self.options.showdecans or self.options.showterms:
					pos = 0.48
					aspascmc = 0.45
					posascmc = 0.43
					poshouses = 0.33				

				self.rPos = self.maxradius*pos
				self.rAspAscMC = self.maxradius*aspascmc
				self.rPosAscMC = self.maxradius*posascmc
				self.rPosHouses = self.maxradius*poshouses
				self.rBase = self.maxradius*0.13
				self.rHouse = self.rBase+self.rHousesectorlen*self.maxradius
				self.rHouseName = self.rBase+(self.rHousesectorlen*self.maxradius)/2.0
		else:
			self.symbolSize = self.maxradius/16
			self.signSize = self.maxradius/20
			self.outerplanetsectorlen = 0.12
			self.planetsectorlen = 0.15
			self.signsectorlen = self.planetsectorlen
			self.signoffs = (self.signsectorlen/2.0)*self.maxradius
			self.planetoffs = (self.planetsectorlen/2.0)*self.maxradius
			self.planetlinelen = 0.03
			self.rHousesectorlen = 0.06
			self.rOuterMax = self.maxradius*0.97
			if self.options.houses:
				self.rOuterHouseName = self.rOuterMax-(self.rHousesectorlen*self.maxradius)/2.0
				self.rOuterHouse = self.rOuterMax-self.rHousesectorlen*self.maxradius
				self.r30 = self.rOuterHouse-self.outerplanetsectorlen*self.maxradius
			else:
				self.r30 = self.rOuterMax-self.outerplanetsectorlen*self.maxradius
				self.rOuterASCMC = self.maxradius*0.92

			self.rOuterPlanet = self.r30+self.planetoffs
			self.rOuterASCMC = self.maxradius*0.92
			self.rOuterArrow = self.rOuterASCMC+self.arrowlen*self.maxradius
			self.rOuterLine = self.r30+self.planetlinelen*self.maxradius
			self.rOuterRetr = self.rOuterLine+self.maxradius*self.retrdiff
			self.rOuter0 = self.r30
			self.rOuter1 = self.rOuter0-self.deg01510len*self.maxradius
			self.rOuter5 = self.rOuter1-self.deg01510len*self.maxradius
			self.rOuter10 = self.rOuter5-self.deg01510len*self.maxradius
			self.rOuterMin = self.maxradius*0.78
			self.rSign = self.r30-self.signoffs
			self.r0 = self.r30-self.signsectorlen*self.maxradius
			self.r1 = self.r0+self.deg01510len*self.maxradius
			self.r5 = self.r1+self.deg01510len*self.maxradius
			self.r10 = self.r5+self.deg01510len*self.maxradius
			self.rASCMC = self.rSign
			self.rArrow = self.rASCMC+self.arrowlen*self.maxradius

			self.rTerms = self.r0
			self.termssectorlen = 0.0
			if self.options.showterms:
				self.termssectorlen = 0.08
			self.termsoffs = (self.termssectorlen/2.0)*self.maxradius
			self.rTermsPlanet = self.r0-self.termsoffs#
			self.rDecans = self.rTerms-self.termssectorlen*self.maxradius
			self.decanssectorlen = 0.0
			if self.options.showdecans:
				self.decanssectorlen = 0.08
			self.decansoffs = (self.decanssectorlen/2.0)*self.maxradius
			self.rInner = self.rDecans-self.decanssectorlen*self.maxradius
			self.rDecansPlanet = self.rInner+self.decansoffs#

			self.rLLine = self.rInner-self.planetlinelen*self.maxradius #line between zodiacpos & planet
			self.rPlanet = self.rInner-self.planetoffs
			self.rAsp = self.rInner-self.planetsectorlen*self.maxradius
			self.rLLine2 = self.rAsp+self.planetlinelen*self.maxradius
			self.rRetr = self.rLLine2+self.maxradius*self.retrdiff

			pos = 0.45
			aspascmc = 0.41
			posascmc = 0.41
			poshouses = 0.32				
			if self.options.showdecans and self.options.showterms:
				pos = 0.30
				aspascmc = 0.25
				posascmc = 0.25
				poshouses = 0.20				
			elif self.options.showdecans or self.options.showterms:
				pos = 0.37
				aspascmc = 0.32
				posascmc = 0.32
				poshouses = 0.24				

			self.rPos = self.maxradius*pos
			self.rAspAscMC = self.maxradius*aspascmc
			self.rPosAscMC = self.maxradius*posascmc
			self.rPosHouses = self.maxradius*poshouses
			self.rBase = self.maxradius*0.11
			self.rHouse = self.rBase+self.rHousesectorlen*self.maxradius
			self.rHouseName = self.maxradius*0.14

		self.smallsymbolSize = 2*self.symbolSize/3

		self.fntMorinus = ImageFont.truetype(common.common.symbols, int(self.symbolSize))
		self.fntSmallMorinus = ImageFont.truetype(common.common.symbols, int(self.smallsymbolSize))
		self.fntMorinusSigns = ImageFont.truetype(common.common.symbols, int(self.signSize))
		self.fntAspects = ImageFont.truetype(common.common.symbols, int(self.symbolSize/2))
		self.fntText = ImageFont.truetype(common.common.abc, int(self.symbolSize/2))
		self.fntAntisText = ImageFont.truetype(common.common.abc, int(self.symbolSize))
		self.fntSmallText = ImageFont.truetype(common.common.abc, int(self.symbolSize/4))
		self.fntBigText = ImageFont.truetype(common.common.abc, int(self.symbolSize/4*3))
		self.fntMorinus2 = ImageFont.truetype(common.common.symbols, int(self.symbolSize/4*3))
		self.deg_symbol = u'\u00b0'

		self.arsigndiff = (0, -1, -1, 2, -1, 3, 4, -1, -1, -1, 6)
		self.hsystem = {'P':mtexts.txts['HSPlacidus'], 'K':mtexts.txts['HSKoch'], 'R':mtexts.txts['HSRegiomontanus'], 'C':mtexts.txts['HSCampanus'], 'E':mtexts.txts['HSEqual'], 'W':mtexts.txts['HSWholeSign'], 'X':mtexts.txts['HSAxial'], 'M':mtexts.txts['HSMorinus'], 'H':mtexts.txts['HSHorizontal'], 'T':mtexts.txts['HSPagePolich'], 'B':mtexts.txts['HSAlcabitus'], 'O':mtexts.txts['HSPorphyrius']}

		self.ayans = {0:mtexts.txts['None'], 1:mtexts.txts['FaganBradley'], 2:mtexts.txts['Lahiri'], 3:mtexts.txts['Deluce'], 4:mtexts.txts['Raman'], 5:mtexts.txts['Ushashashi'], 6:mtexts.txts['Krishnamurti'], 7:mtexts.txts['DjwhalKhul'], 8:mtexts.txts['Yukteshwar'], 9:mtexts.txts['JNBhasin'], 10:mtexts.txts['BabylonianKuglerI2'], 11:mtexts.txts['BabylonianKuglerII2'], 12:mtexts.txts['BabylonianKuglerIII2'], 13:mtexts.txts['BabylonianHuber2'], 14:mtexts.txts['BabylonianMercier2'], 15:mtexts.txts['Aldebaran15Tau2'], 16:mtexts.txts['Hipparchos'], 17:mtexts.txts['Sassanian'], 18:mtexts.txts['GalacticCenter0Sag2'], 19:mtexts.txts['J2000'], 20:mtexts.txts['J1900'], 21:mtexts.txts['B1950']}


	def drawChart(self):
		# PIL can draw only 1-width ellipse (or is there a width=...?)
		self.drawCircles()
		# --- Arabic Parts 안전 초기화(없을 경우 대비) ---
		if not hasattr(self, "apshow"):  self.apshow  = []
		if not hasattr(self, "apshift"): self.apshift = []
		if not hasattr(self, "apyoffs"): self.apyoffs = []
		# ---------------------------------------------

		if self.options.showterms:
			self.drawTermsLines()

		if self.options.showdecans:
			self.drawDecansLines()

		if self.options.houses:
			self.drawHouses(self.chart.houses, self.rBase, self.rInner)

			if self.chart2 != None:
				self.drawHouses(self.chart2.houses, self.r30, self.rOuterMax)

		#Convert to PIL (truetype-font is not supported in wxPython)
		wxImag = self.buffer.ConvertToImage()
		self.img = Image.new('RGB', (wxImag.GetWidth(), wxImag.GetHeight()))
		self.img.frombytes(wxImag.GetData())
		self.draw = ImageDraw.Draw(self.img)

		if self.options.houses:
			self.drawHouseNames(self.chart, self.rHouseName)
			if self.chart2 != None:
				self.drawHouseNames(self.chart2, self.rOuterHouseName)

		self.drawSigns()

		#Convert back from PIL
		wxImg = wx.Image(self.img.size[0], self.img.size[1])
		wxImg.SetData(self.img.tobytes())
		self.buffer = wx.Bitmap(wxImg)
		self.bdc = wx.BufferedDC(None, self.buffer)

		self.drawAscMC(self.chart.houses.ascmc, self.rBase, self.rASCMC, self.rArrow)
		if self.chart2 != None:
			self.drawAscMC(self.chart2.houses.ascmc, self.rOuterMin, self.rOuterASCMC, self.rOuterArrow)

		#calc shift of planets (in order to avoid overlapping)
		self.pshift = self.arrange(self.chart.planets.planets, self.chart.fortune.fortune, self.rPlanet)
		#PIL doesn't want to show short lines
		self.drawPlanetLines(self.pshift, self.chart.planets.planets, self.chart.fortune.fortune, self.rInner, self.rLLine, self.rAsp, self.rLLine2)
		if self.chart2 != None:
			self.pshift2 = self.arrange(self.chart2.planets.planets, self.chart2.fortune.fortune, self.rOuterPlanet)
			self.drawPlanetLines(self.pshift2, self.chart2.planets.planets, self.chart2.fortune.fortune, self.r30, self.rOuterLine)

		#PIL can't draw dashed lines
		if self.options.aspects:
			self.drawAspectLines()
			if self.options.showlof and self.options.showaspectstolof:
				self.drawLoFAspectLines()

		#if self.chart2 == None and self.planetaryday and self.options.showfixstars != options.Options.NONE:  # radix 차트
		if self.chart2 == None and self.options.showfixstars != options.Options.NONE:
			if self.options.showfixstars == options.Options.FIXSTARS:
				self.showfss = self.mergefsaspmatrices()
				fsdata = getattr(getattr(self.chart, 'fixstars', None), 'data', None)
				if fsdata:
					self.fsshift = self.arrangefs(fsdata, self.showfss, self.rFixstars)
					# (있다면) 아래 두 줄도 fsdata가 있을 때만 호출
					try:
						self.drawFixstarsLines(self.showfss)
						self.drawFixstars(self.showfss)
					except Exception:
						pass
				else:
					# 데이터가 없으면 고정성 블록 전체를 스킵
					self.fsshift = []

				self.fsyoffs = self.arrangeyfs(self.chart.fixstars.data, self.fsshift, self.showfss, self.rFixstars)
				self.drawFixstarsLines(self.showfss)

			elif self.options.showfixstars == options.Options.ANTIS:
				pl, lo, am = self._get_overlay_data('ANTIS')
				self.pshiftantis = self.arrangeAntis(pl, lo, am, self.rAntis)
				self.drawAntisLines(pl, lo, am, self.pshiftantis, self.r30, self.rAntisLines)

			elif self.options.showfixstars == options.Options.DODECATEMORIA:
				pl, lo, am = self._get_overlay_data('DODEC')
				self.pshiftantis = self.arrangeAntis(pl, lo, am, self.rAntis)
				self.drawAntisLines(pl, lo, am, self.pshiftantis, self.r30, self.rAntisLines)

			elif self.options.showfixstars == options.Options.CANTIS:
				pl, lo, am = self._get_overlay_data('CANTIS')
				self.pshiftantis = self.arrangeAntis(pl, lo, am, self.rAntis)
				self.drawAntisLines(pl, lo, am, self.pshiftantis, self.r30, self.rAntisLines)

			elif self.options.showfixstars == options.Options.ARABICPARTS:
				# Use Arabic Parts from the active wheel (outer if chart2 exists, else inner)
				C = self.chart2 if self.chart2 is not None else self.chart
				parts_obj = getattr(C, 'parts', None)
				if parts_obj and getattr(parts_obj, 'parts', None):
					parts_ap = list(parts_obj.parts)
					try:
						lof_lon  = C.fortune.fortune[fortune.Fortune.LON]
						lof_name = mtexts.txts.get('LotOfFortune', 'Fortuna')
						parts_ap.append({ arabicparts.ArabicParts.LONG: lof_lon,
										arabicparts.ArabicParts.NAME: lof_name })
					except Exception:
						pass

					if C is self.chart2:
						self._parts_ap2 = parts_ap
						self.apshow2    = list(range(len(parts_ap)))
						_rText = (self.rOuterLine + self.symbolSize * 0.2)
						self.apshift2   = self.arrangeParts(parts_ap, self.apshow2, _rText)
						self.apyoffs2   = self.arrangeyParts(parts_ap, self.apshow2, self.apshift2, _rText)
						self.drawArabicPartsLines(parts_ap, self.apshow2, self.apshift2, C)
					else:
						self._parts_ap = parts_ap
						self.apshow    = list(range(len(parts_ap)))
						_rText = (self.rOuterLine + self.symbolSize * 0.2)
						self.apshift   = self.arrangeParts(parts_ap, self.apshow, _rText)
						self.apyoffs   = self.arrangeyParts(parts_ap, self.apshow, self.apshift, _rText)
						self.drawArabicPartsLines(parts_ap, self.apshow, self.apshift, C)
				else:
					self._fortune_outer_shift = 0.0
					self.drawOuterFortuneLine(self.chart2 if self.chart2 is not None else self.chart)


		wxImag = self.buffer.ConvertToImage()

		self.img = Image.new('RGB', (wxImag.GetWidth(), wxImag.GetHeight()))
		self.img.frombytes(wxImag.GetData())
		self.draw = ImageDraw.Draw(self.img)

		self.drawPlanets(self.chart, self.pshift, self.rPlanet, self.rRetr)
		if self.chart2 != None:
			self.drawPlanets(self.chart2, self.pshift2, self.rOuterPlanet, self.rOuterRetr, True)

		if self.options.showterms:
			self.drawTerms()

		if self.options.showdecans:
			self.drawDecans()

		if self.options.aspects and self.options.symbols:
			self.drawAspectSymbols()
			if self.options.showlof and self.options.showaspectstolof:
				self.drawLoFAspectSymbols()

		if self.options.positions:
			self.drawAscMCPos()
			if self.options.houses:
				self.drawHousePos()

		#if self.options.planetarydayhour and self.planetaryday:
		if self.options.planetarydayhour:
			self.drawPlanetaryDayAndHour()
		#if self.options.housesystem and self.planetaryday:
		if self.options.housesystem:
			self.drawHousesystemName()
		# chart meta labels (inside wheel)
		# chart meta labels (inside wheel)
		if getattr(self.options, 'information', True):
			self.drawChartTimeTopLeft()
			self.drawChartPlaceBottomLeft()

		#if self.chart2 == None and self.planetaryday and self.options.showfixstars != options.Options.NONE:  # radix 차트
		if self.chart2 == None and self.options.showfixstars != options.Options.NONE:
			if self.options.showfixstars == options.Options.FIXSTARS:
				self.drawFixstars(self.showfss)

			elif self.options.showfixstars == options.Options.ANTIS:
				pl, lo, am = self._get_overlay_data('ANTIS')
				self.drawAntis(self.chart, pl, lo, am, self.pshiftantis, self.rAntis)

			elif self.options.showfixstars == options.Options.DODECATEMORIA:
				pl, lo, am = self._get_overlay_data('DODEC')
				self.drawAntis(self.chart, pl, lo, am, self.pshiftantis, self.rAntis)

			elif self.options.showfixstars == options.Options.CANTIS:
				pl, lo, am = self._get_overlay_data('CANTIS')
				self.drawAntis(self.chart, pl, lo, am, self.pshiftantis, self.rAntis)

			elif self.options.showfixstars == options.Options.ARABICPARTS:
				# 외곽/내측 어디에 parts를 만들었는지에 따라 각각 그려준다.
				drew = False
				if hasattr(self, "_parts_ap2") and hasattr(self, "apshow2") and hasattr(self, "apshift2") and hasattr(self, "apyoffs2") and self.chart2 is not None:
					# 외곽 휠(Transit/Return/Election/Secondary 등)에 생성된 아라빅 파츠
					self.drawArabicParts(self._parts_ap2, self.apshow2, self.apshift2, self.apyoffs2, C=self.chart2)
					drew = True
				if hasattr(self, "_parts_ap") and hasattr(self, "apshow") and hasattr(self, "apshift") and hasattr(self, "apyoffs"):
					# 내측(라딕스) 차트에 생성된 아라빅 파츠
					self.drawArabicParts(self._parts_ap, self.apshow, self.apshift, self.apyoffs, C=self.chart)
					drew = True
				if not drew:
					# 둘 다 없으면 포르투나만 텍스트로 표기
					self.drawOuterFortuneText(self.chart2 if self.chart2 is not None else self.chart)


		wxImg = wx.Image(self.img.size[0], self.img.size[1])

		wxImg.SetData(self.img.tobytes())
		self.buffer = wx.Bitmap(wxImg)

		return self.buffer


	def drawCircles(self):
		bkgclr = self.options.clrbackground
		if self.bw:
			bkgclr = (255,255,255)
		self.bdc.SetBackground(wx.Brush(bkgclr))
		self.bdc.Clear()
#		self.bdc.BeginDrawing()

		self.bdc.SetBrush(wx.Brush(bkgclr))	

		(cx, cy) = self.center.Get()

		#rOuterMax and rOuterHouse (for outer housenames)
		if self.chart2 != None and self.options.houses:
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.bdc.DrawCircle(cx, cy, self.rOuterMax)
			self.bdc.DrawCircle(cx, cy, self.rOuterHouse)

		#r30 circle
		#if self.chart2 != None or (self.planetaryday and self.options.showfixstars != options.Options.NONE): #If planetaryday is True => radix chart
		if self.chart2 != None or (self.options.showfixstars != options.Options.NONE):
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)

			w = 3
			if self.chartsize <= GraphChart.SMALL_SIZE:
				w = 1
			elif self.chartsize <= GraphChart.MEDIUM_SIZE:
				w = 2

			pen = wx.Pen(clr, w)
			self.bdc.SetPen(pen)
			self.bdc.DrawCircle(cx, cy, self.r30)

			#Outer 10, 5, 1-circle
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.bdc.DrawCircle(cx, cy, self.rOuter10)

		#r10 Circle
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		pen = wx.Pen(clr, 1)
		self.bdc.SetPen(pen)
		self.bdc.DrawCircle(cx, cy, self.r10)

		#r0 Circle
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)

		if self.options.showterms or self.options.showdecans:
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.bdc.DrawCircle(cx, cy, self.r0)

			#Decans Circle
			if self.options.showterms:
				clr = self.options.clrframe
				if self.bw:
					clr = (0,0,0)
				pen = wx.Pen(clr, 1)
				self.bdc.SetPen(pen)
				self.bdc.DrawCircle(cx, cy, self.rDecans)

		w = 3
		if self.chartsize <= GraphChart.SMALL_SIZE:
			w = 1
		elif self.chartsize <= GraphChart.MEDIUM_SIZE:
			w = 2

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.bdc.DrawCircle(cx, cy, self.rInner)

		#rAsp Circle
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		pen = wx.Pen(clr, 1)
		self.bdc.SetPen(pen)
		self.bdc.DrawCircle(cx, cy, self.rAsp)

		#rHouse Circle
		if self.options.houses:
			clr = self.options.clrhouses
			if self.bw:
				clr = (0,0,0)
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.bdc.DrawCircle(cx, cy, self.rHouse)

		#Base Circle
		clr = self.options.clrAscMC
		if self.bw:
			clr = (0,0,0)

		w = self.options.ascmcsize
		if self.chartsize <= GraphChart.SMALL_SIZE and (w == 5 or w == 4 or w == 3):
			w = 2
		elif self.chartsize <= GraphChart.MEDIUM_SIZE and (w == 5 or w == 4):
			w = 3

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.bdc.DrawCircle(cx, cy, self.rBase)

		asclon = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0:
			asclon -= self.chart.ayanamsha
			asclon = util.normalize(asclon)

		#30-degs
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		w = 3
		if self.chartsize <= GraphChart.SMALL_SIZE:
			w = 1
		elif self.chartsize <= GraphChart.MEDIUM_SIZE:
			w = 2

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.drawLines(GraphChart.DEG30, asclon, self.rInner, self.r30)

		#10-degs
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		w = 2
		if self.chartsize <= GraphChart.MEDIUM_SIZE:
			w = 1

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.drawLines(GraphChart.DEG10, asclon, self.r0, self.r10)

		#5-degs
		self.drawLines(GraphChart.DEG5, asclon, self.r0, self.r5)
		#1-degs
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		pen = wx.Pen(clr, 1)
		self.bdc.SetPen(pen)
		self.drawLines(GraphChart.DEG1, asclon, self.r0, self.r1)

		#Outer 10, 5, 1 -degs
		#if self.chart2 != None or (self.planetaryday and self.options.showfixstars != options.Options.NONE): #If planetaryday is True => radix chart
		if self.chart2 != None or (self.options.showfixstars != options.Options.NONE):
			#10-degs
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)
			w = 2
			if self.chartsize <= GraphChart.MEDIUM_SIZE:
				w = 1

			pen = wx.Pen(clr, w)
			self.bdc.SetPen(pen)
			self.drawLines(GraphChart.DEG10, asclon, self.rOuter0, self.rOuter10)

			#5-degs
			self.drawLines(GraphChart.DEG5, asclon, self.rOuter0, self.rOuter5)
			#1-degs
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.drawLines(GraphChart.DEG1, asclon, self.rOuter0, self.rOuter1)

		#self.bdc.EndDrawing()


	def drawSigns(self):
		(cx, cy) = self.center.Get()
		clr = self.options.clrsigns
		if self.bw:
			clr = (0,0,0)
		j = 0
		asclon = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0:
			asclon -= self.chart.ayanamsha
			asclon = util.normalize(asclon)
		i = math.pi+math.radians(asclon)-GraphChart.DEG30/2

		signs = common.common.Signs1
		if not self.options.signs:
			signs = common.common.Signs2

		while j < chart.Chart.SIGN_NUM:
			x = cx+math.cos(i)*self.rSign
			y = cy+math.sin(i)*self.rSign
			self.draw.text((x-self.signSize/2, y-self.signSize/2), signs[j], font=self.fntMorinusSigns, fill=clr)
			i -= GraphChart.DEG30
			j += 1


	def drawHouses(self, chouses, r1, r2):
		(cx, cy) = self.center.Get()
		clr = self.options.clrhouses
		if self.bw:
			clr = (0,0,0)
		pen = wx.Pen(clr, 1)
		self.bdc.SetPen(pen)
		asc = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0 and self.options.hsys == 'W':
			asc = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.ayanamsha)
		for i in range (1, houses.Houses.HOUSE_NUM+1):
			dif = math.radians(util.normalize(asc-chouses.cusps[i]))
			x1 = cx+math.cos(math.pi+dif)*r1
			y1 = cy+math.sin(math.pi+dif)*r1
			x2 = cx+math.cos(math.pi+dif)*r2
			y2 = cy+math.sin(math.pi+dif)*r2
			self.bdc.DrawLine(x1, y1, x2, y2)
	

	def drawAscMC(self, ascmc, r1, r2, rArrow):
		(cx, cy) = self.center.Get()
		#AscMC
		clr = self.options.clrAscMC
		if self.bw:
			clr = (0,0,0)
		w = self.options.ascmcsize
		if self.chartsize <= GraphChart.SMALL_SIZE and (w == 5 or w == 4 or w == 3):
			w = 2
		elif self.chartsize <= GraphChart.MEDIUM_SIZE and (w == 5 or w == 4):
			w = 3

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)

		for i in range(4):
			ang = math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC])
			if i == 0:
				ang -= math.radians(ascmc[houses.Houses.ASC])
			if i == 1:
				ang -= math.radians(ascmc[houses.Houses.ASC])+math.pi
			if i == 2:
				ang -= math.radians(ascmc[houses.Houses.MC])
			if i == 3:
				ang -= math.radians(ascmc[houses.Houses.MC])+math.pi

			r2comma = r2
			if self.chart2 != None and rArrow == self.rOuterArrow and i != 0 and i != 2:
				r2comma = rArrow

			x1 = cx+math.cos(ang)*r1
			y1 = cy+math.sin(ang)*r1
			x2 = cx+math.cos(ang)*r2comma
			y2 = cy+math.sin(ang)*r2comma
			self.bdc.DrawLine(x1, y1, x2, y2)

			if i == 0 or i == 2:
				self.drawArrow(ang, r2, clr, rArrow)


	def drawArrow(self, ang, r2, clr, rArrow):
		(cx, cy) = self.center.Get()
		offs = math.pi/360.0 

		xl = cx+math.cos(ang+offs)*r2
		yl = cy+math.sin(ang+offs)*r2
		xr = cx+math.cos(ang-offs)*r2
		yr = cy+math.sin(ang-offs)*r2
		xm = cx+math.cos(ang)*rArrow
		ym = cy+math.sin(ang)*rArrow

		li = ((xl, yl, xr, yr), (xr, yr, xm, ym), (xm, ym, xl, yl))
		self.bdc.DrawLineList(li)

#		self.bdc.SetBrush(wx.Brush(clr))	

#		x = (xl+xr)/2
#		x = (x+xm)/2
#		y = (yl+yr)/2
#		y = (y+ym)/2	

#		self.bdc.FloodFill(x, y, clr, wx.FLOOD_BORDER)


	def drawAscMCPos(self):
		(cx, cy) = self.center.Get()
		clrpos = self.options.clrpositions
		if self.bw:
			clrpos = (0,0,0)
		for i in range(2):
			lon = self.chart.houses.ascmc[i]
			if self.options.ayanamsha != 0:
				lon -= self.chart.ayanamsha
				lon = util.normalize(lon)

			(d, m, s) = util.decToDeg(lon)
			d = d%chart.Chart.SIGN_DEG
#			d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				
			wdeg, hdeg = self.draw.textsize(str(d), self.fntText)
			wmin, hmin = self.draw.textsize((str(m).zfill(2)), self.fntSmallText)
			x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[i]))*self.rPosAscMC
			y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[i]))*self.rPosAscMC
			xdeg = x-wdeg/2
			ydeg = y-hdeg/2
			self.draw.text((xdeg, ydeg), str(d), fill=clrpos, font=self.fntText)
			self.draw.text((xdeg+wdeg, ydeg), (str(m)).zfill(2), fill=clrpos, font=self.fntSmallText)


	def drawHousePos(self):
		(cx, cy) = self.center.Get()
		clrpos = self.options.clrpositions
		if self.bw:
			clrpos = (0,0,0)
		skipasc = False
		skipmc = False
		if self.chart.houses.cusps[1] == self.chart.houses.ascmc[houses.Houses.ASC]:
			skipasc = True
		if self.chart.houses.cusps[10] == self.chart.houses.ascmc[houses.Houses.MC]:
			skipmc = True

		asc = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0 and self.options.hsys == 'W':
			asc = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.ayanamsha)
		for i in range (1, houses.Houses.HOUSE_NUM+1):
			if i >= 4 and i < 10:
				continue
			if (skipasc and i == 1) or (skipmc and i == 10):
				continue

			lon = self.chart.houses.cusps[i]
			if self.options.ayanamsha != 0 and self.options.hsys != 'W':
				lon -= self.chart.ayanamsha
				lon = util.normalize(lon)
			(d, m, s) = util.decToDeg(lon)
			d = d%chart.Chart.SIGN_DEG
#			d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				
			wdeg, hdeg = self.draw.textsize(str(d), self.fntText)
			wmin, hmin = self.draw.textsize((str(m).zfill(2)), self.fntSmallText)
			x = cx+math.cos(math.pi+math.radians(asc-self.chart.houses.cusps[i]))*self.rPosHouses
			y = cy+math.sin(math.pi+math.radians(asc-self.chart.houses.cusps[i]))*self.rPosHouses
			xdeg = x-wdeg/2
			ydeg = y-hdeg/2
			self.draw.text((xdeg, ydeg), str(d), fill=clrpos, font=self.fntText)
			self.draw.text((xdeg+wdeg, ydeg), (str(m)).zfill(2), fill=clrpos, font=self.fntSmallText)


	def drawHouseNames(self, chrt, rHouseNames):
		(cx, cy) = self.center.Get()
		clr = self.options.clrhousenumbers
		if self.bw:
			clr = (0,0,0)
		pen = wx.Pen(clr, 1)
		self.bdc.SetPen(pen)
		asc = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0 and self.options.hsys == 'W':
			asc = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.ayanamsha)
		for i in range (1, houses.Houses.HOUSE_NUM+1):
			width = 0.0
			if i != houses.Houses.HOUSE_NUM:
				width = chrt.houses.cusps[i+1]-chrt.houses.cusps[i]
			else:
				width = chrt.houses.cusps[1]-chrt.houses.cusps[houses.Houses.HOUSE_NUM]

			width = util.normalize(width)
			halfwidth = math.radians(width/2.0)
			dif = math.radians(util.normalize(asc-chrt.houses.cusps[i]))
			
			x = cx+math.cos(math.pi+dif-halfwidth)*rHouseNames
			y = cy+math.sin(math.pi+dif-halfwidth)*rHouseNames
			if i == 1 or i == 2:
				xoffs = 0
				yoffs = self.symbolSize/4
				if i == 2:
					xoffs = self.symbolSize/8
			else:
				xoffs = self.symbolSize/4
				yoffs = self.symbolSize/4

			self.draw.text((x-xoffs,y-yoffs), common.common.Housenames[i-1], fill=clr, font=self.fntText)
	

	def drawPlanets(self, chrt, pshift, rPlanet, rRetr, outer=False):
		(cx, cy) = self.center.Get()
		clrs = (self.options.clrdomicil, self.options.clrexal, self.options.clrperegrin, self.options.clrcasus, self.options.clrexil)
		clrpos = self.options.clrpositions
		if self.bw:
			clrpos = (0,0,0)
		for i in range(planets.Planets.PLANETS_NUM+1):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue
			lon = 0.0
			if i < planets.Planets.PLANETS_NUM:
				lon = chrt.planets.planets[i].data[planets.Planet.LONG]
			else:
				lon = chrt.fortune.fortune[fortune.Fortune.LON]

			x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*rPlanet	
			y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*rPlanet	
			
			clr = (0,0,0)
			if not self.bw:
				if self.options.useplanetcolors:
					objidx = i
					if i >= planets.Planets.PLANETS_NUM-1:
						objidx -= 1
					clr = self.options.clrindividual[objidx]
				else:
					if i < planets.Planets.PLANETS_NUM:
						dign = chrt.dignity(i)
						clr = clrs[dign]
					else:
						clr = self.options.clrperegrin

			txtpl = ''
			if i < planets.Planets.PLANETS_NUM:
				txtpl = common.common.Planets[i]
			else:
				txtpl = common.common.fortune

			self.draw.text((x-self.symbolSize/2, y-self.symbolSize/2), txtpl, fill=clr, font=self.fntMorinus)

			#Retrograde
			if i < planets.Planets.PLANETS_NUM:
				if chrt.planets.planets[i].data[planets.Planet.SPLON] <= 0.0:
					t = 'S'
					if chrt.planets.planets[i].data[planets.Planet.SPLON] < 0.0:
						t = 'R'

					x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-chrt.planets.planets[i].data[planets.Planet.LONG]-pshift[i]))*rRetr	
					y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-chrt.planets.planets[i].data[planets.Planet.LONG]-pshift[i]))*rRetr

					self.draw.text((x-self.symbolSize/8, y-self.symbolSize/8), t, fill=clr, font=self.fntSmallText)

			if not outer:
				#Position
				if self.options.positions:
					lon2 = lon
					if self.options.ayanamsha != 0:
						lon2 -= self.chart.ayanamsha
						lon2 = util.normalize(lon2)

					(d, m, s) = util.decToDeg(lon2)
					d = d%chart.Chart.SIGN_DEG
#					d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				
					wdeg, hdeg = self.draw.textsize(str(d), self.fntText)
					wmin, hmin = self.draw.textsize((str(m).zfill(2)), self.fntSmallText)
					x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*self.rPos
					y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*self.rPos	
					xdeg = x-wdeg/2
					ydeg = y-hdeg/2
					self.draw.text((xdeg, ydeg), str(d), fill=clrpos, font=self.fntText)
					self.draw.text((xdeg+wdeg, ydeg), (str(m)).zfill(2), fill=clrpos, font=self.fntSmallText)


	def drawAspectSymbols(self):
		(cx, cy) = self.center.Get()

		for i in range(planets.Planets.PLANETS_NUM-1):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes):
				continue
			for j in range(planets.Planets.PLANETS_NUM-1):
				if (j == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (j == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (j == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((j == astrology.SE_MEAN_NODE or j == astrology.SE_TRUE_NODE) and not self.options.shownodes):
					continue
				asp = self.chart.aspmatrix[j][i]
				lon1 = self.chart.planets.planets[i].data[planets.Planet.LONG]
				lon2 = self.chart.planets.planets[j].data[planets.Planet.LONG]
				showasp = self.isShowAsp(asp.typ, lon1, lon2)
				if showasp:

					if ((i == astrology.SE_MEAN_NODE or j == astrology.SE_MEAN_NODE) and asp.typ != chart.Chart.CONJUNCTIO and not self.options.aspectstonodes):
						continue
					x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
					y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
					x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[j].data[planets.Planet.LONG]))*self.rAsp	
					y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[j].data[planets.Planet.LONG]))*self.rAsp					

					clr = (0,0,0)
					if not self.bw:
						clr = self.options.clraspect[asp.typ]

					self.draw.text(((x1+x2)/2-self.symbolSize/4, (y1+y2)/2-self.symbolSize/4), common.common.Aspects[asp.typ], fill=clr, font=self.fntAspects)					

		for i in range(self.chart.planets.PLANETS_NUM-2):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and (not self.options.shownodes or not self.options.aspectstonodes)):
				continue
			for j in range(2):
					asp = self.chart.aspmatrixAscMC[j][i]
					lon1 = self.chart.planets.planets[i].data[planets.Planet.LONG]
					lon2 = self.chart.houses.ascmc[j]
					showasp = self.isShowAsp(asp.typ, lon1, lon2)
					if showasp:
						x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
						y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
						x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[j]))*self.rAspAscMC
						y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[j]))*self.rAspAscMC	
						
						clr = (0,0,0)
						if not self.bw:
							clr = self.options.clraspect[asp.typ]

						self.draw.text(((x1+x2)/2-self.symbolSize/4, (y1+y2)/2-self.symbolSize/4), common.common.Aspects[asp.typ], fill=clr, font=self.fntAspects)


	def drawLoFAspectSymbols(self):
		(cx, cy) = self.center.Get()

		NODES = 2
		lon2 = self.chart.fortune.fortune[fortune.Fortune.LON]
		for i in range(planets.Planets.PLANETS_NUM-NODES):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]):
				continue
			asp = self.chart.aspmatrixLoF[i]
			lon1 = self.chart.planets.planets[i].data[planets.Planet.LONG]
			showasp = self.isShowAsp(asp.typ, lon1, lon2)
			if showasp:
				x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
				y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
				x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fortune.fortune[fortune.Fortune.LON]))*self.rAsp	
				y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fortune.fortune[fortune.Fortune.LON]))*self.rAsp					

				clr = (0,0,0)
				if not self.bw:
					clr = self.options.clraspect[asp.typ]

				self.draw.text(((x1+x2)/2-self.symbolSize/4, (y1+y2)/2-self.symbolSize/4), common.common.Aspects[asp.typ], fill=clr, font=self.fntAspects)					


	# Fuckin' PIL can't draw a dashed line
	def drawAspectLines(self):
		(cx, cy) = self.center.Get()

		for i in range(planets.Planets.PLANETS_NUM-1):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and (not self.options.shownodes or not self.options.aspectstonodes)):
				continue
			for j in range(planets.Planets.PLANETS_NUM-1):
				if (j == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (j == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (j == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((j == astrology.SE_MEAN_NODE or j == astrology.SE_TRUE_NODE) and (not self.options.shownodes or not self.options.aspectstonodes)):
					continue
				asp = self.chart.aspmatrix[j][i]
				lon1 = self.chart.planets.planets[i].data[planets.Planet.LONG]
				lon2 = self.chart.planets.planets[j].data[planets.Planet.LONG]
				showasp = self.isShowAsp(asp.typ, lon1, lon2)
				if showasp:
					x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
					y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
					x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[j].data[planets.Planet.LONG]))*self.rAsp	
					y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[j].data[planets.Planet.LONG]))*self.rAsp					

					clr = (0,0,0)
					if not self.bw:
						clr = self.options.clraspect[asp.typ]

					pen = wx.Pen(clr, 1)
					if not self.isExact(asp.exact, lon1, lon2):
						pen = wx.Pen(clr, 1, wx.USER_DASH)
						pen.SetDashes([10, 10])

					self.bdc.SetPen(pen)
					self.bdc.DrawLine(x1, y1, x2, y2)
						

		for i in range(self.chart.planets.PLANETS_NUM-2):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]):
				continue
			for j in range(2):
					asp = self.chart.aspmatrixAscMC[j][i]
					lon1 = self.chart.planets.planets[i].data[planets.Planet.LONG]
					lon2 = self.chart.houses.ascmc[j]
					showasp = self.isShowAsp(asp.typ, lon1, lon2)
					if showasp:
						x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
						y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
						x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[j]))*self.rAspAscMC
						y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[j]))*self.rAspAscMC	

						clr = (0,0,0)
						if not self.bw:
							clr = self.options.clraspect[asp.typ]

						pen = wx.Pen(clr, 1)
						if not self.isExact(asp.exact, lon1, lon2):
							pen = wx.Pen(clr, 1, wx.USER_DASH)
							pen.SetDashes([10, 10])

						self.bdc.SetPen(pen)
						self.bdc.DrawLine(x1, y1, x2, y2)


	def drawLoFAspectLines(self):
		(cx, cy) = self.center.Get()

		NODES = 2
		lon2 = self.chart.fortune.fortune[fortune.Fortune.LON]
		for i in range(planets.Planets.PLANETS_NUM-NODES):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]):
				continue
			asp = self.chart.aspmatrixLoF[i]
			lon1 = self.chart.planets.planets[i].data[planets.Planet.LONG]
			showasp = self.isShowAsp(asp.typ, lon1, lon2)
			if showasp:
				x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
				y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.planets.planets[i].data[planets.Planet.LONG]))*self.rAsp	
				x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fortune.fortune[fortune.Fortune.LON]))*self.rAsp	
				y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fortune.fortune[fortune.Fortune.LON]))*self.rAsp					

				clr = (0,0,0)
				if not self.bw:
					clr = self.options.clraspect[asp.typ]

				pen = wx.Pen(clr, 1)
				if not self.isExact(asp.exact, lon1, lon2):
					pen = wx.Pen(clr, 1, wx.USER_DASH)
					pen.SetDashes([10, 10])

				self.bdc.SetPen(pen)
				self.bdc.DrawLine(x1, y1, x2, y2)
						

	def drawPlanetaryDayAndHour(self):
		# 라벨 색(텍스트 기본색)은 유지, 행성 기호만 사용자 색 적용
		clr_lbl = self.options.clrtexts
		if self.bw:
			clr_lbl = (0,0,0)

		# 외측 차트가 있으면 외측 차트 기준으로 요일/시주 계산
		C = self.chart2 if self.chart2 is not None else self.chart

		# 요일 → 행성 인덱스 매핑 (Mon=0 … Sun=6)
		ar = (1, 4, 2, 5, 3, 6, 0)

		x = self.w - self.w/8
		y = self.h/25
		size = self.symbolSize/4*3

		# Planetary Hours 재계산: 리턴(GMT)이어도 '현지 기준' 일출/일몰로 강제
		try:
			# 기준 차트
			# C = self.chart2 if self.chart2 is not None else self.chart  # (이미 위에서 계산됨)

			# 경/위도(부호 포함)
			lon = C.place.deglon + C.place.minlon/60.0
			if not C.place.east:
				lon *= -1
			lat = C.place.deglat + C.place.minlat/60.0
			if not C.place.north:
				lat *= -1

			# tz_hours 결정
			if C.time.zt == chart.Time.ZONE:
				tz_hours = (1 if C.time.plus else -1) * (C.time.zh + C.time.zm/60.0) + (1.0 if getattr(C.time, 'daylightsaving', False) else 0.0)
			elif C.time.zt == chart.Time.LOCALMEAN:
				tz_hours = lon / 15.0
			elif C.time.zt == chart.Time.LOCALAPPARENT:
				ret, te, serr = astrology.swe_time_equ(C.time.jd)  # te: day 단위
				tz_hours = (lon / 15.0) + te*24.0
			else:
				# GREENWICH (리턴 차트 기본) → LMT로 보정해서 현지 일출/일몰 확보
				tz_hours = lon / 15.0

			# 현지 요일(월=0 … 일=6), JD 기반
			offs = float(tz_hours) / 24.0
			jd_local = C.time.jd + offs
			weekday = int(math.floor(jd_local + 0.5)) % 7

			# Planetary Hours 계산/갱신
			C.time.ph = hours.PlanetaryHours(lon, lat, C.place.altitude, weekday, C.time.jd, tz_hours)
		except Exception:
			# 실패 시 기존 로직으로 폴백
			if getattr(C.time, 'ph', None) is None:
				try:
					C.time.calcPHs(C.place)
				except Exception:
					return

		if getattr(C.time, 'ph', None) is None:
			return

		# 일주/시주 인덱스
		idx_day  = ar[C.time.ph.weekday]
		idx_hour = C.time.ph.planetaryhour

		# 사용자 행성색 적용 (가능할 때만)
		if (not self.bw) and getattr(self.options, 'useplanetcolors', False):
			try:
				clr_day = self.options.clrindividual[idx_day]
			except Exception:
				clr_day = clr_lbl
			try:
				clr_hour = self.options.clrindividual[idx_hour]
			except Exception:
				clr_hour = clr_lbl
		else:
			clr_day  = clr_lbl
			clr_hour = clr_lbl

		# 출력
		glyph_day  = common.common.Planets[idx_day]
		glyph_hour = common.common.Planets[idx_hour]

		w_day,  h_icon_day  = self.fntMorinus2.getsize(glyph_day)
		w_hour, h_icon_hour = self.fntMorinus2.getsize(glyph_hour)
		_,      h_label     = self.fntBigText.getsize("Ag")

		line_h = int(max(h_icon_day, h_icon_hour, h_label) * 1.1)
		pad_x  = int(self.symbolSize * 0.25)
		w_icon = max(w_day, w_hour)

		# 1행
		self.draw.text((x, y), glyph_day, fill=clr_day, font=self.fntMorinus2)
		self.draw.text((x + w_icon + pad_x, y), mtexts.txts['Day'],  fill=clr_lbl, font=self.fntBigText)

		# 2행
		y2 = y + line_h
		self.draw.text((x, y2), glyph_hour, fill=clr_hour, font=self.fntMorinus2)
		self.draw.text((x + w_icon + pad_x, y2), mtexts.txts['Hour'], fill=clr_lbl, font=self.fntBigText)

	def drawHousesystemName(self):
		clr = self.options.clrtexts
		if self.bw:
			clr = (0,0,0)

		x = self.w-self.w/6
		y = self.h-self.h/20

		#ayanamsha
		if self.options.ayanamsha != 0:
			w, h = self.fntBigText.getsize(self.hsystem[self.options.hsys])
			y2 = y-h*1.2
			self.draw.text((x,y2), self.ayans[self.options.ayanamsha], fill=clr, font=self.fntBigText)

		self.draw.text((x,y), self.hsystem[self.options.hsys], fill=clr, font=self.fntBigText)

	def drawChartTimeTopLeft(self):
		# 좌상단: 윗줄 = 날짜(예: 1998.July.23), 아랫줄 = 시간+표준(예: 11:20:24ZN)
		clr = self.options.clrtexts
		if self.bw:
			clr = (0, 0, 0)

		# 위치: 화면 안쪽 여백
		x = self.w/25
		y = self.h/25

		# 줄 간격
		_, h = self.fntBigText.getsize("Ag")
		dy = h * 1.1

		# 날짜 문자열 (월은 현지화)
		sign = '-' if self.chart.time.bc else ''
		month_txt = common.common.months[self.chart.time.origmonth - 1]
		date_txt = f"{sign}{self.chart.time.origyear}.{month_txt}.{str(self.chart.time.origday).zfill(2)}"

		# 시간 표기 + 기준(ZN/UT/LC) 현지화
		ztxt = mtexts.txts['UT']
		if self.chart.time.zt == chart.Time.ZONE:
			ztxt = mtexts.txts['ZN']
		elif self.chart.time.zt == chart.Time.LOCALMEAN or self.chart.time.zt == chart.Time.LOCALAPPARENT:
			ztxt = mtexts.txts['LC']
		time_txt = f"{str(self.chart.time.hour).zfill(2)}:{str(self.chart.time.minute).zfill(2)}:{str(self.chart.time.second).zfill(2)}, {ztxt}"

		# 출력
		self.draw.text((x, y),            date_txt, fill=clr, font=self.fntBigText)
		self.draw.text((x, y + dy),       time_txt, fill=clr, font=self.fntBigText)

	def drawChartPlaceBottomLeft(self):
		# 좌하단: 윗줄 = 장소명(그대로), 아랫줄 = 좌표(예: 126°55'E, 37°31N)
		clr = self.options.clrtexts
		if self.bw:
			clr = (0, 0, 0)

		x = self.w/25
		# 하단 기준선 맞추기 (housesystem 텍스트 위치와 균형)
		base_y = self.h - self.h/20

		# 줄 간격
		_, h = self.fntBigText.getsize("Ag")
		dy = h * 1.1

		# 장소명(현지화 X)
		name_txt = str(self.chart.place.place)

		# 방위문자 현지화
		dir_lon = mtexts.txts['E'] if self.chart.place.east  else mtexts.txts['W']
		dir_lat = mtexts.txts['N'] if self.chart.place.north else mtexts.txts['S']

		# 각도 표기(도°/분′), 초는 생략(원하면 동일한 방식으로 추가 가능)
		lon_txt = (str(self.chart.place.deglon)).zfill(2) + self.deg_symbol + (str(self.chart.place.minlon)).zfill(2) + "'" + dir_lon
		lat_txt = (str(self.chart.place.deglat)).zfill(2) + self.deg_symbol + (str(self.chart.place.minlat)).zfill(2) + "'" + dir_lat
		coord_txt = f"{lon_txt}, {lat_txt}"

		# 출력 (장소명 위줄, 좌표는 아래줄)
		self.draw.text((x, base_y - dy),  name_txt,  fill=clr, font=self.fntBigText)
		self.draw.text((x, base_y),       coord_txt, fill=clr, font=self.fntBigText)

	def drawLines(self, deg, shift, r1, r2):
		(cx, cy) = self.center.Get()
		i = math.pi+math.radians(shift)
		while i>-math.pi+math.radians(shift):
			x1 = cx+math.cos(i)*r1
			y1 = cy+math.sin(i)*r1
			x2 = cx+math.cos(i)*r2
			y2 = cy+math.sin(i)*r2

			self.bdc.DrawLine(x1, y1, x2, y2)
			i -= deg


	def drawTermsLines(self):
		(cx, cy) = self.center.Get()
		asclon = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0:
			asclon -= self.chart.ayanamsha
			asclon = util.normalize(asclon)

		shift = math.radians(asclon)
		signdeg = float(chart.Chart.SIGN_DEG)
		num = len(self.options.terms[self.options.selterm])
		subnum = len(self.options.terms[self.options.selterm][0])
		sign = 0.0
		for i in range(num):
			deg = sign
			for j in range(subnum):
				deg += float(self.options.terms[self.options.selterm][i][j][1])

				x1 = cx+math.cos(math.pi+shift-math.radians(deg))*self.rTerms
				y1 = cy+math.sin(math.pi+shift-math.radians(deg))*self.rTerms
				x2 = cx+math.cos(math.pi+shift-math.radians(deg))*self.rDecans
				y2 = cy+math.sin(math.pi+shift-math.radians(deg))*self.rDecans

				self.bdc.DrawLine(x1, y1, x2, y2)

			sign += signdeg


	def drawTerms(self):
		(cx, cy) = self.center.Get()
		clr = (0,0,0)
		if not self.bw:
			clr = self.options.clrsigns

		asclon = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0:
			asclon -= self.chart.ayanamsha
			asclon = util.normalize(asclon)
		shift = math.radians(asclon)
		signdeg = float(chart.Chart.SIGN_DEG)
		num = len(self.options.terms[self.options.selterm])
		subnum = len(self.options.terms[self.options.selterm][0])
		sign = 0.0
		for i in range(num):
			deg = sign
			for j in range(subnum):
				pldeg = deg+float(self.options.terms[self.options.selterm][i][j][1])/2.0
				deg += float(self.options.terms[self.options.selterm][i][j][1])

				x = cx+math.cos(math.pi+shift-math.radians(pldeg))*self.rTermsPlanet
				y = cy+math.sin(math.pi+shift-math.radians(pldeg))*self.rTermsPlanet

				self.draw.text((x-self.smallsymbolSize/2, y-self.smallsymbolSize/2), common.common.Planets[self.options.terms[self.options.selterm][i][j][0]], fill=clr, font=self.fntSmallMorinus)

			sign += signdeg


	def drawDecansLines(self):
		(cx, cy) = self.center.Get()

		asclon = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0:
			asclon -= self.chart.ayanamsha
			asclon = util.normalize(asclon)

		shift = asclon
		deg = GraphChart.DEG10
		i = math.pi+math.radians(shift)
		while i>-math.pi+math.radians(shift):
			x1 = cx+math.cos(i)*self.rInner
			y1 = cy+math.sin(i)*self.rInner
			x2 = cx+math.cos(i)*self.rDecans
			y2 = cy+math.sin(i)*self.rDecans

			self.bdc.DrawLine(x1, y1, x2, y2)
			i -= deg


	def drawDecans(self):
		(cx, cy) = self.center.Get()
		clr = (0,0,0)
		if not self.bw:
			clr = self.options.clrsigns

		asclon = self.chart.houses.ascmc[houses.Houses.ASC]
		if self.options.ayanamsha != 0:
			asclon -= self.chart.ayanamsha
			asclon = util.normalize(asclon)

		shift = math.radians(asclon)
		num = len(self.options.decans[self.options.seldecan])
		subnum = len(self.options.decans[self.options.seldecan][0])
		deg = 5.0
		for i in range(num):
			for j in range(subnum):
				x = cx+math.cos(math.pi+shift-math.radians(deg))*self.rDecansPlanet
				y = cy+math.sin(math.pi+shift-math.radians(deg))*self.rDecansPlanet

				self.draw.text((x-self.smallsymbolSize/2, y-self.smallsymbolSize/2), common.common.Planets[self.options.decans[self.options.seldecan][i][j]], fill=clr, font=self.fntSmallMorinus)

				deg += 10.0


	def drawPlanetLines(self, pshift, pls, frtn, r0, rl1, r02=None, rl2=None):
		clr = (0,0,0)
		if not self.bw:
			clr = self.options.clrframe
		w = 2
		if self.chartsize <= GraphChart.MEDIUM_SIZE:
			w = 1

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		for i in range (planets.Planets.PLANETS_NUM+1):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue
			self.drawPlanetLine(i, r0, rl1, pls, frtn, pshift)
			if r02 != None:
				self.drawPlanetLine(i, r02, rl2, pls, frtn, pshift)


	def drawPlanetLine(self, planet, r1, r2, pls, frtn, pshift):
		(cx, cy) = self.center.Get()

		lon = 0.0
		if planet < planets.Planets.PLANETS_NUM:
			lon = pls[planet].data[planets.Planet.LONG]
		else:
			lon = frtn[fortune.Fortune.LON]

		x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon))*r1
		y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon))*r1
		x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[planet]))*r2
		y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[planet]))*r2
		self.bdc.DrawLine(x1, y1, x2, y2)


	def drawFixstars(self, showfss):
		if not hasattr(self.chart, 'fixstars') or not getattr(self.chart.fixstars, 'data', None):
			return

		(cx, cy) = self.center.Get()

		clr = self.options.clrtexts
		if self.bw:
			clr = (0,0,0)

		num = len(showfss)
		for i in range(num):
			x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]-self.fsshift[i]))*self.rFixstars
			y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]-self.fsshift[i]))*self.rFixstars
			
			txt = self.chart.fixstars.data[showfss[i]][fixstars.FixStars.NAME]
			txt.strip()
			if txt == '':
				txt = self.chart.fixstars.data[showfss[i]][fixstars.FixStars.NOMNAME]

			fslon = self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]
			if self.options.ayanamsha != 0:
				fslon -= self.chart.ayanamsha
				fslon = util.normalize(fslon)
			(d, m, s) = util.decToDeg(fslon)
			d = d%chart.Chart.SIGN_DEG
#			d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
			txt += ' '+str(d)+self.deg_symbol+str(m).zfill(2)+"'"

			xoffs = 0.0
			pos = math.degrees(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]-self.fsshift[i]))
			pos = util.normalize(pos)
			if pos > 90.0 and pos < 270.0:
				w, h = self.fntText.getsize(txt)
				xoffs = w

			self.draw.text((x-xoffs, y-self.symbolSize/4+self.fsyoffs[i]), txt, fill=clr, font=self.fntText)


	def drawFixstarsLines(self, showfss):
		if not hasattr(self.chart, 'fixstars') or not getattr(self.chart.fixstars, 'data', None):
			return

		(cx, cy) = self.center.Get()

		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		w = 2
		if self.chartsize <= GraphChart.MEDIUM_SIZE:
			w = 1

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)

		num = len(showfss)
		for i in range (num):
			x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]))*self.r30
			y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]))*self.r30
			x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]-self.fsshift[i]))*self.rOuterLine
			y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]-self.fsshift[i]))*self.rOuterLine
			self.bdc.DrawLine(x1, y1, x2, y2)

	def arrangeParts(self, parts, showidxs, rText):
		"""
		항성/도데카테모리온과 같은 방식:
		- 가까운 항목끼리 사각형이 겹치면 앞쪽(+), 뒤쪽(-)으로 0.1°씩 각도를 밀어낸다
		- 360/0 경계도 처리
		- 텍스트 폭/높이를 실제로 써서 겹침 판단
		"""
		import math
		(cx, cy) = self.center.Get()
		n = len(showidxs)
		fshift = [0.0] * n
		if n < 2:
			return fshift[:]

		# 정렬용 배열
		order  = [parts[idx][arabicparts.ArabicParts.LONG] for idx in showidxs]
		mixed  = list(range(n))  # showidxs의 인덱스

		# 경도 기준 정렬(오름차순)
		for j in range(n):
			for i in range(n-1):
				if order[i] > order[i+1]:
					order[i], order[i+1] = order[i+1], order[i]
					mixed[i], mixed[i+1] = mixed[i+1], mixed[i]

		def rect(i):
			"""현재 i(정렬 뒤 인덱스)의 라벨 사각형(좌상단 x, y, w, h)"""
			real_idx = mixed[i]
			idx = showidxs[real_idx]
			name = parts[idx][arabicparts.ArabicParts.NAME]
			lon  = order[i]
			ang  = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC] - lon - fshift[real_idx])
			rad  = math.pi + math.radians(ang)
			x    = cx + math.cos(rad) * rText
			y    = cy + math.sin(rad) * rText
			w, h = self.fntText.getsize(name)
			pos  = util.normalize(math.degrees(rad))
			if 90.0 < pos < 270.0:  # 좌반구 오른쪽 정렬
				x -= w
			return (x, y - h/2.0, w, h)

		# 인접쌍 + 360/0 경계 처리
		def do_shift(p1, p2, forward=False):
			shifted = False
			x1, y1, w1, h1 = rect(p1)
			x2, y2, w2, h2 = rect(p2)
			while self.overlap(x1, y1, w1, h1, x2, y2, w2, h2):
				if not forward:
					fshift[mixed[p1]] -= 0.18
				fshift[mixed[p2]] += 0.18
				shifted = True
				STEP_DEG = 0.5    # ← 0.15~0.22 사이 취향대로
				GUARD    = 600     # ← 무한루프 방지

				cnt = 0
				while self.overlap(x1, y1, w1, h1, x2, y2, w2, h2) and cnt < GUARD:
					if not forward:
						fshift[mixed[p1]] -= STEP_DEG
					fshift[mixed[p2]] += STEP_DEG
					cnt += 1
					x1, y1, w1, h1 = rect(p1)
					x2, y2, w2, h2 = rect(p2)

			return shifted

		def do_arrange(forward=False):
			shifted_local = False
			for i in range(n-1):
				if do_shift(i, i+1, forward):
					shifted_local = True
			if shifted_local:
				do_arrange(forward)

		# 여러 번 훑어서 벌리기
		for _ in range(max(2, n + 2)):   # ← n+1 → n+2 정도로 한 번 더
			do_arrange(False)

		# 360/0 경계
		def angle_plus_shift(i):
			return order[i] + (fshift[mixed[i]] if order[i] < 180 else fshift[mixed[i]])
		# 경계에서 거꾸로 겹치는 경우만 앞으로(+ 방향) 밀기
		shifted = do_shift(n-1, 0, True)
		if shifted:
			# 경계 밀림 이후 재정렬
			for _ in range(n):
				do_arrange(True)
		else:
			# 경계는 안 겹치는데, “끝이 앞을 넘어서는” 케이스 보정
			if order[n-1] > 300.0 and order[0] < 60.0:
				lon1 = order[n-1] + fshift[mixed[n-1]]
				lon2 = order[0] + 360.0 + fshift[mixed[0]]
				if lon1 > lon2:
					dist = lon1 - lon2
					fshift[mixed[0]] += dist
					do_shift(n-1, 0, True)
					for i in range(n-1):
						l1 = order[i]   + fshift[mixed[i]]
						l2 = order[i+1] + fshift[mixed[i+1]]
						if l1 < 180.0 and l2 < 180.0 and l1 > l2:
							fshift[mixed[i+1]] += (l1 - l2)
							do_shift(i, i+1, True)
						else:
							break
					for _ in range(n):
						do_arrange(True)

		return fshift[:]


	def drawArabicParts(self, parts, showidxs, fshift, yoffs, C=None):
		C = C or self.chart
		(cx, cy) = self.center.Get()
		clr = self.options.clrtexts if not self.bw else (0, 0, 0)

		for i, idx in enumerate(showidxs):
			lon  = parts[idx][arabicparts.ArabicParts.LONG]
			name = parts[idx][arabicparts.ArabicParts.NAME]

			base = C.houses.ascmc[houses.Houses.ASC] - lon

			ang = util.normalize(base - fshift[i])
			rad = math.pi + math.radians(ang)

			# 라벨 레인: 선 끝보다 살짝 바깥
			r_text = self.rOuterLine + self.symbolSize * 0.2

			# 초기 배치
			x = cx + math.cos(rad) * r_text
			y = cy + math.sin(rad) * r_text + yoffs[i]

			# 좌/우 반구 정렬
			pos = util.normalize(math.degrees(rad))
			w, h = self.fntText.getsize(name)
			if 90.0 < pos < 270.0:
				x -= w
			# ★ outer wheel 침범 방지: 필요 시 바깥으로 살짝 더 밀어내기
			x, y, r_text = self._ensure_text_outside_outer_wheel(rad, x, y, w, h, r_text, pad_px=int(self.symbolSize*0.10))
			self.draw.text((x, y - h/2), name, fill=clr, font=self.fntText)

	def drawOuterFortuneText(self, C=None):
		C = C or self.chart

		# 기존에는 self.chart만 검사/사용해서 외곽 휠에서는 빠졌음 → C를 기준으로 사용
		if not hasattr(C, "fortune") or C.fortune is None:
			return
		try:
			lon = C.fortune.fortune[fortune.Fortune.LON]
		except Exception:
			return

		(cx, cy) = self.center.Get()
		clr  = self.options.clrtexts if not self.bw else (0, 0, 0)
		name = mtexts.txts.get('LotOfFortune', 'Fortuna')

		base = C.houses.ascmc[houses.Houses.ASC] - lon
		# ★ AP와의 충돌 시 포르투나는 반대 부호로 이동하도록, drawArabicPartsLines에서 저장한 값을 그대로 사용
		ang  = util.normalize(base + getattr(self, "_fortune_outer_shift", 0.0))

		rad  = math.pi + math.radians(ang)

		# 라벨 레인: 선 끝보다 살짝 바깥
		r_text = self.rOuterLine + self.symbolSize * 0.2

		x = cx + math.cos(rad) * r_text
		y = cy + math.sin(rad) * r_text

		pos = util.normalize(math.degrees(rad))
		w, h = self.fntText.getsize(name)
		if 90.0 < pos < 270.0:
			x -= w

		# --- 모든 AP 최종 라벨 사각형과 충돌이 없을 때까지 세로 스택 ---
		if hasattr(self, "apshow") and hasattr(self, "apshift") and hasattr(self, "apyoffs"):
			def fort_rect():
				return (x, y - h/2.0, w, h, pos)

			def ap_rect(i):
				idx  = self.apshow[i]
				alon = parts[idx][arabicparts.ArabicParts.LONG]
				aang = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC] - alon - self.apshift[i])
				arad = math.pi + math.radians(aang)
				ax   = cx + math.cos(arad) * r_text
				ay   = cy + math.sin(arad) * r_text + self.apyoffs[i]
				aw, ah = self.fntText.getsize(parts[idx][arabicparts.ArabicParts.NAME])
				apos = util.normalize(math.degrees(arad))
				if 90.0 < apos < 270.0:
					ax -= aw
				return (ax, ay - ah/2.0, aw, ah)

			changed = True
			while changed:
				changed = False
				fx, fy, fw, fh, _ = fort_rect()
				for i in range(len(self.apshow)):
					ax, ay, aw, ah = ap_rect(i)
					if self.overlap(fx, fy, fw, fh, ax, ay, aw, ah):
						# 좌반구(텍스트 오른쪽 정렬)는 아래로(+), 우반구는 위로(-) 이동
						y += 1.0 if (90.0 < pos < 270.0) else -1.0
						changed = True
						break

			pass

		# ★ outer wheel 침범 방지
		#x, y, r_text = self._ensure_text_outside_outer_wheel(rad, x, y, w, h, r_text, pad_px=int(self.symbolSize*0.10))

		self.draw.text((x, y - h/2), name, fill=clr, font=self.fntText)

	def drawArabicPartsLines(self, parts, showidxs, fshift, C=None):
		C = C or self.chart

		(cx, cy) = self.center.Get()
		clr = self.options.clrframe if not self.bw else (0, 0, 0)
		w = 2 if self.chartsize > GraphChart.MEDIUM_SIZE else 1
		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)

		self._af_split_idx = None
		self._af_split_deg = 0.0
		self._fortune_outer_shift = 0.0

		# Fortuna 라인/텍스트에서 재사용할 보정각
		self._fortune_outer_shift = float(self._af_split_deg)

		# 핵심: 시작점은 ‘원래 황경 각’(r30), 끝점은 ‘겹침 보정 후 라벨 각’(rOuterLine)
		for i, idx in enumerate(showidxs):
			lon  = parts[idx][arabicparts.ArabicParts.LONG]
			base = util.normalize(C.houses.ascmc[houses.Houses.ASC] - lon)
			#shift = fshift[i] + (self._af_split_deg if self._af_split_idx == i else 0.0)
			shift = fshift[i]
			rad_in  = math.pi + math.radians(base)                          # r30: 원래 황경
			rad_out = math.pi + math.radians(util.normalize(base - shift))   # rOuterLine: 라벨 각

			x1 = cx + math.cos(rad_in)  * self.r30
			y1 = cy + math.sin(rad_in)  * self.r30
			x2 = cx + math.cos(rad_out) * self.rOuterLine
			y2 = cy + math.sin(rad_out) * self.rOuterLine
			self.bdc.DrawLine(x1, y1, x2, y2)

	def drawAntisLines(self, plnts, lof, ascmc, pshift, r1, r2):
		(cx, cy) = self.center.Get()
		clr = (0,0,0)
		if not self.bw:
			clr = self.options.clrframe
		w = 2
		if self.chartsize <= GraphChart.MEDIUM_SIZE:
			w = 1

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		for i in range (planets.Planets.PLANETS_NUM+3):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue

			lon = 0.0
			if i < planets.Planets.PLANETS_NUM:
				lon = plnts[i].lon
			elif i == planets.Planets.PLANETS_NUM:
				lon = lof.lon
			elif i == planets.Planets.PLANETS_NUM+1:
				lon = ascmc[0].lon
			elif i == planets.Planets.PLANETS_NUM+2:
				lon = ascmc[1].lon

			selected_chart = (self.chart2 if self.chart2 is not None else self.chart)
			base = selected_chart.houses.ascmc[houses.Houses.ASC]
			if self.options.ayanamsha != 0:
				base = util.normalize(base - selected_chart.ayanamsha)

			# 시작/끝 각도
			ang1 = math.pi + math.radians(base - lon)
			ang2 = math.pi + math.radians(base - lon - pshift[i])

			# 라인 좌표
			x1 = cx + math.cos(ang1) * r1
			y1 = cy + math.sin(ang1) * r1
			x2 = cx + math.cos(ang2) * r2
			y2 = cy + math.sin(ang2) * r2

			self.bdc.DrawLine(x1, y1, x2, y2)

	def drawAntis(self, chrt, plnts, lof, ascmc, pshift, r):
		(cx, cy) = self.center.Get()
		clrs = (self.options.clrdomicil, self.options.clrexal, self.options.clrperegrin, self.options.clrcasus, self.options.clrexil)
		clrpls = self.options.clrperegrin
		clrtxt = self.options.clrtexts

		for i in range (planets.Planets.PLANETS_NUM+3):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue
			lon = 0.0
			txt = ''
			fnt = self.fntMorinus
			clr = (0,0,0)
			if i < planets.Planets.PLANETS_NUM:
				lon = plnts[i].lon
				txt = common.common.Planets[i]
				if not self.bw:
# ##################################
# Elias V 8.0.0 : Always show Antiscia and Dodecatemoria to full color.
					#if self.options.useplanetcolors:
					objidx = i
					if i == planets.Planets.PLANETS_NUM-1:
						objidx -= 1
					clr = self.options.clrindividual[objidx]
					#else:
					#	dign = chrt.dignity(i)
					#	clr = clrs[dign]
# ##################################
			elif i == planets.Planets.PLANETS_NUM:
				lon = lof.lon
				txt = common.common.fortune
				if not self.bw:
					if self.options.useplanetcolors:
						clr = self.options.clrindividual[i-1]
					else:
						clr = self.options.clrperegrin
			elif i == planets.Planets.PLANETS_NUM+1:
				lon = ascmc[0].lon
				txt = mtexts.txts['StripAsc']
				fnt = self.fntAntisText
				if not self.bw:
					clr = clrtxt
			elif i == planets.Planets.PLANETS_NUM+2:
				lon = ascmc[1].lon
				txt = mtexts.txts['StripMC']
				fnt = self.fntAntisText
				if not self.bw:
					clr = clrtxt

			selected_chart = (self.chart2 if self.chart2 is not None else self.chart)
			base = selected_chart.houses.ascmc[houses.Houses.ASC]
			if self.options.ayanamsha != 0:
				base = util.normalize(base - selected_chart.ayanamsha)

			ang = math.pi + math.radians(base - lon - pshift[i])
			x = cx + math.cos(ang) * r
			y = cy + math.sin(ang) * r

			self.draw.text((x-self.symbolSize/2, y-self.symbolSize/2), txt, fill=clr, font=fnt)

	def arrange(self, plnts, frtn, rPlanet):
		'''Arranges planets so they won't overlap each other'''

		pls = []
		pshift = []
		order = []
		mixed = []

		for i in range (planets.Planets.PLANETS_NUM+1):
			pls.append(0.0)
			pshift.append(0.0)
			order.append(0)
			mixed.append(0)

		pnum = 0
		for i in range (planets.Planets.PLANETS_NUM+1):
			if i < planets.Planets.PLANETS_NUM:
				pls[pnum] = plnts[i].data[planets.Planet.LONG]
			else:
				pls[pnum] = frtn[fortune.Fortune.LON]

			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue
			mixed[pnum] = i
			pnum += 1

		#arrange in order, initialize
		for i in range(pnum):
			order[i] = pls[i]
			
		for j in range(pnum):
			for i in range(pnum-1):
				if (order[i] > order[i+1]):
					tmp = order[i]
					order[i] = order[i+1]
					order[i+1] = tmp
					tmp = mixed[i]
					mixed[i] = mixed[i+1]
					mixed[i+1] = tmp
		
		#doArrange arranges consecutive two planets only(0 and 1, 1 and 2, ...), this is why we need to do it pnum+1 times
		for i in range(pnum+1):
			self.doArrange(pnum, pshift, order, mixed, rPlanet)

		#Arrange 360-0 transition also
		#We only shift forward at 360-0
		shifted = self.doShift(pnum-1, 0, pshift, order, mixed, rPlanet, True)

		if shifted:
			for i in range(pnum):
				self.doArrange(pnum, pshift, order, mixed, rPlanet, True)

		#check if beyond (not overlapping but beyond)
		else:
			if order[pnum-1] > 300.0 and order[0] < 60.0:
				lon1 = order[pnum-1]+pshift[mixed[pnum-1]]
				lon2 = order[0]+360.0+pshift[mixed[0]]

				if lon1 > lon2:
					dist = lon1-lon2
					pshift[mixed[0]] += dist
					self.doShift(pnum-1, 0, pshift, order, mixed, rPlanet, True)

					for i in range(pnum-1):
						lon1 = order[i]+pshift[mixed[i]]
						lon2 = order[i+1]+pshift[mixed[i+1]]	
						if lon1 < 180.0 and lon2 < 180.0:
							if lon1 > lon2:
								dist = lon1-lon2
								pshift[mixed[i+1]] += dist
								self.doShift(i, i+1, pshift, order, mixed, rPlanet, True)
							else:
								break
						else:
							break

					for i in range(pnum):
						self.doArrange(pnum, pshift, order, mixed, rPlanet, True)

		return pshift[:]


	def doArrange(self, pnum, pshift, order, mixed, rPlanet, forward = False):
		shifted = False

		for i in range(pnum-1):
			shifted = self.doShift(i, i+1, pshift, order, mixed, rPlanet, forward)

		if shifted:
			self.doArrange(pnum, pshift, order, mixed, rPlanet, forward)


	def doShift(self, p1, p2, pshift, order, mixed, rPlanet, forward = False):
		(cx, cy) = self.center.Get()
		shifted = False

		x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
		y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
		x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet
		y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet

		w1, h1 = 0.0, 0.0
		if mixed[p1] < planets.Planets.PLANETS_NUM:
			w1, h1 = self.fntMorinus.getsize(common.common.Planets[mixed[p1]])
		else:
			w1, h1 = self.fntMorinus.getsize(common.common.fortune)
		w2, h2 = 0.0, 0.0
		if mixed[p2] < planets.Planets.PLANETS_NUM:
			w2, h2 = self.fntMorinus.getsize(common.common.Planets[mixed[p2]])
		else:
			w2, h2 = self.fntMorinus.getsize(common.common.fortune)

		while (self.overlap(x1, y1, w1, h1, x2, y2, w2, h2)):
			if not forward:
				pshift[mixed[p1]] -= 0.1
			pshift[mixed[p2]] += 0.1

			x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
			y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
			x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet
			y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet

			if not shifted:
				shifted = True

		return shifted


	def overlap(self, x1, y1, w1, h1, x2, y2, w2, h2):
		xoverlap = (x1 <= x2 and x2 <= x1+w1) or (x2 <= x1 and x1 <= x2+w2)
		yoverlap = (y1 <= y2 and y2 <= y1+h1) or (y2 <= y1 and y1 <= y2+h2)

		if (xoverlap and yoverlap):
			return True

		return False
	# --- NEW: 텍스트 반폭을 각도로 환산(라벨 간 분리 계산용) ---
	def _label_half_deg(self, text, font, r_text, margin_px=4):
		w, _ = font.getsize(text)
		px = (w/2.0) + margin_px
		return (px / float(r_text)) * (180.0 / math.pi)
	# --- /NEW ---
	# NEW: 텍스트 박스가 outer wheel(rOuterLine) 안쪽으로 파고들면,
	# 라벨 반지름을 살짝 키워서 항상 바깥쪽으로 유지
	def _ensure_text_outside_outer_wheel(self, rad, x, y, w, h, r_text, pad_px=2):
		(cx, cy) = self.center.Get()
		# 현재 그릴 사각형 꼭짓점들
		corners = [(x, y - h/2), (x + w, y - h/2), (x, y + h/2), (x + w, y + h/2)]
		mind = min(math.hypot(ax - cx, ay - cy) for (ax, ay) in corners)

		target = self.rOuterLine + pad_px  # outer line에서 약간 여유
		if mind >= target:
			return x, y, r_text

		# 필요한 만큼 반지름을 바깥으로 밀기
		delta = target - mind
		new_r = r_text + delta
		new_x = cx + math.cos(rad) * new_r
		new_y = cy + math.sin(rad) * new_r

		# 좌/우 반구 정렬 다시 적용
		pos = util.normalize(math.degrees(rad))
		if 90.0 < pos < 270.0:
			new_x -= w

		return new_x, new_y, new_r

	# --- antiscia / contra-antiscia / dodecatemoria 안전 계산 ---
	def _mk_lon_obj(self, lon):
		class _O: pass
		o = _O()
		o.lon = util.normalize(lon)
		return o

	def _antis_lon(self, lon):
		# 솔스티스 축(Cancer/Capricorn) 기준 반사 (antiscia.py 구현과 동일한 규칙)
		L = util.normalize(lon)
		if 90.0 < L < 270.0:
			ant = util.normalize(270.0 + (270.0 - L))
		elif L < 90.0:
			ant = util.normalize(90.0 + (90.0 - L))
		elif L > 270.0:
			ant = util.normalize(270.0 - (L - 270.0))
		else:  # 정확히 0 Cancer/Capricorn
			ant = L

		# 아야남샤 적용 시 antiscia.py처럼 반사 후 ayan 만큼 빼서 그려준다
		if self.options.ayanamsha != 0:
			C = self.chart2 if (self.chart2 is not None) else self.chart
			ant = util.normalize(ant - C.ayanamsha)
		return ant

	def _contra_lon(self, lon):
		return util.normalize(self._antis_lon(lon) + 180.0)

	def _dodec_lon(self, lon):
		# 사인 기준 12분할(12th-parts), 아야남샤 반영: (lon-ayan)을 12배 → 다시 ayan 더함
		ayan = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0
		sid  = util.normalize(lon - ayan)
		s    = int(sid / chart.Chart.SIGN_DEG)
		d    = sid - s * chart.Chart.SIGN_DEG
		return util.normalize(s * chart.Chart.SIGN_DEG + d * 12.0)

	def _get_overlay_data(self, kind):
		"""
		kind: 'ANTIS' | 'CANTIS' | 'DODEC'
		chart.antiscia 가 없거나 필드가 None이어도 즉석 계산해서 반환
		반환: (pl_list, lof_obj, [asc_obj, mc_obj])  각각 .lon 속성 보유
		"""
		# chart2(바깥 휠)가 있으면 그것 기준으로, 없으면 chart(안쪽) 기준
		C = self.chart2 if (self.chart2 is not None) else self.chart
		has_antis = getattr(C, "antiscia", None)
		if has_antis is None and hasattr(C, "calcAntiscia"):
			try:
				C.calcAntiscia()
				has_antis = getattr(C, "antiscia", None)
			except Exception:
				has_antis = None

		pl_lons = [C.planets.planets[i].data[planets.Planet.LONG]
				   for i in range(planets.Planets.PLANETS_NUM)]
		lof_lon = C.fortune.fortune[fortune.Fortune.LON]
		asc_lon = C.houses.ascmc[houses.Houses.ASC]
		mc_lon  = C.houses.ascmc[houses.Houses.MC]

		def pick(calc_fn, attr):
			return getattr(has_antis, attr) if (has_antis is not None and hasattr(has_antis, attr)) else calc_fn()

		if kind == 'ANTIS':
			pl = pick(lambda: [self._mk_lon_obj(self._antis_lon(l)) for l in pl_lons], "plantiscia")
			lo = pick(lambda: self._mk_lon_obj(self._antis_lon(lof_lon)),         "lofant")
			am = pick(lambda: [self._mk_lon_obj(self._antis_lon(asc_lon)),
							   self._mk_lon_obj(self._antis_lon(mc_lon))],       "ascmcant")
		elif kind == 'CANTIS':
			pl = pick(lambda: [self._mk_lon_obj(self._contra_lon(l)) for l in pl_lons], "plcontraant")
			lo = pick(lambda: self._mk_lon_obj(self._contra_lon(lof_lon)),            "lofcontraant")
			am = pick(lambda: [self._mk_lon_obj(self._contra_lon(asc_lon)),
							   self._mk_lon_obj(self._contra_lon(mc_lon))],        "ascmccontraant")
		elif kind == 'DODEC':
			pl = pick(lambda: [self._mk_lon_obj(self._dodec_lon(l)) for l in pl_lons], "pldodecatemoria")
			lo = pick(lambda: self._mk_lon_obj(self._dodec_lon(lof_lon)),             "lofdodec")
			am = pick(lambda: [self._mk_lon_obj(self._dodec_lon(asc_lon)),
							   self._mk_lon_obj(self._dodec_lon(mc_lon))],         "ascmcdodec")
		else:
			pl = [self._mk_lon_obj(l) for l in pl_lons]
			lo = self._mk_lon_obj(lof_lon)
			am = [self._mk_lon_obj(asc_lon), self._mk_lon_obj(mc_lon)]

		return pl, lo, am

	def mergefsaspmatrices(self):
		showfss = []
		# Revolution/Election 등에서 fsaspmatrix가 없을 수 있음 → 안전 가드
		if not hasattr(self.chart, 'fsaspmatrix') or self.chart.fsaspmatrix is None:
			# 매트릭스가 없으면 일단 모든 항성을 후보로 (겹침 정렬 로직은 그대로 작동)
			try:
				return list(range(len(self.chart.fixstars.data)))
			except Exception:
				return []

		num = len(self.chart.fsaspmatrix)
		for i in range(num):
			ins = False

			num2 = len(self.chart.fsaspmatrix[i][1])
			for j in range(num2):
				b = self.chart.fsaspmatrix[i][1][j]
				if b <= astrology.SE_SATURN or (b == astrology.SE_URANUS and self.options.transcendental[chart.Chart.TRANSURANUS]) or (b == astrology.SE_NEPTUNE and self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (b == astrology.SE_PLUTO and self.options.transcendental[chart.Chart.TRANSPLUTO]) or (b == astrology.SE_MEAN_NODE and self.options.showfixstarsnodes) or (b == astrology.SE_TRUE_NODE and self.options.showfixstarsnodes):
					lon1 = self.chart.fixstars.data[self.chart.fsaspmatrix[i][0]][fixstars.FixStars.LON]
					lon2 = self.chart.planets.planets[b].data[planets.Planet.LONG]
					showasp = self.isShowAsp(chart.Chart.CONJUNCTIO, lon1, lon2)
					if showasp:
						ins = True
						break

			if ins:
				showfss.append(self.chart.fsaspmatrix[i][0])

		ASC = self.chart.houses.ascmc[houses.Houses.ASC]
		DESC = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC]+180.0)
		MC = self.chart.houses.ascmc[houses.Houses.MC]
		IC = util.normalize(self.chart.houses.ascmc[houses.Houses.MC]+180.0)
		ascmc = [ASC, DESC, MC, IC]
		num = len(self.chart.fsaspmatrixangles)
		for i in range(num):
			num2 = len(self.chart.fsaspmatrixangles[i][1])
			for j in range(num2):
				lon1 = self.chart.fixstars.data[self.chart.fsaspmatrixangles[i][0]][fixstars.FixStars.LON]
				lon2 = ascmc[self.chart.fsaspmatrixangles[i][1][j]]
				showasp = self.isShowAsp(chart.Chart.CONJUNCTIO, lon1, lon2)
				if showasp:
					showfss.append(self.chart.fsaspmatrixangles[i][0])

		if self.options.showfixstarshcs:
			num = len(self.chart.fsaspmatrixhcs)
			for i in range(num):
				num2 = len(self.chart.fsaspmatrixhcs[i][1])
				for j in range(num2):
					lon1 = self.chart.fixstars.data[self.chart.fsaspmatrixhcs[i][0]][fixstars.FixStars.LON]
					lon2 = self.chart.houses.cusps[self.chart.fsaspmatrixhcs[i][1][j]+1]
					showasp = self.isShowAsp(chart.Chart.CONJUNCTIO, lon1, lon2)
					if showasp:
						showfss.append(self.chart.fsaspmatrixhcs[i][0])

		if self.options.showfixstarslof:
			num = len(self.chart.fsaspmatrixlof)
			for i in range(num):
				lon1 = self.chart.fixstars.data[self.chart.fsaspmatrixlof[i]][fixstars.FixStars.LON]
				lon2 = self.chart.fortune.fortune[fortune.Fortune.LON]
				showasp = self.isShowAsp(chart.Chart.CONJUNCTIO, lon1, lon2)
				if showasp:
					showfss.append(self.chart.fsaspmatrixlof[i])

			s = set(showfss)
			showfss = list(s)
			showfss.sort()

		return showfss[:]


	def arrangeyfs(self, fixstrs, fsshift, showfss, rFS):
		(cx, cy) = self.center.Get()

		fsyoffs = []
		num = len(showfss)
		for i in range(num):
			fsyoffs.append(0.0)

		if len(showfss) < 2:
			return fsyoffs[:]

		for j in range(num):
			changed = False
			for i in range(num-1):
				x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[i]][fixstars.FixStars.LON]-fsshift[i]))*rFS
				y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[i]][fixstars.FixStars.LON]-fsshift[i]))*rFS
				x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[i+1]][fixstars.FixStars.LON]-fsshift[i+1]))*rFS
				y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[i+1]][fixstars.FixStars.LON]-fsshift[i+1]))*rFS
			
				txt = fixstrs[showfss[i]][fixstars.FixStars.NAME]
				(d, m, s) = util.decToDeg(fixstrs[showfss[i]][fixstars.FixStars.LON])
#				d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				txt += ' '+str(d)+self.deg_symbol+str(m).zfill(2)+"'"
				w1, h1 = self.fntText.getsize(txt)
				txt = fixstrs[showfss[i+1]][fixstars.FixStars.NAME]
				(d, m, s) = util.decToDeg(fixstrs[showfss[i+1]][fixstars.FixStars.LON])
#				d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				txt += ' '+str(d)+self.deg_symbol+str(m).zfill(2)+"'"
				w2, h2 = self.fntText.getsize(txt)
				while (self.overlap(x1, y1+fsyoffs[i], w1, h1, x2, y2+fsyoffs[i+1], w2, h2)):
					if not changed:
						changed = True
					pos = math.degrees(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[i]][fixstars.FixStars.LON]-fsshift[i]))
					pos = util.normalize(pos)
					deglim = 25.0
					if pos > 90.0-deglim and pos < 270.0-deglim:
						fsyoffs[i+1] += 1.0
					else:
						fsyoffs[i+1] -= 1.0

					txt = fixstrs[showfss[i]][fixstars.FixStars.NAME]
					w1, h1 = self.fntText.getsize(txt)
					txt = fixstrs[showfss[i+1]][fixstars.FixStars.NAME]
					w2, h2 = self.fntText.getsize(txt)

			if not changed:
				break
					
		return fsyoffs[:]


	def arrangefs(self, fixstrs, showfss, rFS):
		'''Arranges fixstars so they won't overlap each other'''

		fsshift = []
		num = len(showfss)
		for i in range(num):
			fsshift.append(0.0)

		if len(showfss) < 2:
			return fsshift[:]

		#doFSArrange arranges consecutive two fixstars only(0 and 1, 1 and 2, ...), this is why we need to do it num+1 times
		for i in range(num+1):
			self.doFSArrange(num, fixstrs, showfss, fsshift, rFS)

		#Arrange 360-0 transition also
		#We only shift forward at 360-0
		shifted = self.doFSShift(num-1, 0, fixstrs, showfss, fsshift, rFS, True)

		if shifted:
			for i in range(num):
				self.doFSArrange(num, fixstrs, showfss, fsshift, rFS, True)
		#check if beyond (not overlapping but beyond)
		else:
			if fixstrs[showfss[num-1]][fixstars.FixStars.LON] > 300.0 and fixstrs[showfss[0]][fixstars.FixStars.LON] < 60.0:
				lon1 = fixstrs[showfss[num-1]][fixstars.FixStars.LON]+fsshift[num-1]
				lon2 = fixstrs[showfss[0]][fixstars.FixStars.LON]+360.0+fsshift[0]

				if lon1 > lon2:
					dist = lon1-lon2
					fsshift[0] += dist
					self.doFSShift(num-1, 0, fixstrs, showfss, fsshift, rFS, True)

					for i in range(num-1):
						lon1 = fixstrs[showfss[i]][fixstars.FixStars.LON]+fsshift[i]
						lon2 = fixstrs[showfss[i+1]][fixstars.FixStars.LON]+fsshift[i+1]	
						if lon1 < 180.0 and lon2 < 180.0:
							if lon1 > lon2:
								dist = lon1-lon2
								fsshift[i+1] += dist
								self.doFSShift(i, i+1, fixstrs, showfss, fsshift, rFS, True)
							else:
								break
						else:
							break

					for i in range(num):
						self.doFSArrange(num, fixstrs, showfss, fsshift, rFS, True)

		return fsshift[:]


	def doFSArrange(self, num, fixstrs, showfss, fsshift, rFS, forward = False):
		shifted = False

		for i in range(num-1):
			shifted = self.doFSShift(i, i+1, fixstrs, showfss, fsshift, rFS, forward)

		if shifted:
			self.doFSArrange(num, fixstrs, showfss, fsshift, rFS, forward)


	def doFSShift(self, f1, f2, fixstrs, showfss, fsshift, rFS, forward = False):
		(cx, cy) = self.center.Get()
		shifted = False

		x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f1]][fixstars.FixStars.LON]-fsshift[f1]))*rFS
		y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f1]][fixstars.FixStars.LON]-fsshift[f1]))*rFS
		x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f2]][fixstars.FixStars.LON]-fsshift[f2]))*rFS
		y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f2]][fixstars.FixStars.LON]-fsshift[f2]))*rFS

		#this is different between fixstars and planets
		w1, h1 = self.symbolSize/2, 3*self.symbolSize/4
		w2, h2 = self.symbolSize/2, 3*self.symbolSize/4

		while (self.overlap(x1, y1, w1, h1, x2, y2, w2, h2)):
			if not forward:
				fsshift[f1] -= 0.1
			fsshift[f2] += 0.1

			x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f1]][fixstars.FixStars.LON]-fsshift[f1]))*rFS
			y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f1]][fixstars.FixStars.LON]-fsshift[f1]))*rFS
			x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f2]][fixstars.FixStars.LON]-fsshift[f2]))*rFS
			y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-fixstrs[showfss[f2]][fixstars.FixStars.LON]-fsshift[f2]))*rFS

			if not shifted:
				shifted = True

		return shifted

		class _LonOnly:
			def __init__(self, lon):
				self.lon = util.normalize(lon)

	def _dodec_from_lon_with_ayan(self, lon):
		ayan = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0
		sid  = util.normalize(lon - ayan)
		s    = int(sid / chart.Chart.SIGN_DEG)
		d    = sid - s * chart.Chart.SIGN_DEG
		return util.normalize(s * chart.Chart.SIGN_DEG + d * 12.0)

	def _build_dodec_overlay(self, C):
		# C: chart 또는 chart2
		pl = []
		for i in range(planets.Planets.PLANETS_NUM):
			lon = C.planets.planets[i].data[planets.Planet.LONG]
			pl.append(_LonOnly(self._dodec_from_lon_with_ayan(lon)))

		lof_lon = C.fortune.fortune[fortune.Fortune.LON]
		lof     = _LonOnly(self._dodec_from_lon_with_ayan(lof_lon))

		asc_lon = C.houses.ascmc[houses.Houses.ASC]
		mc_lon  = C.houses.ascmc[houses.Houses.MC]
		am      = [
			_LonOnly(self._dodec_from_lon_with_ayan(asc_lon)),
			_LonOnly(self._dodec_from_lon_with_ayan(mc_lon))
		]
		return (pl, lof, am)

	def _ensure_ap_for_chart(self, C):
		try:
			if not (hasattr(C, 'parts') and C.parts and getattr(C.parts, 'parts', None)):
				if hasattr(C, 'calcArabicParts'):
					C.calcArabicParts()
				else:
					# calcArabicParts가 없거나 parts가 여전히 비어 있으면 직접 생성
					try:
						# arabicparts 모듈은 이미 본 파일에서 참조 중
						C.parts = arabicparts.ArabicParts(C, self.options)
					except Exception:
						C.parts = None

		except Exception:
			pass

	def arrangeAntis(self, plnts, lof, ascmc, rPlanet):
		'''Arranges antiscia of planets so they won't overlap each other'''

		pls = []
		pshift = []
		order = []
		mixed = []

		for i in range (planets.Planets.PLANETS_NUM+3):#planets(with descNode), lof and ascmc
			pls.append(0.0)
			pshift.append(0.0)
			order.append(0)
			mixed.append(0)

		pnum = 0
		for i in range (planets.Planets.PLANETS_NUM+3):
			if i < planets.Planets.PLANETS_NUM:
				pls[pnum] = plnts[i].lon
			elif i == planets.Planets.PLANETS_NUM:
				pls[pnum] = lof.lon
			elif i == planets.Planets.PLANETS_NUM+1:
				pls[pnum] = ascmc[0].lon
			elif i == planets.Planets.PLANETS_NUM+2:
				pls[pnum] = ascmc[1].lon

			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue
			mixed[pnum] = i
			pnum += 1

		#arrange in order, initialize
		for i in range(pnum):
			order[i] = pls[i]
			
		for j in range(pnum):
			for i in range(pnum-1):
				if (order[i] > order[i+1]):
					tmp = order[i]
					order[i] = order[i+1]
					order[i+1] = tmp
					tmp = mixed[i]
					mixed[i] = mixed[i+1]
					mixed[i+1] = tmp
		
		#doArrange arranges consecutive two planets only(0 and 1, 1 and 2, ...), this is why we need to do it pnum+1 times
		for i in range(pnum+1):
			self.doArrangeAntis(pnum, pshift, order, mixed, rPlanet)

		#Arrange 360-0 transition also
		#We only shift forward at 360-0
		shifted = self.doShiftAntis(pnum-1, 0, pshift, order, mixed, rPlanet, True)

		if shifted:
			for i in range(pnum):
				self.doArrange(pnum, pshift, order, mixed, rPlanet, True)
		#check if beyond (not overlapping but beyond)
		else:
			if order[pnum-1] > 300.0 and order[0] < 60.0:
				lon1 = order[pnum-1]+pshift[mixed[pnum-1]]
				lon2 = order[0]+360.0+pshift[mixed[0]]

				if lon1 > lon2:
					dist = lon1-lon2
					pshift[mixed[0]] += dist
					self.doShiftAntis(pnum-1, 0, pshift, order, mixed, rPlanet, True)

					for i in range(pnum-1):
						lon1 = order[i]+pshift[mixed[i]]
						lon2 = order[i+1]+pshift[mixed[i+1]]	
						if lon1 < 180.0 and lon2 < 180.0:
							if lon1 > lon2:
								dist = lon1-lon2
								pshift[mixed[i+1]] += dist
								self.doShiftAntis(i, i+1, pshift, order, mixed, rPlanet, True)
							else:
								break
						else:
							break

					for i in range(pnum):
						self.doArrangeAntis(pnum, pshift, order, mixed, rPlanet, True)

		return pshift[:]


	def doArrangeAntis(self, pnum, pshift, order, mixed, rPlanet, forward = False):
		shifted = False

		for i in range(pnum-1):
			shifted = self.doShiftAntis(i, i+1, pshift, order, mixed, rPlanet, forward)

		if shifted:
			self.doArrangeAntis(pnum, pshift, order, mixed, rPlanet, forward)


	def doShiftAntis(self, p1, p2, pshift, order, mixed, rPlanet, forward = False):
		(cx, cy) = self.center.Get()
		shifted = False

		x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
		y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
		x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet
		y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet

		w1, h1 = 0.0, 0.0
		if mixed[p1] < planets.Planets.PLANETS_NUM:
			w1, h1 = self.fntMorinus.getsize(common.common.Planets[mixed[p1]])
		elif mixed[p1] == planets.Planets.PLANETS_NUM:
			w1, h1 = self.fntMorinus.getsize(common.common.fortune)
		elif mixed[p1] == planets.Planets.PLANETS_NUM+1:
			w1, h1 = self.fntAntisText.getsize(mtexts.txts['StripAsc'])
		elif mixed[p1] == planets.Planets.PLANETS_NUM+2:
			w1, h1 = self.fntAntisText.getsize(mtexts.txts['StripMC'])

		w2, h2 = 0.0, 0.0
		if mixed[p2] < planets.Planets.PLANETS_NUM:
			w2, h2 = self.fntMorinus.getsize(common.common.Planets[mixed[p2]])
		elif mixed[p2] == planets.Planets.PLANETS_NUM:
			w2, h2 = self.fntMorinus.getsize(common.common.fortune)
		elif mixed[p2] == planets.Planets.PLANETS_NUM+1:
			w2, h2 = self.fntAntisText.getsize(mtexts.txts['StripAsc'])
		elif mixed[p2] == planets.Planets.PLANETS_NUM+2:
			w2, h2 = self.fntAntisText.getsize(mtexts.txts['StripMC'])

		while (self.overlap(x1, y1, w1, h1, x2, y2, w2, h2)):
			if not forward:
				pshift[mixed[p1]] -= 0.1
			pshift[mixed[p2]] += 0.1

			x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
			y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p1]-pshift[mixed[p1]]))*rPlanet
			x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet
			y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-order[p2]-pshift[mixed[p2]]))*rPlanet

			if not shifted:
				shifted = True

		return shifted


	def isShowAsp(self, typ, lon1, lon2):
		res = False

		if typ != chart.Chart.NONE and self.options.aspect[typ]:
			val = True
			#check traditional aspects
			if self.options.traditionalaspects:
				if not(typ == chart.Chart.CONJUNCTIO or typ == chart.Chart.SEXTIL or typ == chart.Chart.QUADRAT or typ == chart.Chart.TRIGON or typ == chart.Chart.OPPOSITIO):
					val = False
				else:
					lona1 = lon1
					lona2 = lon2
					if self.options.ayanamsha != 0:
						lona1 -= self.chart.ayanamsha
						lona1 = util.normalize(lona1)
						lona2 -= self.chart.ayanamsha
						lona2 = util.normalize(lona2)

					sign1 = int(lona1/chart.Chart.SIGN_DEG)
					sign2 = int(lona2/chart.Chart.SIGN_DEG)
					signdiff = math.fabs(sign1-sign2)
					#check pisces-aries transition
					if signdiff > chart.Chart.SIGN_NUM/2:
						signdiff = chart.Chart.SIGN_NUM-signdiff#!?
					if self.arsigndiff[typ] != signdiff:
						val = False

			res = val

		return res


	def isExact(self, exact, lon1, lon2):
		res = False

		if self.options.traditionalaspects:
			lona1 = lon1
			lona2 = lon2
			if self.options.ayanamsha != 0:
				lona1 -= self.chart.ayanamsha
				lona1 = util.normalize(lona1)
				lona2 -= self.chart.ayanamsha
				lona2 = util.normalize(lona2)
			deg1 = int(lona1%chart.Chart.SIGN_DEG)
			deg2 = int(lona2%chart.Chart.SIGN_DEG)
			if deg1 == deg2:
				res = True
		else:
			if exact:
				res = True

		return res

	def drawOuterFortuneLine(self, C=None):
		C = C or self.chart

		if not (self.chart and getattr(self.chart, "fortune", None)):
			return
		try:
			lon = self.chart.fortune.fortune[fortune.Fortune.LON]
		except Exception:
			return

		(cx, cy) = self.center.Get()
		clr = self.options.clrframe if not self.bw else (0, 0, 0)
		w = 2 if self.chartsize > GraphChart.MEDIUM_SIZE else 1
		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)

		base  = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC] - lon)
		shift = float(getattr(self, "_fortune_outer_shift", 0.0))

		rad_in  = math.pi + math.radians(base)                        # r30: 원래 황경
		rad_out = math.pi + math.radians(util.normalize(base + shift))# rOuterLine: 라벨 각

		x1 = cx + math.cos(rad_in)  * self.r30
		y1 = cy + math.sin(rad_in)  * self.r30
		x2 = cx + math.cos(rad_out) * self.rOuterLine
		y2 = cy + math.sin(rad_out) * self.rOuterLine
		self.bdc.DrawLine(x1, y1, x2, y2)

	def arrangeyParts(self, parts, showidxs, fshift, rText):
		"""
		항성의 arrangeyfs와 동일한 요령:
		- 이웃 라벨끼리 겹치면 좌반구/우반구에 따라 위/아래로 1px씩 쌓아 올림
		"""
		import math
		(cx, cy) = self.center.Get()
		n = len(showidxs)
		yoffs = [0.0] * n
		if n < 2:
			return yoffs[:]

		def rect(i):
			idx  = showidxs[i]
			name = parts[idx][arabicparts.ArabicParts.NAME]
			lon  = parts[idx][arabicparts.ArabicParts.LONG]
			ang  = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC] - lon - fshift[i])
			rad  = math.pi + math.radians(ang)
			x    = cx + math.cos(rad) * rText
			y    = cy + math.sin(rad) * rText
			w, h = self.fntText.getsize(name)
			pad = max(1, int(self.symbolSize * 0.2))  
			w  += pad
			h  += pad
			pos  = util.normalize(math.degrees(rad))
			if 90.0 < pos < 270.0:
				x -= w
			return (x, y - h/2.0 + yoffs[i], w, h, pos)

		for _ in range(n):
			changed = False
			for i in range(n-1):
				x1, y1, w1, h1, pos1 = rect(i)
				x2, y2, w2, h2, pos2 = rect(i+1)
				while self.overlap(x1, y1, w1, h1, x2, y2, w2, h2):
					changed = True
					# 좌반구(텍스트 오른쪽 정렬)는 아래로(+), 우반구는 위로(-) 살짝 이동
					if 90.0 < pos2 < 270.0:
						yoffs[i+1] += 1.0
					else:
						yoffs[i+1] -= 1.0
					x1, y1, w1, h1, pos1 = rect(i)
					x2, y2, w2, h2, pos2 = rect(i+1)
			if not changed:
				break

		return yoffs[:]







