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

class GraphChart2:

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

		baseoffset = 0.0
		val = 0
		if self.options.showdecans:
			val += 1
		if self.options.showterms:
			val += 1
		if (self.planetaryday and self.options.showfixstars != options.Options.NONE) or self.chart2 != None:
			val += 1

		if self.options.positions:
			if val == 1:
				baseoffset = self.maxradius*0.02
			elif val == 2:
				baseoffset = self.maxradius*0.08
			elif val == 3:
				baseoffset = self.maxradius*0.12
		elif val == 3:
			baseoffset = self.maxradius*0.05

		self.arrowlen = 0.04
		self.deg01510len = 0.01
		self.retrdiff = 0.01
		if self.chart2 == None:
			if self.planetaryday and self.options.showfixstars != options.Options.NONE: #If planetaryday is True => radix chart
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
				self.rPosDeg = self.rInner-self.planetsectorlen*self.maxradius
				self.rPosMin = self.rPosDeg-0.04*self.maxradius
				self.rRetr = self.rPosMin-0.05*self.maxradius

				posascmc = 0.36
				poshouses = 0.36				
				if self.options.showdecans and self.options.showterms:
					posascmc = 0.24
					poshouses = 0.24				
				elif self.options.showdecans or self.options.showterms:
					posascmc = 0.30
					poshouses = 0.30

				self.rPosAscMC = self.maxradius*posascmc
				self.rPosAscMCMin = self.rPosAscMC-self.maxradius*0.05
				self.rPosHouses = self.maxradius*poshouses
				self.rPosHousesMin = self.rPosHouses-self.maxradius*0.05
				self.rBase = self.maxradius*0.24-baseoffset
				self.rHouse = self.rBase+self.rHousesectorlen*self.maxradius
				self.rHouseName = self.maxradius*0.27-baseoffset
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
				self.rPosDeg = self.rInner-self.planetsectorlen*self.maxradius
				self.rPosMin = self.rPosDeg-0.05*self.maxradius
				self.rRetr = self.rPosMin-0.05*self.maxradius

				posascmc = 0.42
				poshouses = 0.42				
				if self.options.showdecans and self.options.showterms:
					posascmc = 0.30
					poshouses = 0.30				
				elif self.options.showdecans or self.options.showterms:
					posascmc = 0.38
					poshouses = 0.38				

				self.rPosAscMC = self.maxradius*posascmc
				self.rPosAscMCMin = self.rPosAscMC-self.maxradius*0.05
				self.rPosHouses = self.maxradius*poshouses
				self.rPosHousesMin = self.rPosHouses-self.maxradius*0.05
				self.rBase = self.maxradius*0.24-baseoffset
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
			self.rPosDeg = self.rInner-self.planetsectorlen*self.maxradius
			self.rPosMin = self.rPosDeg-0.05*self.maxradius
			self.rRetr = self.rPosMin-0.05*self.maxradius

			posascmc = 0.34
			poshouses = 0.34				
			if self.options.showdecans and self.options.showterms:
				posascmc = 0.20
				poshouses = 0.20				
			elif self.options.showdecans or self.options.showterms:
				posascmc = 0.26
				poshouses = 0.26				

			self.rPosAscMC = self.maxradius*posascmc
			self.rPosAscMCMin = self.rPosAscMC-self.maxradius*0.05
			self.rPosHouses = self.maxradius*poshouses
			self.rPosHousesMin = self.rPosHouses-self.maxradius*0.05
			self.rBase = self.maxradius*0.24-baseoffset
			self.rHouse = self.rBase+self.rHousesectorlen*self.maxradius
			self.rHouseName = self.maxradius*0.27-baseoffset

		self.smallsymbolSize = 2*self.symbolSize/3

		self.fntMorinus = ImageFont.truetype(common.common.symbols, int(self.symbolSize))
		self.fntSmallMorinus = ImageFont.truetype(common.common.symbols, int(self.smallsymbolSize))
		self.fntMorinusSigns = ImageFont.truetype(common.common.symbols, int(self.signSize))
		self.fntText = ImageFont.truetype(common.common.abc, int(self.symbolSize/2))
		self.fntAntisText = ImageFont.truetype(common.common.abc, int(self.symbolSize))
		self.fntSmallText = ImageFont.truetype(common.common.abc, int(self.symbolSize/2))
		self.fntRetr = ImageFont.truetype(common.common.symbols, int(self.symbolSize/2))
		self.fntSmallText2 = ImageFont.truetype(common.common.abc, int(self.symbolSize/3))
		self.fntSmallTextOuter = ImageFont.truetype(common.common.abc, int(self.symbolSize/4))
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
		self.drawPlanetLines(self.pshift, self.chart.planets.planets, self.chart.fortune.fortune, self.rInner, self.rLLine)
		if self.chart2 != None:
			self.pshift2 = self.arrange(self.chart2.planets.planets, self.chart2.fortune.fortune, self.rOuterPlanet)
			self.drawPlanetLines(self.pshift2, self.chart2.planets.planets, self.chart2.fortune.fortune, self.r30, self.rOuterLine)


		if self.chart2 == None and self.planetaryday and self.options.showfixstars != options.Options.NONE: #If planetaryday is True => radix chart
			if self.options.showfixstars == options.Options.FIXSTARS:
				self.showfss = self.mergefsaspmatrices()
				self.fsshift = self.arrangefs(self.chart.fixstars.data, self.showfss, self.rFixstars)
				self.fsyoffs = self.arrangeyfs(self.chart.fixstars.data, self.fsshift, self.showfss, self.rFixstars)
				#PIL doesn't want to show short lines
				self.drawFixstarsLines(self.showfss)
			elif self.options.showfixstars == options.Options.ANTIS:
				self.pshiftantis = self.arrangeAntis(self.chart.antiscia.plantiscia, self.chart.antiscia.lofant, self.chart.antiscia.ascmcant, self.rAntis)
				self.drawAntisLines(self.chart.antiscia.plantiscia, self.chart.antiscia.lofant, self.chart.antiscia.ascmcant, self.pshiftantis, self.r30, self.rAntisLines)
			elif self.options.showfixstars == options.Options.DODECATEMORIA:
				self.pshiftantis = self.arrangeAntis(self.chart.antiscia.pldodecatemoria, self.chart.antiscia.lofdodec, self.chart.antiscia.ascmcdodec, self.rAntis)
				self.drawAntisLines(self.chart.antiscia.pldodecatemoria, self.chart.antiscia.lofdodec, self.chart.antiscia.ascmcdodec, self.pshiftantis, self.r30, self.rAntisLines)
			elif self.options.showfixstars == options.Options.CANTIS:
				self.pshiftantis = self.arrangeAntis(self.chart.antiscia.plcontraant, self.chart.antiscia.lofcontraant, self.chart.antiscia.ascmccontraant, self.rAntis)
				self.drawAntisLines(self.chart.antiscia.plcontraant, self.chart.antiscia.lofcontraant, self.chart.antiscia.ascmccontraant, self.pshiftantis, self.r30, self.rAntisLines)

			elif self.options.showfixstars == options.Options.ARABICPARTS:
				if self.chart.parts and self.chart.parts.parts:
					# 1) AP 원본을 복사하고, 포르투나를 같은 포맷으로 추가
					parts_ap = list(self.chart.parts.parts)
					try:
						lof_lon  = self.chart.fortune.fortune[fortune.Fortune.LON]
						lof_name = mtexts.txts.get('LotOfFortune', 'Fortuna')
						parts_ap.append({
							arabicparts.ArabicParts.LONG: lof_lon,
							arabicparts.ArabicParts.NAME: lof_name,
						})
					except Exception:
						pass  # 포르투나가 없으면 그냥 AP만

					# 2) 이후 로직은 전부 이 확장 리스트(parts_ap)를 기준으로
					self._parts_ap = parts_ap
					self.apshow  = list(range(len(parts_ap)))
					rText = (self.rOuterLine + self.symbolSize * 0.2)
					self.apshift = self.arrangeParts(parts_ap, self.apshow, rText)
					self.apyoffs = self.arrangeyParts(parts_ap, self.apshow, self.apshift, rText)

					# 3) 바깥 원 연결선도 AP(=포르투나 포함) 기준으로 한 번만 그림
					self.drawArabicPartsLines(parts_ap, self.apshow, self.apshift)

					# ⚠️ 중요: 포르투나 전용 선은 더 이상 그리지 않음
					# self.drawOuterFortuneLine()  # ← 이 줄은 삭제

		#Convert to PIL (truetype-font is not supported in wxPython)
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

		if self.options.positions:
			self.drawAscMCPos()
			if self.options.houses:
				self.drawHousePos()

		if self.options.planetarydayhour and self.planetaryday:
			self.drawPlanetaryDayAndHour()
		if self.options.housesystem and self.planetaryday:
			self.drawHousesystemName()

		if self.chart2 == None and self.planetaryday and self.options.showfixstars != options.Options.NONE: #If planetaryday is True => radix chart
			if self.options.showfixstars == options.Options.FIXSTARS:
				self.drawFixstars(self.showfss)
			elif self.options.showfixstars == options.Options.ANTIS:
				self.drawAntis(self.chart, self.chart.antiscia.plantiscia, self.chart.antiscia.lofant, self.chart.antiscia.ascmcant, self.pshiftantis, self.rAntis)
			elif self.options.showfixstars == options.Options.DODECATEMORIA:
				self.drawAntis(self.chart, self.chart.antiscia.pldodecatemoria, self.chart.antiscia.lofdodec, self.chart.antiscia.ascmcdodec, self.pshiftantis, self.rAntis)
			elif self.options.showfixstars == options.Options.CANTIS:
				self.drawAntis(self.chart, self.chart.antiscia.plcontraant, self.chart.antiscia.lofcontraant, self.chart.antiscia.ascmccontraant, self.pshiftantis, self.rAntis)
			elif self.options.showfixstars == options.Options.ARABICPARTS:
				if self.chart.parts and self.chart.parts.parts:
					self.drawArabicParts(self._parts_ap, self.apshow, self.apshift, self.apyoffs)

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

		if self.chart2 == None:
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.bdc.DrawCircle(cx, cy, self.r30)

		#r30 circle
		if self.chart2 != None or (self.planetaryday and self.options.showfixstars != options.Options.NONE): #If planetaryday is True => radix chart
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)

			w = 3
			if self.chartsize <= GraphChart2.SMALL_SIZE:
				w = 1
			elif self.chartsize <= GraphChart2.MEDIUM_SIZE:
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
		if self.chartsize <= GraphChart2.SMALL_SIZE:
			w = 1
		elif self.chartsize <= GraphChart2.MEDIUM_SIZE:
			w = 2

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.bdc.DrawCircle(cx, cy, self.rInner)

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
		if self.chartsize <= GraphChart2.SMALL_SIZE and (w == 5 or w == 4 or w == 3):
			w = 2
		elif self.chartsize <= GraphChart2.MEDIUM_SIZE and (w == 5 or w == 4):
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
		if self.chartsize <= GraphChart2.SMALL_SIZE:
			w = 1
		elif self.chartsize <= GraphChart2.MEDIUM_SIZE:
			w = 2

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.drawLines(GraphChart2.DEG30, asclon, self.rInner, self.r30)

		#10-degs
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		w = 2
		if self.chartsize <= GraphChart2.MEDIUM_SIZE:
			w = 1

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		self.drawLines(GraphChart2.DEG10, asclon, self.r0, self.r10)

		#5-degs
		self.drawLines(GraphChart2.DEG5, asclon, self.r0, self.r5)
		#1-degs
		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		pen = wx.Pen(clr, 1)
		self.bdc.SetPen(pen)
		self.drawLines(GraphChart2.DEG1, asclon, self.r0, self.r1)

		#Outer 10, 5, 1 -degs
		if self.chart2 != None or (self.planetaryday and self.options.showfixstars != options.Options.NONE): #If planetaryday is True => radix chart
			#10-degs
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)
			w = 2
			if self.chartsize <= GraphChart2.MEDIUM_SIZE:
				w = 1

			pen = wx.Pen(clr, w)
			self.bdc.SetPen(pen)
			self.drawLines(GraphChart2.DEG10, asclon, self.rOuter0, self.rOuter10)

			#5-degs
			self.drawLines(GraphChart2.DEG5, asclon, self.rOuter0, self.rOuter5)
			#1-degs
			clr = self.options.clrframe
			if self.bw:
				clr = (0,0,0)
			pen = wx.Pen(clr, 1)
			self.bdc.SetPen(pen)
			self.drawLines(GraphChart2.DEG1, asclon, self.rOuter0, self.rOuter1)

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
		i = math.pi+math.radians(asclon)-GraphChart2.DEG30/2

		signs = common.common.Signs1
		if not self.options.signs:
			signs = common.common.Signs2

		while j < chart.Chart.SIGN_NUM:
			x = cx+math.cos(i)*self.rSign
			y = cy+math.sin(i)*self.rSign
			self.draw.text((x-self.signSize/2, y-self.signSize/2), signs[j], font=self.fntMorinusSigns, fill=clr)
			i -= GraphChart2.DEG30
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
		if self.chartsize <= GraphChart2.SMALL_SIZE and (w == 5 or w == 4 or w == 3):
			w = 2
		elif self.chartsize <= GraphChart2.MEDIUM_SIZE and (w == 5 or w == 4):
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
			d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				
			degtxt = str(d)+self.deg_symbol
			wdeg, hdeg = self.draw.textsize(degtxt, self.fntText)
			x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[i]))*self.rPosHouses
			y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[i]))*self.rPosHouses
			xdeg = x-wdeg/2
			ydeg = y-hdeg/2
			self.draw.text((xdeg, ydeg), degtxt, fill=clrpos, font=self.fntText)

			mintxt = str(m)+"'"
			wdeg, hdeg = self.draw.textsize(mintxt, self.fntSmallText2)
			x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[i]))*self.rPosHousesMin
			y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.houses.ascmc[i]))*self.rPosHousesMin
			xdeg = x-wdeg/2
			ydeg = y-hdeg/2
			self.draw.text((xdeg, ydeg), mintxt, fill=clrpos, font=self.fntSmallText2)


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
			d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				
			degtxt = str(d)+self.deg_symbol
			wdeg, hdeg = self.draw.textsize(degtxt, self.fntText)
			x = cx+math.cos(math.pi+math.radians(asc-self.chart.houses.cusps[i]))*self.rPosHouses
			y = cy+math.sin(math.pi+math.radians(asc-self.chart.houses.cusps[i]))*self.rPosHouses
			xdeg = x-wdeg/2
			ydeg = y-hdeg/2
			self.draw.text((xdeg, ydeg), degtxt, fill=clrpos, font=self.fntText)

			mintxt = str(m)+"'"
			wdeg, hdeg = self.draw.textsize(mintxt, self.fntSmallText2)
			x = cx+math.cos(math.pi+math.radians(asc-self.chart.houses.cusps[i]))*self.rPosHousesMin
			y = cy+math.sin(math.pi+math.radians(asc-self.chart.houses.cusps[i]))*self.rPosHousesMin
			xdeg = x-wdeg/2
			ydeg = y-hdeg/2
			self.draw.text((xdeg, ydeg), mintxt, fill=clrpos, font=self.fntSmallText2)


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
		for i in range (planets.Planets.PLANETS_NUM+1):
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

			if not outer:
				#Position
				lon2 = lon
				if self.options.ayanamsha != 0:
					lon2 -= self.chart.ayanamsha
					lon2 = util.normalize(lon2)

				(d, m, s) = util.decToDeg(lon2)
				d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
				
				degtxt = str(d)+self.deg_symbol
				wdeg, hdeg = self.draw.textsize(degtxt, self.fntText)
				x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*self.rPosDeg
				y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*self.rPosDeg
				xdeg = x-wdeg/2
				ydeg = y-hdeg/2
				self.draw.text((xdeg, ydeg), degtxt, fill=clrpos, font=self.fntText)

				mintxt = str(m)+"'"
				wdeg, hdeg = self.draw.textsize(mintxt, self.fntSmallText2)
				x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*self.rPosMin
				y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-lon-pshift[i]))*self.rPosMin
				xdeg = x-wdeg/2
				ydeg = y-hdeg/2
				self.draw.text((xdeg, ydeg), (mintxt).zfill(2), fill=clrpos, font=self.fntSmallText2)

				#Retrograde
				if i < planets.Planets.PLANETS_NUM:
					rfnt = self.fntSmallText
					if chrt.planets.planets[i].data[planets.Planet.SPLON] <= 0.0:
						t = 'S'
						if chrt.planets.planets[i].data[planets.Planet.SPLON] < 0.0:
							t = common.common.retr
							rfnt = self.fntRetr
