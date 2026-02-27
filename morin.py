# -*- coding: utf-8 -*-

import wx
import wx.adv
import os
import pickle
# ###########################################
# Roberto change  V 7.2.0
import datetime
# ###########################################
import Image
import astrology
import houses
import planets
import chart
import common
import graphchart
import graphchart2
import revolutions
import suntransits
import secdir
import transits
import personaldatadlg
import findtimedlg
import graphephemdlg
import appearance1dlg
import appearance2dlg
import dignitiesdlg
import colorsdlg
import primarydirsdlg
import primarydirsdlgsmall
import fortunedlg
import arabicpartsdlg
import fixstarsdlg
import triplicitiesdlg
import termsdlg
import decansdlg
# ###########################################
# Roberto change  V 7.2.0
import defaultlocdlg
# ###########################################
import ayanamshadlg
import profdlg
import profections
import profectionsframe
import munprofections
import profectionstepperdlg
import proftabledlg
import profstableframe
# ###########################################
# Roberto change  V 7.3.0
import firdariaframe
# ###########################################
import profectiontablestepperdlg
import almutenchartdlg
import almutentopicalsdlg
import almutentopicalsframe
import orbisdlg
import langsdlg
import symbolsdlg
import timespacedlg
import transitmdlg
import revolutionsdlg
import syzygydlg
import suntransitsdlg
import secdirdlg
import stepperdlg
import graphephemframe
import positionsframe
import squarechartframe
import almutenchartframe
import almutenzodsframe
import secdirui
import miscframe
import customerframe
import risesetframe
import speedsframe
import munposframe
import arabicpartsframe
import antisciaframe
# ###################################
# Elias change v 8.0.0
import dodecatemoriaframe
# ###################################
import zodparsframe
import stripframe
import fixstarsframe
import fixstarsaspectsframe
import fixstarsparallelsframe
import hoursframe
import midpointsframe
import aspectsframe
import transitmframe
import transitframe
import secdirframe
import electionsframe
import mundaneframe
import profdlgopts
# ###########################################
# Roberto change  V 7.3.0
import firdariadlg
# ###########################################
import pdsinchartdlgopts
import pdsinchartterrdlgopts
import electionstepperdlg
import zodiacalreleasingframe
import primdirslistframe
import primdirs
import primarykeysdlg
import primdirsrangedlg
import placidiansapd
import placidianutppd
import regiomontanpd
import campanianpd
import _thread
import options
import util
import paranframe
import mtexts
import htmlhelpframe
import customerpd
import ephemcalc
import wx.lib.newevent
import math #solar precession
import circumambulationframe
import fixstardirsframe
import os, sys, wx
import sys  # 위쪽 import들 근처에 이미 있다면 생략
import json
import urllib.request as urllib2
import urllib
import eclipsesframe
import dodecacalcframe

# morin.py 상단 어딘가 (import wx 아래)
LANG_MAP = {
	0: wx.LANGUAGE_ENGLISH,            # English
	1: wx.LANGUAGE_HUNGARIAN,          # Hungarian
	2: wx.LANGUAGE_ITALIAN,            # Italian
	3: wx.LANGUAGE_FRENCH,             # French
	4: wx.LANGUAGE_RUSSIAN,            # Russian
	5: wx.LANGUAGE_SPANISH,            # Spanish
	6: wx.LANGUAGE_CHINESE_SIMPLIFIED, # Chinese (Simplified)
	7: wx.LANGUAGE_CHINESE_TRADITIONAL,# Chinese (Traditional)
	8: wx.LANGUAGE_KOREAN,             # Korean
}

def _res_path(name):
	# PyInstaller(onefile/onedir) 모두에서 아이콘을 안정적으로 찾기 위한 경로 헬퍼
	if hasattr(sys, "_MEIPASS"):  # PyInstaller 실행 시 임시 폴더
		return os.path.join(sys._MEIPASS, name)
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


(PDReadyEvent, EVT_PDREADY) = wx.lib.newevent.NewEvent()
pdlock = _thread.allocate_lock()

#menubar

class MFrame(wx.Frame):

	def _close_non_main_frames(self):
		import wx
		# 메인 프레임(self)을 제외한 모든 TopLevel Frame을 닫는다.
		for w in wx.GetTopLevelWindows():
			try:
				# 메인 프레임은 제외
				if w is self:
					continue
				# Options 같은 wx.Dialog는 건드리지 않고,
				# 보조 차트 창(대부분 wx.Frame 파생)을 닫는다.
				if isinstance(w, wx.Frame) and not isinstance(w, wx.Dialog):
					# True로 강제 종료해 누수 방지
					w.Close(True)
			except Exception:
				# 개별 창에서 에러 나도 전체 동작은 유지
				pass

	def __init__(self, parent, id, title, opts):
# ###########################################
# Roberto Size changed  V 7.X.X
		wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(656, 560))
# ###########################################
		face = {6: 'Noto Sans SC', 7: 'Noto Sans TC', 8: 'Noto Sans KR'}.get(opts.langid, 'FreeSans')
		self.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, face))

		self.fpath = ''
		self.fpathhors = u'Hors'
		self.fpathimgs = u'Images'
		self.title = title
		self.origtitle = title
		self.hortitle = title
		
		self.options = opts
		import importlib
		importlib.reload(mtexts)  # 저장된 mtexts.py 변경분까지 즉시 재적재
		mtexts.setLang(self.options.langid)

		# wx 표준 라벨(파일 대화상자 버튼, About 등)도 새 로케일로 갱신
		self._locale = wx.Locale(LANG_MAP.get(self.options.langid, wx.LANGUAGE_ENGLISH))
		try:
			self._locale.AddCatalog("wxstd")
			self._locale.AddCatalog("wx")
		except Exception:
			pass

		# 선택된 언어로 wx 로케일 고정 (About 라벨 등 표준 문자열이 번역됨)
		self._locale = wx.Locale(LANG_MAP.get(opts.langid, wx.LANGUAGE_ENGLISH))
		try:
			# 표준 카탈로그(라벨 번역) 로드 시도
			self._locale.AddCatalog("wxstd")
			self._locale.AddCatalog("wx")
		except Exception:
			pass
		common.common = common.Common()
		common.common.update(self.options)

		self.CenterOnScreen()
		self.SetMinSize((200,200))
		self.SetBackgroundColour(self.options.clrbackground)

		self.dirty = False

		menubar = wx.MenuBar()
		self.mhoros = wx.Menu()
		self.mtable = wx.Menu()
		self.moptions = wx.Menu()
		self.mcharts = wx.Menu()
		self.mhelp = wx.Menu()

		self.menubar = menubar

		#Horoscope-menu
# ###########################################
# Roberto change  V 7.2.0 # Elias v 8.0.0 add Dodecatemoria
		self.ID_New, self.ID_Data, self.ID_HereAndNow, self.ID_Load, self.ID_Save, self.ID_SaveAsBitmap, self.ID_Synastry, self.ID_FindTime, self.ID_Ephemeris, self.ID_Close, self.ID_Exit = range(100, 111)
# ###########################################

		#Table-menu
# ###########################################
# Roberto change  V 7.3.0 + V 8.0.1		
		(self.ID_Positions, self.ID_TAlmutens, self.ID_AlmutenZodiacal, self.ID_AlmutenChart, self.ID_AlmutenTopical, self.ID_Misc, self.ID_MunPos, 
		self.ID_Antiscia, self.ID_Aspects, self.ID_Midpoints, self.ID_RiseSet, self.ID_Speeds, self.ID_ZodPars, self.ID_FixStars, self.ID_FixStarsAsps, 
		self.ID_Arabians, self.ID_Strip, self.ID_PlanetaryHours, self.ID_ExactTransits, self.ID_Profections, self.ID_CustomerSpeculum, self.ID_Firdaria, self.ID_Dodecatemoria,self.ID_PrimaryDirs , self.ID_AngleAtBirth) = range(111,136)
		self.ID_ZodiacalReleasing = 136
		self.ID_Phasis = 137
		self.ID_Paranatellonta = 138
		self.ID_Circumambulation = 139
		self.ID_Eclipses = 186
		self.ID_Decennials = 187
		self.ID_FixStarAngleDirs = 185  # Angular directions of fixed stars
		self.ID_FixStarsParallels = 188
		#Charts-menu
		self.ID_Transits, self.ID_Revolutions, self.ID_SunTransits, self.ID_SecondaryDirs, self.ID_Elections, self.ID_SquareChart, self.ID_ProfectionsChart, self.ID_MundaneChart = range(140, 148)
		self.ID_SecProgMenu = 5000  # Secondary progressions (submenu header)
		# --- new submenu headers ---
		self.ID_PlanetsPointsMenu = 5001
		self.ID_FixedStarsMenu   = 5002
		self.ID_TimeLordsMenu    = 5003
		self.ID_PrimaryDirsMenu  = 5004
		self.ID_TransitsMenu     = 5005
		self.ID_ChartsMenu      = 5016
		# --- Options submenu headers ---
		# --- New submenu headers ---
		self.ID_SaveMenu            = 5006  # Horoscope > Save group
		self.ID_ArabicPartsOptMenu  = 5011  # Options > ArabicParts (Fortuna+Arabic Parts)
		self.ID_PrimaryDirsOptMenu  = 5012  # Options > PrimaryDirs (Dirs+Keys+PDs in Chart)
		self.ID_TimeLordsOptMenu    = 5013  # Options > TimeLords (Profections+Firdaria)
		self.ID_AppearanceOptMenu   = 5014  # Options > Appearance1 (Appearance1/2+Colors+Symbols)
		self.ID_DignitiesOptMenu    = 5015  # Options > Dignities (Dignities+Minor Dignities)
		self.ID_PlanetsPointsOptMenu    = 5017  # Options > Planets/Points
		# Secondary progressions (Charts submenu)
		self.ID_SecProgChart = 148
		self.ID_SecProgPositions = 149

		#Options-menu
# ###########################################
# Roberto change  V 7.2.0
		(self.ID_Appearance1, self.ID_Appearance2, self.ID_Symbols, self.ID_Dignities, self.ID_MinorDignities, self.ID_Triplicities, self.ID_Terms, 
		self.ID_Decans, self.ID_Almutens, self.ID_ChartAlmuten, self.ID_Topical, self.ID_Colors, self.ID_Ayanamsha, self.ID_HouseSystem, 
		self.ID_Nodes, self.ID_Orbs, self.ID_PrimaryDirsOpt, self.ID_PrimaryKeys, self.ID_PDsInChartOpt, self.ID_PDsInChartOptZod, self.ID_PDsInChartOptMun, self.ID_LotOfFortune, self.ID_ArabicParts, self.ID_Syzygy, self.ID_FixStarsOpt, self.ID_ProfectionsOpt, self.ID_FirdariaOpt, self.ID_DefLocationOpt, self.ID_Languages, self.ID_AutoSaveOpts, self.ID_SaveOpts, self.ID_Reload) = range(151, 183)
# ###########################################

		self.ID_Housesystem1, self.ID_Housesystem2, self.ID_Housesystem3, self.ID_Housesystem4, self.ID_Housesystem5, self.ID_Housesystem6, self.ID_Housesystem7, self.ID_Housesystem8, self.ID_Housesystem9, self.ID_Housesystem10, self.ID_Housesystem11, self.ID_Housesystem12 = range(1050, 1062)

		self.ID_NodeMean = 1070
		self.ID_NodeTrue = 1071

		self.hsbase = 1050
		self.nodebase = 1070
# ###########################################
# Roberto change  V 7.2.0 /  V 7.3.0
		#Help-menu
		self.ID_Help = 183
		self.ID_About = 184
# ###########################################

		#Horoscope-menu
		self.mhoros.Append(self.ID_New, mtexts.menutxts['HMNew'], mtexts.menutxts['HMNewDoc'])
		self.mhoros.Append(self.ID_Data, mtexts.menutxts['HMData'], mtexts.menutxts['HMDataDoc'])
# ###########################################
# Roberto change  V 7.2.0		
		self.mhoros.Append(self.ID_HereAndNow, mtexts.menutxts['HMHereAndNow'], mtexts.menutxts['HMHereAndNowDoc'])
# ###########################################
		self.mhoros.Append(self.ID_Load, mtexts.menutxts['HMLoad'], mtexts.menutxts['HMLoadDoc'])
		# Save group
		self.hsave = wx.Menu()
		self.hsave.Append(self.ID_Save,          mtexts.menutxts['HMSave'],       mtexts.menutxts['HMSaveDoc'])
		self.hsave.Append(self.ID_SaveAsBitmap,  mtexts.menutxts['HMSaveAsBmp'],  mtexts.menutxts['HMSaveAsBmpDoc'])
		self.mhoros.Append(self.ID_SaveMenu, mtexts.txts['Save'], self.hsave)

		self.mhoros.Append(self.ID_Synastry, mtexts.menutxts['HMSynastry'], mtexts.menutxts['HMSynastryDoc'])
		self.mhoros.Append(self.ID_FindTime, mtexts.menutxts['HMFindTime'], mtexts.menutxts['HMFindTimeDoc'])
		self.mhoros.Append(self.ID_Ephemeris, mtexts.menutxts['HMEphemeris'], mtexts.menutxts['HMEphemerisDoc'])
		self.mhoros.AppendSeparator()
		self.mhoros.Append(self.ID_Close, mtexts.menutxts['HMClose'], mtexts.menutxts['HMCloseDoc'])
		self.mhoros.AppendSeparator()
		self.mhoros.Append(self.ID_Exit, mtexts.menutxts['HMExit'], mtexts.menutxts['HMExitDoc'])

		self.filehistory = wx.FileHistory()
		self.filehistory.UseMenu(self.mhoros)
		self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)

		#Table-menu
		# ---------------- Tables (grouped) ----------------

		# Planets/Points
		self.tplanets = wx.Menu()
		self.tplanets.Append(self.ID_Positions,        mtexts.menutxts['TMPositions'],        mtexts.menutxts['TMPositionsDoc'])   
		self.tplanets.Append(self.ID_Antiscia,         mtexts.menutxts['TMAntiscia'],         mtexts.menutxts['TMAntisciaDoc'])        
		self.tplanets.Append(self.ID_Dodecatemoria,    mtexts.menutxts['TMDodecatemoria'],    mtexts.menutxts['TMDodecatemoriaDoc'])
		self.tplanets.Append(self.ID_Strip,            mtexts.menutxts['TMStrip'],            mtexts.menutxts['TMStripDoc'])   
		self.tplanets.Append(self.ID_Aspects,          mtexts.menutxts['TMAspects'],          mtexts.menutxts['TMAspectsDoc']) 
		self.tplanets.Append(self.ID_ZodPars,          mtexts.menutxts['TMZodPars'],          mtexts.menutxts['TMZodParsDoc'])
		self.tplanets.Append(self.ID_Speeds,           mtexts.menutxts['TMSpeeds'],           mtexts.menutxts['TMSpeedsDoc'])
		self.tplanets.Append(self.ID_RiseSet,          mtexts.menutxts['TMRiseSet'],          mtexts.menutxts['TMRiseSetDoc'])     
		self.tplanets.Append(self.ID_PlanetaryHours,   mtexts.menutxts['TMPlanetaryHours'],   mtexts.menutxts['TMPlanetaryHoursDoc'])
		self.tplanets.Append(self.ID_Phasis,           mtexts.menutxts['TMPhasis'],           mtexts.menutxts['TMPhasisDoc'])     
		self.tplanets.Append(self.ID_Midpoints,        mtexts.menutxts['TMMidpoints'],        mtexts.menutxts['TMMidpointsDoc'])
		self.tplanets.Append(self.ID_Arabians,         mtexts.menutxts['TMArabianParts'],     mtexts.menutxts['TMArabianPartsDoc'])
		self.tplanets.Append(self.ID_Eclipses,         mtexts.menutxts['TMEclipses'],         mtexts.menutxts['TMEclipsesDoc'])
		self.tplanets.Append(self.ID_Misc,             mtexts.menutxts['TMMisc'],             mtexts.menutxts['TMMiscDoc'])
		self.mtable.Append(self.ID_PlanetsPointsMenu, mtexts.txts['PlanetsPoints'], self.tplanets)

		# Almutens (existing submenu)
		self.talmutens = wx.Menu()
		self.talmutens.Append(self.ID_AlmutenChart,    mtexts.menutxts['TMAlmutenChart'],    mtexts.menutxts['TMAlmutenChartDoc'])
		self.talmutens.Append(self.ID_AlmutenZodiacal, mtexts.menutxts['TMAlmutenZodiacal'], mtexts.menutxts['TMAlmutenZodiacalDoc'])
		
		self.talmutens.Append(self.ID_AlmutenTopical,  mtexts.menutxts['TMAlmutenTopical'],  mtexts.menutxts['TMAlmutenTopicalDoc'])
		self.mtable.Append(self.ID_TAlmutens, mtexts.menutxts['TMAlmutens'], self.talmutens)
		# (Almutens 서브메뉴가 이미 존재하는 형태는 파일에 보임) :contentReference[oaicite:4]{index=4}

		# Fixed Stars
		self.tfixed = wx.Menu()
		self.tfixed.Append(self.ID_FixStars,        mtexts.menutxts['TMFixStars'],        mtexts.menutxts['TMFixStarsDoc'])
		self.tfixed.Append(self.ID_FixStarsAsps,    mtexts.menutxts['TMFixStarsAsps'],    mtexts.menutxts['TMFixStarsAspsDoc'])
		self.tfixed.Append(self.ID_FixStarsParallels, mtexts.menutxts['TMFixStarsParallels'], mtexts.menutxts['TMFixStarsParallelsDoc'])
		self.tfixed.Append(self.ID_Paranatellonta,  mtexts.menutxts['TMParanatellonta'],  mtexts.menutxts['TMParanatellontaDoc'])
		self.tfixed.Append(self.ID_AngleAtBirth,    mtexts.menutxts['TMAngleAtBirth'],    mtexts.menutxts['TMAngleAtBirthDoc'])
		self.mtable.Append(self.ID_FixedStarsMenu, mtexts.txts['FixStars'], self.tfixed)

		# Time Lords
		self.ttimelords = wx.Menu()
		self.ttimelords.Append(self.ID_Profections,        mtexts.menutxts['TMProfections'],        mtexts.menutxts['TMProfectionsDoc'])
		self.ttimelords.Append(self.ID_Firdaria,           mtexts.menutxts['TMFirdaria'],           mtexts.menutxts['TMFirdariaDoc'])
		self.ttimelords.Append(self.ID_Decennials,        mtexts.menutxts['TMDecennials'],        mtexts.menutxts['TMDecennialsDoc'])
		self.ttimelords.Append(self.ID_ZodiacalReleasing,  mtexts.menutxts['TMZodiacalReleasing'],  mtexts.menutxts['TMZodiacalReleasingDoc'])
		self.ttimelords.Append(self.ID_Circumambulation,   mtexts.menutxts['TMCircumambulation'],   mtexts.menutxts['TMCircumambulationDoc'])
		
		self.mtable.Append(self.ID_TimeLordsMenu, mtexts.txts['TimeLords'], self.ttimelords)

		# Primary Directions
		self.tpd = wx.Menu()
		self.tpd.Append(self.ID_PrimaryDirs,        mtexts.menutxts['TMPrimaryDirs'],        mtexts.menutxts['TMPrimaryDirsDoc'])
		self.tpd.Append(self.ID_FixStarAngleDirs,   mtexts.menutxts['TMFixStarAngleDirs'],   mtexts.menutxts['TMFixStarAngleDirsDoc'])
		self.tpd.Append(self.ID_MunPos,           mtexts.menutxts['TMMunPos'],           mtexts.menutxts['TMMunPosDoc']) 
		self.tpd.Append(self.ID_CustomerSpeculum,   mtexts.menutxts['TMCustomerSpeculum'],   mtexts.menutxts['TMCustomerSpeculumDoc'])
		self.mtable.Append(self.ID_PrimaryDirsMenu, mtexts.txts['PrimaryDirs'], self.tpd)

		# Un-grouped (요청대로 단독 유지)
		self.mtable.Append(self.ID_ExactTransits, mtexts.menutxts['TMExactTransits'], mtexts.menutxts['TMExactTransitsDoc'])

		#Charts-menu
		# 앞부분: 기본 항목 먼저
		self.chartsmenu2 = wx.Menu()
		self.chartsmenu2.Append(self.ID_SquareChart,     mtexts.menutxts['PMSquareChart'],     mtexts.menutxts['PMSquareChartDoc'])
		self.chartsmenu2.Append(self.ID_MundaneChart,    mtexts.menutxts['PMMundane'],         mtexts.menutxts['PMMundaneDoc'])
		self.chartsmenu2.Append(self.ID_Elections,       mtexts.menutxts['PMElections'],       mtexts.menutxts['PMElectionsDoc'])
		self.mcharts.Append(self.ID_ChartsMenu, mtexts.txts['DCharts'], self.chartsmenu2)

		self.mcharts.Append(self.ID_ProfectionsChart,mtexts.menutxts['PMProfections'],     mtexts.menutxts['PMProfectionsDoc'])

		# Secondary Progressions 서브메뉴(기존 그대로)
		self.csecprog = wx.Menu()
		self.csecprog.Append(self.ID_SecProgChart,     mtexts.menutxts['PMSecondaryDirs'],    mtexts.menutxts['PMSecondaryDirsDoc'])
		self.csecprog.Append(self.ID_SecProgPositions, mtexts.menutxts['PMPositionForDate'],  mtexts.menutxts['PMPositionForDateDoc'])
		self.mcharts.Append(self.ID_SecProgMenu, mtexts.txts['SecondaryDirs'], self.csecprog)

		self.mcharts.Append(self.ID_Revolutions,     mtexts.menutxts['PMRevolutions'],     mtexts.menutxts['PMRevolutionsDoc'])

		# Transits 서브메뉴 신설
		self.ctransits = wx.Menu()
		self.ctransits.Append(self.ID_Transits,    mtexts.menutxts['PMTransits'],    mtexts.menutxts['PMTransitsDoc'])
		self.ctransits.Append(self.ID_SunTransits, mtexts.menutxts['PMSunTransits'], mtexts.menutxts['PMSunTransitsDoc'])
		self.mcharts.Append(self.ID_TransitsMenu, mtexts.txts['Transits'], self.ctransits)


		#Options-menu
		self.mhousesystem = wx.Menu()
		self.itplac = self.mhousesystem.Append(self.ID_Housesystem1, mtexts.menutxts['OMHSPlacidus'], '', wx.ITEM_RADIO)
		self.itkoch = self.mhousesystem.Append(self.ID_Housesystem2, mtexts.menutxts['OMHSKoch'], '', wx.ITEM_RADIO)
		self.itregio = self.mhousesystem.Append(self.ID_Housesystem3, mtexts.menutxts['OMHSRegiomontanus'], '', wx.ITEM_RADIO)
		self.itcampa = self.mhousesystem.Append(self.ID_Housesystem4, mtexts.menutxts['OMHSCampanus'], '', wx.ITEM_RADIO)
		self.itequal = self.mhousesystem.Append(self.ID_Housesystem5, mtexts.menutxts['OMHSEqual'], '', wx.ITEM_RADIO)
		self.itwholesign = self.mhousesystem.Append(self.ID_Housesystem6, mtexts.menutxts['OMHSWholeSign'], '', wx.ITEM_RADIO)
		self.itaxial = self.mhousesystem.Append(self.ID_Housesystem7, mtexts.menutxts['OMHSAxial'], '', wx.ITEM_RADIO)
		self.itmorin = self.mhousesystem.Append(self.ID_Housesystem8, mtexts.menutxts['OMHSMorinus'], '', wx.ITEM_RADIO)
		self.ithoriz = self.mhousesystem.Append(self.ID_Housesystem9, mtexts.menutxts['OMHSHorizontal'], '', wx.ITEM_RADIO)
		self.itpage = self.mhousesystem.Append(self.ID_Housesystem10, mtexts.menutxts['OMHSPagePolich'], '', wx.ITEM_RADIO)
		self.italcab = self.mhousesystem.Append(self.ID_Housesystem11, mtexts.menutxts['OMHSAlcabitus'], '', wx.ITEM_RADIO)
		self.itporph = self.mhousesystem.Append(self.ID_Housesystem12, mtexts.menutxts['OMHSPorphyrius'], '', wx.ITEM_RADIO)

		# [Appearance1] submenu: Appearance1/Speculum(=Appearance2)/Colors/Symbols
		self.o_appearance = wx.Menu()
		self.o_appearance.Append(self.ID_Appearance1, mtexts.menutxts['OMAppearance1'], mtexts.menutxts['OMAppearance1Doc'])

		self.o_appearance.Append(self.ID_Colors,      mtexts.menutxts['OMColors'],      mtexts.menutxts['OMColorsDoc'])
		self.o_appearance.Append(self.ID_Symbols,     mtexts.menutxts['OMSymbols'],     mtexts.menutxts['OMSymbolsDoc'])
		self.moptions.Append(self.ID_AppearanceOptMenu, mtexts.txts['DDCharts'], self.o_appearance)

		self.o_appearance.Append(self.ID_Ayanamsha, mtexts.menutxts['OMAyanamsha'], mtexts.menutxts['OMAyanamshaDoc'])
		self.o_appearance.Append(self.ID_HouseSystem, mtexts.menutxts['OMHouseSystem'], self.mhousesystem)
		self.setHouse()

		self.o_planetsopt = wx.Menu()
		self.o_planetsopt.Append(self.ID_Appearance2, mtexts.menutxts['OMAppearance2'], mtexts.menutxts['OMAppearance2Doc'])
		self.o_planetsopt.Append(self.ID_Orbs, mtexts.menutxts['OMOrbs'], mtexts.menutxts['OMOrbsDoc'])
		# [Dignities] submenu: Dignities + Minor Dignities(submenu)
		self.o_digs = wx.Menu()
		self.o_digs.Append(self.ID_Dignities, mtexts.menutxts['OMDignities'], mtexts.menutxts['OMDignitiesDoc'])
		self.mdignities = wx.Menu()
		self.mdignities.Append(self.ID_Triplicities, mtexts.menutxts['OMTriplicities'], mtexts.menutxts['OMTriplicitiesDoc'])
		self.mdignities.Append(self.ID_Terms,        mtexts.menutxts['OMTerms'],        mtexts.menutxts['OMTermsDoc'])
		self.mdignities.Append(self.ID_Decans,       mtexts.menutxts['OMDecans'],       mtexts.menutxts['OMDecansDoc'])
		self.o_digs.Append(self.ID_MinorDignities, mtexts.menutxts['OMMinorDignities'], self.mdignities)
		self.o_planetsopt.Append(self.ID_DignitiesOptMenu, mtexts.txts['Dignities'], self.o_digs)
		self.mnodes = wx.Menu()
		self.meanitem = self.mnodes.Append(self.ID_NodeMean, mtexts.menutxts['OMNMean'], '', wx.ITEM_RADIO)
		self.trueitem = self.mnodes.Append(self.ID_NodeTrue, mtexts.menutxts['OMNTrue'], '', wx.ITEM_RADIO)
		self.o_planetsopt.Append(self.ID_Nodes, mtexts.menutxts['OMNodes'], self.mnodes)
		self.setNode()
		# [ArabicParts] submenu: Arabic Parts(first) + Fortuna(second)
		self.o_arabic = wx.Menu()
		self.o_arabic.Append(self.ID_ArabicParts,  mtexts.menutxts['OMArabicParts'],  mtexts.menutxts['OMArabicPartsDoc'])
		self.o_arabic.Append(self.ID_LotOfFortune, mtexts.menutxts['OMLotFortune'],   mtexts.menutxts['OMLotFortuneDoc'])
		self.o_planetsopt.Append(self.ID_ArabicPartsOptMenu, mtexts.txts['ArabicParts'], self.o_arabic)

		self.o_planetsopt.Append(self.ID_Syzygy,      mtexts.menutxts['OMSyzygy'],      mtexts.menutxts['OMSyzygyDoc'])
		self.moptions.Append(self.ID_PlanetsPointsOptMenu, mtexts.txts['PlanetsPoints'], self.o_planetsopt)

		self.malmutens = wx.Menu()
		self.malmutens.Append(self.ID_ChartAlmuten, mtexts.menutxts['OMChartAlmuten'], mtexts.menutxts['OMChartAlmutenDoc'])
		self.malmutens.Append(self.ID_Topical, mtexts.menutxts['OMTopical'], mtexts.menutxts['OMTopicalDoc'])
		self.moptions.Append(self.ID_Almutens, mtexts.menutxts['OMAlmutens'], self.malmutens)

		self.moptions.Append(self.ID_FixStarsOpt, mtexts.menutxts['OMFixStarsOpt'], mtexts.menutxts['OMFixStarsOptDoc'])
		
		# [TimeLords] submenu: Profections + Firdaria
		self.o_tl = wx.Menu()
		self.o_tl.Append(self.ID_ProfectionsOpt, mtexts.menutxts['OMProfectionsOpt'], mtexts.menutxts['OMProfectionsOptDoc'])
		self.o_tl.Append(self.ID_FirdariaOpt,    mtexts.menutxts['OMFirdariaOpt'],    mtexts.menutxts['OMFirdariaOptDoc'])
		self.moptions.Append(self.ID_TimeLordsOptMenu, mtexts.txts['TimeLords'], self.o_tl)

		# [PrimaryDirs] submenu: Primary Dirs + Primary Keys + PDs in Chart(submenu)
		self.o_pd = wx.Menu()
		self.o_pd.Append(self.ID_PrimaryDirsOpt, mtexts.menutxts['OMPrimaryDirs'], mtexts.menutxts['OMPrimaryDirsDoc'])
		self.o_pd.Append(self.ID_PrimaryKeys,    mtexts.menutxts['OMPrimaryKeys'], mtexts.menutxts['OMPrimaryKeysDoc'])
		self.mpdsinchartopts = wx.Menu()
		self.mpdsinchartopts.Append(self.ID_PDsInChartOptZod, mtexts.menutxts['OMPDsInChartOptZod'], mtexts.menutxts['OMPDsInChartOptZodDoc'])
		self.mpdsinchartopts.Append(self.ID_PDsInChartOptMun, mtexts.menutxts['OMPDsInChartOptMun'], mtexts.menutxts['OMPDsInChartOptMunDoc'])
		self.o_pd.Append(self.ID_PDsInChartOpt, mtexts.menutxts['OMPDsInChartOpt'], self.mpdsinchartopts)
		self.moptions.Append(self.ID_PrimaryDirsOptMenu, mtexts.txts['PrimaryDirs'], self.o_pd)

