# -*- coding: utf-8 -*-
import  wx
import intvalidator
import revolutions
import rangechecker
import util
import mtexts
import wx


#---------------------------------------------------------------------------
# Create and set a help provider.  Normally you would do this in
# the app's OnInit as it must be done before any SetHelpText calls.
provider = wx.SimpleHelpProvider()
wx.HelpProvider.Set(provider)

#---------------------------------------------------------------------------
# 파일 맨 아래쪽(클래스들 끝난 뒤)에 추가
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import wx

class RevolutionYearStepper(wx.Dialog):
	"""
	결과(세 번째) 차트 옆에 띄워서 연도 ±1로 갱신하는 작은 모델리스 팝업.
	get_year() -> int : 현재 기준연도 콜백
	set_year(int) -> None : 연도 설정 및 재계산 콜백
	"""
	def __init__(self, parent, get_year_cb, set_year_cb):
		wx.Dialog.__init__(self, parent, -1, mtexts.txts["Revolution"]+ " "+mtexts.txts["Year"],
						style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		# (선택) parent가 TopLevel이면 효과: 부모 위에만 뜸
		try:
			self.SetWindowStyleFlag(self.GetWindowStyleFlag() | wx.FRAME_FLOAT_ON_PARENT)
		except Exception:
			pass

		self.get_year = get_year_cb
		self.set_year = set_year_cb

		self.lbl = wx.StaticText(self, -1, (mtexts.txts["Year"]+": %s") % (self.get_year(),))
		# 버튼 세로 높이 키우기: 최소 높이 36px
		self.btn_prev = wx.Button(self, -1, "-1 "+mtexts.txts["Year"])
		self.btn_prev.SetMinSize((-1, 45))
		self.btn_next = wx.Button(self, -1, "+1 "+mtexts.txts["Year"])
		self.btn_next.SetMinSize((-1, 45))

		# 라벨 폰트 약간 키우기(선택)
		try:
			f = self.lbl.GetFont()
			f.SetPointSize(f.GetPointSize() + 1)
			self.lbl.SetFont(f)
		except Exception:
			pass

		# 여유 있는 내부 여백
		row = wx.BoxSizer(wx.HORIZONTAL)
		# 순서 변경: +가 왼쪽, -가 오른쪽
		row.Add(self.btn_next, 0, wx.ALL, 8)
		row.Add(self.lbl,      0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 8)
		row.Add(self.btn_prev, 0, wx.ALL, 8)

		outer = wx.BoxSizer(wx.VERTICAL)
		outer.Add(row, 0, wx.ALL, 4)
		self.SetSizerAndFit(outer)

		self.Bind(wx.EVT_BUTTON, self.on_prev, self.btn_prev)
		self.Bind(wx.EVT_BUTTON, self.on_next, self.btn_next)

		# ← / → 단축키
		accel = wx.AcceleratorTable([
			(0, wx.WXK_LEFT,  self.btn_prev.GetId()),
			(0, wx.WXK_RIGHT, self.btn_next.GetId()),
		])
		self.SetAcceleratorTable(accel)

	def _refresh(self):
		self.lbl.SetLabel( (mtexts.txts["Year"]+": %s") % (self.get_year(),))
		self.Layout()
		self.Fit()

	def on_prev(self, evt):
		self.set_year(self.get_year() - 1)
		self._refresh()

	def on_next(self, evt):
		self.set_year(self.get_year() + 1)
		self._refresh()

class RevolutionMonthStepper(wx.Dialog):
	"""
	Lunar Revolution용: 가운데 Year, 그 아래 Month 두 줄 라벨.
	+1 Month 버튼은 '왼쪽', -1 Month는 '오른쪽'. 버튼은 두툼.
	get_ym_cb() -> (year:int, month:int)
	set_ym_cb(year:int, month:int) -> None
	"""
	def __init__(self, parent, get_ym_cb, set_ym_cb):
		wx.Dialog.__init__(self, parent, -1, mtexts.txts["Revolution"]+ " "+mtexts.txts["Month"],
						   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		try:
			self.SetWindowStyleFlag(self.GetWindowStyleFlag() | wx.FRAME_FLOAT_ON_PARENT)
		except Exception:
			pass

		# 콜백 저장
		self.get_ym = get_ym_cb
		self.set_ym = set_ym_cb

		# 라벨 2줄 (가운데 정렬)
		y, m = self.get_ym()
		self.lbl_year  = wx.StaticText(self, -1, (mtexts.txts["Year"]+": %s")   % y)
		self.lbl_month = wx.StaticText(self, -1, (mtexts.txts["Month"]+": %02d") % m)

		vlabel = wx.BoxSizer(wx.VERTICAL)
		vlabel.Add(self.lbl_year,  0, wx.ALIGN_CENTER | wx.BOTTOM, 2)
		vlabel.Add(self.lbl_month, 0, wx.ALIGN_CENTER | wx.TOP,    2)

		# 버튼(+가 왼쪽, 두툼)
		self.btn_next = wx.Button(self, -1, "+1 "+mtexts.txts["Month"]); self.btn_next.SetMinSize((-1, 45))
		self.btn_prev = wx.Button(self, -1, "-1 "+mtexts.txts["Month"]); self.btn_prev.SetMinSize((-1, 45))

		row = wx.BoxSizer(wx.HORIZONTAL)
		row.Add(self.btn_next, 0, wx.ALL, 8)  # +가 왼쪽
		row.Add(vlabel,        0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 8)
		row.Add(self.btn_prev, 0, wx.ALL, 8)

		outer = wx.BoxSizer(wx.VERTICAL)
		outer.Add(row, 0, wx.ALL, 4)
		self.SetSizerAndFit(outer)

		# 이벤트/단축키
		self.Bind(wx.EVT_BUTTON, self._on_prev, self.btn_prev)
		self.Bind(wx.EVT_BUTTON, self._on_next, self.btn_next)
		accel = wx.AcceleratorTable([
			(0, wx.WXK_LEFT,  self.btn_prev.GetId()),
			(0, wx.WXK_RIGHT, self.btn_next.GetId()),
		])
		self.SetAcceleratorTable(accel)

	def _refresh_labels(self):
		y, m = self.get_ym()
		self.lbl_year.SetLabel((mtexts.txts["Year"]+": %s")   % y)
		self.lbl_month.SetLabel((mtexts.txts["Month"]+": %02d") % m)
		self.Layout()
		self.Fit()

	def _on_prev(self, evt):
		y, m = self.get_ym()
		m -= 1
		if m < 1:
			m = 12; y -= 1
		self.set_ym(y, m)
		self._refresh_labels()

	def _on_next(self, evt):
		y, m = self.get_ym()
		m += 1
		if m > 12:
			m = 1; y += 1
		self.set_ym(y, m)
		self._refresh_labels()

class RevolutionsDlg(wx.Dialog):
	def __init__(self, parent):
		# Instead of calling wx.Dialog.__init__ we precreate the dialog
		# so we can set an extra style that must be set before
		# creation, and then we create the GUI object using the Create
		# method.
#        pre = wx.PreDialog()
#        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
#        pre.Create(parent, -1, mtexts.txts['Revolutions'], pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

		# This next step is the most important, it turns this Python
		# object into the real wrapper of the dialog (instead of pre)
		# as far as the wxPython extension is concerned.
#        self.PostCreate(pre)
		wx.Dialog.__init__(self, None, -1, mtexts.txts['Revolutions'], size=wx.DefaultSize)
		# 팝업이 뜨기 '직전'의 top window를 기억해 둔다(대개 리턴 차트 프레임).
		self._prev_top = wx.GetActiveWindow()
		if not isinstance(self._prev_top, wx.TopLevelWindow) or self._prev_top is self:
			self._prev_top = parent

		#main vertical sizer
		mvsizer = wx.BoxSizer(wx.VERTICAL)
		#main horizontal sizer
		mhsizer = wx.BoxSizer(wx.HORIZONTAL)

		#Type
		stype =wx.StaticBox(self, label='')
		typesizer = wx.StaticBoxSizer(stype, wx.VERTICAL)
		self.typecb = wx.ComboBox(self, -1, mtexts.revtypeList[0], size=(100, -1), choices=mtexts.revtypeList, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		typesizer.Add(self.typecb, 0, wx.ALIGN_CENTER|wx.TOP, 20)
		mhsizer.Add(typesizer, 0, wx.GROW|wx.ALIGN_CENTER)

		#Time
		rnge = 3000
		checker = rangechecker.RangeChecker()
		if checker.isExtended():
			rnge = 5000
		self.stime =wx.StaticBox(self, label='')
		timesizer = wx.StaticBoxSizer(self.stime, wx.VERTICAL)
		label = wx.StaticText(self, -1, mtexts.txts['StartingDate'])
		vsubsizer = wx.BoxSizer(wx.VERTICAL)
		vsubsizer.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		fgsizer = wx.FlexGridSizer(2, 3,9,24)
		label = wx.StaticText(self, -1, mtexts.txts['Year']+':')
		vsizer = wx.BoxSizer(wx.VERTICAL)
		vsizer.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		self.year = wx.TextCtrl(self, -1, '', validator=intvalidator.IntValidator(0, rnge), size=(50,-1))
		vsizer.Add(self.year, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		if checker.isExtended():
			self.year.SetHelpText(mtexts.txts['HelpYear'])
		else:
			self.year.SetHelpText(mtexts.txts['HelpYear2'])
		self.year.SetMaxLength(4)
		fgsizer.Add(vsizer, 0, wx.ALIGN_LEFT|wx.ALL, 5)

		vsizer = wx.BoxSizer(wx.VERTICAL)
		label = wx.StaticText(self, -1, mtexts.txts['Month']+':')
		vsizer.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		self.month = wx.TextCtrl(self, -1, '', validator=intvalidator.IntValidator(1, 12), size=(50,-1))
		self.month.SetHelpText(mtexts.txts['HelpMonth'])
		self.month.SetMaxLength(2)
		vsizer.Add(self.month, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		fgsizer.Add(vsizer, 0, wx.ALIGN_LEFT|wx.ALL, 5)

		vsizer = wx.BoxSizer(wx.VERTICAL)
		label = wx.StaticText(self, -1, mtexts.txts['Day']+':')
		vsizer.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		self.day = wx.TextCtrl(self, -1, '', validator=intvalidator.IntValidator(1, 31), size=(50,-1))
		self.day.SetHelpText(mtexts.txts['HelpDay'])
		self.day.SetMaxLength(2)
		vsizer.Add(self.day, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 0)
		fgsizer.Add(vsizer, 0, wx.ALIGN_LEFT|wx.ALL, 5)

		vsubsizer.Add(fgsizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
		timesizer.Add(vsubsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		mhsizer.Add(timesizer, 0, wx.ALIGN_LEFT|wx.LEFT, 5)
		mvsizer.Add(mhsizer, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT, 5)

		btnsizer = wx.StdDialogButtonSizer()

		if wx.Platform != '__WXMSW__':
			btn = wx.ContextHelpButton(self)
			btnsizer.AddButton(btn)
		
		btnOk = wx.Button(self, wx.ID_OK, mtexts.txts['Ok'])
		btnsizer.AddButton(btnOk)
		btnOk.SetHelpText(mtexts.txts['HelpOk'])
		btnOk.SetDefault()

		btn = wx.Button(self, wx.ID_CANCEL, mtexts.txts['Cancel'])
		btnsizer.AddButton(btn)
		btn.SetHelpText(mtexts.txts['HelpCancel'])

		btnsizer.Realize()

		mvsizer.Add(btnsizer, 0, wx.GROW|wx.ALL, 10)
		self.SetSizer(mvsizer)
		mvsizer.Fit(self)
		self.CentreOnParent()
		self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		btnOk.SetFocus()

		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)


	def onOK(self, event):
		if (self.Validate() and self.stime.Validate()):

			if util.checkDate(int(self.year.GetValue()), int(self.month.GetValue()), int(self.day.GetValue())):
				# 날짜만 비교(현지 원본 날짜 우선 사용)
				by = getattr(self._chrt.time, 'origyear',  self._chrt.time.year)
				bm = getattr(self._chrt.time, 'origmonth', self._chrt.time.month)
				bd = getattr(self._chrt.time, 'origday',   self._chrt.time.day)

				y = int(self.year.GetValue()); m = int(self.month.GetValue()); d = int(self.day.GetValue())

				# 출생 '날짜'보다 빠르면 차단 (동일 날짜는 허용)
				if (y, m, d) < (by, bm, bd):
					dlgm = wx.MessageDialog(self, mtexts.txts['TimeSmallerThanBirthTime'], mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
					dlgm.ShowModal()
					dlgm.Destroy()
					return

				self.SetReturnCode(wx.ID_OK)
				wx.CallAfter(self._restore_parent)  # 닫힌 직후 부모를 최상단으로
				try:
					self.EndModal(wx.ID_OK)         # 모달 종료(정석)
				except Exception:
					self.Close()                    # 혹시 모달이 아닐 경우 안전장치
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['InvalidDate']+' ('+self.year.GetValue()+'.'+self.month.GetValue()+'.'+self.day.GetValue()+'.)', mtexts.txts['Error'], wx.OK|wx.ICON_EXCLAMATION)
				dlgm.ShowModal()		
				dlgm.Destroy()

	def _restore_parent(self):
		# 1순위: 팝업 뜨기 직전의 top window (대개 리턴 차트)
		candidates = []
		if getattr(self, "_prev_top", None):
			candidates.append(self._prev_top)

		# 2순위: 직접 parent
		p = self.GetParent()
		if p and p not in candidates:
			candidates.append(p)

		# 3순위: 화면에 떠 있는 TopLevel 중 제목에 Revolution/Return이 들어간 창(리턴 차트 추정)
		try:
			for w in wx.GetTopLevelWindows():
				title = ""
				try:
					title = w.GetTitle() or ""
				except Exception:
					pass
				if isinstance(w, wx.TopLevelWindow) and w.IsShown():
					t = title.lower()
					if ("revolution" in t) or ("return" in t) or ("solar" in t):
						if w not in candidates:
							candidates.append(w)
		except Exception:
			pass

		# 4순위: 그 밖의 보이는 TopLevel들(마지막 안전망)
		try:
			for w in wx.GetTopLevelWindows():
				if isinstance(w, wx.TopLevelWindow) and w.IsShown() and w not in candidates:
					candidates.append(w)
		except Exception:
			pass

		# 순서대로 Raise/Focus 시도
		for w in candidates:
			try:
				w.Raise()
				w.SetFocus()
				break
			except Exception:
				continue

	def onCancel(self, evt):
		self.SetReturnCode(wx.ID_CANCEL)
		wx.CallAfter(self._restore_parent)
		try:
			self.EndModal(wx.ID_CANCEL)
		except Exception:
			self.Close()

	def onClose(self, evt):
		wx.CallAfter(self._restore_parent)
		try:
			if self.IsModal():
				self.SetReturnCode(wx.ID_CANCEL)
				self.EndModal(wx.ID_CANCEL)
			else:
				self.Destroy()
		except Exception:
			pass
			
	def initialize(self, chrt):
		self._chrt = chrt
		year = chrt.time.year
		month = chrt.time.month
		day = chrt.time.day

		#year, month, day = util.incrDay(year, month, day)
		year = chrt.time.origyear + 1
		month = 1
		day = 1

		self.typecb.SetStringSelection(mtexts.revtypeList[revolutions.Revolutions.SOLAR])
		self.year.SetValue(str(year))
		self.month.SetValue(str(month))
		self.day.SetValue(str(day))