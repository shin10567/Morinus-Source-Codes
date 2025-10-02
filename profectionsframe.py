# -*- coding: utf-8 -*-
import transitframe
import common
import mtexts
import util
import wx

class ProfectionsFrame(transitframe.TransitFrame):
	def __init__(self, parent, title, chrt, radix, options):
		transitframe.TransitFrame.__init__(self, parent, title, chrt, radix, options)
		self.Bind(wx.EVT_SHOW, self._on_show_bump_width)
		W = 700   
		H = max(self.GetSize().height, 620)  
		self.SetMinSize((W, H))
		self.SetSize((W, H))
		if hasattr(self, "w"):
			self.w.SetMinSize((W - 40, -1))  
		self.Layout()
		self.SendSizeEvent()
		
	def _on_show_bump_width(self, evt):
		if evt.IsShown():
			wx.CallAfter(self._bump_width, 940)  # ← 원하는 최소 가로폭(px) 숫자만 조절
			self.Unbind(wx.EVT_SHOW)
		evt.Skip()

	def _bump_width(self, min_w):
		# Fit()/restore 이후 최종적으로 넓히기
		self.SetSizeHints(minW=min_w, minH=-1)
		cw, ch = self.GetClientSize().Get()
		if cw < min_w:
			self.SetClientSize((min_w, ch))

		if hasattr(self, "w"):
			self.w.SetMinSize((min_w - 32, -1))

		sizer = self.GetSizer()
		if sizer:
			sizer.Layout()
		self.Layout()
		self.SendSizeEvent()

	def change(self, chrt, title, y, m, d, t):
		self.chart = chrt
		self.w.chart = chrt
		self.w.drawBkg()
		self.w.Refresh()

		#Update Caption
		h, mi, s = util.decToDeg(t)
		title = title.replace(mtexts.txts['Radix'], mtexts.txts['Profections']+' ('+str(y)+'.'+common.common.months[m-1]+'.'+str(d)+' '+str(h)+':'+str(mi).zfill(2)+':'+str(s).zfill(2)+')')
		self.SetTitle(title)