# Roberto change V 7.2.0
		self.moptions.Append(self.ID_DefLocationOpt, mtexts.menutxts['OMDefLocationOpt'], mtexts.menutxts['OMDefLocationOptDoc'])
# ###########################################		
		self.moptions.Append(self.ID_Languages, mtexts.menutxts['OMLanguages'], mtexts.menutxts['OMLanguagesDoc'])
		self.moptions.AppendSeparator()
		self.autosave = self.moptions.Append(self.ID_AutoSaveOpts, mtexts.menutxts['OMAutoSave'], mtexts.menutxts['OMAutoSaveDoc'], wx.ITEM_CHECK)
		self.moptions.Append(self.ID_SaveOpts, mtexts.menutxts['OMSave'], mtexts.menutxts['OMSaveDoc'])
		self.moptions.Append(self.ID_Reload, mtexts.menutxts['OMReload'], mtexts.menutxts['OMReloadDoc'])

		self.setAutoSave()

		#Help-menu
		self.mhelp.Append(self.ID_Help, mtexts.menutxts['HEMHelp'], mtexts.menutxts['HEMHelpDoc'])
		self.mhelp.Append(self.ID_About, mtexts.menutxts['HEMAbout'], mtexts.menutxts['HEMAboutDoc'])


		menubar.Append(self.mhoros,   mtexts.menutxts[u'MHoroscope'])
		menubar.Append(self.mtable,   mtexts.menutxts[u'MTable'])
		menubar.Append(self.mcharts,  mtexts.menutxts[u'MCharts'])
		menubar.Append(self.moptions, mtexts.menutxts[u'MOptions'])
		menubar.Append(self.mhelp,    mtexts.menutxts[u'MHelp'])

		for item in self.mhoros.GetMenuItems():
			face = {6: 'Noto Sans SC', 7: 'Noto Sans TC', 8: 'Noto Sans KR'}.get(self.options.langid, 'FreeSans')
			item.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, face))

		self.SetMenuBar(menubar)
		self.SetIcon(wx.Icon('Morinus.ico', wx.BITMAP_TYPE_ICO))
		self.CreateStatusBar()

		self.Bind(wx.EVT_MENU, self.onNew, id=self.ID_New)
		self.Bind(wx.EVT_MENU, self.onData, id=self.ID_Data)
		self.Bind(wx.EVT_MENU, self.onLoad, id=self.ID_Load)
# ###########################################
# Roberto change  V 7.2.0		
		self.Bind(wx.EVT_MENU, self.onHereAndNow, id=self.ID_HereAndNow)
# ###########################################
		self.Bind(wx.EVT_MENU, self.onSave, id=self.ID_Save)
		self.Bind(wx.EVT_MENU, self.onSaveAsBitmap, id=self.ID_SaveAsBitmap)
		self.Bind(wx.EVT_MENU, self.onSynastry, id=self.ID_Synastry)
		self.Bind(wx.EVT_MENU, self.onFindTime, id=self.ID_FindTime)
		self.Bind(wx.EVT_MENU, self.onEphemeris, id=self.ID_Ephemeris)
		self.Bind(wx.EVT_MENU, self.onClose, id=self.ID_Close)
		self.Bind(wx.EVT_MENU, self.onExit, id=self.ID_Exit)

		if os.name == 'mac' or os.name == 'posix':
			self.Bind(wx.EVT_PAINT, self.onPaint)
		else:
			self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)

		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_MENU_OPEN, self.onMenuOpen)
		#The events EVT_MENU_OPEN and CLOSE are not called on windows in case of accelarator-keys
		self.Bind(wx.EVT_MENU_CLOSE, self.onMenuClose)

		self.Bind(wx.EVT_MENU, self.onPositions, id=self.ID_Positions)
		self.Bind(wx.EVT_MENU, self.onAlmutenZodiacal, id=self.ID_AlmutenZodiacal)
		self.Bind(wx.EVT_MENU, self.onAlmutenChart, id=self.ID_AlmutenChart)
		self.Bind(wx.EVT_MENU, self.onAlmutenTopical, id=self.ID_AlmutenTopical)
		self.Bind(wx.EVT_MENU, self.onMisc, id=self.ID_Misc)
		self.Bind(wx.EVT_MENU, self.onMunPos, id=self.ID_MunPos)
		self.Bind(wx.EVT_MENU, self.onAntiscia, id=self.ID_Antiscia)
# ###################################
# Elias change v 8.0.0    
#		self.Bind(wx.EVT_MENU, self.onDodecatemoria, id=self.ID_Dodecatemoria)
# ###################################	
		self.Bind(wx.EVT_MENU, self.onAspects, id=self.ID_Aspects)
		self.Bind(wx.EVT_MENU, self.onFixStars, id=self.ID_FixStars)
		self.Bind(wx.EVT_MENU, self.onFixStarsAsps, id=self.ID_FixStarsAsps)
		self.Bind(wx.EVT_MENU, self.onFixStarsParallels, id=self.ID_FixStarsParallels)
		self.Bind(wx.EVT_MENU, self.onMidpoints, id=self.ID_Midpoints)
		self.Bind(wx.EVT_MENU, self.onRiseSet, id=self.ID_RiseSet)
		self.Bind(wx.EVT_MENU, self.onSpeeds, id=self.ID_Speeds)
		self.Bind(wx.EVT_MENU, self.onZodPars, id=self.ID_ZodPars)
		self.Bind(wx.EVT_MENU, self.onArabians, id=self.ID_Arabians)
		self.Bind(wx.EVT_MENU, self.onStrip, id=self.ID_Strip)
		self.Bind(wx.EVT_MENU, self.onPlanetaryHours, id=self.ID_PlanetaryHours)
		self.Bind(wx.EVT_MENU, self.onExactTransits, id=self.ID_ExactTransits)
		self.Bind(wx.EVT_MENU, self.onProfections, id=self.ID_Profections)
# ###########################################
# Roberto change V 7.3.0
		self.Bind(wx.EVT_MENU, self.onFirdaria, id=self.ID_Firdaria)
# ###########################################
# ###################################
# Roberto change v 8.0.1   
		self.Bind(wx.EVT_MENU, self.onDodecatemoria, id=self.ID_Dodecatemoria)
		self.Bind(wx.EVT_MENU, self.onAngleAtBirth, id=self.ID_AngleAtBirth)
		self.Bind(wx.EVT_MENU, self.onCustomerSpeculum, id=self.ID_CustomerSpeculum)
		self.Bind(wx.EVT_MENU, self.onPrimaryDirs, id=self.ID_PrimaryDirs)
		self.Bind(wx.EVT_MENU, self.onZodiacalReleasing, id=self.ID_ZodiacalReleasing)
		self.Bind(wx.EVT_MENU, self.onPhasis, id=self.ID_Phasis)
		self.Bind(wx.EVT_MENU, self.onParanatellonta, id=self.ID_Paranatellonta)
		self.Bind(wx.EVT_MENU, self.onCircumambulation, id=self.ID_Circumambulation)
		self.Bind(wx.EVT_MENU, self.onDecennials, id=self.ID_Decennials)
		self.Bind(wx.EVT_MENU, self.onFixStarAngleDirs, id=self.ID_FixStarAngleDirs)
		self.Bind(wx.EVT_MENU, self.onEclipses, id=self.ID_Eclipses)
		self.Bind(wx.EVT_MENU, self.onTransits, id=self.ID_Transits)
		self.Bind(wx.EVT_MENU, self.onRevolutions, id=self.ID_Revolutions)
		self.Bind(wx.EVT_MENU, self.onSunTransits, id=self.ID_SunTransits)
		self.Bind(wx.EVT_MENU, self.onSecondaryDirs, id=self.ID_SecondaryDirs)
		self.Bind(wx.EVT_MENU, self.onSecondaryDirs, id=self.ID_SecProgChart)
		self.Bind(wx.EVT_MENU, self.onSecProgPositionsByDate, id=self.ID_SecProgPositions)
		self.Bind(wx.EVT_MENU, self.onElections, id=self.ID_Elections)
		self.Bind(wx.EVT_MENU, self.onSquareChart, id=self.ID_SquareChart)
		self.Bind(wx.EVT_MENU, self.onProfectionsChart, id=self.ID_ProfectionsChart)
		self.Bind(wx.EVT_MENU, self.onMundaneChart, id=self.ID_MundaneChart)

		self.Bind(wx.EVT_MENU, self.onAppearance1, id=self.ID_Appearance1)
		self.Bind(wx.EVT_MENU, self.onAppearance2, id=self.ID_Appearance2)
		self.Bind(wx.EVT_MENU, self.onSymbols, id=self.ID_Symbols)
		self.Bind(wx.EVT_MENU, self.onDignities, id=self.ID_Dignities)
		self.Bind(wx.EVT_MENU, self.onAyanamsha, id=self.ID_Ayanamsha)
		self.Bind(wx.EVT_MENU, self.onColors, id=self.ID_Colors)
		self.Bind(wx.EVT_MENU_RANGE, self.onHouseSystem, id=self.ID_Housesystem1, id2=self.ID_Housesystem12)
		self.Bind(wx.EVT_MENU_RANGE, self.onNodes, id=self.ID_NodeMean, id2=self.ID_NodeTrue)
		self.Bind(wx.EVT_MENU, self.onOrbs, id=self.ID_Orbs)
		self.Bind(wx.EVT_MENU, self.onPrimaryDirsOpt, id=self.ID_PrimaryDirsOpt)
		self.Bind(wx.EVT_MENU, self.onPrimaryKeys, id=self.ID_PrimaryKeys)
		self.Bind(wx.EVT_MENU, self.onPDsInChartOptZod, id=self.ID_PDsInChartOptZod)
		self.Bind(wx.EVT_MENU, self.onPDsInChartOptMun, id=self.ID_PDsInChartOptMun)
		self.Bind(wx.EVT_MENU, self.onFortune, id=self.ID_LotOfFortune)
		self.Bind(wx.EVT_MENU, self.onArabicParts, id=self.ID_ArabicParts)
		self.Bind(wx.EVT_MENU, self.onSyzygy, id=self.ID_Syzygy)
		self.Bind(wx.EVT_MENU, self.onFixStarsOpt, id=self.ID_FixStarsOpt)
		self.Bind(wx.EVT_MENU, self.onProfectionsOpt, id=self.ID_ProfectionsOpt)
# ###########################################
# Roberto change  V 7.3.0
		self.Bind(wx.EVT_MENU, self.onFirdariaOpt, id=self.ID_FirdariaOpt)
# ###########################################	
# ###########################################
# Roberto change  V 7.2.0
		self.Bind(wx.EVT_MENU, self.onDefLocationOpt, id=self.ID_DefLocationOpt)
# ###########################################		
		
		
		self.Bind(wx.EVT_MENU, self.onLanguages, id=self.ID_Languages)
		self.Bind(wx.EVT_MENU, self.onTriplicities, id=self.ID_Triplicities)
		self.Bind(wx.EVT_MENU, self.onTerms, id=self.ID_Terms)
		self.Bind(wx.EVT_MENU, self.onDecans, id=self.ID_Decans)
		self.Bind(wx.EVT_MENU, self.onChartAlmuten, id=self.ID_ChartAlmuten)
		self.Bind(wx.EVT_MENU, self.onTopicals, id=self.ID_Topical)
		self.Bind(wx.EVT_MENU, self.onAutoSaveOpts, id=self.ID_AutoSaveOpts)
		self.Bind(wx.EVT_MENU, self.onSaveOpts, id=self.ID_SaveOpts)
		self.Bind(wx.EVT_MENU, self.onReload, id=self.ID_Reload)

		self.Bind(wx.EVT_MENU, self.onHelp, id=self.ID_Help)
		self.Bind(wx.EVT_MENU, self.onAbout, id=self.ID_About)
		self.Bind(wx.EVT_MENU, self.onAngleAtBirth, id=self.ID_AngleAtBirth)
		self.SetAcceleratorTable(wx.AcceleratorTable([
			(wx.ACCEL_CTRL, wx.WXK_F11, self.ID_AngleAtBirth),
			(wx.ACCEL_CTRL, ord('1'),  self.ID_ZodiacalReleasing),  # <-- 추가
			(wx.ACCEL_CTRL, ord('2'),  self.ID_Phasis),  # <-- 추가
			(wx.ACCEL_CTRL, ord('3'),  self.ID_Paranatellonta),
			(wx.ACCEL_CTRL, ord('4'),  self.ID_Circumambulation),
			(wx.ACCEL_CTRL, ord('5'),  self.ID_FixStarAngleDirs),
			(wx.ACCEL_NORMAL, wx.WXK_F5, self.ID_Misc),
			(wx.ACCEL_CTRL, ord('6'),  self.ID_Eclipses),
			(wx.ACCEL_CTRL, ord('8'),  self.ID_FixStarsParallels),
	(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_F4, self.ID_SecProgChart),
	(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_F5, self.ID_Elections),
	(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_F9, self.ID_SecProgPositions),
]))

		self.Bind(wx.EVT_CLOSE, self.onExit)

		self.splash = True

		self.enableMenus(False)

		self.moptions.Enable(self.ID_SaveOpts, True)
		if self.options.checkOptsFiles():
			self.moptions.Enable(self.ID_Reload, True)
		else:
			self.moptions.Enable(self.ID_Reload, False)

		self.trdatedlg = None
		self.trmondlg = None
		self.suntrdlg = None
		self.revdlg = None
		self.secdirdlg = None
		self.pdrangedlg = None

		os.environ['SE_EPHE_PATH'] = ''
		astrology.swe_set_ephe_path(common.common.ephepath)
		
		self.drawSplash()

		self.Bind(EVT_PDREADY, self.OnPDReady)


	#Horoscope-menu	
	def onNew(self, event):
		dlg = personaldatadlg.PersonalDataDlg(self, self.options.langid)
		dlg.CenterOnParent()
		dlg.initialize()	

		# this does not return until the dialog is closed.
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			self.dirty = True

			direc = dlg.placerbE.GetValue()
			hemis = dlg.placerbN.GetValue()

			place = chart.Place(dlg.birthplace.GetValue(), int(dlg.londeg.GetValue()), int(dlg.lonmin.GetValue()), 0, direc, int(dlg.latdeg.GetValue()), int(dlg.latmin.GetValue()), 0, hemis, int(dlg.alt.GetValue()))

			plus = True
			if dlg.pluscb.GetCurrentSelection() == 1:
				plus = False
			time = chart.Time(int(dlg.year.GetValue()), int(dlg.month.GetValue()), int(dlg.day.GetValue()), int(dlg.hour.GetValue()), int(dlg.minute.GetValue()), int(dlg.sec.GetValue()), dlg.timeckb.GetValue(), dlg.calcb.GetCurrentSelection(), dlg.zonecb.GetCurrentSelection(), plus, int(dlg.zhour.GetValue()), int(dlg.zminute.GetValue()), dlg.daylightckb.GetValue(), place)

			male = dlg.genderrbM.GetValue()
			self.horoscope = chart.Chart(dlg.name.GetValue(), male, time, place, dlg.typecb.GetCurrentSelection(), dlg.notes.GetValue(), self.options)
			self.splash = False	
			self.enableMenus(True)
			self.drawBkg()
			self.Refresh()
			self.handleStatusBar(True)
			self.handleCaption(True)
