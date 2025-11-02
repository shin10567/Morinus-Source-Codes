# -*- coding: utf-8 -*-
import wx
import chart
import almutentopicalswnd
import mtexts
import util


class AlmutenTopicalsFrame(wx.Frame):

	def __init__(self, parent, chrt, title):
		wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, size=wx.Size(640, 400))

		self.parent = parent
		self.chart = chrt

		#Navigating toolbar
		self.tb = self.CreateToolBar(wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_FLAT)

		self.namescb = wx.ComboBox(self.tb, -1, self.chart.almutens.topicals.names[0], size=(230, -1), choices=self.chart.almutens.topicals.names, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.namescb.SetSelection(0)
		# 좌측 여백용 스페이서
		self.tb.AddControl(wx.StaticText(self.tb, -1, '  '))

		self.tb.AddControl(self.namescb)
		self.namescb.Bind(wx.EVT_COMBOBOX, self.onChange)

		self.tb.Realize()
		# --- fix: normalize toolbar height once and lock it (MSW/wx 4.1 quirk) ---
		def _normalize_tb_once():
			# 1) 콤보박스 실제 높이에 맞춰 ToolBar 행 높이를 강제
			cbh = self.namescb.GetBestSize().height
			# 아이콘이 없더라도 SetToolBitmapSize가 '행 높이' 역할을 함
			self.tb.SetToolBitmapSize((cbh, cbh))
			self.tb.Realize()
			best = self.tb.GetBestSize()
			# 2) 높이만 고정하고 가로폭은 자유롭게 둔다 → 리사이즈해도 표/그리드가 안 깨짐
			h = best[1]
			self.tb.SetMinSize(wx.Size(-1, h))
			try:
				# (minW=-1, minH=h, maxW=-1, maxH=h) → 높이만 고정
				self.tb.SetSizeHints(-1, h, -1, h)
			except Exception:
				pass

			# 3) 프레임이 실제로 보여진 '직후' 레이아웃을 한 번 더 강제
			self.SendSizeEvent()

		# 프레임 표시 직후 실행해야 초기 행 높이 잘못 계산 이슈를 건너뜀
		wx.CallAfter(_normalize_tb_once)
		# --- end fix ---

		self.SendSizeEvent()
		self.Layout()
		self.Update() 
		self.SetMinSize((200,200))

		# 기존: self.w = almutentopicalswnd.AlmutenTopicalsWnd(self, chrt, 0, parent, -1, self.GetClientSize())

		self.w = almutentopicalswnd.AlmutenTopicalsWnd(
			self, chrt, 0, parent, -1, wx.DefaultSize
		)

		mainsz = wx.BoxSizer(wx.VERTICAL)
		mainsz.Add(self.w, 1, wx.EXPAND)
		self.SetSizer(mainsz)
		self.Layout()

		#self.w = almutentopicalswnd.AlmutenTopicalsWnd(self, chrt, 0, parent, -1, self.GetClientSize()) #parent is mainframe, -1 is id

	def onChange(self, event):
		idx = self.namescb.GetCurrentSelection()
		sz = self.GetSizer()
		sz.Detach(self.w)
		self.w.Destroy()

		self.w = almutentopicalswnd.AlmutenTopicalsWnd(
			self, self.chart, idx, self.parent, -1, wx.DefaultSize
		)
		sz.Add(self.w, 1, wx.EXPAND)
		self.Layout()

		


