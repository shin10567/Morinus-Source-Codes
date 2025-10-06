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

		if self.chart2 == None and self.planetaryday and self.options.showfixstars != options.Options.NONE: #If planetaryday is True => radix chart
			if self.options.showfixstars == options.Options.FIXSTARS:
				self.showfss = self.mergefsaspmatrices()
				self.fsshift = self.arrangefs(self.chart.fixstars.data, self.showfss, self.rFixstars)
				self.fsyoffs = self.arrangeyfs(self.chart.fixstars.data, self.fsshift, self.showfss, self.rFixstars)
				#PIL doesn't want to show short lines
				self.drawFixstarsLines(self.showfss)
			elif self.options.showfixstars == options.Options.DODECATEMORIA:
				self.pshiftantis = self.arrangeAntis(self.chart.antiscia.pldodecatemoria, self.chart.antiscia.lofdodec, self.chart.antiscia.ascmcdodec, self.rAntis)
				self.drawAntisLines(self.chart.antiscia.pldodecatemoria, self.chart.antiscia.lofdodec, self.chart.antiscia.ascmcdodec, self.pshiftantis, self.r30, self.rAntisLines)
			elif self.options.showfixstars == options.Options.ANTIS:
				self.pshiftantis = self.arrangeAntis(self.chart.antiscia.plantiscia, self.chart.antiscia.lofant, self.chart.antiscia.ascmcant, self.rAntis)
				self.drawAntisLines(self.chart.antiscia.plantiscia, self.chart.antiscia.lofant, self.chart.antiscia.ascmcant, self.pshiftantis, self.r30, self.rAntisLines)
			elif self.options.showfixstars == options.Options.CANTIS:
				self.pshiftantis = self.arrangeAntis(self.chart.antiscia.plcontraant, self.chart.antiscia.lofcontraant, self.chart.antiscia.ascmccontraant, self.rAntis)
				self.drawAntisLines(self.chart.antiscia.plcontraant, self.chart.antiscia.lofcontraant, self.chart.antiscia.ascmccontraant, self.pshiftantis, self.r30, self.rAntisLines)
			elif self.options.showfixstars == options.Options.ARABICPARTS:
				if self.chart.parts and self.chart.parts.parts:
					self.apshow = list(range(len(self.chart.parts.parts)))
					self.apshift = self.arrangeParts(self.chart.parts.parts, self.apshow, self.rFixstars)
					self.apyoffs = self.arrangeyParts(self.chart.parts.parts, self.apshow, self.apshift, self.rFixstars)
					self.drawArabicPartsLines(self.chart.parts.parts, self.apshow, self.apshift)
					self.drawOuterFortuneLine()  # ⬅ 추가

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

		if self.options.aspects and self.options.symbols:
			self.drawAspectSymbols()
			if self.options.showlof and self.options.showaspectstolof:
				self.drawLoFAspectSymbols()

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
			elif self.options.showfixstars == options.Options.DODECATEMORIA:
				self.drawAntis(self.chart, self.chart.antiscia.pldodecatemoria, self.chart.antiscia.lofdodec, self.chart.antiscia.ascmcdodec, self.pshiftantis, self.rAntis)
			elif self.options.showfixstars == options.Options.ANTIS:
				self.drawAntis(self.chart, self.chart.antiscia.plantiscia, self.chart.antiscia.lofant, self.chart.antiscia.ascmcant, self.pshiftantis, self.rAntis)
			elif self.options.showfixstars == options.Options.CANTIS:
				self.drawAntis(self.chart, self.chart.antiscia.plcontraant, self.chart.antiscia.lofcontraant, self.chart.antiscia.ascmccontraant, self.pshiftantis, self.rAntis)
			elif self.options.showfixstars == options.Options.ARABICPARTS:
				if self.chart.parts and self.chart.parts.parts:
					self.drawArabicParts(self.chart.parts.parts, self.apshow, self.apshift, self.apyoffs)
					self.drawOuterFortuneText()
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
		if self.chart2 != None or (self.planetaryday and self.options.showfixstars != options.Options.NONE): #If planetaryday is True => radix chart
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
		if self.chart2 != None or (self.planetaryday and self.options.showfixstars != options.Options.NONE): #If planetaryday is True => radix chart
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
		FixStars용 arrangefs를 아라빅 파츠에 맞춰 단순화한 버전.
		겹침을 줄이기 위해 각 항목의 각도를 소폭 시프팅합니다.
		"""
		fshift = []
		num = len(showidxs)
		for _ in range(num):
			fshift.append(0.0)

		# 각도 기준 정렬
		order = sorted(range(num), key=lambda k: parts[showidxs[k]][arabicparts.ArabicParts.LONG])
		mixed = order[:]  # 표시 인덱스 매핑

		def text_w(i):
			name = parts[showidxs[i]][arabicparts.ArabicParts.NAME]
			w, h = self.fntText.getsize(name)
			return w

		# 인접 항목 간 겹침 회피
		for _ in range(num+1):
			changed = False
			for ii in range(num-1):
				i1, i2 = order[ii], order[ii+1]
				lon1 = parts[showidxs[i1]][arabicparts.ArabicParts.LONG] + fshift[i1]
				lon2 = parts[showidxs[i2]][arabicparts.ArabicParts.LONG] + fshift[i2]

				# 화면상 길이 추정: 호 길이 ≈ r * 각도
				# 텍스트 폭을 감안해 0.5도 단위로 살짝 민다
				need = (text_w(i1) + text_w(i2)) / (rText if rText else 1.0)
				need_deg = max(0.0, (need * 180.0 / 3.1415926535) * 0.1)  # 완충치

				if lon2 - lon1 < need_deg:
					# 뒤쪽을 앞으로 밀어 겹침 감소
					shift = (need_deg - (lon2 - lon1)) * 0.6
					fshift[i2] += shift
					changed = True
			if not changed:
				break

		return fshift

	def drawArabicParts(self, parts, showidxs, fshift, yoffs):

		(cx, cy) = self.center.Get()
		clr = self.options.clrtexts if not self.bw else (0, 0, 0)

		for i in range(len(showidxs)):
			idx  = showidxs[i]
			lon  = parts[idx][arabicparts.ArabicParts.LONG]
			name = parts[idx][arabicparts.ArabicParts.NAME]

			ayanoffs = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0
			ang_deg  = self.chart.houses.ascmc[houses.Houses.ASC] - ayanoffs - lon - fshift[i]
			rad      = math.pi + math.radians(ang_deg)

			# 살짝 더 바깥으로 밀어내 라벨이 테두리를 침범하지 않게 함
			r_text = self.rFixstars + self.maxradius * 0.006
			x = cx + math.cos(rad) * r_text
			y = cy + math.sin(rad) * r_text
			y += yoffs[i] 
			# 좌/우 반구 기준으로 바깥 정렬
			pos = util.normalize(math.degrees(rad))  # 0..360
			w, h = self.fntText.getsize(name)
			if 90.0 < pos < 270.0:
				# 왼쪽 반구: 기준점을 텍스트의 오른쪽 끝으로
				x -= w
			# 오른쪽 반구: 기준점을 왼쪽 끝으로 그대로 둠

			self.draw.text((x, y - h/2), name, fill=clr, font=self.fntText)

	def drawOuterFortuneText(self):
		# 포르투나의 경도 가져오기
		if not hasattr(self.chart, "fortune") or self.chart.fortune is None:
			return
		try:
			lon = self.chart.fortune.fortune[fortune.Fortune.LON]
		except Exception:
			return

		(cx, cy) = self.center.Get()
		clr = self.options.clrtexts if not self.bw else (0, 0, 0)

		# 라벨 텍스트(다국어 키가 있으면 사용, 없으면 'Fortune')
		name = mtexts.txts.get('LotOfFortune', 'Fortuna')

		ayanoffs = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0
		ang_deg  = self.chart.houses.ascmc[houses.Houses.ASC] - ayanoffs - lon
		rad      = math.pi + math.radians(ang_deg)

		# 바깥 고리 라벨 반지름(고정별·아라빅 파츠와 동일 + 약간의 여백)
		r_text = self.rFixstars + self.maxradius * 0.006
		x = cx + math.cos(rad) * r_text
		y = cy + math.sin(rad) * r_text

		# 왼쪽/오른쪽 반구에 따라 바깥 정렬
		pos = util.normalize(math.degrees(rad))  # 0..360
		w, h = self.fntText.getsize(name)
		if 90.0 < pos < 270.0:
			x -= w  # 왼쪽 반구: 텍스트를 바깥쪽 정렬

		self.draw.text((x, y - h/2), name, fill=clr, font=self.fntText)


	def drawArabicPartsLines(self, parts, showidxs, fshift):
		(cx, cy) = self.center.Get()
		clr = self.options.clrframe if not self.bw else (0,0,0)
		w = 2 if self.chartsize > GraphChart.MEDIUM_SIZE else 1
		pen = wx.Pen(clr, w)
		self.bdc.SetPen(pen)

		for i in range(len(showidxs)):
			idx = showidxs[i]
			lon = parts[idx][arabicparts.ArabicParts.LONG]
			ayanoffs = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0

			ang = self.chart.houses.ascmc[houses.Houses.ASC] - ayanoffs - lon - fshift[i]
			x1 = cx + math.cos(math.pi + math.radians(ang)) * self.r30
			y1 = cy + math.sin(math.pi + math.radians(ang)) * self.r30
			x2 = cx + math.cos(math.pi + math.radians(ang)) * self.rOuterLine
			y2 = cy + math.sin(math.pi + math.radians(ang)) * self.rOuterLine

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
	def drawOuterFortuneLine(self):
		# 포르투나 존재 확인
		if not hasattr(self.chart, "fortune") or self.chart.fortune is None:
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

		# 텍스트와 동일한 기준(아야남샤 반영)으로 두 점 계산
		ayanoffs = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0
		ang = self.chart.houses.ascmc[houses.Houses.ASC] - ayanoffs - lon
		x1 = cx + math.cos(math.pi + math.radians(ang)) * self.r30
		y1 = cy + math.sin(math.pi + math.radians(ang)) * self.r30
		x2 = cx + math.cos(math.pi + math.radians(ang)) * self.rOuterLine
		y2 = cy + math.sin(math.pi + math.radians(ang)) * self.rOuterLine

		self.bdc.DrawLine(x1, y1, x2, y2)

	def arrangeyParts(self, parts, showidxs, fshift, rText):
		(cx, cy) = self.center.Get()
		yoffs = [0.0] * len(showidxs)
		if len(showidxs) < 2:
			return yoffs

		# 각도 기준 정렬(시프팅 반영)
		order = sorted(range(len(showidxs)),
					key=lambda k: parts[showidxs[k]][arabicparts.ArabicParts.LONG] + fshift[k])

		# 겹치면 반구 방향으로 한쪽을 위/아래로 밀기
		step = self.maxradius * 0.012  # 레인 간 간격(필요하면 조절)
		for _ in range(len(order) + 1):
			changed = False
			for a, b in zip(order, order[1:]):
				lon1 = parts[showidxs[a]][arabicparts.ArabicParts.LONG] + fshift[a]
				lon2 = parts[showidxs[b]][arabicparts.ArabicParts.LONG] + fshift[b]

				ayan = self.chart.ayanamsha if self.options.ayanamsha != 0 else 0.0
				ang1 = math.pi + math.radians(self.chart.houses.ascmc[houses.Houses.ASC] - ayan - lon1)
				ang2 = math.pi + math.radians(self.chart.houses.ascmc[houses.Houses.ASC] - ayan - lon2)

				x1 = cx + math.cos(ang1) * rText
				y1 = cy + math.sin(ang1) * rText
				x2 = cx + math.cos(ang2) * rText
				y2 = cy + math.sin(ang2) * rText

				name1 = parts[showidxs[a]][arabicparts.ArabicParts.NAME]
				name2 = parts[showidxs[b]][arabicparts.ArabicParts.NAME]
				w1, h1 = self.fntText.getsize(name1)
				w2, h2 = self.fntText.getsize(name2)

				# 반구에 따라 기준점을 오른쪽 정렬(왼쪽 반구) / 왼쪽 정렬(오른쪽 반구)
				def x_left(x, ang, w):
					deg = util.normalize(math.degrees(ang))
					return x - (w if 90.0 < deg < 270.0 else 0.0)

				while self.overlap(x_left(x1, ang1, w1), y1 + yoffs[a] - h1/2, w1, h1,
								x_left(x2, ang2, w2), y2 + yoffs[b] - h2/2, w2, h2):
					# 뒤쪽(b)을 한 칸 밀기(왼쪽 반구면 아래로, 오른쪽 반구면 위로)
					deg = util.normalize(math.degrees(ang2))
					yoffs[b] += (step if 90.0 < deg < 270.0 else -step)
					changed = True

			if not changed:
				break

		return yoffs








