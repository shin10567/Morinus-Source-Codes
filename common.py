# -*- coding: utf-8 -*-

import os
import sys
import mtexts
import options
class Common:
	def __init__(self):

		self.ephepath = os.path.join('SWEP', 'Ephem')

		self.symbols = os.path.join('Res', 'Morinus.ttf')
		self.abc = os.path.join('Res', 'FreeSans.ttf')
		self.abc_bold = os.path.join('Res', 'FreeSansBold.ttf')
		# 숫자 전용(라틴) 폰트: 언어 설정(CJK)과 무관하게 항상 FreeSans로 강제
		self.abc_ascii = os.path.join('Res', 'FreeSans.ttf')
		self.freesans_bold = os.path.join('Res', 'FreeSansBold.ttf')
		# 프라이빗 폰트 등록: 이 프로세스에서만 파일의 폰트를 쓸 수 있게 함
		try:
			import ctypes
			from ctypes import wintypes
			FR_PRIVATE = 0x10
			AddFontResourceExW = ctypes.windll.gdi32.AddFontResourceExW
			AddFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
			AddFontResourceExW.restype  = wintypes.INT

			# 절대경로로 등록 (상대경로면 현재 작업폴더에 따라 실패 가능)
			def _abs(p):
				base = os.path.dirname(os.path.abspath(sys.argv[0]))
				return os.path.abspath(os.path.join(base, p))

			AddFontResourceExW(_abs(self.symbols).decode('mbcs'), FR_PRIVATE, None)
			AddFontResourceExW(_abs(self.abc).decode('mbcs'),     FR_PRIVATE, None)
			AddFontResourceExW(_abs(self.abc_ascii).decode('mbcs'),     FR_PRIVATE, None)
			AddFontResourceExW(_abs(self.freesans_bold).decode('mbcs'), FR_PRIVATE, None)
		except Exception as _e:
			# 실패해도 앱은 계속 동작하도록 무시 (원인 추적 필요하면 print)
			pass

		#self.abc = os.path.join(u'Res', u'simhei.ttf')

		opts = options.Options()
		if opts.langid < 6:
			self.abc      = os.path.join('Res', 'FreeSans.ttf')
			self.abc_bold = os.path.join('Res', 'FreeSansBold.ttf')
		else:
			if opts.langid == 6:   # Chinese (Simplified)
				self.abc      = os.path.join('Res', 'NotoSansSC-Regular.ttf')
				self.abc_bold = os.path.join('Res', 'NotoSansSC-Bold.ttf')
			elif opts.langid == 7: # Chinese (Traditional)
				self.abc      = os.path.join('Res', 'NotoSansTC-Regular.ttf')
				self.abc_bold = os.path.join('Res', 'NotoSansTC-Bold.ttf')
			elif opts.langid == 8: # Korean
				self.abc      = os.path.join('Res', 'NotoSansKR-Regular.ttf')
				self.abc_bold = os.path.join('Res', 'NotoSansKR-Bold.ttf')
			else:
				# 안전망: 그 외 언어는 라틴 기반 FreeSans
				self.abc      = os.path.join('Res', 'FreeSans.ttf')
				self.abc_bold = os.path.join('Res', 'FreeSansBold.ttf')

		# Bold 파일이 없으면 Regular로 폴백(한글/중국어 Bold 미동봉 상황 고려)
		if not os.path.exists(self.abc_bold):
			self.abc_bold = self.abc

		self.Aspects = ('M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y')
		self.Signs1 = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l')
		self.Signs2 = ('m', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x')
		self.Uranus = ('H', '6')
		self.Pluto = ('J', '7', '8', '9')
		self.Housenames = ('I', '2', '3', 'IV', '5', '6', 'VII', '8', '9', 'X', '11', '12')
		self.Housenames2 = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12')
		self.months = (mtexts.txts['January'], mtexts.txts['February'], mtexts.txts['March'], mtexts.txts['April'], mtexts.txts['May'], mtexts.txts['June'], mtexts.txts['July'], mtexts.txts['August'], mtexts.txts['September'], mtexts.txts['October'], mtexts.txts['November'], mtexts.txts['December'])

		self.monthabbr = (mtexts.txts['Jan2'], mtexts.txts['Feb2'], mtexts.txts['Mar2'], mtexts.txts['Apr2'], mtexts.txts['May2'], mtexts.txts['Jun2'], mtexts.txts['Jul2'], mtexts.txts['Aug2'], mtexts.txts['Sep2'], mtexts.txts['Oct2'], mtexts.txts['Nov2'], mtexts.txts['Dec2'])
		self.days = (mtexts.txts['Monday'], mtexts.txts['Tuesday'], mtexts.txts['Wednesday'], mtexts.txts['Thursday'], mtexts.txts['Friday'], mtexts.txts['Saturday'], mtexts.txts['Sunday'])

		self.fortune = '4'

		self.retr = 'Z'


	def update(self, options):

		uranus = self.Uranus[0]
		if not options.uranus:
			uranus = self.Uranus[1]
		pluto = self.Pluto[options.pluto]

		self.Planets = ('A', 'B', 'C', 'D', 'E', 'F', 'G', uranus, 'I', pluto, 'K', 'L')



