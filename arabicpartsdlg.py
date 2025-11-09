# -*- coding: utf-8 -*-
import sys
import wx
import intvalidator
import chart
import arabicparts
import options
import mtexts
import copy
import astrology
import dlgutils
#---------------------------------------------------------------------------
# Create and set a help provider.  Normally you would do this in
# the app's OnInit as it must be done before any SetHelpText calls.
provider = wx.SimpleHelpProvider()
wx.HelpProvider.Set(provider)

#---------------------------------------------------------------------------
# daimon = 原等于守护神

class PartsListCtrl(wx.ListCtrl):
	def _deg_to_text(self, absdeg):
		try:
			absdeg = int(absdeg) % 360
		except:
			return u'?'
		signs = [u'Ari',u'Tau',u'Gem',u'Can',u'Leo',u'Vir',u'Lib',u'Sco',u'Sag',u'Cap',u'Aqu',u'Pis']
		sg = absdeg // 30
		dg = absdeg % 30
		return u'%d\u00B0%s' % (dg, signs[sg])

	def _render_token_text(self, code, idxABC, triplet):
		# 1) 인덱스 경로
		try:
			label = mtexts.partstxts[code]
		except Exception:
			# 2) 상수값 경로: 역매핑 캐시 사용
			rev = getattr(mtexts, '_conv_rev_cache', None)
			if not isinstance(rev, dict):
				try:
					rev = dict((v, k) for (k, v) in mtexts.conv.items())
				except Exception:
					rev = {}
				mtexts._conv_rev_cache = rev
			label = rev.get(code)
			if label is None:
				# conv 갱신 이후 캐시가 구버전일 수 있음 → 재구축
				try:
					rev = dict((v, k) for (k, v) in mtexts.conv.items())
				except Exception:
					rev = {}
				mtexts._conv_rev_cache = rev
				label = rev.get(code, u'?')

		txt = label
		want_lord = False
		if txt.endswith(u'!'):
			want_lord = True
			txt = txt[:-1]

		if txt == mtexts.txts.get('DE', u'DE'):
			out = self._deg_to_text(triplet[idxABC])
			return out + (u'!' if want_lord else u'')

		if txt == mtexts.txts.get('RE', u'RE'):
			rn = int(triplet[idxABC])
			label = u'#%d' % (rn+1)
			return label + (u'!' if want_lord else u'')

		return label

	def _format_formula_text(self, f1, f2, f3, triplet):
		return u'%s + %s - %s' % (self._render_token_text(f1,0,triplet), self._render_token_text(f2,1,triplet), self._render_token_text(f3,2,triplet))
	INDEXCOL = 0
	ACTIVE = 1
	NAME = 2
	FORMULA = 3
	DIURNAL = 4

	DIURNALTXT = u'*'

	MAX_ARABICPARTS_NUM = 40

	def __init__(self, parent, ID, parts, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)

		self.partsdata = {}
		self.parts_codes = {}
		self.parts_refdeg = {}
		self.parts_active = {}
		self.load(parts)

		self.Populate()
		self.Id = ID
		self.changed = False
		self.removed = False


	def Populate(self):
		self.InsertColumn(PartsListCtrl.INDEXCOL, u'#', format=wx.LIST_FORMAT_CENTER)
		self.InsertColumn(PartsListCtrl.ACTIVE, mtexts.txts['Active'], format=wx.LIST_FORMAT_CENTER)
		self.InsertColumn(PartsListCtrl.NAME, mtexts.txts['Name'])
		self.InsertColumn(PartsListCtrl.FORMULA, mtexts.txts['Formula'])
		self.InsertColumn(PartsListCtrl.DIURNAL, mtexts.txts['Diurnal'], format=wx.LIST_FORMAT_CENTER)
		
		items = self.partsdata.items()
		for key, data in items:
			index = self.InsertItem(sys.maxsize, data[0])
			self.SetItem(index, PartsListCtrl.NAME, data[0])
			self.SetItem(index, PartsListCtrl.FORMULA, data[1])
			self.SetItem(index, PartsListCtrl.DIURNAL, data[2])
			self.SetItemData(index, key)
			# Active/Index 표시
			active = self.parts_active.get(key, True)
			self.SetItem(index, PartsListCtrl.ACTIVE, mtexts.txts['On'] if active else mtexts.txts['Off'])
			self.SetItem(index, PartsListCtrl.INDEXCOL, u'#%d' % (index+2))
		self.SetColumnWidth(PartsListCtrl.INDEXCOL, 50)
		self.SetColumnWidth(PartsListCtrl.ACTIVE, 65)
		self.SetColumnWidth(PartsListCtrl.NAME, 160)#wx.LIST_AUTOSIZE)
		self.SetColumnWidth(PartsListCtrl.FORMULA, 140)
		self.SetColumnWidth(PartsListCtrl.DIURNAL, 65)

		self.currentItem = -1
		if len(self.partsdata):
			self.currentItem = 0
			self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)


	def GetListCtrl(self):
		return self


	def getColumnText(self, index, col):
		item = self.GetItem(index, col)
		return item.GetText()


	def OnItemSelected(self, event):
		# Phoenix/Classic 모두 안전하게
		try:
			idx = event.GetIndex()
		except AttributeError:
			idx = getattr(event, 'm_itemIndex', -1)

		if idx is None:
			idx = -1
		self.currentItem = idx

		if idx >= 0:
			try:
				key = self.GetItemData(idx)
				self.GetParent().activeckb.SetValue(self.parts_active.get(key, True))
			except Exception:
				pass

		event.Skip()

	def OnColClick(self,event):
		event.Skip()

	def _renumber_rows(self):
		# LoF는 항상 첫 행(#1), 나머지는 #2부터
		count = self.GetItemCount()
		if count <= 0:
			return
		self.SetItem(0, PartsListCtrl.INDEXCOL, u'#1')
		for row in range(1, count):
			self.SetItem(row, PartsListCtrl.INDEXCOL, u'#%d' % (row+1))

	def _refresh_active_for_row(self, row):
		if row < 0 or row >= self.GetItemCount():
			return
		key = self.GetItemData(row)
		active = self.parts_active.get(key, True)
		self.SetItem(row, PartsListCtrl.ACTIVE, mtexts.txts['On'] if active else mtexts.txts['Off'])

	def AddFullItem(self, name, disp_formula, diurnal, codes, triplet, active=True):
		num = self.GetItemCount()
		if num >= PartsListCtrl.MAX_ARABICPARTS_NUM:
			return False
		index = self.InsertItem(num, name)
		self.SetItem(index, PartsListCtrl.NAME, name)
		self.SetItem(index, PartsListCtrl.FORMULA, disp_formula)
		self.SetItem(index, PartsListCtrl.DIURNAL, diurnal)
		key = (max(self.partsdata.keys())+1) if len(self.partsdata) else 1
		self.SetItemData(index, key)
		self.partsdata[key] = (name, disp_formula, diurnal)
		self.parts_codes[key] = codes
		self.parts_refdeg[key] = triplet
		self.parts_active[key] = bool(active)
		self.SetItem(index, PartsListCtrl.ACTIVE, mtexts.txts['On'] if active else mtexts.txts['Off'])
		self.SetItem(index, PartsListCtrl.INDEXCOL, u'#%d' % (index+2))
		self.currentItem = index
		self.EnsureVisible(self.currentItem)
		self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
		self.changed = True
		self._renumber_rows()
		return True

	def OnAdd(self, item):

		name = self.name.GetValue()
		if not name or not name.strip():
			wx.MessageBox(mtexts.txts['ArabicPartNameEmpty'], mtexts.txts['Confirm'])
			return

		num = self.GetItemCount()
		if num >= PartsListCtrl.MAX_ARABICPARTS_NUM:
			txt = mtexts.txts['MaxArabicPartsNum']+str(PartsListCtrl.MAX_ARABICPARTS_NUM)+u'!'
			dlgm = wx.MessageDialog(self, txt, '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()#
			return

		if self.checkName(item[PartsListCtrl.NAME]):
			dlgm = wx.MessageDialog(self, mtexts.txts['ArabicPartAlreadyExists'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()#
			return

		if item[PartsListCtrl.NAME] == '':
			dlgm = wx.MessageDialog(self, mtexts.txts['ArabicPartNameEmpty'], '', wx.OK|wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()#
			return

		self.InsertItem(num, item[PartsListCtrl.NAME])
		for i in range(1, len(item)):
			self.SetItem(num, i, item[i])

		self.currentItem = num
		self.EnsureVisible(self.currentItem) #This scrolls the list to the added item at the end
		self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

		self.changed = True

	def checkName(self, name):
		for i in range(self.GetItemCount()):
			if name == self.getColumnText(i, PartsListCtrl.NAME):
				return True

		return False

	def OnRemove(self):
		# 실제 선택 행을 우선 사용, 없으면 currentItem 사용
		try:
			row = self.GetFirstSelected()
		except Exception:
			row = getattr(self, 'currentItem', -1)

		if row is None:
			row = -1
		if row == -1:
			return

		# ★ LoF(#1, 항상 0번째 행) 삭제 금지
		if row == 0:
			try:
				self.GetParent()._show_lof_blocked()
			except Exception:
				pass
			return

		dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
		val = dlg.ShowModal()
		if val == wx.ID_YES:
			key  = self.GetItemData(row)
			name = self.getColumnText(row, PartsListCtrl.NAME)

			self.DeleteItem(row)

			# 참조 차수 맵/내부 데이터 갱신(있으면)
			try: self.GetParent().refdeg_by_name.pop(name, None)
			except: pass
			try:
				self.partsdata.pop(key, None)
				self.parts_codes.pop(key, None)
				self.parts_refdeg.pop(key, None)
			except: pass

			# 다음 선택 행 보정
			cnt = self.GetItemCount()
			if cnt <= 0:
				self.currentItem = -1
			else:
				nextrow = min(row, cnt-1)
				self.currentItem = nextrow
				self.EnsureVisible(nextrow)
				self.SetItemState(nextrow, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

			self.changed = True
			self.removed = True
			self._renumber_rows()
		dlg.Destroy()

	def OnRemoveAll(self):
		if self.currentItem != -1:
			dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				self.DeleteAllItems()
			try:
				self.GetParent().refdeg_by_name = {}
			except:
				pass

			self.currentItem = -1
			self.partsdata = {}
			self.parts_codes = {}
			self.parts_refdeg = {}

			self.changed = True
			self.removed = True
			self.parts_active = {}
			dlg.Destroy()

	def load(self, parts):
		if parts is not None:
			idx = 1
			num = len(parts)
			for i in range(num):
				# Diurnal 표시문자
				diurnal = PartsListCtrl.DIURNALTXT if parts[i][2] else u''

				# 코드 3개(A,B,C)
				f1, f2, f3 = parts[i][1]

				# RE/DE 트리플렛
				trip = (0, 0, 0)
				try:
					if len(parts[i]) > 3 and isinstance(parts[i][3], (list, tuple)):
						trip = tuple(parts[i][3])
				except:
					pass
				# 활성 상태(옵션 포맷에 없으므로 기본 True)
				self.parts_active[idx] = True

				# 내부 저장
				self.parts_codes[idx] = (f1, f2, f3)
				self.parts_refdeg[idx] = trip
				try:
					active = bool(parts[i][4]) if len(parts[i]) > 4 else True
				except:
					active = True
				self.parts_active[idx] = active
				# 표시용 포뮬러(실제값 반영: R0/R1.., 18°Ari 등)
				disp = self._format_formula_text(f1, f2, f3, trip)
				self.partsdata[idx] = (parts[i][0], disp, diurnal)

				idx += 1

	def save(self, opts):
		if not self.changed:
			return self.changed, self.removed

		if opts.arabicparts != None:
			del opts.arabicparts

		parts = []
		for row in range(self.GetItemCount()):
			name = self.getColumnText(row, PartsListCtrl.NAME)
			key = self.GetItemData(row)
			# LoF(#1)은 ItemData가 없으므로 parts_codes에 키가 없음 → 저장에서 제외
			if key not in self.parts_codes:
				continue
			f1, f2, f3 = self.parts_codes.get(key, (0,0,0))

			trip = self.parts_refdeg.get(key, (0,0,0))
			diurnal = self.getColumnText(row, PartsListCtrl.DIURNAL)
			diur = (diurnal != '')
			active = self.parts_active.get(key, True)
			# 5-튜플로 저장: (name, (A,B,C), diur, (refA,refB,refC), active)
			parts.append((name, (f1, f2, f3), diur, trip, active))

		opts.arabicparts = copy.deepcopy(parts)
		return self.changed, self.removed


	def getFormula(self, txt, num):
		if num == 1:
			idx = txt.find(u'+')
			f = txt[0:idx]
		elif num == 2:
			idx = txt.find(u'+')
			idx2 = txt.find(u'-')
			f = txt[idx+1:idx2]
		else:
			idx = txt.find(u'-')
			f = txt[idx+1:]

		#remove whitespaces
		f = f.strip()

		return mtexts.conv[f]
			
class RefDegDlg(wx.Dialog):
	def __init__(self, parent, needA, needB, needC, maxref, init_triplet=(0,0,0)):
		wx.Dialog.__init__(self, parent, -1, 'Set RE/DE', style=(wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX))
		self.values = [init_triplet[0], init_triplet[1], init_triplet[2]]
		vsizer = wx.BoxSizer(wx.VERTICAL)
		self.rows = []
		self.signs = [mtexts.txts['Aries'], mtexts.txts['Taurus'], mtexts.txts['Gemini'], mtexts.txts['Cancer'], mtexts.txts['Leo2'], mtexts.txts['Virgo'], mtexts.txts['Libra'], mtexts.txts['Scorpio'], mtexts.txts['Sagittarius'], mtexts.txts['Capricornus'], mtexts.txts['Aquarius'], mtexts.txts['Pisces']]
		for idx,need in enumerate([needA, needB, needC]):
			if not need:
				self.rows.append(None)
				continue
			hs = wx.BoxSizer(wx.HORIZONTAL)
			lbl = wx.StaticText(self, -1, ['A','B','C'][idx]+':')
			hs.Add(lbl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
			if need == 'DE':
				cb = wx.ComboBox(self, -1, self.signs[0], choices=self.signs, style=wx.CB_DROPDOWN|wx.CB_READONLY)
				sp = wx.SpinCtrl(self, -1, '', min=0, max=29)
				try:
					absd = int(self.values[idx]) % 360
					sg = absd // 30
					dg = absd % 30
					cb.SetSelection(sg)
					sp.SetValue(dg)
				except:
					pass
				hs.Add(cb, 0, wx.ALL, 5)
				hs.Add(wx.StaticText(self, -1, u' '), 0, wx.ALL, 2)
				hs.Add(sp, 0, wx.ALL, 5)
				self.rows.append(('DE', cb, sp))
			else:
				# R0(LoF), R1..R{maxref} 라벨 콤보
				choices = [u'#%d' % (k+1) for k in range(maxref)]
				init_idx = 0
				try:
					_n = int(self.values[idx])
					if 0 <= _n < maxref:
						init_idx = _n
				except:
					pass
				cb = wx.ComboBox(self, -1, choices[init_idx], choices=choices, style=wx.CB_DROPDOWN|wx.CB_READONLY)

				hs.Add(wx.StaticText(self, -1, mtexts.txts['RefColon']), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
				hs.Add(cb, 0, wx.ALL, 5)
				self.rows.append(('RE', cb))

			vsizer.Add(hs, 0, wx.ALL, 2)
		btns = self.CreateButtonSizer(wx.OK)
		vsizer.Add(btns, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
		self.SetSizerAndFit(vsizer)

	def getValues(self):
		out=[0,0,0]
		for idx,row in enumerate(self.rows):
			if row is None:
				continue
			if row[0]=='DE':
				cb, sp = row[1], row[2]
				out[idx] = cb.GetSelection()*30 + sp.GetValue()
			else:
				cb = row[1]
				sel = cb.GetSelection()
				out[idx] = sel 
		return tuple(out)

class ArabicPartsDlg(wx.Dialog):

	def _is_lof_selected(self):
		"""리스트에서 LoF(#1)가 선택되어 있으면 True"""
		try:
			row = self.li.GetFirstSelected()
		except Exception:
			return False
		return (row == 0)  # LoF는 항상 0번째 행

	def _show_lof_blocked(self):
		"""LoF 편집 차단 안내(정보 아이콘, 현지화)"""
		title = mtexts.txts.get('Info', u'Information')
		msg   = mtexts.txts.get('LoFLocked', u'Fortuna cannot be modified, deleted, or deactivated here.')
		wx.MessageBox(msg, title, wx.OK | wx.ICON_INFORMATION)



	def _get_lof_formula_text(self, options, parent):
		A  = mtexts.txts.get('AC', u'AC')
		SU = mtexts.txts.get('SU', u'SU')
		MO = mtexts.txts.get('MO', u'MO')
		try:
			typ = options.lotoffortune
		except Exception:
			typ = getattr(chart.Chart, 'LFMOONSUN', 0)
		# 공식 문자열 구성(옵션 + 현재 주/야 반영)
		if typ == chart.Chart.LFMOONSUN:
			# 고정식: AC + MO - SU (항상 주간식 그대로 표시)
			return u'%s + %s - %s' % (A, MO, SU)
		elif typ == getattr(chart.Chart, 'LFDMOONSUN', -1):
			# 주/야 스왑형(달-해)이라도, 옵션 창에서는 '항상 주간식'으로 표시
			# 주간식: AC + MO - SU
			return u'%s + %s - %s' % (A, MO, SU)
		else:
			# 주/야 스왑형(해-달)이라도, 옵션 창에서는 '항상 주간식'으로 표시
			# 주간식: AC + SU - MO
			return u'%s + %s - %s' % (A, SU, MO)

	def _make_lof_header(self, options, parent):

		# 표시용 약어(현지화 반영)
		A  = mtexts.txts.get('AC', u'AC')
		SU = mtexts.txts.get('SU', u'SU')
		MO = mtexts.txts.get('MO', u'MO')
		# LoF 공식 유형
		try:
			typ = options.lotoffortune
		except Exception:
			typ = getattr(chart.Chart, 'LFMOONSUN', 0)
		# 공식 문자열 구성
		if typ == chart.Chart.LFMOONSUN:
			# 고정식: AC + MO - SU (항상 주간식)
			formula = u'%s + %s - %s' % (A, MO, SU)
		elif typ == getattr(chart.Chart, 'LFDMOONSUN', -1):
			# (달-해) 스왑형도 '항상 주간식'으로 표시
			formula = u'%s + %s - %s' % (A, MO, SU)
		else:
			# (해-달) 스왑형도 '항상 주간식'으로 표시
			formula = u'%s + %s - %s' % (A, SU, MO)

		title = mtexts.txts.get('LotOfFortune', u'Fortuna')
		# 순번 규칙: LoF는 #1
		return u'#1  %s: %s' % (title, formula)

	def __init__(self, parent, options):#, inittxt):

		# Instead of calling wx.Dialog.__init__ we precreate the dialog
		# so we can set an extra style that must be set before
		# creation, and then we create the GUI object using the Create
		# method.
#        pre = wx.PreDialog()
#        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
#        pre.Create(parent, -1, mtexts.txts['ArabicParts'], pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

		# This next step is the most important, it turns this Python
		# object into the real wrapper of the dialog (instead of pre)
		# as far as the wxPython extension is concerned.
#        self.PostCreate(pre)
		#wx.Dialog.__init__(self, None, -1, mtexts.txts['ArabicParts'], size=wx.DefaultSize)
		dlgutils.precreate_context_help_dialog(self, parent, mtexts.txts['ArabicParts'])
		#main vertical sizer
		mvsizer = wx.BoxSizer(wx.VERTICAL)
		#main horizontal sizer
		mhsizer = wx.BoxSizer(wx.HORIZONTAL)

		COMBOSIZE = 80
		ROW_PAD   = 2  # 모든 줄(공식/RE/DE)에서 동일 여백
		# 부호 라벨의 폭을 한 번만 측정해 고정(모든 줄에서 동일)
		OPW_OPEN  = self.GetTextExtent(u'+(')[0]
		OPW_MINUS = self.GetTextExtent(u'-')[0]
		OPW_CLOSE = self.GetTextExtent(u')')[0]

		#AscRef
		self.sascref =wx.StaticBox(self, label='')
		refsizer = wx.StaticBoxSizer(self.sascref, wx.VERTICAL)

		row = wx.BoxSizer(wx.HORIZONTAL)

		label = wx.StaticText(self, -1, mtexts.txts['Ascendant']+':')
		row.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		self.refcb = wx.ComboBox(self, -1, mtexts.partsreftxts[0], size=(COMBOSIZE, -1),
								choices=mtexts.partsreftxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.refcb.SetStringSelection(mtexts.partsreftxts[0])
		row.Add(self.refcb, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		# 박스 안에서 위·아래 여유공간을 동일하게 분배 → 정확한 수직 중앙 정렬
		refsizer.AddStretchSpacer(1)
		refsizer.Add(row, 0, wx.ALIGN_LEFT)
		refsizer.AddStretchSpacer(1)

		vsubsizer = wx.BoxSizer(wx.VERTICAL)
		vsubsizer.Add(refsizer, 1, wx.GROW|wx.ALIGN_LEFT|wx.RIGHT, 5)

		#DayNight Orb
		self.sorb =wx.StaticBox(self, label=mtexts.txts['DayNightOrb'])
		orbsizer = wx.StaticBoxSizer(self.sorb, wx.HORIZONTAL)
		# 'Deg:' 라벨 → deg 입력칸 → ',' → 'Min:' 라벨 → min 입력칸
		lbl_deg = wx.StaticText(self, -1, mtexts.txts['Deg'] + u':')
		orbsizer.Add(lbl_deg, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		self.orbdeg = wx.TextCtrl(self, -1, '',
								validator=intvalidator.IntValidator(0, 6),
								size=(40,-1))
		self.orbdeg.SetHelpText(mtexts.txts['HelpDayNightOrbDeg'])
		self.orbdeg.SetMaxLength(1)
		orbsizer.Add(self.orbdeg, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		orbsizer.Add(wx.StaticText(self, -1, u'   '), 0, wx.ALL|wx.ALIGN_LEFT, 5)

		lbl_min = wx.StaticText(self, -1, mtexts.txts['Min'] + u':')
		orbsizer.Add(lbl_min, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		self.orbmin = wx.TextCtrl(self, -1, '',
								validator=intvalidator.IntValidator(0, 59),
								size=(40,-1))
		self.orbmin.SetHelpText(mtexts.txts['HelpMin'])
		self.orbmin.SetMaxLength(2)
		orbsizer.Add(self.orbmin, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		vsubsizer.Add(orbsizer, 1, wx.GROW|wx.ALIGN_LEFT|wx.RIGHT, 5)

		# --- ensure RE/DE tokens exist in mtexts (safe, no override) ---
		def _ensure_re_de_tokens():
			if 'DE' not in mtexts.txts:
				mtexts.txts['DE'] = u'DE'
			if 'RE' not in mtexts.txts:
				mtexts.txts['RE'] = u'RE'
			need = [mtexts.txts['DE'], mtexts.txts['DE']+u'!', mtexts.txts['RE'], mtexts.txts['RE']+u'!']
			pts = list(mtexts.partstxts)
			for t in need:
				if t not in pts:
					pts.append(t)
			mtexts.partstxts = tuple(pts)
			if mtexts.txts['DE'] not in mtexts.conv:
				mtexts.conv[mtexts.txts['DE']] = arabicparts.ArabicParts.DEG
			if (mtexts.txts['DE']+u'!') not in mtexts.conv:
				mtexts.conv[mtexts.txts['DE']+u'!'] = arabicparts.ArabicParts.DEGLORD
			if mtexts.txts['RE'] not in mtexts.conv:
				mtexts.conv[mtexts.txts['RE']] = arabicparts.ArabicParts.RE
			if (mtexts.txts['RE']+u'!') not in mtexts.conv:
				mtexts.conv[mtexts.txts['RE']+u'!'] = arabicparts.ArabicParts.REFLORD

		#이 줄을 실제로 추가
		_ensure_re_de_tokens()

		#Editor
		self.seditor =wx.StaticBox(self, label='')
		editorsizer = wx.StaticBoxSizer(self.seditor, wx.VERTICAL)
		label = wx.StaticText(self, -1, mtexts.txts['Name']+':')
		editorsizer.Add(label, 0, wx.LEFT, 5)
		self.name = wx.TextCtrl(self, -1, '', size=(200,-1))
		self.name.SetMaxLength(20)
		editorsizer.Add(self.name, 0, wx.ALL, 5)
		hsizer = wx.BoxSizer(wx.HORIZONTAL)

		self.acb = wx.ComboBox(self, -1, mtexts.partstxts[0], size=(COMBOSIZE, -1), choices=mtexts.partstxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.acb.SetStringSelection(mtexts.partstxts[0])
		hsizer.Add(self.acb, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		op_open1  = wx.StaticText(self, -1, u'+('); op_open1.SetMinSize((OPW_OPEN,  -1))
		hsizer.Add(op_open1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		self.bcb = wx.ComboBox(self, -1, mtexts.partstxts[0], size=(COMBOSIZE, -1), choices=mtexts.partstxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.bcb.SetStringSelection(mtexts.partstxts[0])
		hsizer.Add(self.bcb, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		op_minus1 = wx.StaticText(self, -1, u'-');  op_minus1.SetMinSize((OPW_MINUS, -1))
		hsizer.Add(op_minus1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		self.ccb = wx.ComboBox(self, -1, mtexts.partstxts[0], size=(COMBOSIZE, -1), choices=mtexts.partstxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.ccb.SetStringSelection(mtexts.partstxts[0])
		hsizer.Add(self.ccb, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		op_close1 = wx.StaticText(self, -1, u')');  op_close1.SetMinSize((OPW_CLOSE, -1))
		hsizer.Add(op_close1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		editorsizer.Add(hsizer, 0, wx.ALIGN_CENTER|wx.ALL, ROW_PAD)


		# --- Inline RE / DE rows (initially locked) ---
		self._signs = [mtexts.txts['Aries'], mtexts.txts['Taurus'], mtexts.txts['Gemini'], mtexts.txts['Cancer'],
					   mtexts.txts['Leo'], mtexts.txts['Virgo'], mtexts.txts['Libra'], mtexts.txts['Scorpio'],
					   mtexts.txts['Sagittarius'], mtexts.txts['Capricornus'], mtexts.txts['Aquarius'], mtexts.txts['Pisces']]

		# RE 제목
		self.sre = wx.StaticBox(self, label=mtexts.txts.get('RE', u'RE'))
		self.re_box = wx.StaticBoxSizer(self.sre, wx.VERTICAL)

		# RE 행: A + ( B - C )
		resizer = wx.BoxSizer(wx.HORIZONTAL)
		self.reA = wx.ComboBox(self, -1, u'#1', size=(COMBOSIZE, -1), choices=[u'#1'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
		resizer.Add(self.reA, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		op_open2  = wx.StaticText(self, -1, u'+('); op_open2.SetMinSize((OPW_OPEN,  -1))
		resizer.Add(op_open2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		self.reB = wx.ComboBox(self, -1, u'#1', size=(COMBOSIZE, -1), choices=[u'#1'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
		resizer.Add(self.reB, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		op_minus2 = wx.StaticText(self, -1, u'-');  op_minus2.SetMinSize((OPW_MINUS, -1))
		resizer.Add(op_minus2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		self.reC = wx.ComboBox(self, -1, u'#1', size=(COMBOSIZE, -1), choices=[u'#1'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
		resizer.Add(self.reC, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		op_close2 = wx.StaticText(self, -1, u')');  op_close2.SetMinSize((OPW_CLOSE, -1))
		resizer.Add(op_close2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		self.re_box.Add(resizer, 0, wx.ALIGN_CENTER|wx.ALL, ROW_PAD)

		editorsizer.Add(self.re_box, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

		# DE 제목
		self.sde = wx.StaticBox(self, label=mtexts.txts.get('Degree', u'Degree'))
		self.de_box = wx.StaticBoxSizer(self.sde, wx.VERTICAL)

		# DE 행: A + ( B - C )  — 각 항은 (별자리 콤보 위 / 돗수 스핀 아래)로 세로 스택
		desizer = wx.BoxSizer(wx.HORIZONTAL)

		colA = wx.BoxSizer(wx.VERTICAL)
		self.deA_sign = wx.ComboBox(self, -1, self._signs[0], choices=self._signs, size=(COMBOSIZE,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.deA_deg  = wx.SpinCtrl(self, -1, '', min=0, max=29, size=(81,-1))
		self.deA_deg.SetHelpText(mtexts.txts.get('HelpDegree', u'Must be between 0 and 29'))
		colA.Add(self.deA_sign, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 2); colA.Add(self.deA_deg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 2)

		colB = wx.BoxSizer(wx.VERTICAL)
		self.deB_sign = wx.ComboBox(self, -1, self._signs[0], choices=self._signs, size=(COMBOSIZE,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.deB_deg  = wx.SpinCtrl(self, -1, '', min=0, max=29, size=(81,-1))
		self.deB_deg.SetHelpText(mtexts.txts.get('HelpDegree', u'Must be between 0 and 29'))
		colB.Add(self.deB_sign, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 2); colB.Add(self.deB_deg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 2)

		colC = wx.BoxSizer(wx.VERTICAL)
		self.deC_sign = wx.ComboBox(self, -1, self._signs[0], choices=self._signs, size=(COMBOSIZE,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.deC_deg  = wx.SpinCtrl(self, -1, '', min=0, max=29, size=(81,-1))
		self.deC_deg.SetHelpText(mtexts.txts.get('HelpDegree', u'Must be between 0 and 29'))
		colC.Add(self.deC_sign, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 2); colC.Add(self.deC_deg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT|wx.BOTTOM, 2)

		desizer.Add(colA, 0, wx.ALL, ROW_PAD)

		op_open3  = wx.StaticText(self, -1, u'+('); op_open3.SetMinSize((OPW_OPEN,  -1))
		desizer.Add(op_open3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		desizer.Add(colB, 0, wx.ALL, ROW_PAD)

		op_minus3 = wx.StaticText(self, -1, u'-');  op_minus3.SetMinSize((OPW_MINUS, -1))
		desizer.Add(op_minus3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)

		desizer.Add(colC, 0, wx.ALL, ROW_PAD)

		op_close3 = wx.StaticText(self, -1, u')');  op_close3.SetMinSize((OPW_CLOSE, -1))
		desizer.Add(op_close3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, ROW_PAD)


		self.de_box.Add(desizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		editorsizer.Add(self.de_box, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)


		# 초기엔 전부 잠금 + 이벤트 바인딩
		for w in (self.reA, self.reB, self.reC,
				  self.deA_sign, self.deA_deg, self.deB_sign, self.deB_deg, self.deC_sign, self.deC_deg):
			w.Enable(False)
		self.reA.Bind(wx.EVT_COMBOBOX, lambda e: self._OnInlineREChanged(0))
		self.reB.Bind(wx.EVT_COMBOBOX, lambda e: self._OnInlineREChanged(1))
		self.reC.Bind(wx.EVT_COMBOBOX, lambda e: self._OnInlineREChanged(2))
		self.deA_sign.Bind(wx.EVT_COMBOBOX, lambda e: self._OnInlineDEChanged(0))
		self.deB_sign.Bind(wx.EVT_COMBOBOX, lambda e: self._OnInlineDEChanged(1))
		self.deC_sign.Bind(wx.EVT_COMBOBOX, lambda e: self._OnInlineDEChanged(2))
		self.deA_deg.Bind(wx.EVT_SPINCTRL, lambda e: self._OnInlineDEChanged(0))
		self.deB_deg.Bind(wx.EVT_SPINCTRL, lambda e: self._OnInlineDEChanged(1))
		self.deC_deg.Bind(wx.EVT_SPINCTRL, lambda e: self._OnInlineDEChanged(2))
		self.deA_deg.Bind(wx.EVT_SPINCTRL, lambda e: self._OnInlineDEChanged(0))
		self.deB_deg.Bind(wx.EVT_SPINCTRL, lambda e: self._OnInlineDEChanged(1))
		self.deC_deg.Bind(wx.EVT_SPINCTRL, lambda e: self._OnInlineDEChanged(2))
		# 텍스트로 직접 입력할 때도 검증(원문자열로 판단) + 포커스 이탈 시 재검증
		self.deA_deg.Bind(wx.EVT_TEXT, lambda e: self._OnDEDegText(self.deA_deg, e))
		self.deB_deg.Bind(wx.EVT_TEXT, lambda e: self._OnDEDegText(self.deB_deg, e))
		self.deC_deg.Bind(wx.EVT_TEXT, lambda e: self._OnDEDegText(self.deC_deg, e))
		self.deA_deg.Bind(wx.EVT_KILL_FOCUS, lambda e: (self._ValidateDEDeg(self.deA_deg), e.Skip()))
		self.deB_deg.Bind(wx.EVT_KILL_FOCUS, lambda e: (self._ValidateDEDeg(self.deB_deg), e.Skip()))
		self.deC_deg.Bind(wx.EVT_KILL_FOCUS, lambda e: (self._ValidateDEDeg(self.deC_deg), e.Skip()))


		self.pending_refdeg = [0, 0, 0]  # A,B,C 임시 RE/DE 값 (DE=절대경도 0..359, RE=정수 0=R0, 1=R1...)
		self.acb.Bind(wx.EVT_COMBOBOX, self._OnTokenChangedA)
		self.bcb.Bind(wx.EVT_COMBOBOX, self._OnTokenChangedB)
		self.ccb.Bind(wx.EVT_COMBOBOX, self._OnTokenChangedC)
		self.diurnalckb = wx.CheckBox(self, -1, mtexts.txts['Diurnal'])
		editorsizer.Add(self.diurnalckb, 0, wx.ALL, 5)
		vsubsizer.Add(editorsizer, 0, wx.ALIGN_LEFT|wx.RIGHT, 5)

		#buttons
		sbtns =wx.StaticBox(self, label='')
		btnssizer = wx.StaticBoxSizer(sbtns, wx.VERTICAL)
		vsizer = wx.BoxSizer(wx.VERTICAL)
		ID_Add = wx.NewId()
		btnAdd = wx.Button(self, ID_Add, mtexts.txts['Add'])
		vsizer.Add(btnAdd, 0, wx.GROW|wx.ALL, 5)
		ID_Modify = wx.NewId()
		btnModify = wx.Button(self, ID_Modify, mtexts.txts["Modify"])
		vsizer.Add(btnModify, 0, wx.GROW|wx.ALL, 5)
		ID_Remove = wx.NewId()
		btnRemove = wx.Button(self, ID_Remove, mtexts.txts['Remove'])
		vsizer.Add(btnRemove, 0, wx.GROW|wx.ALL, 5)
		ID_RemoveAll = wx.NewId()
		btnRemoveAll = wx.Button(self, ID_RemoveAll, mtexts.txts['RemoveAll'])
		vsizer.Add(btnRemoveAll, 0, wx.GROW|wx.ALL, 5)

		btnssizer.Add(vsizer, 0, wx.GROW|wx.ALL, 5)#
		vsubsizer.Add(btnssizer, 0, wx.GROW|wx.ALIGN_LEFT|wx.RIGHT, 5)

		mhsizer.Add(vsubsizer, 0, wx.ALIGN_LEFT|wx.ALL, 0)

		#parts
		sparts =wx.StaticBox(self, label='')
		partssizer = wx.StaticBoxSizer(sparts, wx.VERTICAL)

		# 패널을 하나 두고 그 안에 헤더와 리스트를 배치(StaticBox 경계와 겹침 방지)
		parts_panel = wx.Panel(self)
		pp_vsizer = wx.BoxSizer(wx.VERTICAL)
		parts_panel.SetSizer(pp_vsizer)
		partssizer.Add(parts_panel, 1, wx.EXPAND|wx.ALL, 5)

		# 사용자 정의 랏 리스트(실제 편집/선택용) ─ 같은 리스트에 LoF(#1) 행을 맨 위에 삽입
		ID_Parts = wx.NewId()
		self.li = PartsListCtrl(parts_panel, ID_Parts, options.arabicparts,
								size=(485,-1),
								style=wx.LC_VRULES|wx.LC_REPORT|wx.LC_SINGLE_SEL)
		pp_vsizer.Add(self.li, 1, wx.EXPAND|wx.TOP, 6)

		# 헤더 바로 아래에 LoF #1 행 추가
		lof_row = self.li.InsertItem(0, u'#1')
		self.li.SetItem(lof_row, self.li.ACTIVE, mtexts.txts['On'])
		self.li.SetItem(lof_row, self.li.NAME, mtexts.txts.get('LotOfFortune', u'Fortuna'))
		self.li.SetItem(lof_row, self.li.FORMULA, self._get_lof_formula_text(options, self.GetParent() or parent))
		# LoF의 Diurnal 표시는 옵션(lotoffortune)에 따라 결정
		try:
			_typ = options.lotoffortune
		except Exception:
			_typ = getattr(chart.Chart, 'LFMOONSUN', 0)

		diur_mark = PartsListCtrl.DIURNALTXT if _typ in (chart.Chart.LFDSUNMOON, chart.Chart.LFDMOONSUN) else u''
		self.li.SetItem(lof_row, self.li.DIURNAL, diur_mark)

		# LoF 행은 저장 대상이 아니므로 ItemData(키)를 지정하지 않음
		self.li._renumber_rows()
		self._rebuild_re_choices()
		self.li.Bind(wx.EVT_LIST_ITEM_SELECTED, self._OnRowSelected)
		# LoF(#1) 삽입으로 시각적 선택이 #2로 밀리는 문제를 내부 상태와 동기화
		try:
			if self.li.GetItemCount() > 1:
				self.li.currentItem = 1
				self.li.SetItemState(1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
				self.li.EnsureVisible(1)
			else:
				self.li.currentItem = 0
		except Exception:
			pass

		self.refdeg_by_name = {}
		if options.arabicparts:
			for it in options.arabicparts:
				try:
					name = it[0]
					trip = it[3]
					if isinstance(trip, (list, tuple)) and len(trip)==3:
						self.refdeg_by_name[name] = tuple(trip)
				except:
					pass
		# partssizer.Add(self.li, ...) 불필요

		# 현재 선택된 랏 활성/비활성 토글 박스
		self.activeckb = wx.CheckBox(self, -1, mtexts.txts.get('Active', 'Active'))
		self.activeckb.SetValue(True)
		partssizer.Add(self.activeckb, 0, wx.ALL, 5)
		self.activeckb.Bind(wx.EVT_CHECKBOX, self.OnToggleActive)
		# --- 초기 진입 선택/토글 정합성 보정 ---
		try:
			cnt = self.li.GetItemCount()
			if cnt > 1:
				self.li.currentItem = 1
				self.li.SetItemState(1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
				self.li.Focus(1)
			else:
				self.li.currentItem = 0
				self.li.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
				self.li.Focus(0)
			# 선택된 행 기준으로 이름/Diurnal/Active/RE·DE 인라인 모두 동기화
			self._OnRowSelected(None)
		except Exception:
			pass

		mhsizer.Add(partssizer, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALL, 0)
		mvsizer.Add(mhsizer, 0, wx.ALIGN_LEFT|wx.ALL, 5)

		self.Bind(wx.EVT_BUTTON, self.OnAdd, id=ID_Add)
		self.Bind(wx.EVT_BUTTON, self.OnModify, id=ID_Modify)
		self.Bind(wx.EVT_BUTTON, self.OnRemove, id=ID_Remove)
		self.Bind(wx.EVT_BUTTON, self.OnRemoveAll, id=ID_RemoveAll)

		btnsizer = wx.StdDialogButtonSizer()

		if wx.Platform != '__WXMSW__':
			btn = wx.ContextHelpButton(self)
			btnsizer.AddButton(btn)

		btnOk = wx.Button(self, wx.ID_OK, mtexts.txts['Ok'])
		btnOk.SetHelpText(mtexts.txts['HelpOk'])
		btnOk.SetDefault()
		btnsizer.AddButton(btnOk)

		btn = wx.Button(self, wx.ID_CANCEL, mtexts.txts['Cancel'])
		btn.SetHelpText(mtexts.txts['HelpCancel'])
		btnsizer.AddButton(btn)

		btnsizer.Realize()

		mvsizer.Add(btnsizer, 0, wx.GROW|wx.ALL, 10)
		self.SetSizer(mvsizer)
		self.Layout()
		mvsizer.Fit(self)
		cur_h = self.GetSize().height
		self.SetMinSize((875, cur_h))    # 최소폭도 같이 잡아두면 Fit이 줄이지 못함
		self.SetSize((875, cur_h))
		self.Layout()
		self._update_inline_visibility()
		btnOk.SetFocus()

	def OnToggleActive(self, event):
		row = getattr(self.li, 'currentItem', -1)
		if row < 0:
			return
		# 삭제 직후 유효 범위 가드
		if row >= self.li.GetItemCount():
			return
		# LoF(#1)은 토글 불가: 되돌리고 안내
		if row == 0:
			self.activeckb.SetValue(True)
			self._show_lof_blocked()
			return
		key = self.li.GetItemData(row)
		val = bool(self.activeckb.GetValue())
		self.li.parts_active[key] = val

		self.li._refresh_active_for_row(row)
		self.li.changed = True

	def _OnTokenChangedA(self, event):
		self._handle_token_click(0)

	def _OnTokenChangedB(self, event):
		self._handle_token_click(1)

	def _OnTokenChangedC(self, event):
		self._handle_token_click(2)

	def _rebuild_re_choices(self):
		# 현재 리스트 아이템 수 기준으로 #1..#N 구성, 단 "자기 자신(#현재 선택된 행)"은 제외
		try:
			maxref = self.li.GetItemCount()
		except Exception:
			maxref = 1

		# 현재 선택된 행(LoF=#1은 제외 대상 아님)
		try:
			self_idx = getattr(self.li, 'currentItem', -1)
		except Exception:
			self_idx = -1
		if self_idx is None or self_idx <= 0:
			self_idx = None  # 자기 자신 제외 없음 (LoF 선택/미선택/신규 추가 시)

		# 전체 Rn 후보(0..maxref-1)에서 자기 자신만 제외
		rn_all = list(range(maxref))
		if self_idx is not None and self_idx in rn_all:
			rn_all.remove(self_idx)

		# 표시에 쓸 라벨과 내부 매핑 구성
		labels = [u'#%d' % (rn + 1) for rn in rn_all]

		for cb in (self.reA, self.reB, self.reC):
			# 이전에 선택돼 있던 "실제 Rn" 복원 시도
			prev_rn = None
			try:
				# 기존 매핑이 있으면 그걸로 역추적
				if hasattr(cb, '_rn_map') and isinstance(cb._rn_map, list):
					prev_sel = cb.GetSelection()
					if 0 <= prev_sel < len(cb._rn_map):
						prev_rn = int(cb._rn_map[prev_sel])
				else:
					# 구버전: 선택 인덱스 == 실제 Rn
					prev_rn = int(cb.GetSelection())
			except Exception:
				prev_rn = None

			# 새 아이템/매핑 반영
			cb.SetItems(labels)
			cb._rn_map = list(rn_all)  # 표시 인덱스 -> 실제 Rn

			# 이전 Rn이 여전히 유효하면 그 위치로, 아니면 0번
			sel_index = 0
			if prev_rn is not None:
				try:
					sel_index = cb._rn_map.index(prev_rn)
				except ValueError:
					sel_index = 0
			# 가드
			if not cb._rn_map:
				# 리스트가 비어버리는 경우는 사실상 없음(LoF만 있어도 R0은 남음)
				cb._rn_map = [0]
				cb.SetItems([u'#1'])
				sel_index = 0

			try:
				cb.SetSelection(sel_index)
			except Exception:
				pass

	def _update_inline_refdeg_enabled(self):
		sels  = [self.acb.GetCurrentSelection(), self.bcb.GetCurrentSelection(), self.ccb.GetCurrentSelection()]
		toks  = [mtexts.partstxts[s] for s in sels]
		bases = [t[:-1] if t.endswith(u'!') else t for t in toks]
		re_cbs = (self.reA, self.reB, self.reC)
		de_sgs = (self.deA_sign, self.deB_sign, self.deC_sign)
		de_dgs = (self.deA_deg,  self.deB_deg,  self.deC_deg)
		for idx, base in enumerate(bases):
			isRE = (base == mtexts.txts.get('RE', u'RE'))
			isDE = (base == mtexts.txts.get('DE', u'DE'))
			try: re_cbs[idx].Enable(isRE)
			except: pass
			try: de_sgs[idx].Enable(isDE); de_dgs[idx].Enable(isDE)
			except: pass
	def _show_sizer(self, sizer, show):
		# StaticBoxSizer 전체를 토글 표시
		try:
			sizer.ShowItems(show)
		except Exception:
			# 구버전 대비: 아이템 순회로 처리
			try:
				for i in range(sizer.GetItemCount()):
					itm = sizer.GetItem(i)
					win = itm.GetWindow()
					if win:
						win.Show(show)
			except:
				pass

	def _update_inline_visibility(self):
		# 박스는 항상 보이게 유지. 필요 여부는 Enable/Disable로만 제어.
		try:
			self._show_sizer(self.re_box, True)
		except:
			pass
		try:
			self._show_sizer(self.de_box, True)
		except:
			pass
		self.Layout()

	def _index_for_code(self, code_val):
		# mtexts.conv 역탐색: parts_codes의 정수 코드 → partstxts 인덱스
		for idx, label in enumerate(mtexts.partstxts):
			try:
				if mtexts.conv[label] == code_val:
					return idx
			except:
				pass
		return 0

	def _sync_inline_from_pending(self):
		sels  = [self.acb.GetCurrentSelection(), self.bcb.GetCurrentSelection(), self.ccb.GetCurrentSelection()]
		toks  = [mtexts.partstxts[s] for s in sels]
		bases = [t[:-1] if t.endswith(u'!') else t for t in toks]
		# RE: 콤보 인덱스 == Rn
		for idx in (0,1,2):
			if bases[idx] == mtexts.txts.get('RE', u'RE'):
				# 실제 Rn 값을 현재 콤보의 표시 인덱스로 역매핑
				try:
					rn = int(self.pending_refdeg[idx])
				except Exception:
					rn = 0
				cb = (self.reA, self.reB, self.reC)[idx]
				try:
					if hasattr(cb, '_rn_map') and rn in cb._rn_map:
						cb.SetSelection(cb._rn_map.index(rn))
					else:
						# 매핑이 없거나 rn이 제외되었으면 0번으로 대체
						cb.SetSelection(0)
				except Exception:
					pass

			if bases[idx] == mtexts.txts.get('DE', u'DE'):
				try:
					absd = int(self.pending_refdeg[idx]) % 360
				except:
					absd = 0
				sg = absd // 30; dg = absd % 30
				try:
					(self.deA_sign, self.deB_sign, self.deC_sign)[idx].SetSelection(sg)
					(self.deA_deg,  self.deB_deg,  self.deC_deg)[idx].SetValue(dg)
				except:
					pass
	def _compute_triplet_for_add(self):
		"""
		새 랏 추가 시 사용할 (refA, refB, refC) 계산:
		1) 현재 선택된 행의 저장값(parts_refdeg/refdeg_by_name)으로 기본값 구성
		2) 현재 A/B/C 토큰이 RE/DE이면, 인라인 컨트롤 값으로 그 위치만 덮어쓰기
		"""
		# 1) 선택된 행의 저장값을 기본으로
		base = list(getattr(self, 'pending_refdeg', [0, 0, 0]))
		try:
			selrow = getattr(self.li, 'currentItem', -1)
		except:
			selrow = -1
		if selrow is not None and selrow >= 0 and selrow != 0:
			try:
				key = self.li.GetItemData(selrow)
				trip = self.li.parts_refdeg.get(key)
				if not trip:
					# 이름 기반 백업
					nm = self.li.getColumnText(selrow, self.li.NAME)
					trip = self.refdeg_by_name.get(nm)
				if isinstance(trip, (tuple, list)) and len(trip) == 3:
					base = [int(trip[0]), int(trip[1]), int(trip[2])]
			except:
				pass

		# 2) 현재 토큰이 RE/DE인 위치만 인라인 값으로 덮어쓰기
		sels  = [self.acb.GetCurrentSelection(), self.bcb.GetCurrentSelection(), self.ccb.GetCurrentSelection()]
		toks  = [mtexts.partstxts[s] for s in sels]
		bases = [t[:-1] if t.endswith(u'!') else t for t in toks]

		for idx, tk in enumerate(bases):
			if tk == mtexts.txts.get('RE', u'RE'):
				try:
					cb = (self.reA, self.reB, self.reC)[idx]
					base[idx] = int(cb.GetSelection())
				except:
					base[idx] = 0
			elif tk == mtexts.txts.get('DE', u'DE'):
				try:
					sg = (self.deA_sign, self.deB_sign, self.deC_sign)[idx].GetSelection()
					dg = (self.deA_deg,  self.deB_deg,  self.deC_deg)[idx].GetValue()
					sg = max(0, int(sg))
					dg = max(0, min(29, int(dg)))
					base[idx] = int((sg * 30) + dg) % 360
				except:
					base[idx] = 0

		return tuple(base)

	def _OnInlineREChanged(self, idx):
		cb = (self.reA, self.reB, self.reC)[idx]
		try:
			sel_index = cb.GetSelection()
		except Exception:
			sel_index = 0
		# 표시 인덱스를 실제 Rn으로 변환(자기 자신 제외 매핑 반영)
		try:
			if hasattr(cb, '_rn_map') and 0 <= sel_index < len(cb._rn_map):
				rn = int(cb._rn_map[sel_index])
			else:
				rn = int(sel_index)
		except Exception:
			rn = 0
		self.pending_refdeg[idx] = rn

	def _OnInlineDEChanged(self, idx):
		sg = (self.deA_sign, self.deB_sign, self.deC_sign)[idx].GetSelection()
		dg = (self.deA_deg,  self.deB_deg,  self.deC_deg)[idx].GetValue()
		if dg > 29:
			self._ShowRangeErrorAndClamp((self.deA_deg, self.deB_deg, self.deC_deg)[idx])
			dg = 29
		try:
			self.pending_refdeg[idx] = int((max(0, sg) * 30) + max(0, min(29, dg)))
		except:
			self.pending_refdeg[idx] = 0

	def _handle_token_click(self, which):
		# which: 0(A)/1(B)/2(C)
		sels = [
			self.acb.GetCurrentSelection(),
			self.bcb.GetCurrentSelection(),
			self.ccb.GetCurrentSelection()
		]
		tok = mtexts.partstxts[sels[which]]
		base = tok[:-1] if tok.endswith(u'!') else tok

		need = None
		if base == mtexts.txts.get('DE', u'DE'):
			need = 'DE'
		elif base == mtexts.txts.get('RE', u'RE'):
			need = 'RE'

		if not need:
			self.pending_refdeg[which] = 0
			self._update_inline_refdeg_enabled()
			self._update_inline_visibility()
			return

		self._rebuild_re_choices()
		self._update_inline_refdeg_enabled()
		self._sync_inline_from_pending()
		self._update_inline_visibility()
		return

		# 초기값: 현재 선택된 랏이 있으면 그 랏의 저장값, 없으면 임시버퍼
		init_triplet = tuple(self.pending_refdeg)
		selrow = getattr(self.li, 'currentItem', -1)
		if selrow is not None and selrow >= 0:
			selname = self.li.getColumnText(selrow, self.li.NAME)
			init_triplet = self.refdeg_by_name.get(selname, init_triplet)

		maxref = self.li.GetItemCount()  # R0..Rmaxref
		dlg = RefDegDlg(self, needs[0], needs[1], needs[2], maxref, init_triplet)
		if dlg.ShowModal() == wx.ID_OK:
			vals = dlg.getValues()
			v = int(vals[which])

			# 여기서는 "저장"하지 않는다! (다른 랏이 바뀌는 버그 방지)
			# 자기 자신 참조 방지는 Modify 시점에 처리
			self.pending_refdeg[which] = v
		dlg.Destroy()

	def _deg_to_text(self, absdeg):
		try:
			absdeg = int(absdeg) % 360
		except:
			return u'?'
		# mtexts에서 현지화 문자열을 가져오되, 키가 없으면 원래 약어로 폴백
		sign_keys = (u'Ari',u'Tau',u'Gem',u'Can',u'Leo',u'Vir',u'Lib',u'Sco',u'Sag',u'Cap',u'Aqu',u'Pis')
		signs = [mtexts.txts.get(k, k) for k in sign_keys]
		sg = absdeg // 30
		dg = absdeg % 30
		return u'%d\u00B0%s' % (dg, signs[sg])

	def _render_token_text(self, code, idxABC, triplet):
		"""
		code: mtexts.partstxts 인덱스 (A/B/C용 선택값)
		idxABC: 0(A)/1(B)/2(C)
		triplet: (refA,refB,refC) ─ RE는 정수 Rn, DE는 절대경도(0..359)
		"""
		txt = mtexts.partstxts[code]
		want_lord = False
		if txt.endswith(u'!'):
			want_lord = True
			txt = txt[:-1]

		if txt == mtexts.txts['DE']:
			t = self._deg_to_text(triplet[idxABC])
			return t + (u'!' if want_lord else u'')
		if txt == mtexts.txts['RE']:
			rn = int(triplet[idxABC])
			if rn < 0: rn = 0
			label = u'#%d' % (rn+1)
			return label + (u'!' if want_lord else u'')

		# 그 외(ASC, SU, LOF 등)는 원래 문자열 그대로
		return mtexts.partstxts[code]

	def _format_formula_text(self, a_sel, b_sel, c_sel, triplet):
		a_txt = self._render_token_text(a_sel, 0, triplet)
		b_txt = self._render_token_text(b_sel, 1, triplet)
		c_txt = self._render_token_text(c_sel, 2, triplet)
		# 603 스타일 "A + B - C"
		return u'%s + %s - %s' % (a_txt, b_txt, c_txt)

	def _refreshRowDisplay(self, row, name, a_sel, b_sel, c_sel, triplet):
		# 리스트 컨트롤의 "Formula" 칼럼 텍스트를 실제값으로 교체
		formula_text = self._format_formula_text(a_sel, b_sel, c_sel, triplet)
		try:
			self.li.SetItem(row, self.li.NAME, name)
			self.li.SetItem(row, self.li.FORMULA, formula_text)
		except:
			# 칼럼 인덱스 이름이 다르면 네 파일의 상수에 맞춰 조정
			pass

	def OnAdd(self, event):
		name = self.name.GetValue().strip()
		if not name:
			dlgm = wx.MessageDialog(self, mtexts.txts.get('ArabicPartNameEmpty', u'Name is empty'), '',
									wx.OK | wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return
		if self.li.checkName(name):
			dlgm = wx.MessageDialog(self, mtexts.txts.get('ArabicPartAlreadyExists', u'Already exists'), '',
									wx.OK | wx.ICON_INFORMATION)
			dlgm.ShowModal()
			dlgm.Destroy()
			return

		diurnal = ''
		if self.diurnalckb.GetValue():
			diurnal = PartsListCtrl.DIURNALTXT

		# 선택된 행의 저장값을 기본으로 하고, RE/DE인 위치만 인라인 값으로 덮어써서 사용
		trip = self._compute_triplet_for_add()

		# compute codes (기존 그대로)
		f1 = mtexts.conv[mtexts.partstxts[self.acb.GetCurrentSelection()]]
		f2 = mtexts.conv[mtexts.partstxts[self.bcb.GetCurrentSelection()]]
		f3 = mtexts.conv[mtexts.partstxts[self.ccb.GetCurrentSelection()]]

		disp = self.li._format_formula_text(f1, f2, f3, trip)
		self.refdeg_by_name[name] = trip
		self.li.AddFullItem(name, disp, diurnal, (f1, f2, f3), trip)
		self._rebuild_re_choices()

		# 추가 후엔 임시버퍼 초기화
		self.pending_refdeg = [0,0,0]

		# 행 표시 갱신
		row = self.li.GetItemCount() - 1
		self._refreshRowDisplay(row, name, self.acb.GetCurrentSelection(), self.bcb.GetCurrentSelection(),
								self.ccb.GetCurrentSelection(), trip)
		self.pending_refdeg = [0,0,0]

	def OnModify(self, event):
		if self._is_lof_selected():
			self._show_lof_blocked()
			return

		# 선택된 행
		i = self.li.GetFirstSelected() if hasattr(self.li, 'GetFirstSelected') else getattr(self.li, 'currentItem', -1)
		if i is None or i < 0:
			return
		if i == 0:
			self._show_lof_blocked()
			return

		# 기존/신규 이름
		old_name = self.li.getColumnText(i, self.li.NAME)
		new_name = self.name.GetValue().strip() or old_name
		if new_name != old_name and self.li.checkName(new_name):
			dlgm = wx.MessageDialog(self, mtexts.txts.get('ArabicPartAlreadyExists', u'Already exists'), '',
									wx.OK | wx.ICON_INFORMATION)
			dlgm.ShowModal(); dlgm.Destroy()
			return

		# Diurnal 체크 상태 → 표시 문자
		diur_text = PartsListCtrl.DIURNALTXT if self.diurnalckb.GetValue() else u''

		# A/B/C 토큰 선택
		a_sel = self.acb.GetCurrentSelection()
		b_sel = self.bcb.GetCurrentSelection()
		c_sel = self.ccb.GetCurrentSelection()

		# RE/DE 값: 저장된 값 우선, 없으면 임시버퍼
		vals_saved = self.refdeg_by_name.get(old_name, tuple(getattr(self, 'pending_refdeg', [0,0,0])))
		# 현재 A/B/C 토큰이 RE/DE인 위치는 '인라인에서 막 바꾼 값(pending)'으로 덮어쓴다
		vals_list = list(vals_saved)
		for idx, sel in enumerate((a_sel, b_sel, c_sel)):
			tok = mtexts.partstxts[sel]
			base = tok[:-1] if tok.endswith(u'!') else tok
			if base == mtexts.txts.get('RE', u'RE') or base == mtexts.txts.get('DE', u'DE'):
				try:
					vals_list[idx] = int(self.pending_refdeg[idx])
				except:
					vals_list[idx] = 0
		vals = tuple(vals_list)
		# 자기 자신을 RE로 가리키면 루프 방지(R0로 강등)
		self_index_zero_based = i  # RE 값은 '#1 -> 0'의 0-based 인덱스
		vals = list(vals)
		maxref = max(0, self.li.GetItemCount() - 1)  # 유효 범위 가드

		for idx, sel in enumerate((a_sel, b_sel, c_sel)):
			tok = mtexts.partstxts[sel]
			base = tok[:-1] if tok.endswith(u'!') else tok
			if base == mtexts.txts.get('RE', u'RE'):
				# 범위 클램프 + 자기참조 방지
				try:
					v = int(vals[idx])
				except:
					v = 0
				if v < 0 or v > maxref:
					v = 0
				if v == self_index_zero_based:
					v = 0
				vals[idx] = v
			elif base == mtexts.txts.get('DE', u'DE'):
				# DE는 0..359로만 클램프
				try:
					v = int(vals[idx]) % 360
				except:
					v = 0
				vals[idx] = v

		vals = tuple(vals)

		# 내부 코드 갱신(실제 계산용)
		key = self.li.GetItemData(i)
		self.li.parts_codes[key] = (
			mtexts.conv[mtexts.partstxts[a_sel]],
			mtexts.conv[mtexts.partstxts[b_sel]],
			mtexts.conv[mtexts.partstxts[c_sel]],
		)
		self.li.parts_refdeg[key] = vals

		# 표시용 수식 갱신(리스트 칼럼 텍스트)
		disp_formula = self._format_formula_text(a_sel, b_sel, c_sel, vals)

		# 리스트 셀 텍스트 갱신: 이름/공식/Diurnal
		self.li.SetItem(i, self.li.NAME, new_name)
		self.li.SetItem(i, self.li.FORMULA, disp_formula)
		self.li.SetItem(i, self.li.DIURNAL, diur_text)

		# partsdata 튜플도 함께 갱신(저장 시 직렬화에 쓰임)
		self.li.partsdata[key] = (new_name, disp_formula, diur_text)

		# 이름 바뀐 경우 RE/DE 참조 저장 테이블 rename
		if new_name != old_name:
			try:
				self.refdeg_by_name.pop(old_name, None)
			except:
				pass
			self.refdeg_by_name[new_name] = vals
		else:
			# 이름 동일해도 최신 RE/DE 저장
			self.refdeg_by_name[new_name] = vals

		# 변경 플래그
		self.li.changed = True
		# 임시버퍼는 초기화(헷갈림 방지)
		self.pending_refdeg = [0, 0, 0]

	def OnRemove(self):
		# 아이템 없으면 그냥 리턴
		if self.GetItemCount() == 0:
			return
		# 선택이 풀려 있으면 첫 행 선택으로 가드
		if self.currentItem == -1:
			self.currentItem = 0
			self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

		# ★ LoF(#1) 행은 삭제 금지
		if self.currentItem == 0:
			self.GetParent()._show_lof_blocked()
			return

		dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)

		val = dlg.ShowModal()
		if val == wx.ID_YES:
			key = self.GetItemData(self.currentItem)
			name = self.getColumnText(self.currentItem, PartsListCtrl.NAME)
			self.DeleteItem(self.currentItem)
			try:
				self.GetParent().refdeg_by_name.pop(name, None)
			except:
				pass
			try:
				self.partsdata.pop(key, None)
				self.parts_codes.pop(key, None)
				self.parts_refdeg.pop(key, None)
			except:
				pass
			if self.GetItemCount() == 0:
				self.currentItem = -1
			elif self.currentItem >= self.GetItemCount():
				self.currentItem = self.GetItemCount() - 1
				self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
			else:
				self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
			self.changed = True
			self.removed = True
		dlg.Destroy()

	def _OnRowSelected(self, event):
		# 초기 생성 시점에 리스트 선택 이벤트가 먼저 발생할 수 있다.
		# 아직 active 체크박스가 만들어지지 않았다면 조용히 건너뛴다.
		if not hasattr(self, 'activeckb'):
			try:
				event.Skip()
			except Exception:
				pass
			return

		# 안전한 선택 인덱스 취득
		i = getattr(self.li, 'currentItem', -1)
		try:
			i = event.GetIndex()
		except Exception:
			pass
		if i is None or i < 0:
			return

		# 리스트의 현재 행을 동기화
		self.li.currentItem = i

		# 이름/주야(diurnal) UI 싱크
		try:
			self.name.SetValue(self.li.getColumnText(i, self.li.NAME))
		except Exception:
			pass
		try:
			self.diurnalckb.SetValue(bool(self.li.getColumnText(i, self.li.DIURNAL)))
		except Exception:
			pass

		# Active 체크박스 동기화
		on_label = mtexts.txts.get('On', u'On')
		cur_txt  = self.li.getColumnText(i, self.li.ACTIVE)
		if i == 0:
			# LoF(#1): Active 비활성, 항상 On
			self.activeckb.SetValue(True)
			self.activeckb.Enable(False)
		else:
			self.activeckb.Enable(True)
			try:
				key = self.li.GetItemData(i)
				cur_active = bool(self.li.parts_active.get(key, True))
			except Exception:
				cur_active = (cur_txt == on_label)
			self.activeckb.SetValue(cur_active)
			self.diurnalckb.Enable(True)

		# 선택된 파츠의 (A,B,C) 코드 → 콤보 반영
		try:
			key = self.li.GetItemData(i)
			codes = self.li.parts_codes.get(key)
			if isinstance(codes, tuple) and len(codes) == 3:
				self.acb.SetSelection(self._index_for_code(codes[0]))
				self.bcb.SetSelection(self._index_for_code(codes[1]))
				self.ccb.SetSelection(self._index_for_code(codes[2]))
		except Exception:
			pass

		# LoF(#1) 선택 시: 옵션 타입을 '주간식'으로 강제 반영 + Diurnal 켜진 채 비활성(2·3번)
		if i == 0:
			try:
				_typ = options.lotoffortune
			except Exception:
				_typ = getattr(chart.Chart, 'LFMOONSUN', 0)
			lbl_AC = mtexts.txts.get('AC', u'Asc')
			lbl_SU = mtexts.txts.get('SU', u'Sun')
			lbl_MO = mtexts.txts.get('MO', u'Moon')
			ACcode = mtexts.conv.get(lbl_AC)
			SUcode = mtexts.conv.get(lbl_SU)
			MOcode = mtexts.conv.get(lbl_MO)
			if ACcode is not None:
				self.acb.SetSelection(self._index_for_code(ACcode))
			if _typ == getattr(chart.Chart, 'LFDSUNMOON', -9999):
				if SUcode is not None: self.bcb.SetSelection(self._index_for_code(SUcode))   # B=SUN
				if MOcode is not None: self.ccb.SetSelection(self._index_for_code(MOcode))   # C=MOON
			else:
				if MOcode is not None: self.bcb.SetSelection(self._index_for_code(MOcode))   # B=MOON
				if SUcode is not None: self.ccb.SetSelection(self._index_for_code(SUcode))   # C=SUN

			self.diurnalckb.SetValue(_typ in (getattr(chart.Chart, 'LFDSUNMOON', -9999),
											  getattr(chart.Chart, 'LFDMOONSUN', -9999)))
			self.diurnalckb.Enable(False)

		# 인라인 RE/DE 컨트롤도 선택 행 값으로 동기화
		try:
			name = self.li.getColumnText(i, self.li.NAME)
			vals = self.refdeg_by_name.get(name, tuple(self.pending_refdeg))
			self.pending_refdeg = [int(vals[0]), int(vals[1]), int(vals[2])]
		except Exception:
			pass
		self._rebuild_re_choices()
		self._update_inline_refdeg_enabled()
		self._sync_inline_from_pending()
		self._update_inline_visibility()

		try:
			event.Skip()
		except Exception:
			pass

		event.Skip()

	def OnRemoveAll(self):

		# ★ LoF가 항상 포함되므로 여기서 전체 삭제는 불가
		self._show_lof_blocked()
		return

		if self.currentItem != -1:
			dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)

		val = dlg.ShowModal()
		if val == wx.ID_YES:
			self.DeleteAllItems()
			try:
				self.GetParent().refdeg_by_name = {}
			except:
				pass
			self.currentItem = -1
			self.partsdata = {}
			self.parts_codes = {}
			self.parts_refdeg = {}
			self.changed = True
			self.removed = True
		dlg.Destroy()

	def OnRemove(self, event):
		if self._is_lof_selected():
			self._show_lof_blocked()
			return
		self.li.OnRemove()

	def OnRemoveAll(self, event):
		# LoF(#1)은 남기고 #2부터 모두 삭제
		count = self.li.GetItemCount()
		if count <= 1:
			wx.MessageBox(mtexts.txts.get('RemovedExceptLoF', u'No parts to remove.'),
						  mtexts.txts.get('Info', u'Information'), wx.OK | wx.ICON_INFORMATION)
			return

		# ★ 삭제 전 확인(질문 아이콘)
		dlg = wx.MessageDialog(self,
							   mtexts.txts.get('AreYouSure', u'Are you sure?'),
							   mtexts.txts.get('Confirm', u'Confirm'),
							   wx.YES_NO | wx.ICON_QUESTION)
		ans = dlg.ShowModal()
		dlg.Destroy()
		if ans != wx.ID_YES:
			return

		for row in range(count-1, 0, -1):
			key  = self.li.GetItemData(row)
			name = self.li.getColumnText(row, self.li.NAME)
			self.li.DeleteItem(row)
			try: self.refdeg_by_name.pop(name, None)
			except: pass
			try:
				self.li.partsdata.pop(key, None)
				self.li.parts_codes.pop(key, None)
				self.li.parts_refdeg.pop(key, None)
				self.li.parts_active.pop(key, None)
			except: pass
		self.li._renumber_rows()
		self.li.changed = True
		self.li.removed = True
		# 삭제 후 포커스/선택을 Fortuna(#1)로 강제하고 UI 상태 동기화
		try:
			if self.li.GetItemCount() >= 1:
				self.li.currentItem = 0
				self.li.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
				self.li.EnsureVisible(0)
				self._OnRowSelected(None)  # LoF는 Active 항상 ON + 체크박스 비활성로 반영
		except Exception:
			pass
		wx.MessageBox(mtexts.txts.get('RemovedExceptLoF', u'All parts except Fortuna were removed.'),
					  mtexts.txts.get('Info', u'Information'), wx.OK | wx.ICON_INFORMATION)


	def fill(self, opts):
		self.refcb.SetStringSelection(mtexts.partsreftxts[opts.arabicpartsref])
		self.orbdeg.SetValue(str(opts.daynightorbdeg))
		self.orbmin.SetValue(str(opts.daynightorbmin))


	def check(self, opts):
		changed = False
		removed = False

		if self.refcb.GetCurrentSelection() != opts.arabicpartsref:
			opts.arabicpartsref = self.refcb.GetCurrentSelection()
			changed = True

		if int(self.orbdeg.GetValue()) != opts.daynightorbdeg:
			opts.daynightorbdeg = int(self.orbdeg.GetValue())
			changed = True

		if int(self.orbmin.GetValue()) != opts.daynightorbmin:
			opts.daynightorbmin = int(self.orbmin.GetValue())
			changed = True

		ch, rem = self.li.save(opts)
		if ch:
			changed = True
			if rem:
				removed = True

		return changed, removed

	def _ValidateDEDeg(self, spin):
		"""DE 돗수 검증(0..29). 초과 시 RangeError 메시지."""
		try:
			v = int(spin.GetValue())
		except Exception:
			return
		if v > 29 or v < 0:
			self._ShowRangeErrorAndClamp(spin)

	def _OnDEDegText(self, spin, evt):
		"""텍스트 입력 즉시 원문자열로 검증(SpinCtrl의 자동 클램프 전에 잡기)"""
		s = evt.GetString()
		try:
			v = int(s) if s.strip() != u'' else 0
		except Exception:
			evt.Skip(); return
		if v > 29 or v < 0:
			self._ShowRangeErrorAndClamp(spin)
		evt.Skip()


	def _ShowRangeErrorAndClamp(self, spin):
		wx.MessageBox(mtexts.txts.get('RangeError', u'Range error'),
					mtexts.txts.get('Error', u'Information'),
					wx.OK | wx.ICON_EXCLAMATION)
		try:
			# 범위 밖이면 가장 가까운 값으로
			v = int(spin.GetValue())
		except Exception:
			v = 0
		if v > 29: v = 29
		if v < 0:  v = 0
		spin.SetValue(v)




