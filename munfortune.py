# -*- coding: utf-8 -*-
import math
import astrology
import houses
import planets
import placspec
import util
import chart


class MundaneFortune:
	'''Computes mundane Lot-of-Fortune (acc. to Placidus)'''
	LON = 0
	LAT = 1
	RA = 2
	DECL = 3

	def __init__(self, typ, ascmc2, pls, obl, placelat, abovehorizon):

		ramc = ascmc2[houses.Houses.MC][houses.Houses.RA]
		aoasc = ramc+90.0
		if aoasc >= 360.0:
			aoasc -= 360.0
		ramoon = pls.planets[astrology.SE_MOON].dataEqu[planets.Planet.RAEQU]
		rasun = pls.planets[astrology.SE_SUN].dataEqu[planets.Planet.RAEQU]
		adsun = 0.0
		self.mLoFvalid = False
		val = math.tan(math.radians(placelat))*math.tan(math.radians(pls.planets[astrology.SE_SUN].dataEqu[planets.Planet.DECLEQU]))
		if math.fabs(val) <= 1.0:
			adsun = math.degrees(math.asin(val))
			self.mLoFvalid = True
		aosun = rasun-adsun
		if aosun < 0.0:
			aosun += 360.0
		# AD/AO 계산을 Moon, Sun 모두에 대해 수행
		# Sun
		val_s = math.tan(math.radians(placelat)) * math.tan(math.radians(pls.planets[astrology.SE_SUN].dataEqu[planets.Planet.DECLEQU]))
		adsun = math.degrees(math.asin(val_s)) if math.fabs(val_s) <= 1.0 else 0.0
		aosun = rasun - adsun
		if aosun < 0.0:
			aosun += 360.0

		# Moon
		val_m = math.tan(math.radians(placelat)) * math.tan(math.radians(pls.planets[astrology.SE_MOON].dataEqu[planets.Planet.DECLEQU]))
		admoon = math.degrees(math.asin(val_m)) if math.fabs(val_m) <= 1.0 else 0.0
		aomoon = ramoon - admoon
		if aomoon < 0.0:
			aomoon += 360.0

		# 공식 분기(옵션 typ + 섹트 abovehorizon)
		# - LFMOONSUN: 항상 Asc + Moon(RA) - Sun(AO)
		# - LFDSUNMOON: 낮이면 Asc + Sun(RA) - Moon(AO), 밤이면 Asc + Moon(RA) - Sun(AO)
		# - LFDMOONSUN: 낮이면 Asc + Moon(RA) - Sun(AO), 밤이면 Asc + Sun(RA) - Moon(AO)
		use_sunRA_moonAO = None  # True면 Sun(RA)-Moon(AO), False면 Moon(RA)-Sun(AO)

		if typ == chart.Chart.LFMOONSUN:
			use_sunRA_moonAO = False
		elif typ == chart.Chart.LFDSUNMOON:
			use_sunRA_moonAO = True if abovehorizon else False
		elif typ == chart.Chart.LFDMOONSUN:
			use_sunRA_moonAO = False if abovehorizon else True

		if use_sunRA_moonAO:
			raMLoF = aoasc + rasun - aomoon
			declMLoF = pls.planets[astrology.SE_SUN].dataEqu[planets.Planet.DECLEQU]
		else:
			raMLoF = aoasc + ramoon - aosun
			declMLoF = pls.planets[astrology.SE_MOON].dataEqu[planets.Planet.DECLEQU]

		raMLoF = util.normalize(raMLoF)
		#declMLoF = pls.planets[astrology.SE_MOON].dataEqu[planets.Planet.DECLEQU]
		lonMLoF, latMLoF, dist = astrology.swe_cotrans(raMLoF, declMLoF, 1.0, obl)

		self.mfortune = (lonMLoF, latMLoF, raMLoF, declMLoF)

		self.speculum = placspec.PlacidianSpeculum(placelat, ascmc2, lonMLoF, latMLoF, raMLoF, declMLoF)

		self.valid = self.mLoFvalid and self.speculum.valid





