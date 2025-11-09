# -*- coding: utf-8 -*-
import wx
import chart
import positionswnd
import positionswnd2
import transitwnd
import squarechartwnd
import primdirs
import placidiansapd
import placidianutppd
import regiomontanpd
import campanianpd
import primdirsrevlistframe
import wx.lib.newevent
import _thread
import mtexts
import common

(PDReadyEvent, EVT_PDREADY) = wx.lib.newevent.NewEvent()
pdlock = _thread.allocate_lock()


class TransitFrame(wx.Frame):
	CHART = 0
	COMPOUND = 1
	POSITIONS = 2
	SQUARE = 3

	def __init__(self, parent, title, chrt, radix, options, sel=0):
		wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, wx.Size(640, 400))

		self.chart = chrt
		self.radix = radix
		self.options = options
		self.parent = parent
		self.title = title

		self.pmenu = wx.Menu()
		self.ID_Selection = wx.NewId()
		self.ID_PrimaryDirections = wx.NewId()
		self.ID_SaveAsBitmap = wx.NewId()
		self.ID_BlackAndWhite = wx.NewId()

		self.ID_Chart = wx.NewId()
		self.ID_Comparison = wx.NewId()
		self.ID_Positions = wx.NewId()
		self.ID_Square = wx.NewId()

		self.ID_PDDirect = wx.NewId()
		self.ID_PDConverse = wx.NewId()
		self.ID_PDBoth = wx.NewId()
		self.ID_PDToRadix = wx.NewId()

		self.selmenu = wx.Menu()
		self.chartmenu = self.selmenu.Append(self.ID_Chart, mtexts.txts['Chart'], '', wx.ITEM_RADIO)
		self.compoundmenu = self.selmenu.Append(self.ID_Comparison, mtexts.txts['Comparison'], '', wx.ITEM_RADIO)
		self.positionsmenu = self.selmenu.Append(self.ID_Positions, mtexts.txts['Positions'], '', wx.ITEM_RADIO)
		self.squaremenu = self.selmenu.Append(self.ID_Square, mtexts.txts['Square'], '', wx.ITEM_RADIO)

		self.pmenu.Append(self.ID_Selection, mtexts.txts['Windows'], self.selmenu)

		if self.chart.htype == chart.Chart.SOLAR or self.chart.htype == chart.Chart.LUNAR:
			self.pdselmenu = wx.Menu()
			self.pddirectmenu = self.pdselmenu.Append(self.ID_PDDirect, mtexts.txts['Direct'], '')
			self.pdconversemenu = self.pdselmenu.Append(self.ID_PDConverse, mtexts.txts['Converse'], '')
			self.pdbothmenu = self.pdselmenu.Append(self.ID_PDBoth, mtexts.txts['Both'], '')
			#self.pdtoradix = self.pdselmenu.Append(self.ID_PDToRadix, mtexts.txts['PDToRadix'], '', wx.ITEM_CHECK)
			#self.pdtoradix.Enable(False)
			self.pmenu.Append(self.ID_PrimaryDirections, mtexts.txts['PrimaryDirs'], self.pdselmenu)

		self.pmenu.Append(self.ID_SaveAsBitmap, mtexts.txts['SaveAsBmp'], mtexts.txts['SaveChart'])
		self.mbw = self.pmenu.Append(self.ID_BlackAndWhite, mtexts.txts['BlackAndWhite'], mtexts.txts['ChartBW'], wx.ITEM_CHECK)
		
		self.SetMinSize((200,200))
		self.SetPosition((130, 130));
		self.Bind(wx.EVT_RIGHT_UP, self.onPopupMenu)

		self.Bind(wx.EVT_MENU, self.onChart, id=self.ID_Chart)
		self.Bind(wx.EVT_MENU, self.onComparison, id=self.ID_Comparison)
		self.Bind(wx.EVT_MENU, self.onPositions, id=self.ID_Positions)
		self.Bind(wx.EVT_MENU, self.onSquare, id=self.ID_Square)
		if self.chart.htype == chart.Chart.SOLAR or self.chart.htype == chart.Chart.LUNAR:
			self.Bind(wx.EVT_MENU, self.onPDDirect, id=self.ID_PDDirect)
			self.Bind(wx.EVT_MENU, self.onPDConverse, id=self.ID_PDConverse)
			self.Bind(wx.EVT_MENU, self.onPDBoth, id=self.ID_PDBoth)
			self.Bind(wx.EVT_MENU, self.onPDToRadix, id=self.ID_PDToRadix)
		self.Bind(wx.EVT_MENU, self.onSaveAsBitmap, id=self.ID_SaveAsBitmap)
		self.Bind(wx.EVT_MENU, self.onBlackAndWhite, id=self.ID_BlackAndWhite)

		if self.options.bw:
			self.mbw.Check()

		self.selection = sel
		if sel == TransitFrame.CHART:
			self.w = transitwnd.TransitWnd(self, self.chart, radix, options, parent)
			self.chartmenu.Check()
		else:
			self.w = transitwnd.TransitWnd(self, self.chart, self.radix, self.options, self.parent, True)
			self.compoundmenu.Check()

		self.Bind(EVT_PDREADY, self.OnPDReady)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		# === status bar: split 2 fields (left datetime, right lon/lat) ===
		self.statusbar = getattr(self, 'statusbar', None) or self.CreateStatusBar(2)
		self.statusbar.SetFieldsCount(2)
		# 반반 폭(비율 지정): 음수면 비율, [-1, -1] = 1:1
		self.statusbar.SetStatusWidths([-1, -1])
		# 상태바 폰트를 메인과 동일하게 맞춤
		app = wx.GetApp()
		top = app.GetTopWindow() if app else None
		main_sb = top.GetStatusBar() if top else None
		if main_sb:
			self.statusbar.SetFont(main_sb.GetFont())
			self.SendSizeEvent()

		self._update_status_time_place()

	def onPopupMenu(self, event):
		self.PopupMenu(self.pmenu, event.GetPosition())


	def onChart(self, event):
		if self.selection != TransitFrame.CHART:
			self.selection = TransitFrame.CHART
			self.w.Destroy()
			self.w = transitwnd.TransitWnd(self, self.chart, self.radix, self.options, self.parent, False, -1, self.GetClientSize())
			self._update_status_time_place()

	def onComparison(self, event):
		if self.selection != TransitFrame.COMPOUND:
			self.selection = TransitFrame.COMPOUND
			self.w.Destroy()
			self.w = transitwnd.TransitWnd(self, self.chart, self.radix, self.options, self.parent, True, -1, self.GetClientSize())
			self._update_status_time_place()

	def onPositions(self, event):
		if self.selection != TransitFrame.POSITIONS:
			self.selection = TransitFrame.POSITIONS
			self.w.Destroy()
			if wx.Platform == '__WXMSW__':
				self.w = positionswnd2.PositionsWnd2(self, self.chart, self.options, self.parent, -1, self.GetClientSize())
				self.w.Refresh()
			else:
				self.w = positionswnd.PositionsWnd(self, self.chart, self.options, self.parent, -1, self.GetClientSize())
				self._update_status_time_place()

	def onSquare(self, event):
		if self.selection != TransitFrame.SQUARE:
			self.selection = TransitFrame.SQUARE
			self.w.Destroy()
			self.w = squarechartwnd.SquareChartWnd(self, self.chart, self.options, self.parent, -1, self.GetClientSize())
			self._update_status_time_place()

	def _fmt_lonlat(self, p):
		deg = u"\N{DEGREE SIGN}"
		lon_txt = f"{p.deglon}{deg}{str(p.minlon).zfill(2)}' " + ('E' if p.east else 'W')
		lat_txt = f"{p.deglat}{deg}{str(p.minlat).zfill(2)}' " + ('N' if p.north else 'S')
		return lon_txt, lat_txt

	def _update_status_time_place(self):
		try:
			t = self.chart.time
			p = self.chart.place
		except Exception:
			return

		# === 왼쪽: yyyy.month.dd HH:MM:SS + ZN/UT/LC (메인 차트와 동일 양식) ===
		# BC 표시
		signtxt = '-' if getattr(t, 'bc', False) else ''
		# 타임존 라벨(ZN/UT/LC)
		ztxt = mtexts.txts['UT']
		if t.zt == chart.Time.ZONE:
			ztxt = mtexts.txts['ZN']
		elif t.zt == chart.Time.LOCALMEAN or t.zt == chart.Time.LOCALAPPARENT:
			ztxt = mtexts.txts['LC']
		# 월 이름(로케일 반영): common.common.months
		try:
			month_name = common.common.months[t.origmonth-1]
		except Exception:
			# fallback
			month_name = str(t.origmonth).zfill(2)

		left_txt = (
			f"{signtxt}{t.origyear}."
			f"{month_name}."
			f"{str(t.origday).zfill(2)}, "
			f"{str(t.hour).zfill(2)}:{str(t.minute).zfill(2)}:{str(t.second).zfill(2)}"
			f"{ztxt}"
		)

		# === 오른쪽: Long./Lat. (메인 상태바의 포맷 그대로) ===
		deg_symbol = u'°'  
		dir_lon = mtexts.txts['E'] if p.east else mtexts.txts['W']
		dir_lat = mtexts.txts['N'] if p.north else mtexts.txts['S']

		right_txt = (
			f"{mtexts.txts['Long']}: "
			f"{str(p.deglon).zfill(2)}{deg_symbol}{str(p.minlon).zfill(2)}'"
			f"{dir_lon},"
			f" {mtexts.txts['Lat']}: "
			f"{str(p.deglat).zfill(2)}{deg_symbol}{str(p.minlat).zfill(2)}'"
			f"{dir_lat}"
		)

		try:
			(getattr(self, 'statusbar', None) or self.CreateStatusBar(2)).SetStatusText(left_txt, 0)
			self.statusbar.SetStatusText(right_txt, 1)
		except Exception:
			pass

	def onPDDirect(self, event):
		self.onPD(primdirs.PrimDirs.DIRECT)


	def onPDConverse(self, event):
		self.onPD(primdirs.PrimDirs.CONVERSE)

	def onPDBoth(self, event):
		self.onPD(primdirs.PrimDirs.BOTHDC)

	def onPDToRadix(self, event):
		#Because on Windows the EVT_MENU_CLOSE event is not sent in case of accelerator-keys
		if wx.Platform == '__WXMSW__' and not self.splash:
			self.handleStatusBar(True)

