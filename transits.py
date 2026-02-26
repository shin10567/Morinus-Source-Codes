# -*- coding: utf-8 -*-
import astrology
import chart
import fortune
import planets
import util
import arabicparts

class Transit:
	NONE = -1
	RETR = 0
	STAT = 1

	ASC = 0
	MC = 1
	ASCMC = 2
	PLANET = 3
	SIGN = 4
	ANTISCION = 5
	CONTRAANTISCION = 6
	LOF = 7

	def __init__(self):
		self.plt = chart.Chart.NONE #PlanetTransiting
		self.pltretr = Transit.NONE
		self.obj = chart.Chart.NONE #Radix object (Planet, Asc, MC), sign change, antiscion or LoF
		self.objretr = Transit.NONE
		self.objtype = chart.Chart.NONE
		self.aspect = chart.Chart.NONE
		self.house = chart.Chart.NONE
		self.day = chart.Chart.NONE
		self.time = 0.0
		self.sign_left = chart.Chart.NONE   # 표시에 쓸 '왼쪽' 사인 인덱스
		self.sign_right = chart.Chart.NONE  # 표시에 쓸 '오른쪽' 사인 인덱스

class Transits:
	NONE = -1

	HOUR = 0
	MINUTE = 1
	SECOND = 2
	OVER = 3

	CIRCLE = 360.0
	OFFSET = 20.0 # arbitrary, greater then the Moon's average speed

	def __init__(self):
		self.transits = []
		self.flags = Transits.NONE


	def month(self, year, month, chrt, planet = -1, pos = None):
		self.flags = astrology.SEFLG_SPEED+astrology.SEFLG_SWIEPH
		if chrt.options.topocentric:
			self.flags += astrology.SEFLG_TOPOCTR
		# 리턴/특정경도(planet 지정) 탐색은, 아야남샤가 켜져 있으면 시데럴 프레임에서 수행
		# (레볼루션/선 트랜짓이 '아야남샤 적용 도수' 기준으로 정확히 맞도록)
		if planet != Transits.NONE and chrt.options.ayanamsha != 0:
			astrology.swe_set_sid_mode(chrt.options.ayanamsha-1, 0, 0)
			self.flags |= astrology.SEFLG_SIDEREAL

		lastday = 1
		for day in range(1, 31):
			valid = util.checkDate(year, month, day)
			if valid:	
				lastday = day

				valid = util.checkDate(year, month, day+1)
				if valid:
					lastday = day+1
					self.day(year, month, day, chrt, planet, pos)
				else:
					break
			else:
				break

		#lastday in month-first day in next month
		time1 = chart.Time(year, month, lastday, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
		
		year, month = util.incrMonth(year, month)
		time2 = chart.Time(year, month, 1, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)

		cnt = len(self.transits)

		if planet == Transits.NONE:
			self.cycle(time1, chrt, time2)
		else:
			self.cycleplanet(time1, chrt, time2, planet, pos)

		self.order(cnt)

#		self.printTransits(self.transits)


	def day(self, year, month, day, chrt, planet = -1, pos = None):
		if self.flags == Transits.NONE:
			self.flags = astrology.SEFLG_SPEED+astrology.SEFLG_SWIEPH
			if chrt.options.topocentric:
				self.flags += astrology.SEFLG_TOPOCTR
			# month() 없이 day()가 직접 호출될 때도 동일 규칙 적용
			if planet != Transits.NONE and chrt.options.ayanamsha != 0:
				astrology.swe_set_sid_mode(chrt.options.ayanamsha-1, 0, 0)
				self.flags |= astrology.SEFLG_SIDEREAL

		time1 = chart.Time(year, month, day, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
		time2 = chart.Time(year, month, day+1, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
				
		cnt = len(self.transits)
		if planet == Transits.NONE:
			self.cycle(time1, chrt, time2)
		else:
			self.cycleplanet(time1, chrt, time2, planet, pos)

		self.order(cnt)


	def order(self, cnt):
		if len(self.transits) > cnt+1:
			beg = cnt
			for cyc in range(len(self.transits)-beg+1):
				for i in range(beg, len(self.transits)-1):
					if self.transits[i].time > self.transits[i+1].time:
						tr = self.transits[i]
						self.transits[i] = self.transits[i+1]
						self.transits[i+1] = tr		


	def cycle(self, time1, chrt, time2):
		for j in range (planets.Planets.PLANETS_NUM-2):
			#skip Moon
			if j == astrology.SE_MOON:
				continue

			planet1 = planets.Planet(time1.jd, j, self.flags)
			planet2 = planets.Planet(time2.jd, j, self.flags)

			for a in range(len(chart.Chart.Aspects)):
				#skip minor aspects
				if a == chart.Chart.SEMISEXTIL or a == chart.Chart.SEMIQUADRAT or a == chart.Chart.QUINTILE or a == chart.Chart.SESQUIQUADRAT or a == chart.Chart.BIQUINTILE or a == chart.Chart.QUINQUNX:
					continue
				for l in range(2):
					if l == 1 and (a == chart.Chart.CONJUNCTIO or a == chart.Chart.OPPOSITIO):
						continue
					for k in range (planets.Planets.PLANETS_NUM-2):
						lon = chrt.planets.planets[k].data[planets.Planet.LONG]
						# 810 방식: 리턴 탐색은 트로피컬 목표각 사용 (수동 -아야남샤 금지)
						if l == 0:
								lon += chart.Chart.Aspects[a]
								if lon > 360.0:
									lon -= 360.0
						else:
							lon -= chart.Chart.Aspects[a]
							if lon < 0.0:
								lon += 360.0
					
						tr = self.get(planet1, planet2, time1, chrt, lon, j, k, a, Transits.HOUR, Transit.PLANET)
						if tr != None:
							self.transits.append(tr)

					#ascmc
					for h in range(2):
						lon = chrt.houses.ascmc[h]
						# 810 방식: 트로피컬 목표각 사용
						if l == 0:
							lon += chart.Chart.Aspects[a]
							if lon > 360.0:
								lon -= 360.0
						else:
							lon -= chart.Chart.Aspects[a]
							if lon < 0.0:
								lon += 360.0

						tr = self.get(planet1, planet2, time1, chrt, lon, j, h, a, Transits.HOUR, Transit.ASCMC)
						if tr != None:
							self.transits.append(tr)
											
			#signs
			signs = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0]
			for sgn in range(len(signs)):
				lona = signs[sgn]
				tr = self.get(planet1, planet2, time1, chrt, lona, j, 0, 0, Transits.HOUR, Transit.SIGN)
				if tr != None:
					self.transits.append(tr)

			#Antiscia
			for p in range (planets.Planets.PLANETS_NUM-2):
				# 이미 시데럴 보정된 값이므로 추가 보정 금지
				lona = chrt.antiscia.plantiscia[p].lon
				# 810 방식: 비교는 트로피컬이어야 하므로, 저장값이 시데럴이면 +아야남샤로 트로피컬 복원
				if chrt.options.ayanamsha != 0:
					lona = util.normalize(lona + chrt.ayanamsha)
				tr = self.get(planet1, planet2, time1, chrt, lona, j, p, chart.Chart.CONJUNCTIO, Transits.HOUR, Transit.ANTISCION)

				if tr != None:
					self.transits.append(tr)

			#ContraAntiscia
			for p in range (planets.Planets.PLANETS_NUM-2):
				# 이미 시데럴 보정된 값이므로 추가 보정 금지
				lona = chrt.antiscia.plcontraant[p].lon
				if chrt.options.ayanamsha != 0:
					lona = util.normalize(lona + chrt.ayanamsha)
				tr = self.get(planet1, planet2, time1, chrt, lona, j, p, chart.Chart.CONJUNCTIO, Transits.HOUR, Transit.ANTISCION)

				if tr != None:
					self.transits.append(tr)												

			#LoF
			lona = chrt.fortune.fortune[fortune.Fortune.LON]
			# 810 방식: 트로피컬 목표각 사용
			tr = self.get(planet1, planet2, time1, chrt, lona, j, 0, 0, Transits.HOUR, Transit.LOF)
			if tr != None:
				self.transits.append(tr)													

	def cycleplanet(self, time1, chrt, time2, planet, pos):
		# (중요) planet 지정 탐색에서 self.flags가 시데럴이면, 목표 경도(lon)도 시데럴이어야 한다.
		planet1 = planets.Planet(time1.jd, planet, self.flags)
		planet2 = planets.Planet(time2.jd, planet, self.flags)

		if chrt.options.ayanamsha != 0 and (self.flags & astrology.SEFLG_SIDEREAL):
			# 네이털 JD에서의 ayanamsha를 Swiss에서 직접 얻어 사용(저장값 의존 제거)
			ay0 = astrology.swe_get_ayanamsa_ut(chrt.time.jd)
			if pos is None:
				lon = util.normalize(chrt.planets.planets[planet].data[planets.Planet.LONG] - ay0)
			else:
				lon = util.normalize(pos - ay0)
		else:
			# 트로피컬 탐색
			lon = chrt.planets.planets[planet].data[planets.Planet.LONG] if pos is None else pos
		tr = self.get(planet1, planet2, time1, chrt, lon, planet, planet, chart.Chart.CONJUNCTIO, Transits.HOUR, Transit.PLANET)
		if tr != None:
			self.transits.append(tr)

	def get(self, planet1, planet2, time1, chrt, lon, j, k, a, unit, typ):
		if self.check(planet1.data[planets.Planet.LONG], planet2.data[planets.Planet.LONG], lon):
			fr = 0
			to = 60
			if unit == Transits.HOUR:
				fr = 0
				to = 24

			for val in range(fr, to):
				time = None
				if unit == Transits.HOUR:
					time1 = chart.Time(time1.year, time1.month, time1.day, val, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
					time2 = None
					if val+1 < to:
						time2 = chart.Time(time1.year, time1.month, time1.day, val+1, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
					else:
						y, m, d = util.incrDay(time1.year, time1.month, time1.day)
						time2 = chart.Time(y, m, d, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
				elif unit == Transits.MINUTE:
					time1 = chart.Time(time1.year, time1.month, time1.day, time1.hour, val, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
					time2 = None
					if val+1 < to:
						time2 = chart.Time(time1.year, time1.month, time1.day, time1.hour, val+1, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
					else:
						if time1.hour+1 < 24:
							time2 = chart.Time(time1.year, time1.month, time1.day, time1.hour+1, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
						else:
							y, m, d = util.incrDay(time1.year, time1.month, time1.day)
							time2 = chart.Time(y, m, d, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
				elif unit == Transits.SECOND:
					time1 = chart.Time(time1.year, time1.month, time1.day, time1.hour, time1.minute, val, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
					time2 = None
					if val+1 < to:
						time2 = chart.Time(time1.year, time1.month, time1.day, time1.hour, time1.minute, val+1, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
					else:
						if time1.minute+1 < 60:
							time2 = chart.Time(time1.year, time1.month, time1.day, time1.hour, time1.minute+1, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
						else:
							if time1.hour+1 < 24:
								time2 = chart.Time(time1.year, time1.month, time1.day, time1.hour+1, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
							else:
								y, m, d = util.incrDay(time1.year, time1.month, time1.day)
								time2 = chart.Time(y, m, d, 0, 0, 0, False, chrt.time.cal, chart.Time.GREENWICH, True, 0, 0, False, chrt.place, False)
				else:
#					print 'unit > SECOND'
					return None	

				planet1 = planets.Planet(time1.jd, j, self.flags)
				planet2 = planets.Planet(time2.jd, j, self.flags)
	
				if self.check(planet1.data[planets.Planet.LONG], planet2.data[planets.Planet.LONG], lon):
					un = Transits.OVER
					if unit == Transits.HOUR:
						un = Transits.MINUTE
					if unit == Transits.MINUTE:
						un = Transits.SECOND
				
					if un != Transits.OVER:
						return self.get(planet1, planet2, time1, chrt, lon, j, k, a, un, typ)
					else:
						tr = Transit()
						tr.plt = j
						tr.objtype = typ
						if typ == Transit.SIGN:
							# 경계 부동소수 오차 보정
							eps = 1e-6

							# 이 시각( time1 )의 황경 속도 부호로 순/역행 판정
							retr = planet1.data[planets.Planet.SPLON] < 0.0

							if retr:
								# 역행: 경계 바로 아래(-eps)가 ‘입궁하는’ 사인
								idx = int(util.normalize(lon - eps) / chart.Chart.SIGN_DEG)
								# 표기 규칙: 왼쪽 = 그 다음 사인(=지금 막 떠나온 궁), 오른쪽 = 입궁하는 궁
								left_idx  = (idx + 1) % 12
								right_idx = idx
							else:
								# 순행: 경계 바로 위(+eps)가 ‘입궁하는’ 사인
								idx = int(util.normalize(lon + eps) / chart.Chart.SIGN_DEG)
								# (참고) 순행 표기는 보통 왼쪽=이전, 오른쪽=입궁 → 기존과 동일
								left_idx  = (idx + 11) % 12
								right_idx = idx

							# 기존 호환용: obj엔 ‘입궁하는’ 사인 인덱스를 계속 넣어둔다
							tr.obj = idx

							# 새로 추가한 좌/우 표기용 인덱스 저장
							tr.sign_left = left_idx
							tr.sign_right = right_idx
						else:
							tr.obj = k

						if planet1.data[planets.Planet.SPLON] < 0.0:
							tr.pltretr = Transit.RETR
						elif planet1.data[planets.Planet.SPLON] == 0.0:
							tr.pltretr = Transit.STAT
						if typ == Transit.PLANET:
							if chrt.planets.planets[k].data[planets.Planet.SPLON] < 0.0:
								tr.objretr = Transit.RETR
							elif chrt.planets.planets[k].data[planets.Planet.SPLON] == 0.0:
								tr.objretr = Transit.STAT

						if typ != Transit.SIGN:
							tr.aspect = a
						tr.house = chrt.houses.getHousePos(planet1.data[planets.Planet.LONG], chrt.options)
						tr.day = time1.day
						tr.time = time1.time

						return tr
				
		return None



	def check(self, lon1, lon2, lon):
		# Normalize to [0,360)
		lon1 = util.normalize(lon1); lon2 = util.normalize(lon2); lon = util.normalize(lon)
		# Signed smallest arc from lon1->lon2 in (-180, 180]
		delta = (lon2 - lon1 + 540.0) % 360.0 - 180.0
		if delta == 0.0:
			return False
		# Signed offset from lon1->target
		offs = (lon - lon1 + 540.0) % 360.0 - 180.0
		if offs == 0.0:
			return True
		# Prograde vs Retrograde window test
		if delta > 0.0:
			return 0.0 < offs <= delta
		return 0.0 > offs >= delta
	
	
	def printTransits(self, ls):
		planets = ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')
		asps = ['conjunctio', 'semisextil', 'semiquadrat', 'sextil', 'quintile', 'quadrat', 'trigon', 'sesquiquadrat', 'biquintile', 'qinqunx', 'oppositio']
		signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricornus', 'Aquarius', 'Pisces']
		ascmc = ['Asc', 'MC']
	
		for tr in ls:
			d, m, s = util.decToDeg(tr.time)
			if tr.objtype == Transit.PLANET:
				print ('day %d: %s %s %s house:%d %d:%02d:%02d' % (tr.day, planets[tr.plt], asps[tr.aspect], planets[tr.obj], tr.house+1, d, m, s))
			elif tr.objtype == Transit.ASCMC:
				print ('day %d: %s %s %s house:%d %d:%02d:%02d' % (tr.day, planets[tr.plt], asps[tr.aspect], ascmc[tr.obj], tr.house+1, d, m, s))
			else:
				print ('day %d: %s %s house:%d %d:%02d:%02d' % (tr.day, planets[tr.plt], signs[tr.obj], tr.house+1, d, m, s))
	
	
	
	
	
	