#							t = 'R'

						wdeg, hdeg = self.draw.textsize(t, rfnt)
						x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-chrt.planets.planets[i].data[planets.Planet.LONG]-pshift[i]))*rRetr	
						y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-chrt.planets.planets[i].data[planets.Planet.LONG]-pshift[i]))*rRetr
						xdeg = x-wdeg/2
						ydeg = y-hdeg/2

						self.draw.text((xdeg, ydeg), t, fill=clr, font=rfnt)
			else:
				#Retrograde
				if i < planets.Planets.PLANETS_NUM:
					if chrt.planets.planets[i].data[planets.Planet.SPLON] <= 0.0:
						t = 'S'
						if chrt.planets.planets[i].data[planets.Planet.SPLON] < 0.0:
							t = 'R'

						x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-chrt.planets.planets[i].data[planets.Planet.LONG]-pshift[i]))*rRetr	
						y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-chrt.planets.planets[i].data[planets.Planet.LONG]-pshift[i]))*rRetr

						self.draw.text((x-self.symbolSize/8, y-self.symbolSize/8), t, fill=clr, font=self.fntSmallTextOuter)


	def drawPlanetaryDayAndHour(self):
		clr = self.options.clrtexts
		if self.bw:
			clr = (0,0,0)
		ar = (1, 4, 2, 5, 3, 6, 0)
		x = self.w-self.w/8
		y = self.h/25
		size = self.symbolSize/4*3
		self.draw.text((x,y), common.common.Planets[ar[self.chart.time.ph.weekday]], fill=clr, font=self.fntMorinus2)
		self.draw.text((x+size+size/2,y), mtexts.txts['Day'], fill=clr, font=self.fntBigText)
		self.draw.text((x,y+size+size/2), common.common.Planets[self.chart.time.ph.planetaryhour], fill=clr, font=self.fntMorinus2)
		self.draw.text((x+size+size/2,y+size+size/2), mtexts.txts['Hour'], fill=clr, font=self.fntBigText)


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
		deg = GraphChart2.DEG10
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


	def drawPlanetLines(self, pshift, pls, frtn, r0, rl1):
		clr = (0,0,0)
		if not self.bw:
			clr = self.options.clrframe
		w = 2
		if self.chartsize <= GraphChart2.MEDIUM_SIZE:
			w = 1

		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)
		for i in range (planets.Planets.PLANETS_NUM+1):
			if (i == astrology.SE_URANUS and not self.options.transcendental[chart.Chart.TRANSURANUS]) or (i == astrology.SE_NEPTUNE and not self.options.transcendental[chart.Chart.TRANSNEPTUNE]) or (i == astrology.SE_PLUTO and not self.options.transcendental[chart.Chart.TRANSPLUTO]) or ((i == astrology.SE_MEAN_NODE or i == astrology.SE_TRUE_NODE) and not self.options.shownodes) or (i == planets.Planets.PLANETS_NUM and not self.options.showlof):
				continue
			self.drawPlanetLine(i, r0, rl1, pls, frtn, pshift)


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
			d, m = util.roundDeg(d%chart.Chart.SIGN_DEG, m, s)
			txt += ' '+str(d)+self.deg_symbol+str(m).zfill(2)+"'"

			xoffs = 0.0
			pos = math.degrees(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-self.chart.fixstars.data[showfss[i]][fixstars.FixStars.LON]-self.fsshift[i]))
			pos = util.normalize(pos)
			if pos > 90.0 and pos < 270.0:
				w, h = self.fntText.getsize(txt)
				xoffs = w

			self.draw.text((x-xoffs, y-self.symbolSize/4+self.fsyoffs[i]), txt, fill=clr, font=self.fntText)


	def drawFixstarsLines(self, showfss):
		(cx, cy) = self.center.Get()

		clr = self.options.clrframe
		if self.bw:
			clr = (0,0,0)
		w = 2
		if self.chartsize <= GraphChart2.MEDIUM_SIZE:
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


	def drawArabicParts(self, parts, showidxs, fshift, yoffs):
		(cx, cy) = self.center.Get()
		clr = self.options.clrtexts if not self.bw else (0, 0, 0)

		for i, idx in enumerate(showidxs):
			lon  = parts[idx][arabicparts.ArabicParts.LONG]
			name = parts[idx][arabicparts.ArabicParts.NAME]

			base = self.chart.houses.ascmc[houses.Houses.ASC] - lon
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
			x, y, r_text = self._ensure_text_outside_outer_wheel(rad, x, y, w, h, r_text, pad_px=int(self.symbolSize*0.10))
			self.draw.text((x, y - h/2), name, fill=clr, font=self.fntText)

	def drawOuterFortuneText(self):
		if not hasattr(self.chart, "fortune") or self.chart.fortune is None:
			return
		try:
			lon = self.chart.fortune.fortune[fortune.Fortune.LON]
		except Exception:
			return

		(cx, cy) = self.center.Get()
		clr  = self.options.clrtexts if not self.bw else (0, 0, 0)
		name = mtexts.txts.get('LotOfFortune', 'Fortuna')

		base = self.chart.houses.ascmc[houses.Houses.ASC] - lon
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

	def drawArabicPartsLines(self, parts, showidxs, fshift):
		(cx, cy) = self.center.Get()
		clr = self.options.clrframe if not self.bw else (0, 0, 0)
		w = 2 if self.chartsize > GraphChart2.MEDIUM_SIZE else 1
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
			base = util.normalize(self.chart.houses.ascmc[houses.Houses.ASC] - lon)
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
		if self.chartsize <= GraphChart2.MEDIUM_SIZE:
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

			ayanoffs = 0.0
			if self.options.ayanamsha != 0:
				ayanoffs = self.chart.ayanamsha

			x1 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-ayanoffs-lon))*r1
			y1 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-ayanoffs-lon))*r1
			x2 = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-ayanoffs-lon-pshift[i]))*r2
			y2 = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-ayanoffs-lon-pshift[i]))*r2
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
					if self.options.useplanetcolors:
						objidx = i
						if i == planets.Planets.PLANETS_NUM-1:
							objidx -= 1
						clr = self.options.clrindividual[objidx]
					else:
						dign = chrt.dignity(i)
						clr = clrs[dign]
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

			ayanoffs = 0.0
			if self.options.ayanamsha != 0:
				ayanoffs = self.chart.ayanamsha

			x = cx+math.cos(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-ayanoffs-lon-pshift[i]))*r
			y = cy+math.sin(math.pi+math.radians(self.chart.houses.ascmc[houses.Houses.ASC]-ayanoffs-lon-pshift[i]))*r
			
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

	# 아랫줄(새로 추가) — 텍스트 폭을 각도로 환산(반지름 r_text 기준)
	def _label_half_deg(self, text, font, r_text, margin_px=4):
		w, _ = font.getsize(text)
		px = (w/2.0) + margin_px
		return (px / float(r_text)) * (180.0 / math.pi)
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

	def mergefsaspmatrices(self):
		showfss = []

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

	def drawOuterFortuneLine(self):
		if not (self.chart and getattr(self.chart, "fortune", None)):
			return
		try:
			lon = self.chart.fortune.fortune[fortune.Fortune.LON]
		except Exception:
			return

		(cx, cy) = self.center.Get()
		clr = self.options.clrframe if not self.bw else (0, 0, 0)
		w = 2 if self.chartsize > GraphChart2.MEDIUM_SIZE else 1
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