#		self.autosave.Check(self.options.autosave)
#		self.options.autosave = self.pdtoradix.IsChecked()


	def onSaveAsBitmap(self, event):
		self.w.onSaveAsBitmap(event)


	def onBlackAndWhite(self, event):
		self.w.onBlackAndWhite(event)


	def onPD(self, direction):
		pdrange = primdirs.PrimDirs.RANGEREV

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
			self.pds = placidiansapd.PlacidianSAPD(self.chart, self.options, pdrange, direction, self.abort)
		elif self.options.primarydir == primdirs.PrimDirs.PLACIDIANUNDERTHEPOLE:
			self.pds = placidianutppd.PlacidianUTPPD(self.chart, self.options, pdrange, direction, self.abort)
		elif self.options.primarydir == primdirs.PrimDirs.REGIOMONTAN:
			self.pds = regiomontanpd.RegiomontanPD(self.chart, self.options, pdrange, direction, self.abort)
		else:
			self.pds = campanianpd.CampanianPD(self.chart, self.options, pdrange, direction, self.abort)

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
				pdw = primdirsrevlistframe.PrimDirsRevListFrame(self, self.parent, self.chart, self.options, self.pds, self.title.replace(mtexts.typeList[self.chart.htype], mtexts.txts['PrimaryDirs']))

				pdw.Show(True)
			else:
				dlgm = wx.MessageDialog(self, mtexts.txts['NoPDsWithSettings'], mtexts.txts['Information'], wx.OK|wx.ICON_INFORMATION)
				dlgm.ShowModal()
				dlgm.Destroy()#

		if self.pds != None:
			del self.pds

		del self.abort
	def OnClose(self, evt):
		try:
			if hasattr(self, "abort") and self.abort:
				self.abort.aborting()
		except Exception:
			pass
		try:
			if hasattr(self, "timer") and self.timer:
				self.timer.Stop()
				del self.timer
		except Exception:
			pass
		try:
			if hasattr(self, "progbar") and self.progbar:
				self.progbar.Destroy()
				del self.progbar
		except Exception:
			pass
		try:
			self.Destroy()
		finally:
			evt.Skip()