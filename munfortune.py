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
		# typ, abovehorizon은 플라시두스식에서는 사용하지 않음

		ramc = ascmc2[houses.Houses.MC][houses.Houses.RA]

		# OA(Asc) ~ RAMC + 90°
		aoasc = ramc + 90.0
		if aoasc >= 360.0:
			aoasc -= 360.0

		ramoon = pls.planets[astrology.SE_MOON].dataEqu[planets.Planet.RAEQU]
		rasun = pls.planets[astrology.SE_SUN].dataEqu[planets.Planet.RAEQU]

		# 플라시두스식: 태양에 대해서만 AD/AO 계산
		self.mLoFvalid = False
		decsun = pls.planets[astrology.SE_SUN].dataEqu[planets.Planet.DECLEQU]
		val = math.tan(math.radians(placelat)) * math.tan(math.radians(decsun))
		adsun = 0.0
		if math.fabs(val) <= 1.0:
			adsun = math.degrees(math.asin(val))
			self.mLoFvalid = True

		aosun = rasun - adsun
		if aosun < 0.0:
			aosun += 360.0

		# Placidus / Negusanti:
		# RA(LoF) = OA(Asc) + RA(Moon) − OA(Sun)
		raMLoF = aoasc + ramoon - aosun
		raMLoF = util.normalize(raMLoF)

		# 먼데인 포르투나의 적위는 항상 달과 동일
		declMLoF = pls.planets[astrology.SE_MOON].dataEqu[planets.Planet.DECLEQU]

		lonMLoF, latMLoF, dist = astrology.swe_cotrans(raMLoF, declMLoF, 1.0, obl)

		self.mfortune = (lonMLoF, latMLoF, raMLoF, declMLoF)

		self.speculum = placspec.PlacidianSpeculum(
			placelat, ascmc2, lonMLoF, latMLoF, raMLoF, declMLoF
		)

		self.valid = self.mLoFvalid and self.speculum.valid