#			self.calc()##

		dlg.Destroy()


	def onData(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = personaldatadlg.PersonalDataDlg(self, self.options.langid)
		dlg.CenterOnParent()
		dlg.fill(self.horoscope)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			changed = dlg.check(self.horoscope)

			#if self.dirty and changed:
			if changed:
				dlgm = wx.MessageDialog(self, mtexts.txts['DiscardCurrHor'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
				if dlgm.ShowModal() == wx.ID_NO:
					self.save()
				dlgm.Destroy()#

			if changed:
				self.dirty = True

			direc = dlg.placerbE.GetValue()
			hemis = dlg.placerbN.GetValue()
			place = chart.Place(dlg.birthplace.GetValue(), int(dlg.londeg.GetValue()), int(dlg.lonmin.GetValue()), 0, direc, int(dlg.latdeg.GetValue()), int(dlg.latmin.GetValue()), 0, hemis, int(dlg.alt.GetValue()))

			plus = True
			if dlg.pluscb.GetCurrentSelection() == 1:
				plus = False
			time = chart.Time(int(dlg.year.GetValue()), int(dlg.month.GetValue()), int(dlg.day.GetValue()), int(dlg.hour.GetValue()), int(dlg.minute.GetValue()), int(dlg.sec.GetValue()), dlg.timeckb.GetValue(), dlg.calcb.GetCurrentSelection(), dlg.zonecb.GetCurrentSelection(), plus, int(dlg.zhour.GetValue()), int(dlg.zminute.GetValue()), dlg.daylightckb.GetValue(), place)

			male = dlg.genderrbM.GetValue()
			self.horoscope = chart.Chart(dlg.name.GetValue(), male, time, place, dlg.typecb.GetCurrentSelection(), dlg.notes.GetValue(), self.options)
			self.splash = False	
			self.enableMenus(True)
			self.drawBkg()
			self.Refresh()
			self.handleStatusBar(True)
			self.handleCaption(True)
#			self.calc()##

			if changed:
				self.closeChildWnds()

		dlg.Destroy()
		

# ###########################################
# Roberto change  V 7.2.0		
	def onHereAndNow(self, event):
				
		self.dirty = True
	
		place = chart.Place(self.options.deflocname, self.options.defloclondeg, self.options.defloclonmin, 0, self.options.defloceast, self.options.defloclatdeg, self.options.defloclatmin, 0, self.options.deflocnorth, self.options.deflocalt)
	
		now = datetime.datetime.now()
		time = chart.Time(now.year, now.month, now.day, now.hour, now.minute, now.second, False, chart.Time.GREGORIAN, chart.Time.ZONE, self.options.deflocplus, self.options.defloczhour, self.options.defloczminute, self.options.deflocdst, place)
	
		self.horoscope = chart.Chart(mtexts.txts['HereAndNow'], True, time, place, chart.Chart.HORARY, '', self.options)
		self.splash = False	
		self.enableMenus(True)
		self.drawBkg()
		self.Refresh()
		self.handleStatusBar(True)
		self.handleCaption(True)
# ###########################################


	def showFindTime(self, bc, fnd, arplac):
		place = chart.Place('London, GBR', 0, 6, 0, False, 51, 31, 0, True, 10)

		h, m, s = util.decToDeg(fnd[3])
		time = chart.Time(fnd[0], fnd[1], fnd[2], h, m, s, bc, chart.Time.GREGORIAN, chart.Time.GREENWICH, True, 0, 0, False, place)
		#Calc obliquity
		d = astrology.swe_deltat(time.jd)
		serr, obl = astrology.swe_calc(time.jd+d, astrology.SE_ECL_NUT, 0)

		if arplac[2]:
			#calc GMTMidnight:
			timeMidnight = chart.Time(time.year, time.month, time.day, 0, 0, 0, bc, chart.Time.GREGORIAN, chart.Time.GREENWICH, True, 0, 0, False, place)
			place = self.calcPlace(time.time, timeMidnight.sidTime, arplac[0], arplac[1], obl[0])

		url = "http://api.geonames.org/findNearbyJSON?%s"

		params = {
			"username" : 'morinus',
			#"lang" : "en",
			"lng" : place.lon,
			"lat" : place.lat,
			"featureClass" : "P"
			}

		url = url % urllib.parse.urlencode(params)
		place1 = ""
		try:
			page = urllib2.urlopen(url)
			doc = json.loads(page.read())

			for item in doc['geonames']:
				place1 = item['toponymName']
				values = place1
				place1 = item['countryName']
				values = values+", "+place1

		except Exception as e:
			values = None

		place.place=values

		self.horoscope = chart.Chart('Search', True, time, place, chart.Chart.RADIX, '', self.options)

		if (not self.splash):
			self.destroyDlgs()
			self.closeChildWnds()

		self.dirty = True
		self.splash = False	
		self.fpath = ''
		self.enableMenus(True)
		self.clickedPlId = None
		self.drawBkg()
		self.Refresh()
		self.handleStatusBar(True)
		self.handleCaption(True)


	def calcPlace(self, gmt, gmst0, mclon, asclon, obl):
		robl = math.radians(obl)
		deltaGMST = gmt*1.00273790927949
		gmstNat = util.normalizeTime(gmst0+deltaGMST)

		ramc = 0.0
		if mclon == 90.0:
			ramc = 90.0
		elif mclon == 270.0:
			ramc = 270.0
		else:
			rmclon = math.radians(mclon)
			X = math.degrees(math.atan(math.tan(rmclon)*math.cos(robl)))
			if mclon >= 0.0 and mclon < 90.0:
				ramc = X
			elif mclon > 90.0 and mclon < 270.0:
				ramc = X+180.0
			elif mclon > 270.0 and mclon < 360.0:
				ramc = X+360.0

		lmstNat = ramc/15.0

		lonInTime = gmstNat-lmstNat

		if not (-12.0 <= lonInTime and lonInTime <= 12.0):
			if lonInTime < -12.0:
				lonInTime += 24.0
			elif lonInTime > 12.0:
				lonInTime -= 24.0

		lon = 0.0
		east = False
		if lonInTime == 0.0:
			lon = 0.0
		elif 0.0 < lonInTime and lonInTime <= 12.0: #West
			lon = lonInTime*15.0
		elif -12.0 <= lonInTime and lonInTime < 0.0: #East
			lon = lonInTime*15.0
			east = True

		#Lat
		rasclon = math.radians(asclon)
		rramc = math.radians(ramc)

		lat = 30.0#
		north = True
		if math.sin(robl) != 0.0:
			lat = math.degrees(math.atan(-(math.cos(rramc)*(1/math.tan(rasclon))+math.sin(rramc)*math.cos(robl))/math.sin(robl)))
			if lat < 0.0:
				north = False

		lon = math.fabs(lon)
		lat = math.fabs(lat)
		
		ld, lm, ls = util.decToDeg(lon)
		lad, lam, las = util.decToDeg(lat)

		return chart.Place('Place', ld, lm, ls, east, lad, lam, las, north, 10)


	def onLoad(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.dirty:
			dlgm = wx.MessageDialog(self, mtexts.txts['DiscardCurrHor'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
			if dlgm.ShowModal() == wx.ID_NO:
				dlgm.Destroy()#
				return

			dlgm.Destroy()#

		dlg = wx.FileDialog(self, mtexts.txts['OpenHor'], '', '', mtexts.txts['HORFiles'], wx.FD_OPEN)
		if os.path.isdir(self.fpathhors):
			dlg.SetDirectory(self.fpathhors)
		else:
			dlg.SetDirectory(u'.')

		if dlg.ShowModal() == wx.ID_OK:
			dpath = dlg.GetDirectory()
			fpath = dlg.GetPath()

			if not fpath.endswith(u'.hor'):
				fpath+=u'.hor'

			chrt = self.subLoad(fpath, dpath)

			if chrt != None:
				self.horoscope = chrt
				self.splash = False	
				self.drawBkg()
				self.Refresh()
				self.fpathhors = dpath
				self.fpath = fpath
				self.enableMenus(True)
				self.handleStatusBar(True)
				self.handleCaption(True)
				self.dirty = False
#				self.calc()##

				self.filehistory.AddFileToHistory(fpath)

		dlg.Destroy()#


	def subLoad(self, fpath, dpath, dontclose = False):
		chrt = None

		try:
			f = open(fpath, 'rb')		
			name = pickle.load(f)
			male = pickle.load(f)
			htype = pickle.load(f)
			bc = pickle.load(f)
			year = pickle.load(f)
			month = pickle.load(f)
			day = pickle.load(f)
			hour = pickle.load(f)
			minute = pickle.load(f)
			second = pickle.load(f)
			cal = pickle.load(f)
			zt = pickle.load(f)
			plus = pickle.load(f)
			zh = pickle.load(f)
			zm = pickle.load(f)
			daylightsaving = pickle.load(f)
			place = pickle.load(f)
			deglon = pickle.load(f)
			minlon = pickle.load(f)
			seclon = pickle.load(f)
			east = pickle.load(f)
			deglat = pickle.load(f)
			minlat = pickle.load(f)
			seclat = pickle.load(f)
			north = pickle.load(f)
			altitude = pickle.load(f)
			notes = pickle.load(f)
			f.close()

			if (not self.splash) and (not dontclose):
				self.closeChildWnds()
			
			place = chart.Place(place, deglon, minlon, 0, east, deglat, minlat, seclat, north, altitude)
			time = chart.Time(year, month, day, hour, minute, second, bc, cal, zt, plus, zh, zm, daylightsaving, place)
			chrt = chart.Chart(name, male, time, place, htype, notes, self.options)
		except IOError:
			dlgm = wx.MessageDialog(self, mtexts.txts['FileError'], mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
			dlgm.ShowModal()
			dlgm.Destroy()#

		return chrt 


	def onSave(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		self.save()


	def save(self):
		dlg = wx.FileDialog(self, mtexts.txts['SaveHor'], '', self.horoscope.name, mtexts.txts['HORFiles'], wx.FD_SAVE)
		if os.path.isdir(self.fpathhors):
			dlg.SetDirectory(self.fpathhors)
		else:
			dlg.SetDirectory(u'.')

		if dlg.ShowModal() == wx.ID_OK:
			dpath = dlg.GetDirectory()
			fpath = dlg.GetPath()

			if not fpath.endswith(u'.hor'):
				fpath+=u'.hor'
			#Check if fpath already exists!?
			if os.path.isfile(fpath):
				dlgm = wx.MessageDialog(self, mtexts.txts['FileExists'], mtexts.txts['Message'], wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
				if dlgm.ShowModal() == wx.ID_NO:
					dlgm.Destroy()#
					return
				dlgm.Destroy()#
			
			try:
				with open(fpath, 'wb') as f:
					import pickle
					p = pickle.Pickler(f, 2)
					p.dump(self.horoscope.name)
					p.dump(self.horoscope.male)
					p.dump(self.horoscope.htype)
					p.dump(self.horoscope.time.bc)
					p.dump(self.horoscope.time.origyear)
					p.dump(self.horoscope.time.origmonth)
					p.dump(self.horoscope.time.origday)
					p.dump(self.horoscope.time.hour)
					p.dump(self.horoscope.time.minute)
					p.dump(self.horoscope.time.second)
					p.dump(self.horoscope.time.cal)
					p.dump(self.horoscope.time.zt)
					p.dump(self.horoscope.time.plus)
					p.dump(self.horoscope.time.zh)
					p.dump(self.horoscope.time.zm)
					p.dump(self.horoscope.time.daylightsaving)
					p.dump(self.horoscope.place.place)
					p.dump(self.horoscope.place.deglon)
					p.dump(self.horoscope.place.minlon)
					p.dump(self.horoscope.place.seclon)
					p.dump(self.horoscope.place.east)
					p.dump(self.horoscope.place.deglat)
					p.dump(self.horoscope.place.minlat)
					p.dump(self.horoscope.place.seclat)
					p.dump(self.horoscope.place.north)
					p.dump(self.horoscope.place.altitude)
					p.dump(self.horoscope.notes)
				self.fpathhors = dpath
				self.fpath = fpath
				self.dirty = False
			except IOError:
				dlgm = wx.MessageDialog(self, mtexts.txts['FileError'], mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
				dlgm.ShowModal()
				dlgm.Destroy()
		dlg.Destroy()#


	def onSaveAsBitmap(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		name = self.horoscope.name
		if name == '':
			name = mtexts.txts['Horoscope']
		dlg = wx.FileDialog(self, mtexts.txts['SaveAsBmp'], '', name, mtexts.txts['BMPFiles'], wx.FD_SAVE)
		if os.path.isdir(self.fpathimgs):
			dlg.SetDirectory(self.fpathimgs)
		else:
			dlg.SetDirectory(u'.')

		if dlg.ShowModal() == wx.ID_OK:
			dpath = dlg.GetDirectory()
			fpath = dlg.GetPath()
			if not fpath.endswith(u'.bmp'):
				fpath+=u'.bmp'
			#Check if fpath already exists!?
			if os.path.isfile(fpath):
				dlgm = wx.MessageDialog(self, mtexts.txts['FileExists'], mtexts.txts['Message'], wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
				if dlgm.ShowModal() == wx.ID_NO:
					dlgm.Destroy()#
					return
				dlgm.Destroy()#

			self.buffer.SaveFile(fpath, wx.BITMAP_TYPE_BMP)		
			self.fpathimgs = dpath

		dlg.Destroy()#


	def onSynastry(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = wx.FileDialog(self, mtexts.txts['OpenHor'], '', '', mtexts.txts['HORFiles'], wx.FD_OPEN)
		if os.path.isdir(self.fpathhors):
			dlg.SetDirectory(self.fpathhors)
		else:
			dlg.SetDirectory(u'.')

		chrt = None
		if dlg.ShowModal() == wx.ID_OK:
			dpath = dlg.GetDirectory()
			fpath = dlg.GetPath()

			if not fpath.endswith(u'.hor'):
				fpath+=u'.hor'

			chrt = self.subLoad(fpath, dpath, True)

		dlg.Destroy()#

		if chrt != None:
			txt = self.horoscope.name+u' - '+chrt.name+' '+mtexts.txts['Synastry']+' ('+str(chrt.time.origyear)+'.'+common.common.months[chrt.time.origmonth-1]+'.'+str(chrt.time.origday)+' '+str(chrt.time.hour)+':'+str(chrt.time.minute).zfill(2)+':'+str(chrt.time.second).zfill(2)+')'
			tw = transitframe.TransitFrame(self, txt, chrt, self.horoscope, self.options, transitframe.TransitFrame.COMPOUND)
			tw.Show(True)


	def onFindTime(self, event):
		findtimdlg = findtimedlg.FindTimeDlg(self)
		findtimdlg.fill()
		findtimdlg.CenterOnParent()

#		findtimdlg.ShowModal() # because the "Calculating"-dialog will also be modal and it enables the Menues of the MainFrame!!
		findtimdlg.Show()


	def onEphemeris(self, event):
		ephemdlg = graphephemdlg.GraphEphemDlg(self)
		ephemdlg.CenterOnParent()
		val = ephemdlg.ShowModal()

		if val == wx.ID_OK:
			year = int(ephemdlg.year.GetValue())
			wait = wx.BusyCursor()
			eph = ephemcalc.EphemCalc(year, self.options)
			ephemfr = graphephemframe.GraphEphemFrame(self, mtexts.txts['Ephemeris'], year, eph.posArr, self.options)
			ephemfr.Show(True)


	def onClose(self, event):
		if self.dirty:
			dlgm = wx.MessageDialog(self, mtexts.txts['DiscardCurrHor'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
			if dlgm.ShowModal() == wx.ID_NO:
				dlgm.Destroy()#
				return
			dlgm.Destroy()#

		self.destroyDlgs()

		self.fpath = ''
		self.dirty = False
		self.splash = True
		self.enableMenus(False)
		self.closeChildWnds()
		self.drawSplash()
		self.handleStatusBar(False)
		self.handleCaption(False)
		self.Refresh()	


	def onExit(self, event):
		# 1) 진행 중인 길게 도는 작업 중지 신호
		try:
			if hasattr(self, "abort") and self.abort:
				self.abort.aborting()
		except Exception:
			pass

		# 2) 타이머 정지
		try:
			if hasattr(self, "timer") and self.timer:
				self.timer.Stop()
				del self.timer
		except Exception:
			pass

		# 3) 프로그레스 다이얼로그 파괴
		try:
			if hasattr(self, "progbar") and self.progbar:
				self.progbar.Destroy()
				del self.progbar
		except Exception:
			pass

		if self.dirty:
			dlgm = wx.MessageDialog(self, mtexts.txts['DiscardCurrHor'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)

			if dlgm.ShowModal() == wx.ID_NO:
				dlgm.Destroy()#
				return
			dlgm.Destroy()#

		self.destroyDlgs()
		try:
			del self.filehistory
		except Exception:
			pass

		# 6) 메인 프레임 파괴 → 메인루프 종료

		self.Destroy()


	def OnFileHistory(self, evt):
		if self.dirty:
			dlgm = wx.MessageDialog(self, mtexts.txts['DiscardCurrHor'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)

			if dlgm.ShowModal() == wx.ID_NO:
				dlgm.Destroy()#
				return

			dlgm.Destroy()#

		# get the file based on the menu ID
		fileNum = evt.GetId()-wx.ID_FILE1
		path = self.filehistory.GetHistoryFile(fileNum)

		#check file
		if os.path.exists(path):
			dname = os.path.dirname(path)
			chrt = self.subLoad(path, dname)

			if chrt != None:
				self.horoscope = chrt
				self.splash = False	
				self.drawBkg()
				self.Refresh()
				self.fpathhors = dname
				self.fpath = path
				self.enableMenus(True)
				self.handleStatusBar(True)
				self.handleCaption(True)
				self.dirty = False
#				self.calc()##

				self.filehistory.AddFileToHistory(path)

			# add it back to the history so it will be moved up the list
#			self.filehistory.AddFileToHistory(path)

			self.destroyDlgs()
		else:
			dlgm = wx.MessageDialog(self, mtexts.txts['FileError'], mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
			dlgm.ShowModal()
			dlgm.Destroy()#
			self.filehistory.RemoveFileFromHistory(fileNum)


	def destroyDlgs(self):
		if self.trdatedlg != None:
			self.trdatedlg.Destroy()
			self.trdatedlg = None
		if self.trmondlg != None:
			self.trmondlg.Destroy()
			self.trmondlg = None
		if self.suntrdlg != None:
			self.suntrdlg.Destroy()
			self.suntrdlg = None
		if self.revdlg != None:
			self.revdlg.Destroy()
			self.revdlg = None
		if self.secdirdlg != None:
			self.secdirdlg.Destroy()
			self.secdirdlg = None
		if self.pdrangedlg != None:
			self.pdrangedlg.Destroy()
			self.pdrangedlg = None


	#Table-menu
	def onPositions(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			speculum = 0
			if self.options.primarydir == primdirs.PrimDirs.REGIOMONTAN:
				speculum = 1
			if (True in self.options.speculums[speculum]) or self.options.speculumdodecat[speculum]:
				wait = wx.BusyCursor()
				posframe = positionsframe.PositionsFrame(self, self.title, self.horoscope, self.options)
				posframe.Show(True)
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['SelectColumn'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()#


	def onAlmutenZodiacal(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			almutenfr = almutenzodsframe.AlmutenZodsFrame(self, self.title, self.horoscope, self.options)
			almutenfr.Show(True)


	def onAlmutenChart(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			almutenfr = almutenchartframe.AlmutenChartFrame(self, self.title, self.horoscope, self.options)
			almutenfr.Show(True)


	def onAlmutenTopical(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			if self.horoscope.options.topicals != None and len(self.horoscope.almutens.topicals.names) != 0:
				wait = wx.BusyCursor()
				topicalframe = almutentopicalsframe.AlmutenTopicalsFrame(self, self.horoscope, self.title)
				topicalframe.Show(True)
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoTopicalsCreated'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()#


	def onMisc(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			tblframe = miscframe.MiscFrame(self, self.title, self.horoscope, self.options)
			tblframe.Show(True)


	def onAspects(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			aspsframe = aspectsframe.AspectsFrame(self, self.title, self.horoscope, self.options)
			aspsframe.Show(True)


	def onMidpoints(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			midsframe = midpointsframe.MidPointsFrame(self, self.title, self.horoscope, self.options)
			midsframe.Show(True)


	def onRiseSet(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			risesetfr = risesetframe.RiseSetFrame(self, self.title, self.horoscope, self.options)
			risesetfr.Show(True)


	def onSpeeds(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			speedsfr = speedsframe.SpeedsFrame(self, self.title, self.horoscope, self.options)
			speedsfr.Show(True)


	def onMunPos(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			munposfr = munposframe.MunPosFrame(self, self.title, self.horoscope, self.options)
			munposfr.Show(True)


	def onAntiscia(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			antisciafr = antisciaframe.AntisciaFrame(self, self.title, self.horoscope, self.options)
			antisciafr.Show(True)

# ###################################
# Elias change v 8.0.0
#	def onDodecatemoria(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
#		if wx.Platform == '__WXMSW__' and not self.splash:
#			self.handleStatusBar(True)

#		if not self.splash:
#			wait = wx.BusyCursor()
#			dodecatemoriafr = dodecatemoriaframe.DodecatemoriaFrame(self, self.title, self.horoscope, self.options)
#			dodecatemoriafr.Show(True)
# ###################################      

	def onZodPars(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			zodparsfr = zodparsframe.ZodParsFrame(self, self.title, self.horoscope, self.options)
			zodparsfr.Show(True)


	def onStrip(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			stripfr = stripframe.StripFrame(self, self.title, self.horoscope, self.options)
			stripfr.Show(True)


	def onFixStars(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			if not self.checkFixStars():
				return

			if len(self.options.fixstars) == 0:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoSelFixStars'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()
				return	

			wait = wx.BusyCursor()
			fixstarsfr = fixstarsframe.FixStarsFrame(self, self.title, self.horoscope, self.options)
			fixstarsfr.Show(True)


	def onFixStarsAsps(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			if not self.checkFixStars():
				return

			if len(self.options.fixstars) == 0:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoSelFixStars'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()
				return	

			wait = wx.BusyCursor()
			fixstarsaspsfr = fixstarsaspectsframe.FixStarsAspectsFrame(self, self.title, self.horoscope, self.options)
			fixstarsaspsfr.Show(True)

	def onFixStarsParallels(self, event):
		# Windows에서 가속키 사용 시 EVT_MENU_CLOSE가 누락되는 케이스 정합
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			if not self.checkFixStars():
				return
			if len(self.options.fixstars) == 0:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoSelFixStars'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()
				return

			wait = wx.BusyCursor()
			fr = fixstarsparallelsframe.FixStarsParallelsFrame(self, self.title, self.horoscope, self.options)
			fr.Show(True)

	def onPlanetaryHours(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			planetaryfr = hoursframe.HoursFrame(self, self.title, self.horoscope, self.options)
			planetaryfr.Show(True)


	def onArabians(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			partsfr = arabicpartsframe.ArabicPartsFrame(self, self.title, self.horoscope, self.options)
			partsfr.Show(True)


	def onExactTransits(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		if self.trmondlg == None:
			self.trmondlg = transitmdlg.TransitMonthDlg(None, self.horoscope.time)
		self.trmondlg.CenterOnParent()
		val = self.trmondlg.ShowModal()

		if val == wx.ID_OK:	
			year = int(self.trmondlg.year.GetValue())
			month = int(self.trmondlg.month.GetValue())

			wait = wx.BusyCursor()

			trans = transits.Transits()
			trans.month(year, month, self.horoscope)
			tw = transitmframe.TransitMonthFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.txts['Transit']+' ('+str(year)+'.'+common.common.months[month-1]+')'), trans.transits, year, month, self.horoscope, self.options)
			tw.Show(True)

	def onAngleAtBirth(self, event):
		# Windows에서 단축키로 열었을 때 상태바 처리(기존 패턴과 동일)
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		# 차트 없으면 비활성 메시지
		if self.horoscope is None:
			wx.MessageBox(u"차트가 없습니다.", mtexts.txts["AngleatBirth"])
			return

		# 열기
		import angleatbirthframe
		fr = angleatbirthframe.AngleAtBirthFrame(self, self.title, self.horoscope, self.options)

	def onProfections(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		pdlg = proftabledlg.ProfTableDlg(self)
		pdlg.initialize()

		pdlg.CenterOnParent()

		val = pdlg.ShowModal()
		if val == wx.ID_OK:
			proftype = chart.Chart.YEAR
			mainsigs = pdlg.mainrb.GetValue()

			pchart = self.horoscope

			wait = wx.BusyCursor()

			#Cycle
			y = self.horoscope.time.year
			m = self.horoscope.time.month
			d = self.horoscope.time.day
			t = self.horoscope.time.time

			#Feb29?
			if self.horoscope.time.month == 2 and self.horoscope.time.day == 29:
				d -= 1

			pcharts = []

			cyc = 0
			while(cyc < 12):
				if self.options.zodprof:
					prof = profections.Profections(self.horoscope, y, m, d, t, cyc)
					pchart = chart.Chart(self.horoscope.name, self.horoscope.male, self.horoscope.time, self.horoscope.place, chart.Chart.PROFECTION, '', self.options, False, proftype)
					pchart.calcProfPos(prof)
				else:
					if not self.options.usezodprojsprof and (y+cyc == self.horoscope.time.year or (y+cyc-self.horoscope.time.year) % 12 == 0) and m == self.horoscope.time.month and d == self.horoscope.time.day:
						pchart = self.horoscope
					else:
						prof = munprofections.MunProfections(self.horoscope, y, m, d, t, cyc)
						proflondeg, proflonmin, proflonsec = util.decToDeg(prof.lonZ)
						profplace = chart.Place(mtexts.txts['Profections'], proflondeg, proflonmin, proflonsec, prof.east, self.horoscope.place.deglat, self.horoscope.place.minlat, self.horoscope.place.seclat, self.horoscope.place.north, self.horoscope.place.altitude)
						pchart = chart.Chart(self.horoscope.name, self.horoscope.male, self.horoscope.time, profplace, chart.Chart.PROFECTION, '', self.options, False, proftype, self.options.usezodprojsprof)
						pchartpls = chart.Chart(self.horoscope.name, self.horoscope.male, self.horoscope.time, self.horoscope.place, chart.Chart.PROFECTION, '', self.options, False, proftype, self.options.usezodprojsprof)
						#modify planets, ...
						pchart.planets.calcMundaneProfPos(pchart.houses.ascmc2, pchartpls.planets.planets, self.horoscope.place.lat, self.horoscope.obl[0])
	
						#modify lof
						pchart.fortune.calcMundaneProfPos(pchart.houses.ascmc2, pchartpls.fortune, self.horoscope.place.lat, self.horoscope.obl[0])
	
				pcharts.append((pchart, y+cyc, m, d, t))
				cyc += 1

			profsfr = profstableframe.ProfsTableFrame(self, self.title, pcharts, self.options, mainsigs)
			profsfr.Show(True)

			pstepdlg = profectiontablestepperdlg.ProfectionTableStepperDlg(profsfr, self.horoscope, self.options, proftype)
			pstepdlg.CenterOnParent()
			pstepdlg.Show(True)

		pdlg.Destroy()


	def onCustomerSpeculum(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			speculum = 0
			if self.options.primarydir == primdirs.PrimDirs.REGIOMONTAN:
				speculum = 1
			if (True in self.options.speculums[speculum]) or self.options.speculumdodecat[speculum]:
					if self.horoscope.cpd != None:
						wait = wx.BusyCursor()
						custframe = customerframe.CustomerFrame(self, self.title, self.horoscope, self.options, self.horoscope.cpd)
						custframe.Show(True)
					elif self.horoscope.cpd2 != None:
						wait = wx.BusyCursor()
						custframe = customerframe.CustomerFrame(self, self.title, self.horoscope, self.options, self.horoscope.cpd2)
						custframe.Show(True)
					else:
						dlgm = wx.MessageDialog(self, mtexts.txts['CheckUser'], '', wx.OK|wx.ICON_INFORMATION)
						dlgm.ShowModal()
						dlgm.Destroy()#
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['SelectColumn'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()#

# ###########################################
# Roberto change  V 7.3.0
	def onFirdaria(self, event):
		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy(); return
		if not self.splash:
			wait = wx.BusyCursor()
			firdfr = firdariaframe.FirdariaFrame(self, self.title, self.horoscope, self.options)
			firdfr.Show(True)
# ###########################################

# ###################################
# Roberto change v 8.0.1
	#def onDodecatemoria(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		#if wx.Platform == '__WXMSW__' and not self.splash:
			#self.handleStatusBar(True)
	
		#if not self.splash:
			#wait = wx.BusyCursor()
			#dodecatemoriafr = dodecatemoriaframe.DodecatemoriaFrame(self, self.title, self.horoscope, self.options)
			#dodecatemoriafr.Show(True)
# ###################################
	def onDodecatemoria(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			wait = wx.BusyCursor()
			try:
				# 1) 기존 도데카테모리온 창
				dodeca_table_fr = dodecatemoriaframe.DodecatemoriaFrame(self, self.title, self.horoscope, self.options)
				dodeca_table_fr.Show(True)

				# 2) 새 도데카테모리온 계산기 창
				#    - 새 텍스트 키 추가 없이, 기존 키를 재사용
				calc_title = self.title.replace(
					mtexts.typeList[self.horoscope.htype],
					mtexts.txts.get('Dodecatemorion', 'Dodecatemoria')
				)
				dodeca_calc_fr = dodecacalcframe.DodecaCalcFrame(self, calc_title, self.horoscope, self.options)
				dodeca_calc_fr.Show(True)
			finally:
				del wait

	def onCircumambulation(self, event):
		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy(); return
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)
		if not self.splash:
			wait = wx.BusyCursor()
			try:
				import circumambulationframe
				fr = circumambulationframe.CircumFrame(self, self.title, self.horoscope, self.options)
				fr.Show(True)
			finally:
				del wait

	def onFixStarAngleDirs(self, event):
		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy(); return
		# Windows 가속키 사용 시 상태바 처리(프로그램 기존 관례)
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.splash:
			# 고정별 카탈로그/선택 검증 (onFixStars 로직과 동일)
			if not self.checkFixStars():
				return
			if len(self.options.fixstars) == 0:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoSelFixStars'], '', wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal(); dlgm.Destroy(); return

			# >>> PD 범위/방향 팝업 재사용 <<<
			if self.pdrangedlg == None:
				self.pdrangedlg = primdirsrangedlg.PrimDirsRangeDlg(None)
			self.pdrangedlg.CenterOnParent()
			val = self.pdrangedlg.ShowModal()
			if val != wx.ID_OK:
				return

			# PD와 동일하게 범위/방향 읽기
			pdrange = primdirs.PrimDirs.RANGEALL
			if self.pdrangedlg.range25rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE25
			elif self.pdrangedlg.range50rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE50
			elif self.pdrangedlg.range75rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE75
			elif self.pdrangedlg.range100rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE100

			direction = primdirs.PrimDirs.BOTHDC
			if self.pdrangedlg.directrb.GetValue():
				direction = primdirs.PrimDirs.DIRECT
			elif self.pdrangedlg.converserb.GetValue():
				direction = primdirs.PrimDirs.CONVERSE

			wait = wx.BusyCursor()
			try:
				# pdrange, direction을 프레임에 전달
				fr = fixstardirsframe.FixedStarDirsFrame(self, self.title, self.horoscope, self.options, pdrange, direction)
				fr.Show(True)
			finally:
				del wait

	def onEclipses(self, event):
		if self.horoscope is None:
			return
		fr = eclipsesframe.EclipsesFrame(self, self.title, self.horoscope, self.options)
		fr.Show(True)

	def onZodiacalReleasing(self, event):
		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy(); return
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)
		if not self.splash:
			import zodiacalreleasingframe
			fr = zodiacalreleasingframe.ZRFrame(self, self.title, self.horoscope, self.options)
	def onDecennials(self, event):
		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy(); return
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)
		if not self.splash:
			wait = wx.BusyCursor()
			try:
				import decennialsframe
				fr = decennialsframe.DecennialsFrame(self, self.title, self.horoscope, self.options)
				#fr.Show(True)
			finally:
				del wait

	def onPhasis(self, event):
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)
		if not self.splash:
			wait = wx.BusyCursor()
			try:
				import phasisframe
				fr = phasisframe.PhasisFrame(self, self.title, self.horoscope, self.options)
				fr.Show(True)
			finally:
				del wait

	def onParanatellonta(self, event):
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)
		if not self.splash:
			wait = wx.BusyCursor()
			try:
				import paranframe
				fr = paranframe.ParanFrame(self, self.title, self.horoscope, self.options)
				fr.Show(True)
			finally:
				del wait

	def onPrimaryDirs(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		if self.pdrangedlg == None:
			self.pdrangedlg = primdirsrangedlg.PrimDirsRangeDlg(None)

		self.pdrangedlg.CenterOnParent()

		val = self.pdrangedlg.ShowModal()
		if val == wx.ID_OK:
			pdrange = primdirs.PrimDirs.RANGEALL
			if self.pdrangedlg.range25rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE25
			elif self.pdrangedlg.range50rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE50
			elif self.pdrangedlg.range75rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE75
			elif self.pdrangedlg.range100rb.GetValue():
				pdrange = primdirs.PrimDirs.RANGE100

			direction = primdirs.PrimDirs.BOTHDC
			if self.pdrangedlg.directrb.GetValue():
				direction = primdirs.PrimDirs.DIRECT
			elif self.pdrangedlg.converserb.GetValue():
				direction = primdirs.PrimDirs.CONVERSE

			keytxt = ''
			if self.options.pdkeydyn:
				keytxt = mtexts.typeListDyn[self.options.pdkeyd]
			else:
				keytxt = mtexts.typeListStat[self.options.pdkeys]

			txt = mtexts.typeListDirs[self.options.primarydir]+'; '+keytxt+'\n'+mtexts.txts['BusyInfo']

			self.progbar = wx.ProgressDialog(mtexts.txts['Calculating'], txt, parent=self, style = wx.PD_CAN_ABORT|wx.PD_APP_MODAL)
			self.progbar.Fit()

			self.pds = None
			self.pdready = False
			self.abort = primdirs.AbortPD()
			thId = _thread.start_new_thread(self.calcPDs, (pdrange, direction, self))

			self.timer = wx.Timer(self)
			self.Bind(wx.EVT_TIMER, self.OnTimer)
			self.timer.Start(500)


	def calcPDs(self, pdrange, direction, win):
		if self.options.primarydir == primdirs.PrimDirs.PLACIDIANSEMIARC:
			self.pds = placidiansapd.PlacidianSAPD(self.horoscope, self.options, pdrange, direction, self.abort)
		elif self.options.primarydir == primdirs.PrimDirs.PLACIDIANUNDERTHEPOLE:
			self.pds = placidianutppd.PlacidianUTPPD(self.horoscope, self.options, pdrange, direction, self.abort)
		elif self.options.primarydir == primdirs.PrimDirs.REGIOMONTAN:
			self.pds = regiomontanpd.RegiomontanPD(self.horoscope, self.options, pdrange, direction, self.abort)
		else:
			self.pds = campanianpd.CampanianPD(self.horoscope, self.options, pdrange, direction, self.abort)

		pdlock.acquire()
		self.pdready = True
		pdlock.release()
		evt = PDReadyEvent()
		wx.PostEvent(win, evt)


	def OnTimer(self, event):
		pdlock.acquire()
		if not self.pdready:
			(keepGoing, skip) = self.progbar.Pulse()

			if not keepGoing:
				self.abort.aborting()
		pdlock.release()


	def OnPDReady(self, event):
		self.timer.Stop()
		del self.timer
		self.progbar.Destroy()
		del self.progbar

		if self.abort.abort:
			self.Refresh()
		else:
			if self.pds != None and len(self.pds.pds) > 0:
				pdw = primdirslistframe.PrimDirsListFrame(self, self.horoscope, self.options, self.pds, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.txts['PrimaryDirs']))

				pdw.Show(True)
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoPDsWithSettings'], mtexts.txts['Information'], wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()#

		if self.pds != None:
			del self.pds

		del self.abort


	#Charts-menu
	def onTransits(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		if self.trdatedlg == None:
			self.trdatedlg = timespacedlg.TimeSpaceDlg(None, mtexts.txts['Transits'], self.options.langid)
			self.trdatedlg.initialize(self.horoscope)
		self.trdatedlg.CenterOnParent()

		val = self.trdatedlg.ShowModal()
		if val == wx.ID_OK:	
			wait = wx.BusyCursor()

			direc = self.trdatedlg.placerbE.GetValue()
			hemis = self.trdatedlg.placerbN.GetValue()
			place = chart.Place(self.trdatedlg.birthplace.GetValue(), int(self.trdatedlg.londeg.GetValue()), int(self.trdatedlg.lonmin.GetValue()), 0, direc, int(self.trdatedlg.latdeg.GetValue()), int(self.trdatedlg.latmin.GetValue()), 0, hemis, 0) #Transit doesn't calculate planetary hours => altitude is zero

			plus = True
			if self.trdatedlg.pluscb.GetCurrentSelection() == 1:
				plus = False
			time = chart.Time(int(self.trdatedlg.year.GetValue()), int(self.trdatedlg.month.GetValue()), int(self.trdatedlg.day.GetValue()), int(self.trdatedlg.hour.GetValue()), int(self.trdatedlg.minute.GetValue()), int(self.trdatedlg.sec.GetValue()), self.trdatedlg.timeckb.GetValue(), self.trdatedlg.calcb.GetCurrentSelection(), self.trdatedlg.zonecb.GetCurrentSelection(), plus, int(self.trdatedlg.zhour.GetValue()), int(self.trdatedlg.zminute.GetValue()), self.trdatedlg.daylightckb.GetValue(), place, False)

			trans = chart.Chart(self.horoscope.name, self.horoscope.male, time, place, chart.Chart.TRANSIT, '', self.options, False)

			tw = transitframe.TransitFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.typeList[chart.Chart.TRANSIT]+' ('+str(time.year)+'.'+common.common.months[time.month-1]+'.'+str(time.day)+' '+str(time.hour)+':'+str(time.minute).zfill(2)+':'+str(time.second).zfill(2)+')'), trans, self.horoscope, self.options)
			tw.Show(True)


	def onRevolutions(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		if self.revdlg == None:
			# 메인 프레임(self)을 parent로
			self.revdlg = revolutionsdlg.RevolutionsDlg(self)
			self.revdlg.initialize(self.horoscope)
		self.revdlg.CenterOnParent()
		try:
			val = self.revdlg.ShowModal()
			if val != wx.ID_OK:
				return
			if val == wx.ID_OK:
				wx.BeginBusyCursor()
				revs = revolutions.Revolutions()
				result = revs.compute(self.revdlg.typecb.GetCurrentSelection(),
									int(self.revdlg.year.GetValue()),
									int(self.revdlg.month.GetValue()),
									int(self.revdlg.day.GetValue()),
									self.horoscope)
				wx.EndBusyCursor()

				t1, t2, t3, t4, t5, t6 = revs.t[0], revs.t[1], revs.t[2], revs.t[3], revs.t[4], revs.t[5]
				if result:
					if self.options.ayanamsha != 0:
						sel = self.revdlg.typecb.GetCurrentSelection()
						pid = None
						if sel == revolutions.Revolutions.SOLAR:
							pid = astrology.SE_SUN
						elif sel == revolutions.Revolutions.LUNAR:
							pid = astrology.SE_MOON
						elif sel == revolutions.Revolutions.MERCURY:
							pid = astrology.SE_MERCURY
						elif sel == revolutions.Revolutions.VENUS:
							pid = astrology.SE_VENUS
						elif sel == revolutions.Revolutions.MARS:
							pid = astrology.SE_MARS
						elif sel == revolutions.Revolutions.JUPITER:
							pid = astrology.SE_JUPITER
						elif sel == revolutions.Revolutions.SATURN:
							pid = astrology.SE_SATURN

						if pid is not None:
							t1, t2, t3, t4, t5, t6 = self.calcPrecNutCorrectedRevolution(revs, pid)

					dlg = timespacedlg.TimeSpaceDlg(self, mtexts.txts['Revolutions'], self.options.langid)
					ti = (t1, t2, t3, t4, t5, t6, chart.Time.GREGORIAN, chart.Time.GREENWICH, 0, 0)
					dlg.initialize(self.horoscope, ti)
					dlg.CenterOnParent()

					val = dlg.ShowModal()
					if val != wx.ID_OK:
						dlg.Destroy()
						return
					if val == wx.ID_OK:
						wait = wx.BusyCursor()
						direc = dlg.placerbE.GetValue()
						hemis = dlg.placerbN.GetValue()
						place = chart.Place(dlg.birthplace.GetValue(), int(dlg.londeg.GetValue()), int(dlg.lonmin.GetValue()), 0, direc, int(dlg.latdeg.GetValue()), int(dlg.latmin.GetValue()), 0, hemis, 0)#the same as for the transits
						# ★ 리턴 place 확정 후 2차 보정(특히 topocentric+달에서 각분 잔차 제거)
						if self.options.ayanamsha != 0 and pid is not None:
							try:
								t1, t2, t3, t4, t5, t6 = self.calcPrecNutCorrectedRevolution(
									revs, pid,
									topo_place=place,
									seed=(t1, t2, t3, t4, t5, t6)
								)
							except Exception:
								pass
						plus = True
						if dlg.pluscb.GetCurrentSelection() == 1:
							plus = False
						time = chart.Time(t1, t2, t3, t4, t5, t6, False, self.horoscope.time.cal, chart.Time.GREENWICH, plus, 0, 0, False, place, False)

						revtype = chart.Chart.REVOLUTION
						if self.revdlg.typecb.GetCurrentSelection() == 0:
							revtype = chart.Chart.SOLAR
						elif self.revdlg.typecb.GetCurrentSelection() == 1:
							revtype = chart.Chart.LUNAR

						revolution = chart.Chart(self.horoscope.name, self.horoscope.male, time, place, revtype, '', self.options, False)
						dlg.Destroy()
						rw = transitframe.TransitFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.typeList[revtype]+' ('+str(time.year)+'.'+common.common.months[time.month-1]+'.'+str(time.day)+' '+str(time.hour)+':'+str(time.minute).zfill(2)+':'+str(time.second).zfill(2)+'('+mtexts.txts['GMT']+'))'), revolution, self.horoscope, self.options)
						rw.Show(True)
						wx.CallAfter(rw.Raise)
						wx.CallAfter(rw.SetFocus)
						# 현재 프레임/컨텍스트 저장
						self._rev_frame = rw
						self._rev_ctx   = {'place': place, 'plus': plus, 'revtype': revtype}

						# 이전에 떠 있던 스텝퍼가 있으면 닫기(다른 리턴일 수도 있으니 먼저 정리)
						try:
							if hasattr(self, "_rev_stepper") and self._rev_stepper:
								self._rev_stepper.Destroy()
								self._rev_stepper = None
						except Exception:
							pass

						# ★ 솔라 리턴에서만 스텝퍼를 띄운다
						if self.revdlg.typecb.GetCurrentSelection() == revolutions.Revolutions.SOLAR:

							# 현재 리턴 연도 저장 (dlg에서 받은 t1이 리턴 연도)
							self._rev_year = t1

							# 리턴 프레임이 닫히면 스텝퍼도 함께 닫기
							def _on_close(evt):
								try:
									if hasattr(self, "_rev_stepper") and self._rev_stepper:
										self._rev_stepper.Destroy()
										self._rev_stepper = None
								except Exception:
									pass
								evt.Skip()
							self._rev_frame.Bind(wx.EVT_CLOSE, _on_close)

							# 연도 갱신 콜백(솔라 리턴만 지원)
							def _set_rev_year_and_refresh(new_year):
								revs2 = revolutions.Revolutions()
								ok = revs2.compute(revolutions.Revolutions.SOLAR,
												int(new_year),
												self.horoscope.time.month,
												self.horoscope.time.day,
												self.horoscope)
								if not ok:
									return

								y, m, d, hh, mi, ss = revs2.t[0], revs2.t[1], revs2.t[2], revs2.t[3], revs2.t[4], revs2.t[5]
								try:
									if self.options.ayanamsha != 0:
										y, m, d, hh, mi, ss = self.calcPrecNutCorrectedRevolution(revs2, astrology.SE_SUN)
								except Exception:
									pass

								time2 = chart.Time(y, m, d, hh, mi, ss, False,
												self.horoscope.time.cal, chart.Time.GREENWICH,
												self._rev_ctx['plus'], 0, 0, False, self._rev_ctx['place'], False)
								chart2 = chart.Chart(self.horoscope.name, self.horoscope.male, time2,
													self._rev_ctx['place'], self._rev_ctx['revtype'], '', self.options, False)

								newtitle2 = self.title.replace(
									mtexts.typeList[self.horoscope.htype],
									mtexts.typeList[self._rev_ctx['revtype']]+' ('+str(time2.year)+'.'
									+common.common.months[time2.month-1]+'.'+str(time2.day)+' '
									+str(time2.hour)+':'+str(time2.minute).zfill(2)+':'+str(time2.second).zfill(2)+'('
									+mtexts.txts['GMT']+'))'
								)

								try:
									self._rev_frame.change_chart(chart2)
									self._rev_frame.SetTitle(newtitle2)
									wx.CallAfter(self._rev_frame.Raise)
									wx.CallAfter(self._rev_frame.SetFocus)
								except Exception:
									try:
										self._rev_frame.Destroy()
									except Exception:
										pass
									self._rev_frame = transitframe.TransitFrame(self, newtitle2, chart2, self.horoscope, self.options)
									self._rev_frame.Show(True)
									wx.CallAfter(self._rev_frame.Raise)
									wx.CallAfter(self._rev_frame.SetFocus)
									self._rev_frame.Bind(wx.EVT_CLOSE, _on_close)

								self._rev_year = int(new_year)

							# 스텝퍼 생성(부모는 메인 프레임)
							from revolutionsdlg import RevolutionYearStepper
							self._rev_stepper = RevolutionYearStepper(
								parent=self,
								get_year_cb=lambda: self._rev_year,
								set_year_cb=_set_rev_year_and_refresh
							)
							self._rev_stepper.Show(True)
							try:
								self._rev_stepper.CentreOnScreen()
							except Exception:
								self._rev_stepper.CenterOnScreen()
							self._rev_stepper.Raise()
						# ★ 루나 리턴에도 월 스텝퍼를 붙인다
						# SOLAR 분기 밑에 이어서:
						elif self.revdlg.typecb.GetCurrentSelection() == revolutions.Revolutions.LUNAR:

							# 1) 다이얼로그에서 고른 시작 날짜를 기억(월만 바꿔가며 재계산)
							self._lr_year  = int(self.revdlg.year.GetValue())
							self._lr_month = int(self.revdlg.month.GetValue())
							self._lr_day   = int(self.revdlg.day.GetValue())

							# 리턴 프레임이 닫히면 스텝퍼도 함께 닫기
							def _on_close(evt):
								try:
									if hasattr(self, "_rev_stepper") and self._rev_stepper:
										self._rev_stepper.Destroy()
										self._rev_stepper = None
								except Exception:
									pass
								evt.Skip()
							self._rev_frame.Bind(wx.EVT_CLOSE, _on_close)

							# 2) (yy, mm)로 루나 리턴 재계산 후 프레임 갱신
							def _set_lr_ym_and_refresh(yy, mm):
								revs2 = revolutions.Revolutions()

								# 31→2월 같은 불가능한 날짜 보정
								dd = int(self._lr_day)
								try:
									while not util.checkDate(int(yy), int(mm), int(dd)) and dd > 1:
										dd -= 1
								except Exception:
									pass

								ok = revs2.compute(revolutions.Revolutions.LUNAR,
												int(yy), int(mm), int(dd), self.horoscope)
								if not ok:
									return

								y, m, d, hh, mi, ss = revs2.t[0], revs2.t[1], revs2.t[2], revs2.t[3], revs2.t[4], revs2.t[5]
								try:
									if self.options.ayanamsha != 0:
										y, m, d, hh, mi, ss = self.calcPrecNutCorrectedRevolution(revs2, astrology.SE_MOON)
								except Exception:
									pass
								time2 = chart.Time(y, m, d, hh, mi, ss, False,
												self.horoscope.time.cal, chart.Time.GREENWICH,
												self._rev_ctx['plus'], 0, 0, False, self._rev_ctx['place'], False)
								chart2 = chart.Chart(self.horoscope.name, self.horoscope.male, time2,
													self._rev_ctx['place'], self._rev_ctx['revtype'], '', self.options, False)

								newtitle2 = self.title.replace(
									mtexts.typeList[self.horoscope.htype],
									mtexts.typeList[self._rev_ctx['revtype']]+' ('+str(time2.year)+'.'
									+ common.common.months[time2.month-1]+'.'+str(time2.day)+' '
									+ str(time2.hour)+':'+str(time2.minute).zfill(2)+':'+str(time2.second).zfill(2)+'('
									+ mtexts.txts['GMT']+'))'
								)

								try:
									# 일부 빌드에선 이 메서드가 없습니다(당신 케이스).
									self._rev_frame.change_chart(chart2)
									self._rev_frame.SetTitle(newtitle2)
									wx.CallAfter(self._rev_frame.Raise)
									wx.CallAfter(self._rev_frame.SetFocus)
								except Exception:
									# ★ 폴백: 기존 프레임을 안전하게 닫고 새로 띄웁니다(솔라와 동일 패턴).
									try:
										self._rev_frame.Destroy()
									except Exception:
										pass

									# 새 리턴 프레임 오픈
									self._rev_frame = transitframe.TransitFrame(self, newtitle2, chart2, self.horoscope, self.options)
									self._rev_frame.Show(True)
									wx.CallAfter(self._rev_frame.Raise)
									wx.CallAfter(self._rev_frame.SetFocus)

									# 리턴 프레임이 닫히면 스텝퍼도 같이 닫히도록(이미 위에서 정의한 핸들러)
									self._rev_frame.Bind(wx.EVT_CLOSE, _on_close)

							# 3) 스텝퍼에 현재값/설정 콜백 연결
							def _get_lr_ym():
								return (self._lr_year, self._lr_month)

							def _set_lr_ym(yy, mm):
								self._lr_year, self._lr_month = int(yy), int(mm)
								_set_lr_ym_and_refresh(self._lr_year, self._lr_month)

							from revolutionsdlg import RevolutionMonthStepper  # 있어도 무방, 없으면 추가
							self._rev_stepper = RevolutionMonthStepper(
								parent=self,            # ★ 메인 프레임을 부모로!
								get_ym_cb=_get_lr_ym,
								set_ym_cb=_set_lr_ym,
							)
							self._rev_stepper.Show(True)
							try:
								self._rev_stepper.CentreOnScreen()
							except Exception:
								self._rev_stepper.CenterOnScreen()
							self._rev_stepper.Raise()

					dlg.Destroy()
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['CouldnotComputeRevolution'], mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
				dlgm.ShowModal()
				dlgm.Destroy()
				pass
		finally:
			try:
				self.revdlg.Destroy()
			except Exception:
				pass
			self.revdlg = None

	def calcPrecNutCorrectedRevolution(self, revs, planet_id, topo_place=None, seed=None):
		"""
		Ayanamsha ON 리턴 정밀 보정(공통):
		- sid_lon = trop_lon - ayanamsha_ut(jd)
		- sid_speed = trop_speed - d(ayanamsha)/dt
		- (중요) topocentric일 때:
		  * 네이틀 목표각은 네이틀 place(출생지)로 계산
		  * 리턴(탐색) 쪽은 topo_place(리턴 다이얼로그에서 고른 place)로 계산
		- 마지막은 '정수 초'에서 |오차|가 최소가 되도록 스냅(달은 더 넓게)
		"""
		place_nat = self.horoscope.place
		place_trn = topo_place if topo_place is not None else place_nat

		# 1) 시작 JD(시드)
		if seed is not None:
			sy, sm, sd, sh, smin, ss = seed
		else:
			sy, sm, sd, sh, smin, ss = revs.t[0], revs.t[1], revs.t[2], revs.t[3], revs.t[4], revs.t[5]

		time0 = chart.Time(
			int(sy), int(sm), int(sd), int(sh), int(smin), int(ss),
			False, self.horoscope.time.cal, chart.Time.GREENWICH,
			False, 0, 0, False, place_trn, False
		)
		jd = time0.jd

		# 2) sid-mode는 ayanamsha_ut 계산을 위해서만 세팅(우린 lon 자체는 tropical로 계산)
		astrology.swe_set_sid_mode(self.options.ayanamsha-1, 0, 0)

		pflag = (astrology.SEFLG_SWIEPH | astrology.SEFLG_SPEED)
		if self.options.topocentric:
			pflag |= astrology.SEFLG_TOPOCTR

		def _wrap180(x):
			return (x + 180.0) % 360.0 - 180.0

		def _sid_lon_vel(jd_ut, pl):
			# topocentric은 호출 시점(place)에 맞춰 세팅
			if self.options.topocentric:
				astrology.swe_set_topo(pl.lon, pl.lat, pl.altitude)

			serr, dat = astrology.swe_calc_ut(jd_ut, planet_id, pflag)
			lon_trop = util.normalize(dat[0])
			vel_trop = dat[3]  # deg/day

			ay = astrology.swe_get_ayanamsa_ut(jd_ut)
			eps = 0.5  # days
			ay_p = astrology.swe_get_ayanamsa_ut(jd_ut + eps)
			ay_m = astrology.swe_get_ayanamsa_ut(jd_ut - eps)
			ay_rate = _wrap180(ay_p - ay_m) / (2.0 * eps)

			lon_sid = util.normalize(lon_trop - ay)
			vel_sid = vel_trop - ay_rate
			return lon_sid, vel_sid

		# 3) 네이틀 목표(네이틀 place 기준 고정)
		nat_lon_sid, _ = _sid_lon_vel(self.horoscope.time.jd, place_nat)

		def _f(jd_ut):
			# 탐색은 리턴 place 기준
			lon_sid, _ = _sid_lon_vel(jd_ut, place_trn)
			return _wrap180(nat_lon_sid - lon_sid)

		# 4) Newton (클램프 포함)
		diff = _f(jd)
		for _ in range(80):
			if abs(diff) <= 1e-10:
				break
			_, vel_sid = _sid_lon_vel(jd, place_trn)
			if abs(vel_sid) < 1e-7:
				break

			step = diff / vel_sid  # days
			if step > 30.0:
				step = 30.0
			elif step < -30.0:
				step = -30.0

			jd += step
			diff = _f(jd)

		# 5) 폴백: 브라켓+이분법
		if abs(diff) > 1e-8:
			_, vel_sid = _sid_lon_vel(jd, place_trn)
			span = 2.0 if abs(vel_sid) >= 0.3 else 40.0

			lo = jd - span
			hi = jd + span
			flo = _f(lo)
			fhi = _f(hi)

			for _ in range(12):
				if flo * fhi < 0.0:
					break
				span *= 2.0
				lo = jd - span
				hi = jd + span
				flo = _f(lo)
				fhi = _f(hi)

			if flo * fhi < 0.0:
				for _ in range(100):
					mid = (lo + hi) / 2.0
					fmid = _f(mid)
					if abs(fmid) <= 1e-10:
						jd = mid
						break
					if flo * fmid <= 0.0:
						hi = mid
						fhi = fmid
					else:
						lo = mid
						flo = fmid
					jd = (lo + hi) / 2.0

		# 6) 정수 초 스냅(달은 넓게)
		_, vel_sid = _sid_lon_vel(jd, place_trn)
		if planet_id == astrology.SE_MOON:
			W = 900   # 달은 topocentric/수치 잔차 대비(±15분)
		elif abs(vel_sid) < 0.05:
			W = 1200
		elif abs(vel_sid) < 0.3:
			W = 300
		else:
			W = 60

		jd0 = round(jd * 86400.0) / 86400.0
		best_jd = jd0
		best_abs = abs(_f(best_jd))
		for dt in range(-W, W + 1):
			jd_try = jd0 + (dt / 86400.0)
			v = abs(_f(jd_try))
			if v < best_abs:
				best_abs = v
				best_jd = jd_try
		jd = best_jd

		# 7) JD → YMDHMS
		y, m, d, hour = astrology.swe_revjul(jd, astrology.SE_GREG_CAL)
		total = int(round(hour * 3600.0))
		if total >= 24 * 3600:
			total -= 24 * 3600
			y, m, d = util.incrDay(int(y), int(m), int(d))
		elif total < 0:
			total += 24 * 3600
			y, m, d = util.decrDay(int(y), int(m), int(d))

		hh = total // 3600
		total %= 3600
		mi = total // 60
		ss = total % 60

		return int(y), int(m), int(d), int(hh), int(mi), int(ss)


	def calcPrecNutCorrectedSolar(self, revs):
		# 기존 호환: Solar는 generic을 호출
		return self.calcPrecNutCorrectedRevolution(revs, astrology.SE_SUN)

	def onSunTransits(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		if self.suntrdlg == None:
			self.suntrdlg = suntransitsdlg.SunTransitsDlg(None)
			self.suntrdlg.initialize(self.horoscope)

		self.suntrdlg.CenterOnParent()

		val = self.suntrdlg.ShowModal()
		if val == wx.ID_OK:	
			wx.BeginBusyCursor()

			lons = (self.horoscope.houses.ascmc[houses.Houses.ASC], self.horoscope.houses.ascmc[houses.Houses.MC], self.horoscope.planets.planets[astrology.SE_SUN].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_MOON].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_MERCURY].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_VENUS].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_MARS].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_JUPITER].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_SATURN].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_URANUS].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_NEPTUNE].data[planets.Planet.LONG], self.horoscope.planets.planets[astrology.SE_PLUTO].data[planets.Planet.LONG])
			btns = (self.suntrdlg.ascrb.GetValue(), self.suntrdlg.mcrb.GetValue(), self.suntrdlg.sunrb.GetValue(), self.suntrdlg.moonrb.GetValue(), self.suntrdlg.mercuryrb.GetValue(), self.suntrdlg.venusrb.GetValue(), self.suntrdlg.marsrb.GetValue(), self.suntrdlg.jupiterrb.GetValue(), self.suntrdlg.saturnrb.GetValue(), self.suntrdlg.uranusrb.GetValue(), self.suntrdlg.neptunerb.GetValue(), self.suntrdlg.plutorb.GetValue())

			trlon = lons[0]
			for i in range(len(btns)):
				if btns[i]:
					trlon = lons[i]
			
			suntrs = suntransits.SunTransits()
			result = suntrs.compute(int(self.suntrdlg.year.GetValue()), int(self.suntrdlg.month.GetValue()), int(self.suntrdlg.day.GetValue()), self.horoscope, trlon)

			wx.EndBusyCursor()

			if result:
				dlg = timespacedlg.TimeSpaceDlg(self, mtexts.txts['SunTransits'], self.options.langid)
				ti = (suntrs.t[0], suntrs.t[1], suntrs.t[2], suntrs.t[3], suntrs.t[4], suntrs.t[5], chart.Time.GREGORIAN, chart.Time.GREENWICH, 0, 0)
				dlg.initialize(self.horoscope, ti)	
				dlg.CenterOnParent()

				val = dlg.ShowModal()

				if val == wx.ID_OK:
					wait = wx.BusyCursor()
					direc = dlg.placerbE.GetValue()
					hemis = dlg.placerbN.GetValue()
					place = chart.Place(dlg.birthplace.GetValue(), int(dlg.londeg.GetValue()), int(dlg.lonmin.GetValue()), 0, direc, int(dlg.latdeg.GetValue()), int(dlg.latmin.GetValue()), 0, hemis, 0)#Same as for the transits

					plus = True
					if dlg.pluscb.GetCurrentSelection() == 1:
						plus = False
					time = chart.Time(suntrs.t[0], suntrs.t[1], suntrs.t[2], suntrs.t[3], suntrs.t[4], suntrs.t[5], False, chart.Time.GREGORIAN, chart.Time.GREENWICH, plus, 0, 0, False, place, False)

					suntrschart = chart.Chart(self.horoscope.name, self.horoscope.male, time, place, chart.Chart.TRANSIT, '', self.options, False)

					rw = transitframe.TransitFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.typeList[chart.Chart.TRANSIT]+' ('+str(time.year)+'.'+common.common.months[time.month-1]+'.'+str(time.day)+' '+str(time.hour)+':'+str(time.minute).zfill(2)+':'+str(time.second).zfill(2)+'('+mtexts.txts['GMT']+'))'), suntrschart, self.horoscope, self.options)
					rw.Show(True)

				dlg.Destroy()

			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['CouldnotComputeTransit'], mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
				dlgm.ShowModal()
				dlgm.Destroy()#


	def onSecondaryDirs(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		if self.secdirdlg == None:
			self.secdirdlg = secdirdlg.SecondaryDirsDlg(None)
			self.secdirdlg.initialize()

		self.secdirdlg.CenterOnParent()

		val = self.secdirdlg.ShowModal()
		if val == wx.ID_OK:
			age = int(self.secdirdlg.age.GetValue())
			direct = self.secdirdlg.directrb.GetValue()
			soltime = self.secdirdlg.solartimerb.GetValue()

			zt = chart.Time.LOCALMEAN
			if soltime:
				zt = chart.Time.LOCALAPPARENT
			zh = 0
			zm = 0

			sdir = secdir.SecDir(self.horoscope, age, direct, soltime)
			y, m, d, hour, minute, second = sdir.compute()

			dlg = timespacedlg.TimeSpaceDlg(self, mtexts.txts['SecondaryDirs'], self.options.langid)
			ti = (y, m, d, hour, minute, second, self.horoscope.time.cal, zt, zh, zm)
			dlg.initialize(self.horoscope, ti)	
			dlg.CenterOnParent()

			val = dlg.ShowModal()

			if val == wx.ID_OK:
				wait = wx.BusyCursor()

				direc = dlg.placerbE.GetValue()
				hemis = dlg.placerbN.GetValue()
				place = chart.Place(dlg.birthplace.GetValue(), int(dlg.londeg.GetValue()), int(dlg.lonmin.GetValue()), 0, direc, int(dlg.latdeg.GetValue()), int(dlg.latmin.GetValue()), 0, hemis, 0)#Also, no altitude neccesary here

				plus = True
				if dlg.pluscb.GetCurrentSelection() == 1:
					plus = False
				time = chart.Time(y, m, d, hour, minute, second, False, self.horoscope.time.cal, zt, plus, zh, zm, False, place, False)

				secdirchart = chart.Chart(self.horoscope.name, self.horoscope.male, time, place, chart.Chart.TRANSIT, '', self.options, False)

				sf = secdirframe.SecDirFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.txts['SecondaryDir']+' ('+str(time.year)+'.'+common.common.months[time.month-1]+'.'+str(time.day)+' '+str(time.hour)+':'+str(time.minute).zfill(2)+':'+str(time.second).zfill(2)+')'), secdirchart, self.horoscope, self.options)
				sf.Show(True)

				stepdlg = stepperdlg.StepperDlg(sf, self.horoscope, age, direct, soltime, self.options, self.title)
				stepdlg.CenterOnParent()
				stepdlg.Show(True)

			dlg.Destroy()

	def onSecProgPositionsByDate(self, event):
		#COLS = (mtexts.txts['Planets'], mtexts.txts['Longitude'], mtexts.txts['Latitude'], mtexts.txts['Dodecatemorion'], mtexts.txts['Declination'])
		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy(); return
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)
		if self.splash:
			return

		import posfordate

		nt = self.horoscope.time

		def _caption_for(chrt):
			# 타이틀: "Positions for Date (진행날짜 ...)" 형태로
			t = chrt.time
			try:
				base = self.title.replace(mtexts.txts['Radix'], mtexts.txts['PositionForDate'])
			except Exception:
				base = self.title
			return base.replace(
				mtexts.txts['PositionForDate'],
				mtexts.txts['PositionForDate']+' ('+str(t.year)+'.'+common.common.months[t.month-1]+'.'+str(t.day)+' '+
				str(t.hour)+':'+str(t.minute).zfill(2)+':'+str(t.second).zfill(2)+')',
				1
			)
		def _on_posfordate_frame_close(evt):
			# 차트 창을 닫으면 secdirui도 같이 닫는다
			try:
				if hasattr(self, "_secui_dlg") and self._secui_dlg:
					try:
						self._secui_dlg.Destroy()
					except Exception:
						pass
					self._secui_dlg = None
			except Exception:
				pass

			# 프레임 레퍼런스도 정리 (죽은 핸들 방지)
			try:
				self._posfordate_fr = None
			except Exception:
				pass

			evt.Skip()

		def _bind_posfordate_frame_close(fr):
			# 중복 Bind 방지
			try:
				if fr and not getattr(fr, "_posfordate_closebound", False):
					fr.Bind(wx.EVT_CLOSE, _on_posfordate_frame_close)
					fr._posfordate_closebound = True
			except Exception:
				pass
		def _ensure_posfordate_stack():
			"""항상: 메인(라딕스) < Positions-for-Date 차트 < 팝업 다이얼로그"""
			# (재진입 방지) Raise가 다시 EVT_ACTIVATE를 유발할 수 있음
			if getattr(self, "_posfordate_stack_guard", False):
				return
			self._posfordate_stack_guard = True
			try:
				try:
					if hasattr(self, "_posfordate_fr") and self._posfordate_fr:
						self._posfordate_fr.Raise()
				except Exception:
					pass
				try:
					if hasattr(self, "_secui_dlg") and self._secui_dlg:
						self._secui_dlg.Raise()
				except Exception:
					pass
			finally:
				self._posfordate_stack_guard = False

		def _bind_secui_stack(dlg):
			try:
				if dlg and not getattr(dlg, "_posfordate_stackbound", False):
					try:
						dlg.SetWindowStyleFlag(dlg.GetWindowStyleFlag() | wx.FRAME_FLOAT_ON_PARENT)
					except Exception:
						pass
					dlg._posfordate_stackbound = True
			except Exception:
				pass
		def _apply(yy, mm_, dd_):
			# Calculate → 동일 프레임 갱신(차트로)
			try:
				age_int, age_years, (py, pm, pd), prg = posfordate.make_progressed_chart_by_real_date(
					self.horoscope, self.options, yy, mm_, dd_
				)

				# 라벨/입력 갱신: 정수 나이 = age_int (반올림 금지)
				try:
					self._secui_dlg.set_snapshot(int(age_int), (int(yy), int(mm_), int(dd_)), (int(py), int(pm), int(pd)))
				except Exception:
					pass

				# (선택) 예전 표 창이 열려있으면 닫아버림
				try:
					if hasattr(self, "_secprog_tbl") and self._secprog_tbl:
						self._secprog_tbl.Destroy()
						self._secprog_tbl = None
				except Exception:
					pass

				title = _caption_for(prg)

				if hasattr(self, "_posfordate_fr") and self._posfordate_fr:
					# 기존 프레임이 있으면 갱신
					self._posfordate_fr.change(prg, title)
					_bind_posfordate_frame_close(self._posfordate_fr)
					# change()가 타이틀을 건드릴 수 있어 확실히 덮어쓰기
					try:
						self._posfordate_fr.SetTitle(title)
						if hasattr(self._posfordate_fr, "_update_age_and_realdate"):
							self._posfordate_fr._update_age_and_realdate()
					except Exception:
						pass
					self._posfordate_fr.Raise()
				else:
					try:
						wx.CallAfter(_ensure_posfordate_stack)
					except Exception:
						pass
					# 없으면 새로 생성
					self._posfordate_fr = secdirframe.SecDirFrame(self, title, prg, self.horoscope, self.options)
					_bind_posfordate_frame_close(self._posfordate_fr)
					self._posfordate_fr.Show(True)
					self._posfordate_fr.Raise()
					try:
						wx.CallAfter(_ensure_posfordate_stack)
					except Exception:
						pass
			except Exception as e:
				try:
					wx.MessageBox(u"Positions for Date chart error (Calculate): %s" % e, mtexts.txts['PositionForDate'])
				except:
					pass
			# Calculate 후에도 스택 유지
			try:
				wx.CallAfter(_ensure_posfordate_stack)
			except Exception:
				pass
			return
		# 0세 차트 먼저 계산 (입력 기본값 = 네이탈 원래 날짜)
		try:
			by, bm, bd = nt.origyear, nt.origmonth, nt.origday
			age0i, age0, (ppy, ppm, ppd), prg0 = posfordate.make_progressed_chart_by_real_date(
				self.horoscope, self.options, by, bm, bd
			)
		except Exception:
			by, bm, bd = nt.origyear, nt.origmonth, nt.origday
			age0i, age0, (ppy, ppm, ppd), prg0 = 0, 0.0, (nt.origyear, nt.origmonth, nt.origday), self.horoscope

		# (선택) 예전 표 창이 열려있으면 닫기
		try:
			if hasattr(self, "_secprog_tbl") and self._secprog_tbl:
				self._secprog_tbl.Destroy()
				self._secprog_tbl = None
		except Exception:
			pass

		# 차트 프레임 생성/갱신 (먼저 차트를 띄우고)
		try:
			title0 = _caption_for(prg0)
			if not hasattr(self, "_posfordate_fr") or not self._posfordate_fr:
				self._posfordate_fr = secdirframe.SecDirFrame(self, title0, prg0, self.horoscope, self.options)
				_bind_posfordate_frame_close(self._posfordate_fr)
				self._posfordate_fr.Show(True)
				wx.CallAfter(self._posfordate_fr.Raise)
				wx.CallAfter(self._posfordate_fr.SetFocus)
			else:
				self._posfordate_fr.change(prg0, title0)
				_bind_posfordate_frame_close(self._posfordate_fr)
				try:
					self._posfordate_fr.SetTitle(title0)
					if hasattr(self._posfordate_fr, "_update_age_and_realdate"):
						self._posfordate_fr._update_age_and_realdate()
				except Exception:
					pass
				wx.CallAfter(self._posfordate_fr.Raise)
				wx.CallAfter(self._posfordate_fr.SetFocus)
		except Exception as e:
			try:
				wx.MessageBox(u"Positions for Date chart error (initial): %s" % e, mtexts.txts['PositionForDate'])
			except:
				pass

		# 다이얼로그 열기 (모델리스) — 부모를 '새 차트 프레임'으로 두고, 항상 차트 위로
		def _open_secui():
			parent_for_dlg = self._posfordate_fr if (hasattr(self, "_posfordate_fr") and self._posfordate_fr) else self
			self._secui_dlg = secdirui.SecDirDialog(parent_for_dlg, _apply, None)
			_bind_secui_stack(self._secui_dlg)
			try:
				self._secui_dlg.CenterOnParent()
			except Exception:
				pass
			self._secui_dlg.Show(True)

		try:
			need_new = (not hasattr(self, "_secui_dlg") or not self._secui_dlg)
			if not need_new:
				try:
					# 예전 패치로 '메인 프레임'을 부모로 잡아버린 경우 → 메인이 튀어올라 새 차트를 덮음
					if hasattr(self, "_posfordate_fr") and self._posfordate_fr:
						if self._secui_dlg.GetParent() != self._posfordate_fr:
							try:
								self._secui_dlg.Destroy()
							except Exception:
								pass
							self._secui_dlg = None
							need_new = True
				except Exception:
					need_new = True

			if need_new:
				_open_secui()
			else:
				_bind_secui_stack(self._secui_dlg)
				self._secui_dlg.Show(True)
		except Exception:
			try:
				if hasattr(self, "_secui_dlg") and self._secui_dlg:
					self._secui_dlg.Destroy()
			except Exception:
				pass
			self._secui_dlg = None
			_open_secui()

		# 라벨/입력 초기화(다이얼로그 생성 이후)
		try:
			self._secui_dlg.set_snapshot(int(age0i), (by, bm, bd), (ppy, ppm, ppd))
		except Exception:
			pass

		# 최종 스택: 메인 < 새 차트 < 팝업
		try:
			wx.CallAfter(_ensure_posfordate_stack)
		except Exception:
			pass
	def onElections(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		time = chart.Time(self.horoscope.time.origyear, self.horoscope.time.origmonth, self.horoscope.time.origday, self.horoscope.time.hour, self.horoscope.time.minute, self.horoscope.time.second, self.horoscope.time.bc, self.horoscope.time.cal, self.horoscope.time.zt, self.horoscope.time.plus, self.horoscope.time.zh, self.horoscope.time.zm, self.horoscope.time.daylightsaving, self.horoscope.place, False)

		electionchart = chart.Chart(self.horoscope.name, self.horoscope.male, time, self.horoscope.place, chart.Chart.TRANSIT, '', self.options, False)

		ef = electionsframe.ElectionsFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.txts['Elections']+' ('+str(time.origyear)+'.'+common.common.months[time.origmonth-1]+'.'+str(time.origday)+' '+str(time.hour)+':'+str(time.minute).zfill(2)+':'+str(time.second).zfill(2)+')'), electionchart, self.horoscope, self.options)
		ef.Show(True)

		estepdlg = electionstepperdlg.ElectionStepperDlg(ef, self.horoscope, self.options, self.title)
		estepdlg.CenterOnParent()
		estepdlg.Show(True)


	def onSquareChart(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		sc = squarechartframe.SquareChartFrame(self, self.title, self.horoscope, self.options)
		sc.Show(True)


	def onProfectionsChart(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.horoscope.time.bc:
			dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		pdlg = profdlg.ProfDlg(self, self.horoscope.time.jd, self.horoscope.place)
#		h, m, s = util.decToDeg(self.horoscope.time.time)
		pdlg.initialize(self.horoscope.time.year, self.horoscope.time.month, self.horoscope.time.day, 12, 0, 0)

		pdlg.CenterOnParent()

		val = pdlg.ShowModal()
		if val == wx.ID_OK:
			y = int(pdlg.year.GetValue())
			m = int(pdlg.month.GetValue())
			d = int(pdlg.day.GetValue())
			h = int(pdlg.hour.GetValue())
			mi = int(pdlg.minute.GetValue())
			s = int(pdlg.second.GetValue())
			proftype = chart.Chart.YEAR

			t = h+mi/60.0+s/3600.0

			if self.options.zodprof:
				prof = profections.Profections(self.horoscope, y, m, d, t)
				pchart = chart.Chart(self.horoscope.name, self.horoscope.male, self.horoscope.time, self.horoscope.place, chart.Chart.PROFECTION, '', self.options, False, proftype)
				pchart.calcProfPos(prof)
			else:
				if not self.options.usezodprojsprof and (y == self.horoscope.time.year or (y-self.horoscope.time.year) % 12 == 0) and m == self.horoscope.time.month and d == self.horoscope.time.day:
					pchart = self.horoscope
				else:
					prof = munprofections.MunProfections(self.horoscope, y, m, d, t)
					proflondeg, proflonmin, proflonsec = util.decToDeg(prof.lonZ)
					profplace = chart.Place(mtexts.txts['Profections'], proflondeg, proflonmin, proflonsec, prof.east, self.horoscope.place.deglat, self.horoscope.place.minlat, self.horoscope.place.seclat, self.horoscope.place.north, self.horoscope.place.altitude)
					pchart = chart.Chart(self.horoscope.name, self.horoscope.male, self.horoscope.time, profplace, chart.Chart.PROFECTION, '', self.options, False, proftype, self.options.usezodprojsprof)
					pchartpls = chart.Chart(self.horoscope.name, self.horoscope.male, self.horoscope.time, self.horoscope.place, chart.Chart.PROFECTION, '', self.options, False, proftype, self.options.usezodprojsprof)
					#modify planets ...
					pchart.planets.calcMundaneProfPos(pchart.houses.ascmc2, pchartpls.planets.planets, self.horoscope.place.lat, self.horoscope.obl[0])

					#modify lof
					pchart.fortune.calcMundaneProfPos(pchart.houses.ascmc2, pchartpls.fortune, self.horoscope.place.lat, self.horoscope.obl[0])
	
					#recalc AspMatrix
					pchart.calcAspMatrix()

			pf = profectionsframe.ProfectionsFrame(self, self.title.replace(mtexts.typeList[self.horoscope.htype], mtexts.txts['Profections']+' ('+str(y)+'.'+str(m)+'.'+str(d)+' '+str(h).zfill(2)+':'+str(mi).zfill(2)+':'+str(s).zfill(2)+')'), pchart, self.horoscope, self.options)
			pf.Show(True)

			pstepdlg = profectionstepperdlg.ProfectionStepperDlg(pf, self.horoscope, y, m, d, t, self.options, self.title)
			pstepdlg.CenterOnParent()
			pstepdlg.Show(True)

		pdlg.Destroy()


	def onMundaneChart(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

#		if self.horoscope.time.bc:
#	 		dlgm = wx.MessageDialog(self, mtexts.txts['NotAvailable'], '', wx.OK|wx.ICON_INFORMATION)
#			dlgm.ShowModal()
#			dlgm.Destroy()
#			return

		mf = mundaneframe.MundaneFrame(self, self.title, self.options, self.horoscope, None)
		mf.Show(True)


	#Options-menu
	def onAppearance1(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = appearance1dlg.Appearance1Dlg(self)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		dlg.fill(self.options)

		topocentric = self.options.topocentric
#		traditionalaspects = self.options.traditionalaspects
		netb = self.options.netbook
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if(dlg.check(self.options)):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveAppearance1():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if netb != self.options.netbook:
					if self.options.subprimarydir == primdirs.PrimDirs.BOTH:
						self.options.subprimarydir = primdirs.PrimDirs.MUNDANE

				if not self.splash:
					self.closeChildWnds()


					if topocentric != self.options.topocentric:
						self.horoscope.recalc()
#					elif traditionalaspects != self.options.traditionalaspects:
#						self.horoscope.recalcAlmutens()

					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onAppearance2(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = appearance2dlg.Appearance2Dlg(self)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveAppearance2():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onSymbols(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = symbolsdlg.SymbolsDlg(self)
		dlg.CenterOnParent()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				common.common.update(self.options)

				if self.options.autosave:
					if self.options.saveSymbols():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onDignities(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = dignitiesdlg.DignitiesDlg(self, self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveDignities():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onAyanamsha(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = ayanamshadlg.AyanamshaDlg(self)
		dlg.CenterOnParent()
		dlg.fill(self.options)

		ayan = self.options.ayanamsha
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveAyanamsa():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()

					if ayan != self.options.ayanamsha:
						self.horoscope.recalc()

					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onColors(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = colorsdlg.ColorsDlg(self)
		dlg.CenterOnParent()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveColors():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onHouseSystem(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		typ = event.GetId()-self.hsbase
		hs = ('P', 'K', 'R', 'C', 'E', 'W', 'X', 'M', 'H', 'T', 'B', 'O')

		if self.options.hsys != hs[typ]:
			self.options.hsys = hs[typ]
			self.enableOptMenus(True)

			if self.options.autosave:
				if self.options.saveHouseSystem():
					self.moptions.Enable(self.ID_SaveOpts, True)

			if not self.splash:
				self.closeChildWnds()
				self.horoscope.setHouseSystem()
				self.horoscope.calcAspMatrix()
				self.horoscope.calcFixStarAspMatrix()
				self.horoscope.calcArabicParts()
				self.horoscope.recalcAlmutens()
				self.drawBkg()
				self.Refresh()


	def onNodes(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		typ = event.GetId()-self.nodebase
		nodes = (True, False)

		if self.options.meannode != nodes[typ]:
			self.options.meannode = nodes[typ]
			self.enableOptMenus(True)

			if self.options.autosave:
				if self.options.saveNodes():
					self.moptions.Enable(self.ID_SaveOpts, True)

			if not self.splash:
				self.closeChildWnds()
				self.horoscope.setNodes()
				self.horoscope.calcAspMatrix()
				self.horoscope.calcFixStarAspMatrix()
				self.drawBkg()
				self.Refresh()


	def onOrbs(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = orbisdlg.OrbisDlg(self, self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			dlg.save(dlg.currid)

			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveOrbs():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.calcAspMatrix()
					self.horoscope.calcFixStarAspMatrix()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onFortune(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = fortunedlg.FortuneDlg(self)
		dlg.CenterOnParent()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveFortune():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.calcFortune()
					self.horoscope.calcArabicParts()
					self.horoscope.calcAntiscia()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onArabicParts(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = arabicpartsdlg.ArabicPartsDlg(self, self.options)
		dlg.CenterOnParent()
		dlg.fill(self.options)
		wx.EndBusyCursor()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			ch, rem = dlg.check(self.options)
			if ch:
				self.enableOptMenus(True)

				if rem:
					if self.options.topicals != None:
						del self.options.topicals	
						self.options.topicals = None

				if self.options.autosave:
					if self.options.saveTopicalandParts():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.calcFortune()
					self.horoscope.calcAntiscia()
					self.horoscope.calcArabicParts()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onSyzygy(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = syzygydlg.SyzygyDlg(self)
		dlg.CenterOnParent()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveSyzygy():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.calcSyzygy()
					self.horoscope.calcArabicParts()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onFixStarsOpt(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if not self.checkFixStars():
			return
# ###########################################
# Elias -  V 8.0.0
# ###########################################
		dlg = fixstarsdlg.FixStarsDlg(self, self.options, common.common.ephepath)
# ###########################################
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options.fixstars):
				self.enableOptMenus(True)

				self.options.clearPDFSSel()

				if self.options.autosave:
					if self.options.saveFixstars():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.rebuildFixStars()
					self.horoscope.calcFixStarAspMatrix()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onProfectionsOpt(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = profdlgopts.ProfDlgOpts(self)
		dlg.fill(self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveProfections():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


# ###########################################
# Roberto change  V 7.2.0
	def onDefLocationOpt(self, event):
		dlg = defaultlocdlg.DefaultLocDlg(self, self.options.langid)
		dlg.fill(self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveDefLocation():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()
# ###########################################		


	def onLanguages(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = langsdlg.LanguagesDlg(self, self.options.langid)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:
			if dlg.check(self.options):
				self.enableOptMenus(True)

				#if self.options.autosave:
				#	if self.options.saveLanguages():
				self.moptions.Enable(self.ID_SaveOpts, True)
				if not self.splash:
					self.closeChildWnds()
#-------------------------------------------------------------------------------
				self.enableOptMenus(True)

				hasChart = self.mtable.IsEnabled(self.ID_Aspects)

				#os.remove(os.path.join(common.common.ephepath, 'fixstars.cat'))
				if self.options.langid<6:
					common.common.abc = os.path.join('Res', 'FreeSans.ttf')
					#shutil.copyfile(os.path.join(common.common.ephepath, 'fixstarsE.cat'), os.path.join(common.common.ephepath, 'fixstars.cat'))
				else:
					if self.options.langid == 6:
						common.common.abc      = os.path.join('Res', 'NotoSansSC-Regular.ttf')
						common.common.abc_bold = os.path.join('Res', 'NotoSansSC-Bold.ttf')
					elif self.options.langid == 7:
						common.common.abc      = os.path.join('Res', 'NotoSansTC-Regular.ttf')
						common.common.abc_bold = os.path.join('Res', 'NotoSansTC-Bold.ttf')
					elif self.options.langid == 8:
						common.common.abc      = os.path.join('Res', 'NotoSansKR-Regular.ttf')
						common.common.abc_bold = os.path.join('Res', 'NotoSansKR-Bold.ttf')
					else:
						common.common.abc      = os.path.join('Res', 'FreeSans.ttf')
						common.common.abc_bold = os.path.join('Res', 'FreeSansBold.ttf')

					if not os.path.exists(common.common.abc_bold):
						common.common.abc_bold = common.common.abc

				mtexts.setLang(self.options.langid)

				try:
					# 프레임에서 메뉴바를 안전하게 떼고(분리) 새로 붙인다
					self.SetMenuBar(None)
				except Exception:
					pass
				# 새 메뉴바 생성

				self.menubar = wx.MenuBar()
				self.mhoros = wx.Menu()
				self.mtable = wx.Menu()
				self.moptions = wx.Menu()
				self.mcharts = wx.Menu()
				self.mhelp = wx.Menu()
				#self.mhoros.Destroy()

		#Horoscope-menu
# ###########################################
# Roberto change  V 7.2.0 # Elias v 8.0.0 add Dodecatemoria
				self.ID_New, self.ID_Data, self.ID_HereAndNow, self.ID_Load, self.ID_Save, self.ID_SaveAsBitmap, self.ID_Synastry, self.ID_FindTime, self.ID_Ephemeris, self.ID_Close, self.ID_Exit = range(100, 111)
# ###########################################

		#Table-menu
# ###########################################
# Roberto change  V 7.3.0 + V 8.0.1
				(self.ID_Positions, self.ID_TAlmutens, self.ID_AlmutenZodiacal, self.ID_AlmutenChart, self.ID_AlmutenTopical, self.ID_Misc, self.ID_MunPos,
				self.ID_Antiscia, self.ID_Aspects, self.ID_Midpoints, self.ID_RiseSet, self.ID_Speeds, self.ID_ZodPars, self.ID_FixStars, self.ID_FixStarsAsps,
				self.ID_Arabians, self.ID_Strip, self.ID_PlanetaryHours, self.ID_ExactTransits, self.ID_Profections, self.ID_CustomerSpeculum, self.ID_Firdaria, self.ID_PrimaryDirs,self.ID_Dodecatemoria ) = range(111,135)
				self.ID_ZodiacalReleasing = 136
				self.ID_Phasis = 137
				self.ID_Paranatellonta = 138
				self.ID_Circumambulation = 139
				self.ID_Eclipses = 186
				self.ID_FixStarAngleDirs = 185  # Angular directions of fixed stars
		#Charts-menu
				self.ID_Transits, self.ID_Revolutions, self.ID_SunTransits, self.ID_SecondaryDirs, self.ID_Elections, self.ID_SquareChart, self.ID_ProfectionsChart, self.ID_MundaneChart = range(140, 148)

				self.ID_SecProgMenu = 5000  # Secondary progressions (submenu header)
				# --- new submenu headers ---
				self.ID_PlanetsPointsMenu = 5001
				self.ID_FixedStarsMenu   = 5002
				self.ID_TimeLordsMenu    = 5003
				self.ID_PrimaryDirsMenu  = 5004
				self.ID_TransitsMenu     = 5005
				self.ID_ChartsMenu      = 5016
				# --- Options submenu headers ---
				# --- New submenu headers ---
				self.ID_SaveMenu            = 5006  # Horoscope > Save group
				self.ID_ArabicPartsOptMenu  = 5011  # Options > ArabicParts (Fortuna+Arabic Parts)
				self.ID_PrimaryDirsOptMenu  = 5012  # Options > PrimaryDirs (Dirs+Keys+PDs in Chart)
				self.ID_TimeLordsOptMenu    = 5013  # Options > TimeLords (Profections+Firdaria)
				self.ID_AppearanceOptMenu   = 5014  # Options > Appearance1 (Appearance1/2+Colors+Symbols)
				self.ID_DignitiesOptMenu    = 5015  # Options > Dignities (Dignities+Minor Dignities)
				self.ID_PlanetsPointsOptMenu    = 5017  # Options > Planets/Points
				# Secondary progressions (Charts submenu)
				self.ID_SecProgChart = 148
				self.ID_SecProgPositions = 149
		#Options-menu
# ###########################################
# Roberto change  V 7.2.0
				(self.ID_Appearance1, self.ID_Appearance2, self.ID_Symbols, self.ID_Dignities, self.ID_MinorDignities, self.ID_Triplicities, self.ID_Terms,
				self.ID_Decans, self.ID_Almutens, self.ID_ChartAlmuten, self.ID_Topical, self.ID_Colors, self.ID_Ayanamsha, self.ID_HouseSystem,
				self.ID_Nodes, self.ID_Orbs, self.ID_PrimaryDirsOpt, self.ID_PrimaryKeys, self.ID_PDsInChartOpt, self.ID_PDsInChartOptZod, self.ID_PDsInChartOptMun, self.ID_LotOfFortune, self.ID_ArabicParts, self.ID_Syzygy, self.ID_FixStarsOpt, self.ID_ProfectionsOpt, self.ID_FirdariaOpt, self.ID_DefLocationOpt, self.ID_Languages, self.ID_AutoSaveOpts, self.ID_SaveOpts, self.ID_Reload) = range(151, 183)
# ###########################################

				self.ID_Housesystem1, self.ID_Housesystem2, self.ID_Housesystem3, self.ID_Housesystem4, self.ID_Housesystem5, self.ID_Housesystem6, self.ID_Housesystem7, self.ID_Housesystem8, self.ID_Housesystem9, self.ID_Housesystem10, self.ID_Housesystem11, self.ID_Housesystem12 = range(1050, 1062)

				self.ID_NodeMean = 1070
				self.ID_NodeTrue = 1071

				self.hsbase = 1050
				self.nodebase = 1070
# ###########################################
# Roberto change  V 7.2.0 /  V 7.3.0
		#Help-menu
				self.ID_Help = 183
				self.ID_About = 184
# ###########################################

		#Horoscope-menu
				self.mhoros.Append(self.ID_New, mtexts.menutxts['HMNew'], mtexts.menutxts['HMNewDoc'])
				self.mhoros.Append(self.ID_Data, mtexts.menutxts['HMData'], mtexts.menutxts['HMDataDoc'])
# ###########################################
# Roberto change  V 7.2.0
				self.mhoros.Append(self.ID_HereAndNow, mtexts.menutxts['HMHereAndNow'], mtexts.menutxts['HMHereAndNowDoc'])
# ###########################################
				self.mhoros.Append(self.ID_Load, mtexts.menutxts['HMLoad'], mtexts.menutxts['HMLoadDoc'])
				# Save group
				self.hsave = wx.Menu()
				self.hsave.Append(self.ID_Save,          mtexts.menutxts['HMSave'],       mtexts.menutxts['HMSaveDoc'])
				self.hsave.Append(self.ID_SaveAsBitmap,  mtexts.menutxts['HMSaveAsBmp'],  mtexts.menutxts['HMSaveAsBmpDoc'])
				self.mhoros.Append(self.ID_SaveMenu, mtexts.txts['Save'], self.hsave)

				self.mhoros.Append(self.ID_Synastry, mtexts.menutxts['HMSynastry'], mtexts.menutxts['HMSynastryDoc'])
				self.mhoros.Append(self.ID_FindTime, mtexts.menutxts['HMFindTime'], mtexts.menutxts['HMFindTimeDoc'])
				self.mhoros.Append(self.ID_Ephemeris, mtexts.menutxts['HMEphemeris'], mtexts.menutxts['HMEphemerisDoc'])
				self.mhoros.AppendSeparator()
				self.mhoros.Append(self.ID_Close, mtexts.menutxts['HMClose'], mtexts.menutxts['HMCloseDoc'])
				self.mhoros.AppendSeparator()
				self.mhoros.Append(self.ID_Exit, mtexts.menutxts['HMExit'], mtexts.menutxts['HMExitDoc'])

				self.filehistory = wx.FileHistory()
				self.filehistory.UseMenu(self.mhoros)
				self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)

		#Table-menu
				# ---------------- Tables (grouped) ----------------

				# Planets/Points
				self.tplanets = wx.Menu()
				self.tplanets.Append(self.ID_Positions,        mtexts.menutxts['TMPositions'],        mtexts.menutxts['TMPositionsDoc'])    
				self.tplanets.Append(self.ID_Antiscia,         mtexts.menutxts['TMAntiscia'],         mtexts.menutxts['TMAntisciaDoc'])          
				self.tplanets.Append(self.ID_Dodecatemoria,    mtexts.menutxts['TMDodecatemoria'],    mtexts.menutxts['TMDodecatemoriaDoc'])
				self.tplanets.Append(self.ID_Strip,            mtexts.menutxts['TMStrip'],            mtexts.menutxts['TMStripDoc']) 
				self.tplanets.Append(self.ID_Aspects,          mtexts.menutxts['TMAspects'],          mtexts.menutxts['TMAspectsDoc']) 
				self.tplanets.Append(self.ID_ZodPars,          mtexts.menutxts['TMZodPars'],          mtexts.menutxts['TMZodParsDoc'])
				self.tplanets.Append(self.ID_Speeds,           mtexts.menutxts['TMSpeeds'],           mtexts.menutxts['TMSpeedsDoc'])
				self.tplanets.Append(self.ID_RiseSet,          mtexts.menutxts['TMRiseSet'],          mtexts.menutxts['TMRiseSetDoc'])     
				self.tplanets.Append(self.ID_PlanetaryHours,   mtexts.menutxts['TMPlanetaryHours'],   mtexts.menutxts['TMPlanetaryHoursDoc'])
				self.tplanets.Append(self.ID_Phasis,           mtexts.menutxts['TMPhasis'],           mtexts.menutxts['TMPhasisDoc'])     
				self.tplanets.Append(self.ID_Midpoints,        mtexts.menutxts['TMMidpoints'],        mtexts.menutxts['TMMidpointsDoc'])
				self.tplanets.Append(self.ID_Arabians,         mtexts.menutxts['TMArabianParts'],     mtexts.menutxts['TMArabianPartsDoc'])
				self.tplanets.Append(self.ID_Eclipses,         mtexts.menutxts['TMEclipses'],         mtexts.menutxts['TMEclipsesDoc'])
				self.tplanets.Append(self.ID_Misc,             mtexts.menutxts['TMMisc'],             mtexts.menutxts['TMMiscDoc'])
				self.mtable.Append(self.ID_PlanetsPointsMenu, mtexts.txts['PlanetsPoints'], self.tplanets)

				# Almutens (existing submenu)
				self.talmutens = wx.Menu()
				self.talmutens.Append(self.ID_AlmutenChart,    mtexts.menutxts['TMAlmutenChart'],    mtexts.menutxts['TMAlmutenChartDoc'])
				self.talmutens.Append(self.ID_AlmutenZodiacal, mtexts.menutxts['TMAlmutenZodiacal'], mtexts.menutxts['TMAlmutenZodiacalDoc'])
				
				self.talmutens.Append(self.ID_AlmutenTopical,  mtexts.menutxts['TMAlmutenTopical'],  mtexts.menutxts['TMAlmutenTopicalDoc'])
				self.mtable.Append(self.ID_TAlmutens, mtexts.menutxts['TMAlmutens'], self.talmutens)
				# (Almutens 서브메뉴가 이미 존재하는 형태는 파일에 보임) :contentReference[oaicite:4]{index=4}

				# Fixed Stars
				self.tfixed = wx.Menu()
				self.tfixed.Append(self.ID_FixStars,        mtexts.menutxts['TMFixStars'],        mtexts.menutxts['TMFixStarsDoc'])
				self.tfixed.Append(self.ID_FixStarsAsps,    mtexts.menutxts['TMFixStarsAsps'],    mtexts.menutxts['TMFixStarsAspsDoc'])
				self.tfixed.Append(self.ID_FixStarsParallels, mtexts.menutxts['TMFixStarsParallels'], mtexts.menutxts['TMFixStarsParallelsDoc'])
				self.tfixed.Append(self.ID_Paranatellonta,  mtexts.menutxts['TMParanatellonta'],  mtexts.menutxts['TMParanatellontaDoc'])
				self.tfixed.Append(self.ID_AngleAtBirth,    mtexts.menutxts['TMAngleAtBirth'],    mtexts.menutxts['TMAngleAtBirthDoc'])
				self.mtable.Append(self.ID_FixedStarsMenu, mtexts.txts['FixStars'], self.tfixed)

				# Time Lords
				self.ttimelords = wx.Menu()
				self.ttimelords.Append(self.ID_Profections,        mtexts.menutxts['TMProfections'],        mtexts.menutxts['TMProfectionsDoc'])
				self.ttimelords.Append(self.ID_Firdaria,           mtexts.menutxts['TMFirdaria'],           mtexts.menutxts['TMFirdariaDoc'])
				self.ttimelords.Append(self.ID_Decennials,        mtexts.menutxts['TMDecennials'],        mtexts.menutxts['TMDecennialsDoc'])
				self.ttimelords.Append(self.ID_ZodiacalReleasing,  mtexts.menutxts['TMZodiacalReleasing'],  mtexts.menutxts['TMZodiacalReleasingDoc'])
				self.ttimelords.Append(self.ID_Circumambulation,   mtexts.menutxts['TMCircumambulation'],   mtexts.menutxts['TMCircumambulationDoc'])
				
				self.mtable.Append(self.ID_TimeLordsMenu, mtexts.txts['TimeLords'], self.ttimelords)

				# Primary Directions
				self.tpd = wx.Menu()
				self.tpd.Append(self.ID_PrimaryDirs,        mtexts.menutxts['TMPrimaryDirs'],        mtexts.menutxts['TMPrimaryDirsDoc'])
				self.tpd.Append(self.ID_FixStarAngleDirs,   mtexts.menutxts['TMFixStarAngleDirs'],   mtexts.menutxts['TMFixStarAngleDirsDoc'])
				self.tpd.Append(self.ID_MunPos,           mtexts.menutxts['TMMunPos'],           mtexts.menutxts['TMMunPosDoc'])
				self.tpd.Append(self.ID_CustomerSpeculum,   mtexts.menutxts['TMCustomerSpeculum'],   mtexts.menutxts['TMCustomerSpeculumDoc'])
				self.mtable.Append(self.ID_PrimaryDirsMenu, mtexts.txts['PrimaryDirs'], self.tpd)

				# Un-grouped (요청대로 단독 유지)
				self.mtable.Append(self.ID_ExactTransits, mtexts.menutxts['TMExactTransits'], mtexts.menutxts['TMExactTransitsDoc'])

		#Charts-menu
				# 앞부분: 기본 항목 먼저
				self.chartsmenu2 = wx.Menu()
				self.chartsmenu2.Append(self.ID_SquareChart,     mtexts.menutxts['PMSquareChart'],     mtexts.menutxts['PMSquareChartDoc'])
				self.chartsmenu2.Append(self.ID_MundaneChart,    mtexts.menutxts['PMMundane'],         mtexts.menutxts['PMMundaneDoc'])
				self.chartsmenu2.Append(self.ID_Elections,       mtexts.menutxts['PMElections'],       mtexts.menutxts['PMElectionsDoc'])
				self.mcharts.Append(self.ID_ChartsMenu, mtexts.txts['DCharts'], self.chartsmenu2)

				self.mcharts.Append(self.ID_ProfectionsChart,mtexts.menutxts['PMProfections'],     mtexts.menutxts['PMProfectionsDoc'])

				# Secondary Progressions 서브메뉴(기존 그대로)
				self.csecprog = wx.Menu()
				self.csecprog.Append(self.ID_SecProgChart,     mtexts.menutxts['PMSecondaryDirs'],    mtexts.menutxts['PMSecondaryDirsDoc'])
				self.csecprog.Append(self.ID_SecProgPositions, mtexts.menutxts['PMPositionForDate'],  mtexts.menutxts['PMPositionForDateDoc'])
				self.mcharts.Append(self.ID_SecProgMenu, mtexts.txts['SecondaryDirs'], self.csecprog)
				
				self.mcharts.Append(self.ID_Revolutions,     mtexts.menutxts['PMRevolutions'],     mtexts.menutxts['PMRevolutionsDoc'])

				# Transits 서브메뉴 신설
				self.ctransits = wx.Menu()
				self.ctransits.Append(self.ID_Transits,    mtexts.menutxts['PMTransits'],    mtexts.menutxts['PMTransitsDoc'])
				self.ctransits.Append(self.ID_SunTransits, mtexts.menutxts['PMSunTransits'], mtexts.menutxts['PMSunTransitsDoc'])
				self.mcharts.Append(self.ID_TransitsMenu, mtexts.txts['Transits'], self.ctransits)

		#Options-menu
				self.mhousesystem = wx.Menu()
				self.itplac = self.mhousesystem.Append(self.ID_Housesystem1, mtexts.menutxts['OMHSPlacidus'], '', wx.ITEM_RADIO)
				self.itkoch = self.mhousesystem.Append(self.ID_Housesystem2, mtexts.menutxts['OMHSKoch'], '', wx.ITEM_RADIO)
				self.itregio = self.mhousesystem.Append(self.ID_Housesystem3, mtexts.menutxts['OMHSRegiomontanus'], '', wx.ITEM_RADIO)
				self.itcampa = self.mhousesystem.Append(self.ID_Housesystem4, mtexts.menutxts['OMHSCampanus'], '', wx.ITEM_RADIO)
				self.itequal = self.mhousesystem.Append(self.ID_Housesystem5, mtexts.menutxts['OMHSEqual'], '', wx.ITEM_RADIO)
				self.itwholesign = self.mhousesystem.Append(self.ID_Housesystem6, mtexts.menutxts['OMHSWholeSign'], '', wx.ITEM_RADIO)
				self.itaxial = self.mhousesystem.Append(self.ID_Housesystem7, mtexts.menutxts['OMHSAxial'], '', wx.ITEM_RADIO)
				self.itmorin = self.mhousesystem.Append(self.ID_Housesystem8, mtexts.menutxts['OMHSMorinus'], '', wx.ITEM_RADIO)
				self.ithoriz = self.mhousesystem.Append(self.ID_Housesystem9, mtexts.menutxts['OMHSHorizontal'], '', wx.ITEM_RADIO)
				self.itpage = self.mhousesystem.Append(self.ID_Housesystem10, mtexts.menutxts['OMHSPagePolich'], '', wx.ITEM_RADIO)
				self.italcab = self.mhousesystem.Append(self.ID_Housesystem11, mtexts.menutxts['OMHSAlcabitus'], '', wx.ITEM_RADIO)
				self.itporph = self.mhousesystem.Append(self.ID_Housesystem12, mtexts.menutxts['OMHSPorphyrius'], '', wx.ITEM_RADIO)

				# [Appearance1] submenu: Appearance1/Speculum(=Appearance2)/Colors/Symbols
				self.o_appearance = wx.Menu()
				self.o_appearance.Append(self.ID_Appearance1, mtexts.menutxts['OMAppearance1'], mtexts.menutxts['OMAppearance1Doc'])

				self.o_appearance.Append(self.ID_Colors,      mtexts.menutxts['OMColors'],      mtexts.menutxts['OMColorsDoc'])
				self.o_appearance.Append(self.ID_Symbols,     mtexts.menutxts['OMSymbols'],     mtexts.menutxts['OMSymbolsDoc'])
				self.moptions.Append(self.ID_AppearanceOptMenu, mtexts.txts['DDCharts'], self.o_appearance)

				self.o_appearance.Append(self.ID_Ayanamsha, mtexts.menutxts['OMAyanamsha'], mtexts.menutxts['OMAyanamshaDoc'])
				self.o_appearance.Append(self.ID_HouseSystem, mtexts.menutxts['OMHouseSystem'], self.mhousesystem)
				self.setHouse()

				self.o_planetsopt = wx.Menu()
				self.o_planetsopt.Append(self.ID_Appearance2, mtexts.menutxts['OMAppearance2'], mtexts.menutxts['OMAppearance2Doc'])
				self.o_planetsopt.Append(self.ID_Orbs, mtexts.menutxts['OMOrbs'], mtexts.menutxts['OMOrbsDoc'])
				# [Dignities] submenu: Dignities + Minor Dignities(submenu)
				self.o_digs = wx.Menu()
				self.o_digs.Append(self.ID_Dignities, mtexts.menutxts['OMDignities'], mtexts.menutxts['OMDignitiesDoc'])
				self.mdignities = wx.Menu()
				self.mdignities.Append(self.ID_Triplicities, mtexts.menutxts['OMTriplicities'], mtexts.menutxts['OMTriplicitiesDoc'])
				self.mdignities.Append(self.ID_Terms,        mtexts.menutxts['OMTerms'],        mtexts.menutxts['OMTermsDoc'])
				self.mdignities.Append(self.ID_Decans,       mtexts.menutxts['OMDecans'],       mtexts.menutxts['OMDecansDoc'])
				self.o_digs.Append(self.ID_MinorDignities, mtexts.menutxts['OMMinorDignities'], self.mdignities)
				self.o_planetsopt.Append(self.ID_DignitiesOptMenu, mtexts.txts['Dignities'], self.o_digs)
				self.mnodes = wx.Menu()
				self.meanitem = self.mnodes.Append(self.ID_NodeMean, mtexts.menutxts['OMNMean'], '', wx.ITEM_RADIO)
				self.trueitem = self.mnodes.Append(self.ID_NodeTrue, mtexts.menutxts['OMNTrue'], '', wx.ITEM_RADIO)
				self.o_planetsopt.Append(self.ID_Nodes, mtexts.menutxts['OMNodes'], self.mnodes)
				self.setNode()
				# [ArabicParts] submenu: Arabic Parts(first) + Fortuna(second)
				self.o_arabic = wx.Menu()
				self.o_arabic.Append(self.ID_ArabicParts,  mtexts.menutxts['OMArabicParts'],  mtexts.menutxts['OMArabicPartsDoc'])
				self.o_arabic.Append(self.ID_LotOfFortune, mtexts.menutxts['OMLotFortune'],   mtexts.menutxts['OMLotFortuneDoc'])
				self.o_planetsopt.Append(self.ID_ArabicPartsOptMenu, mtexts.txts['ArabicParts'], self.o_arabic)

				self.o_planetsopt.Append(self.ID_Syzygy,      mtexts.menutxts['OMSyzygy'],      mtexts.menutxts['OMSyzygyDoc'])
				self.moptions.Append(self.ID_PlanetsPointsOptMenu, mtexts.txts['PlanetsPoints'], self.o_planetsopt)

				self.malmutens = wx.Menu()
				self.malmutens.Append(self.ID_ChartAlmuten, mtexts.menutxts['OMChartAlmuten'], mtexts.menutxts['OMChartAlmutenDoc'])
				self.malmutens.Append(self.ID_Topical, mtexts.menutxts['OMTopical'], mtexts.menutxts['OMTopicalDoc'])
				self.moptions.Append(self.ID_Almutens, mtexts.menutxts['OMAlmutens'], self.malmutens)

				self.moptions.Append(self.ID_FixStarsOpt, mtexts.menutxts['OMFixStarsOpt'], mtexts.menutxts['OMFixStarsOptDoc'])
				
				# [TimeLords] submenu: Profections + Firdaria
				self.o_tl = wx.Menu()
				self.o_tl.Append(self.ID_ProfectionsOpt, mtexts.menutxts['OMProfectionsOpt'], mtexts.menutxts['OMProfectionsOptDoc'])
				self.o_tl.Append(self.ID_FirdariaOpt,    mtexts.menutxts['OMFirdariaOpt'],    mtexts.menutxts['OMFirdariaOptDoc'])
				self.moptions.Append(self.ID_TimeLordsOptMenu, mtexts.txts['TimeLords'], self.o_tl)

				# [PrimaryDirs] submenu: Primary Dirs + Primary Keys + PDs in Chart(submenu)
				self.o_pd = wx.Menu()
				self.o_pd.Append(self.ID_PrimaryDirsOpt, mtexts.menutxts['OMPrimaryDirs'], mtexts.menutxts['OMPrimaryDirsDoc'])
				self.o_pd.Append(self.ID_PrimaryKeys,    mtexts.menutxts['OMPrimaryKeys'], mtexts.menutxts['OMPrimaryKeysDoc'])
				self.mpdsinchartopts = wx.Menu()
				self.mpdsinchartopts.Append(self.ID_PDsInChartOptZod, mtexts.menutxts['OMPDsInChartOptZod'], mtexts.menutxts['OMPDsInChartOptZodDoc'])
				self.mpdsinchartopts.Append(self.ID_PDsInChartOptMun, mtexts.menutxts['OMPDsInChartOptMun'], mtexts.menutxts['OMPDsInChartOptMunDoc'])
				self.o_pd.Append(self.ID_PDsInChartOpt, mtexts.menutxts['OMPDsInChartOpt'], self.mpdsinchartopts)
				self.moptions.Append(self.ID_PrimaryDirsOptMenu, mtexts.txts['PrimaryDirs'], self.o_pd)

# ###########################################
# Roberto change V 7.2.0
				self.moptions.Append(self.ID_DefLocationOpt, mtexts.menutxts['OMDefLocationOpt'], mtexts.menutxts['OMDefLocationOptDoc'])
# ###########################################
				self.moptions.Append(self.ID_Languages, mtexts.menutxts['OMLanguages'], mtexts.menutxts['OMLanguagesDoc'])
				self.moptions.AppendSeparator()
				self.autosave = self.moptions.Append(self.ID_AutoSaveOpts, mtexts.menutxts['OMAutoSave'], mtexts.menutxts['OMAutoSaveDoc'], wx.ITEM_CHECK)
				self.moptions.Append(self.ID_SaveOpts, mtexts.menutxts['OMSave'], mtexts.menutxts['OMSaveDoc'])
				self.moptions.Append(self.ID_Reload, mtexts.menutxts['OMReload'], mtexts.menutxts['OMReloadDoc'])

				self.setAutoSave()

		#Help-menu
				self.mhelp.Append(self.ID_Help, mtexts.menutxts['HEMHelp'], mtexts.menutxts['HEMHelpDoc'])
				self.mhelp.Append(self.ID_About, mtexts.menutxts['HEMAbout'], mtexts.menutxts['HEMAboutDoc'])


				self.menubar.Append(self.mhoros, mtexts.menutxts['MHoroscope'])
				self.menubar.Append(self.mtable, mtexts.menutxts['MTable'])
				self.menubar.Append(self.mcharts, mtexts.menutxts['MCharts'])
				self.menubar.Append(self.moptions, mtexts.menutxts['MOptions'])
				self.menubar.Append(self.mhelp, mtexts.menutxts['MHelp'])
				self.SetMenuBar(self.menubar)

				self.handleStatusBar(False)

				self.Bind(wx.EVT_MENU, self.onNew, id=self.ID_New)
				self.Bind(wx.EVT_MENU, self.onData, id=self.ID_Data)
				self.Bind(wx.EVT_MENU, self.onLoad, id=self.ID_Load)
# ###########################################
# Roberto change  V 7.2.0
				self.Bind(wx.EVT_MENU, self.onHereAndNow, id=self.ID_HereAndNow)
# ###########################################
				self.Bind(wx.EVT_MENU, self.onSave, id=self.ID_Save)
				self.Bind(wx.EVT_MENU, self.onSaveAsBitmap, id=self.ID_SaveAsBitmap)
				self.Bind(wx.EVT_MENU, self.onSynastry, id=self.ID_Synastry)
				self.Bind(wx.EVT_MENU, self.onFindTime, id=self.ID_FindTime)
				self.Bind(wx.EVT_MENU, self.onEphemeris, id=self.ID_Ephemeris)
				self.Bind(wx.EVT_MENU, self.onClose, id=self.ID_Close)
				self.Bind(wx.EVT_MENU, self.onExit, id=self.ID_Exit)

				if os.name == 'mac' or os.name == 'posix':
					self.Bind(wx.EVT_PAINT, self.onPaint)
				else:
					self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)

				self.Bind(wx.EVT_SIZE, self.onSize)
				self.Bind(wx.EVT_MENU_OPEN, self.onMenuOpen)
		#The events EVT_MENU_OPEN and CLOSE are not called on windows in case of accelarator-keys
				self.Bind(wx.EVT_MENU_CLOSE, self.onMenuClose)

				self.Bind(wx.EVT_MENU, self.onPositions, id=self.ID_Positions)
				self.Bind(wx.EVT_MENU, self.onAlmutenZodiacal, id=self.ID_AlmutenZodiacal)
				self.Bind(wx.EVT_MENU, self.onAlmutenChart, id=self.ID_AlmutenChart)
				self.Bind(wx.EVT_MENU, self.onAlmutenTopical, id=self.ID_AlmutenTopical)
				self.Bind(wx.EVT_MENU, self.onMisc, id=self.ID_Misc)
				self.Bind(wx.EVT_MENU, self.onMunPos, id=self.ID_MunPos)
				self.Bind(wx.EVT_MENU, self.onAntiscia, id=self.ID_Antiscia)
# ###################################
# Elias change v 8.0.0
#		self.Bind(wx.EVT_MENU, self.onDodecatemoria, id=self.ID_Dodecatemoria)
# ###################################
				self.Bind(wx.EVT_MENU, self.onAspects, id=self.ID_Aspects)
				self.Bind(wx.EVT_MENU, self.onFixStars, id=self.ID_FixStars)
				self.Bind(wx.EVT_MENU, self.onFixStarsAsps, id=self.ID_FixStarsAsps)
				self.Bind(wx.EVT_MENU, self.onFixStarsParallels, id=self.ID_FixStarsParallels)
				self.Bind(wx.EVT_MENU, self.onMidpoints, id=self.ID_Midpoints)
				self.Bind(wx.EVT_MENU, self.onRiseSet, id=self.ID_RiseSet)
				self.Bind(wx.EVT_MENU, self.onSpeeds, id=self.ID_Speeds)
				self.Bind(wx.EVT_MENU, self.onZodPars, id=self.ID_ZodPars)
				self.Bind(wx.EVT_MENU, self.onArabians, id=self.ID_Arabians)
				self.Bind(wx.EVT_MENU, self.onStrip, id=self.ID_Strip)
				self.Bind(wx.EVT_MENU, self.onPlanetaryHours, id=self.ID_PlanetaryHours)
				self.Bind(wx.EVT_MENU, self.onExactTransits, id=self.ID_ExactTransits)
				self.Bind(wx.EVT_MENU, self.onProfections, id=self.ID_Profections)
# ###########################################
# Roberto change V 7.3.0
				self.Bind(wx.EVT_MENU, self.onFirdaria, id=self.ID_Firdaria)
# ###########################################
# ###################################
# Roberto change v 8.0.1
				self.Bind(wx.EVT_MENU, self.onDodecatemoria, id=self.ID_Dodecatemoria)
# ###################################
				self.Bind(wx.EVT_MENU, self.onCustomerSpeculum, id=self.ID_CustomerSpeculum)
				self.Bind(wx.EVT_MENU, self.onPrimaryDirs, id=self.ID_PrimaryDirs)

				self.Bind(wx.EVT_MENU, self.onTransits, id=self.ID_Transits)
				self.Bind(wx.EVT_MENU, self.onRevolutions, id=self.ID_Revolutions)
				self.Bind(wx.EVT_MENU, self.onSunTransits, id=self.ID_SunTransits)
				self.Bind(wx.EVT_MENU, self.onSecondaryDirs, id=self.ID_SecondaryDirs)
				self.Bind(wx.EVT_MENU, self.onElections, id=self.ID_Elections)
				self.Bind(wx.EVT_MENU, self.onSquareChart, id=self.ID_SquareChart)
				self.Bind(wx.EVT_MENU, self.onProfectionsChart, id=self.ID_ProfectionsChart)
				self.Bind(wx.EVT_MENU, self.onMundaneChart, id=self.ID_MundaneChart)

				self.Bind(wx.EVT_MENU, self.onAppearance1, id=self.ID_Appearance1)
				self.Bind(wx.EVT_MENU, self.onAppearance2, id=self.ID_Appearance2)
				self.Bind(wx.EVT_MENU, self.onSymbols, id=self.ID_Symbols)
				self.Bind(wx.EVT_MENU, self.onDignities, id=self.ID_Dignities)
				self.Bind(wx.EVT_MENU, self.onAyanamsha, id=self.ID_Ayanamsha)
				self.Bind(wx.EVT_MENU, self.onColors, id=self.ID_Colors)
				self.Bind(wx.EVT_MENU_RANGE, self.onHouseSystem, id=self.ID_Housesystem1, id2=self.ID_Housesystem12)
				self.Bind(wx.EVT_MENU_RANGE, self.onNodes, id=self.ID_NodeMean, id2=self.ID_NodeTrue)
				self.Bind(wx.EVT_MENU, self.onOrbs, id=self.ID_Orbs)
				self.Bind(wx.EVT_MENU, self.onPrimaryDirsOpt, id=self.ID_PrimaryDirsOpt)
				self.Bind(wx.EVT_MENU, self.onPrimaryKeys, id=self.ID_PrimaryKeys)
				self.Bind(wx.EVT_MENU, self.onPDsInChartOptZod, id=self.ID_PDsInChartOptZod)
				self.Bind(wx.EVT_MENU, self.onPDsInChartOptMun, id=self.ID_PDsInChartOptMun)
				self.Bind(wx.EVT_MENU, self.onFortune, id=self.ID_LotOfFortune)
				self.Bind(wx.EVT_MENU, self.onArabicParts, id=self.ID_ArabicParts)
				self.Bind(wx.EVT_MENU, self.onSyzygy, id=self.ID_Syzygy)
				self.Bind(wx.EVT_MENU, self.onFixStarsOpt, id=self.ID_FixStarsOpt)
				self.Bind(wx.EVT_MENU, self.onProfectionsOpt, id=self.ID_ProfectionsOpt)
# ###########################################
# Roberto change  V 7.3.0
				self.Bind(wx.EVT_MENU, self.onFirdariaOpt, id=self.ID_FirdariaOpt)
# ###########################################
# ###########################################
# Roberto change  V 7.2.0
				self.Bind(wx.EVT_MENU, self.onDefLocationOpt, id=self.ID_DefLocationOpt)
# ###########################################


				self.Bind(wx.EVT_MENU, self.onLanguages, id=self.ID_Languages)
				self.Bind(wx.EVT_MENU, self.onTriplicities, id=self.ID_Triplicities)
				self.Bind(wx.EVT_MENU, self.onTerms, id=self.ID_Terms)
				self.Bind(wx.EVT_MENU, self.onDecans, id=self.ID_Decans)
				self.Bind(wx.EVT_MENU, self.onChartAlmuten, id=self.ID_ChartAlmuten)
				self.Bind(wx.EVT_MENU, self.onTopicals, id=self.ID_Topical)
				self.Bind(wx.EVT_MENU, self.onAutoSaveOpts, id=self.ID_AutoSaveOpts)
				self.Bind(wx.EVT_MENU, self.onSaveOpts, id=self.ID_SaveOpts)
				self.Bind(wx.EVT_MENU, self.onReload, id=self.ID_Reload)

				self.Bind(wx.EVT_MENU, self.onHelp, id=self.ID_Help)
				self.Bind(wx.EVT_MENU, self.onAbout, id=self.ID_About)

				self.Bind(wx.EVT_CLOSE, self.onExit)

				self.splash = True

				self.enableMenus(False)
				self.moptions.Enable(self.ID_SaveOpts, True)
				if self.options.checkOptsFiles():
					self.moptions.Enable(self.ID_Reload, True)
				else:
					self.moptions.Enable(self.ID_Reload, False)



				if hasChart:
					self.handleStatusBar(True)
					self.handleCaption(True)
					self.splash = False
					self.enableMenus(True)


				if self.options.autosave:
					if self.options.saveLanguages():
						self.moptions.Enable(self.ID_SaveOpts, True)
#-------------------------------------------------------------------------------

		dlg.Destroy()


	def onTriplicities(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = triplicitiesdlg.TriplicitiesDlg(self, self.options)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveTriplicities():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.recalcAlmutens()
#					self.drawBkg()
#					self.Refresh()

		dlg.Destroy()


	def onTerms(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = termsdlg.TermsDlg(self, self.options)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveTerms():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onDecans(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = decansdlg.DecansDlg(self, self.options)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveDecans():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onChartAlmuten(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = almutenchartdlg.AlmutenChartDlg(self)
		dlg.fill(self.options)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveChartAlmuten():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onTopicals(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()
		dlg = almutentopicalsdlg.AlmutenTopicalsDlg(self, self.options)
		dlg.fill(self.options)
		dlg.CenterOnParent()
		wx.EndBusyCursor()
		val = dlg.ShowModal()
		if val == wx.ID_OK:
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveTopicalandParts():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.horoscope.recalcAlmutens()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()

# ###########################################
# Roberto change V 7.3.0
	def onFirdariaOpt(self, event):
		dlg = firdariadlg.FirdariaDlg(self)
		dlg.fill(self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.saveFirdaria():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()

# ###########################################


	def onPrimaryDirsOpt(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		wx.BeginBusyCursor()

		dlg = None
		if self.options.netbook:
			dlg = primarydirsdlgsmall.PrimDirsDlgSmall(self, self.options, common.common.ephepath)
		else:
			dlg = primarydirsdlg.PrimDirsDlg(self, self.options, common.common.ephepath)

		dlg.CenterOnParent()
		wx.EndBusyCursor()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			changed, changedU1, changedU2 = dlg.check(self.options)
			if changed or changedU1 or changedU2:
				if changedU1 and not self.splash:
					cpd = None
					if self.options.pdcustomer:
						cpd = customerpd.CustomerPD(self.options.pdcustomerlon[0], self.options.pdcustomerlon[1], self.options.pdcustomerlon[2], self.options.pdcustomerlat[0], self.options.pdcustomerlat[1], self.options.pdcustomerlat[2], self.options.pdcustomersouthern, self.horoscope.place.lat, self.horoscope.houses.ascmc2, self.horoscope.obl[0], self.horoscope.raequasc)
					self.horoscope.setCustomer(cpd)

				if changedU2 and not self.splash:
					cpd2 = None
					if self.options.pdcustomer2:
						cpd2 = customerpd.CustomerPD(self.options.pdcustomer2lon[0], self.options.pdcustomer2lon[1], self.options.pdcustomer2lon[2], self.options.pdcustomer2lat[0], self.options.pdcustomer2lat[1], self.options.pdcustomer2lat[2], self.options.pdcustomer2southern, self.horoscope.place.lat, self.horoscope.houses.ascmc2, self.horoscope.obl[0], self.horoscope.raequasc)
					self.horoscope.setCustomer2(cpd2)

				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.savePrimaryDirs():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onPrimaryKeys(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = primarykeysdlg.PrimaryKeysDlg(self, self.options)
		dlg.CenterOnParent()
		dlg.fill(self.options)

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.savePrimaryKeys():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onPDsInChartOptZod(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = pdsinchartdlgopts.PDsInChartsDlgOpts(self)
		dlg.fill(self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.savePDsInChart():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onPDsInChartOptMun(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = pdsinchartterrdlgopts.PDsInChartsTerrDlgOpts(self)
		dlg.fill(self.options)
		dlg.CenterOnParent()

		val = dlg.ShowModal()
		if val == wx.ID_OK:	
			if dlg.check(self.options):
				self.enableOptMenus(True)

				if self.options.autosave:
					if self.options.savePDsInChart():
						self.moptions.Enable(self.ID_SaveOpts, True)

				if not self.splash:
					self.closeChildWnds()
					self.drawBkg()
					self.Refresh()

		dlg.Destroy()


	def onAutoSaveOpts(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		self.options.autosave = self.autosave.IsChecked()
		if self.options.autosave:
			if self.options.save():
				self.moptions.Enable(self.ID_SaveOpts, True)


	def onSaveOpts(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		if self.options.save():
			self.moptions.Enable(self.ID_SaveOpts, True)


	def onReload(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
		val = dlg.ShowModal()
		if val == wx.ID_YES:
			if self.options.checkOptsFiles():
				self.options.removeOptsFiles()
			self.options.reload()
			common.common.update(self.options)
			self.enableOptMenus(False)
			self.setHouse()
			self.setNode()
			self.setAutoSave()
			if not self.splash:
				self.closeChildWnds()
				self.horoscope.recalc()
				self.drawBkg()
				self.Refresh()


	def onHelp(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		fname = os.path.join('Res', mtexts.helptxt)

		if not os.path.exists(fname):
			txt = fname+' '+mtexts.txts['NotFound']
			dlgm = wx.MessageDialog(self, txt, mtexts.txts['Error'], wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
		else:
			hframe = htmlhelpframe.HtmlHelpFrame(self, -1, mtexts.txts['Morinus'], fname)
			hframe.Show(True)


	def onAbout(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

		info = wx.adv.AboutDialogInfo()
		info.Name = mtexts.txts['Morinus']
# ###########################################
# V 8.1.0 kept from V 8.0.5
# Elias -  V 8.0.5
# Roberto - V 7.4.4-804

		info.Version = '9.5.9'
# ###########################################
		info.Copyright = mtexts.txts['FreeSoft']
		info.Description = mtexts.txts['Description']+str(astrology.swe_version())
		info.WebSite = 'https://sourceforge.net/p/morinus-updated/'
		info.Developers = ['In alphabetical surname order:\n\nRobert Nagy (Hungary); robert.pluto@gmail.com (programming and astrology)\n\nPhilippe Epaud (France); philipeau@free.fr (French translation)\nMargherita Fiorello (Italy); margherita.fiorello@gmail.com (astrology, Italian translation)\nMartin Gansten (Sweden); http://www.martingansten.com/ (astrology)\nJaime Chica Londoño (Colombia); aulavirtual@astrochart.org (Spanish translation)\nRoberto Luporini (Italy); roberto.luporini@tiscali.it (programming and astrological astronomy)\nElías D. Molins (Spain); elias@biblioteca-astrologia.es (programming and astrology)\nPetr Radek (Czech Rep.); petr_radek@raz-dva.cz (astrology)\nJames Ren (China);541632950@qq.com (programming and astrology, Chinese translation)\nShin Ji-Hyeon (South Korea); shin10567@naver.com (programming and astrology, Korean translation)\nEndre Csaba Simon (Finland); secsaba@gmail.com (programming and astrology)\nVáclav Jan Špirhanzl (Czech Rep.); vjs.morinus@gmail.com (MacOS version)\nDenis Steinhoff (Israel); denis@steindan.com (astrology, Russian translation)']
		info.License = mtexts.licensetxt

		# --- Use GenericAboutDialog so we can override tab captions from mtexts ---
		try:
			dlg = wx.adv.GenericAboutDialog(info, self)
		except AttributeError:
			dlg = None  # very old wxPython fallback

		if dlg:
			labels = {
				u"Info":       mtexts.txts.get("AboutTabInfo",       u"Info"),
				u"License":    mtexts.txts.get("AboutTabLicense",    u"License"),
				u"Developers": mtexts.txts.get("AboutTabDevelopers", u"Developers"),
			}

			def _find_notebook(win):
				for child in win.GetChildren():
					if isinstance(child, wx.Notebook):
						return child
					nb = _find_notebook(child)
					if nb:
						return nb
				return None

			nb = _find_notebook(dlg)
			if nb:
				for i in range(nb.GetPageCount()):
					old = nb.GetPageText(i)
					if old in labels:
						nb.SetPageText(i, labels[old])

			dlg.Layout()
			dlg.Fit()
			dlg.CenterOnParent()
			dlg.ShowModal()
			dlg.Destroy()
		else:
			# Last-resort fallback (very old wx): show stock AboutBox (labels will follow wx's built-ins)
			wx.adv.AboutBox(info)

	#Misc
	def setHouse(self):
		sysh = (self.itplac, self.itkoch, self.itregio, self.itcampa, self.itequal, self.itwholesign, self.itaxial, self.itmorin, self.ithoriz, self.itpage, self.italcab, self.itporph)
		for i in range(len(sysh)):
			if houses.Houses.hsystems[i] == self.options.hsys:
				sysh[i].Check(True)


	def setNode(self):
		if self.options.meannode:
			self.meanitem.Check(True)
		else:
			self.trueitem.Check(True)


	def setAutoSave(self):
		self.autosave.Check(self.options.autosave)


	def closeChildWnds(self):
		li = self.GetChildren()
		for ch in li:
			x,y = ch.GetClientSize()
			if ch.GetName() != 'status_line' and y > 50:
				ch.Destroy()


	def onMenuOpen(self, event):
		if not self.splash:
			self.handleStatusBar(False)


	def onMenuClose(self, event):
		if not self.splash:
			self.handleStatusBar(True)


	def enableMenus(self, bEnable):
		self.mhoros.Enable(self.ID_New, not bEnable)
		self.mhoros.Enable(self.ID_Data, bEnable)
# ###########################################
# Roberto change  V 7.2.0		
		self.mhoros.Enable(self.ID_HereAndNow, not bEnable)
# ###########################################
		self.mhoros.Enable(self.ID_Save, bEnable)
		self.mhoros.Enable(self.ID_SaveAsBitmap, bEnable)
		self.mhoros.Enable(self.ID_SaveMenu, bEnable)
		self.mhoros.Enable(self.ID_Synastry, bEnable)
		self.mhoros.Enable(self.ID_Close, bEnable)
		self.mtable.Enable(self.ID_Positions, bEnable)
		self.mtable.Enable(self.ID_TAlmutens, bEnable)
		self.mtable.Enable(self.ID_AlmutenZodiacal, bEnable)
		self.mtable.Enable(self.ID_AlmutenChart, bEnable)
		self.mtable.Enable(self.ID_AlmutenTopical, bEnable)
		self.mtable.Enable(self.ID_Misc, bEnable)
		self.mtable.Enable(self.ID_MunPos, bEnable)
		self.mtable.Enable(self.ID_Antiscia, bEnable)
# ###################################
# Elias change v 8.0.0
#		self.mtable.Enable(self.ID_Dodecatemoria, bEnable)
# ###################################    
		self.mtable.Enable(self.ID_Aspects, bEnable)
		self.mtable.Enable(self.ID_FixStars, bEnable)
		self.mtable.Enable(self.ID_FixStarsAsps, bEnable)
		self.mtable.Enable(self.ID_Midpoints, bEnable)
		self.mtable.Enable(self.ID_RiseSet, bEnable)
		self.mtable.Enable(self.ID_Speeds, bEnable)
		self.mtable.Enable(self.ID_ZodPars, bEnable)
		self.mtable.Enable(self.ID_Arabians, bEnable)
		self.mtable.Enable(self.ID_Strip, bEnable)
		self.mtable.Enable(self.ID_PlanetaryHours, bEnable)
		self.mtable.Enable(self.ID_ExactTransits, bEnable)
		self.mtable.Enable(self.ID_Profections, bEnable)
		self.mtable.Enable(self.ID_CustomerSpeculum, bEnable)
# ###########################################
# Roberto change  V 7.3.0		
		self.mtable.Enable(self.ID_Firdaria, bEnable)
# ###########################################		
# ###################################
# Roberto change v 8.0.1
		self.mtable.Enable(self.ID_Dodecatemoria, bEnable)
		self.mtable.Enable(self.ID_AngleAtBirth, bEnable)
		self.mtable.Enable(self.ID_PrimaryDirs, bEnable)
		self.mtable.Enable(self.ID_ZodiacalReleasing, bEnable)
		self.mtable.Enable(self.ID_Phasis, bEnable)
		self.mtable.Enable(self.ID_Paranatellonta, bEnable)
		self.mtable.Enable(self.ID_Circumambulation, bEnable)
		self.mtable.Enable(self.ID_FixStarAngleDirs, bEnable)
		self.mtable.Enable(self.ID_Eclipses, bEnable)
		self.mcharts.Enable(self.ID_Transits, bEnable)
		self.mcharts.Enable(self.ID_Revolutions, bEnable)
		self.mcharts.Enable(self.ID_SunTransits, bEnable)
		self.mcharts.Enable(self.ID_SecProgMenu, bEnable)
		self.mcharts.Enable(self.ID_ChartsMenu, bEnable)
		self.mcharts.Enable(self.ID_SecProgChart, bEnable)
		self.mcharts.Enable(self.ID_SecProgPositions, bEnable)
		self.mcharts.Enable(self.ID_Elections, bEnable)
		self.mcharts.Enable(self.ID_SquareChart, bEnable)
		self.mcharts.Enable(self.ID_ProfectionsChart, bEnable)
		self.mcharts.Enable(self.ID_MundaneChart, bEnable)
		# --- NEW: disable/enable newly added grouped submenus when no chart is open ---
		# Tables (group headers)
		for _mid in (
			getattr(self, 'ID_PlanetsPointsMenu', None),
			getattr(self, 'ID_FixedStarsMenu',   None),
			getattr(self, 'ID_TimeLordsMenu',    None),
			getattr(self, 'ID_PrimaryDirsMenu',  None),
			getattr(self, 'ID_ChartsMenu',  None),
			getattr(self, 'ID_PlanetsPointsoptMenu',  None),
		):
			try:
				if _mid is not None:
					self.mtable.Enable(_mid, bEnable)
			except Exception:
				# In case the submenu wasn't built in this build variant
				pass

		# Charts (group header)
		try:
			self.mcharts.Enable(self.ID_TransitsMenu, bEnable)
		except Exception:
			pass


	def enableOptMenus(self, bEnable):
		self.moptions.Enable(self.ID_SaveOpts, bEnable)
		self.moptions.Enable(self.ID_Reload, bEnable)


	def handleStatusBar(self, bHor):
		sb = self.GetStatusBar()
		if sb is None:
			sb = self.CreateStatusBar(name='status_line')
		if bHor:
			sb.SetFieldsCount(4)
			sb.SetStatusWidths([160, 80, 220, 220])
			txt = self.horoscope.name
			if self.horoscope.name == '':
				txt = mtexts.txts['Untitled']
			self.SetStatusText(txt, 0)
			self.SetStatusText(mtexts.typeList[self.horoscope.htype], 1)
			signtxt = ''
			if self.horoscope.time.bc:
				signtxt = '-'
			ztxt = mtexts.txts['UT']
			if self.horoscope.time.zt == chart.Time.ZONE:
				ztxt = mtexts.txts['ZN']
			if self.horoscope.time.zt == chart.Time.LOCALMEAN or self.horoscope.time.zt == chart.Time.LOCALAPPARENT:
				ztxt = mtexts.txts['LC']
			txt = signtxt+str(self.horoscope.time.origyear)+'.'+common.common.months[self.horoscope.time.origmonth-1]+'.'+(str(self.horoscope.time.origday)).zfill(2)+', '+(str(self.horoscope.time.hour)).zfill(2)+':'+(str(self.horoscope.time.minute)).zfill(2)+':'+(str(self.horoscope.time.second)).zfill(2)+ztxt
			self.SetStatusText(txt, 2)
			deg_symbol = u'°'
			t1 = mtexts.txts['Long']+': '
			t2 = ', '+mtexts.txts['Lat']+': '
			dirlontxt = mtexts.txts['E']
			if not self.horoscope.place.east:
				dirlontxt = mtexts.txts['W']
			dirlattxt = mtexts.txts['N']
			if not self.horoscope.place.north:
				dirlattxt = mtexts.txts['S']

			txt = t1+(str(self.horoscope.place.deglon)).zfill(2)+deg_symbol+(str(self.horoscope.place.minlon)).zfill(2)+"'"+dirlontxt+t2+(str(self.horoscope.place.deglat)).zfill(2)+deg_symbol+(str(self.horoscope.place.minlat)).zfill(2)+"'"+dirlattxt
			self.SetStatusText(txt, 3)
		else:
			sb.SetFieldsCount(1)
			self.SetStatusText('')


	def handleCaption(self, bHor):
		if bHor:
			name = self.horoscope.name
			if name == '':
				name = mtexts.txts['Untitled']
			path = self.fpath
			if self.fpath == '':
				path = '-----'

			txt = self.origtitle+' - '+'['+name+', '+mtexts.typeList[self.horoscope.htype]+'; '+path+']'
			self.title = txt
		else:
			self.title = self.origtitle

		self.SetTitle(self.title)


	def checkFixStars(self):
		res = True

		# 고정별 카탈로그 탐색 우선순위:
		# 1) <ephepath>\sefstars.txt
		# 2) <ephepath>\SWEP\Ephem\sefstars.txt
		# 3) <ephepath>\fixstars.cat
		# 4) <ephepath>\fixedstars.cat
		# 5) <ephepath>\SWEP\Ephem\fixstars.cat
		# 6) <ephepath>\SWEP\Ephem\fixedstars.cat
		base = common.common.ephepath
		p0 = os.path.join(base, 'sefstars.txt')
		p1 = os.path.join(base, 'fixstars.cat')
		p2 = os.path.join(base, 'fixedstars.cat')
		p3 = os.path.join(base, 'SWEP', 'Ephem', 'sefstars.txt')
		p4 = os.path.join(base, 'SWEP', 'Ephem', 'fixstars.cat')
		p5 = os.path.join(base, 'SWEP', 'Ephem', 'fixedstars.cat')

		if   os.path.exists(p0): fname = p0
		elif os.path.exists(p3): fname = p3
		elif os.path.exists(p1): fname = p1
		elif os.path.exists(p2): fname = p2
		elif os.path.exists(p4): fname = p4
		elif os.path.exists(p5): fname = p5
		else:
			# 아무것도 못 찾았을 때: 시도한 경로들을 안내
			tried = [p0, p3, p1, p2, p4, p5]
			txt = (mtexts.txts.get('NotFound', 'Not found') + u':\n' +
				   u'\n'.join(tried))
			dlgm = wx.MessageDialog(self, txt, mtexts.txts.get('Error','Error'),
									wx.OK | wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			res = False
		# --- [ADD] 선호이름 JSON을 옵션에 로드(세션 시작 시 복구) ---
		try:
			if not hasattr(self.options, 'fixstarAliasMap') or not isinstance(self.options.fixstarAliasMap, dict):
				self.options.fixstarAliasMap = {}
			alias_json = os.path.join(base, 'fixstar_aliases.json')
			if os.path.isfile(alias_json):
				import json as _json
				with open(alias_json, 'r') as _f:
					_data = _json.load(_f)
				if isinstance(_data, dict):
					self.options.fixstarAliasMap.update({k: v for k, v in _data.items() if isinstance(k, str)})
		except Exception:
			pass
		# -------------------------------------------------------------------

		return res


	def drawSplash(self):
		splashpath = os.path.join('Res', 'Morinus.jpg')
		self.buffer = wx.Image(splashpath).ConvertToBitmap()


	def drawBkg(self):
		gchart = None
		if self.options.theme == 0:
			gchart = graphchart.GraphChart(self.horoscope, self.GetClientSize(), self.options, self.options.bw)
		else:
			gchart = graphchart2.GraphChart2(self.horoscope, self.GetClientSize(), self.options, self.options.bw)

		if gchart != None:
			self.buffer = gchart.drawChart()


	def onEraseBackground(self, event):
		dc = wx.ClientDC(self)
#		dc = event.GetDC()
		x = y = 0

		if self.splash:
			wx.size = self.GetClientSize()
			x = wx.size.x/2-self.buffer.GetWidth()/2
			y = wx.size.y/2-self.buffer.GetHeight()/2

			bkgclr = self.options.clrbackground
			if self.options.bw:
				bkgclr = (255,255,255)
			self.SetBackgroundColour(bkgclr)
			self.ClearBackground()

		dc.DrawBitmap(self.buffer, x, y)


	def onPaint(self, event):
		dc = wx.ClientDC(self)
#		dc = event.GetDC()
		x = y = 0

		if self.splash:
			wx.size = self.GetClientSize()
			x = wx.size.x/2-self.buffer.GetWidth()/2
			y = wx.size.y/2-self.buffer.GetHeight()/2

			bkgclr = self.options.clrbackground
			if self.options.bw:
				bkgclr = (255,255,255)
			self.SetBackgroundColour(bkgclr)

		dc.DrawBitmap(self.buffer, x, y)


	def onSize(self, event):
		if self.splash:
			self.Refresh()
		else:
			self.drawBkg()
			self.Refresh()


	def calc(self):
		for planet in self.horoscope.planets.planets:
			print ('')
			print ('%s:' % planet.name)

			(d, m, s) = decToDeg(planet.data[0])
			print ('lon: %02d %02d\' %02d"' % (d, m, s))
			(d, m, s) = decToDeg(planet.data[1])
			print ('lat: %02d %02d\' %02d"' % (d, m, s))
			(d, m, s) = decToDeg(planet.data[3])
			if planet.data[3] > 0:
				print ('speed: %02d %02d\' %02d"' % (d, m, s))
			else:
				print ('speed: %02d %02d\' %02d"  R' % (d, m, s))


		print ('')
		print ('Houses')
		for i in range(1, Houses.HOUSE_NUM+1):
			(d, m, s) = decToDeg(self.horoscope.houses.cusps[i])
			print ('house[%d]: %02d %02d\' %02d"' % (i, d, m, s))

		print ('')
		print ('Vars')
		xvars = ('Asc', 'MC', 'ARMC', 'Vertex', 'Equatorial Ascendant', 'Co-Asc', 'Co-Asc2', 'Polar Asc')
		for i in range(0, 8):
			(d, m, s) = decToDeg(self.horoscope.houses.ascmc[i])
			print ('%s = %02d %02d\' %02d"' % (xvars[i], d, m, s))


#import swisseph as swe
from sweastrology import *
def _get_obliquity_deg(jd_ut):
	# mean obliquity
	return swe.obl_ecl(jd_ut)[0]  # degrees

def lot_declination_deg(lon_ecl_deg, jd_ut, beta_ecl_deg=0.0):
	"""

	"""
	eps = _get_obliquity_deg(jd_ut)
	# swe.cotrans((lon, lat, dist), eps) -> (RA, Dec, dist) in degrees
	ra_deg, dec_deg, _ = swe.cotrans((lon_ecl_deg, beta_ecl_deg, 1.0), eps)
	return dec_deg

def fmt_decl_deg(x):
	
	sign = u'+' if x >= 0 else u'−'
	ax = abs(x)
	d = int(ax)
	m = int((ax - d) * 60)
	s = int(round(((ax - d) * 60 - m) * 60))
	
	if s == 60:
		s = 0; m += 1
	if m == 60:
		m = 0; d += 1
	return u"%s%02d°%02d′%02d″" % (sign, d, m, s)






