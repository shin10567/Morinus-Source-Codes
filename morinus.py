# -*- coding: utf-8 -*-
#!/usr/bin/env python


#Morinus, Astrology program
#Copyright (C) 2008-  Robert Nagy, robert.pluto@gmail.com

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
if getattr(sys, 'frozen', False):
	os.chdir(os.path.dirname(sys.executable))
else:
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
import os
import sys
import wx
import options
import mtexts
import morin
import wx

# 모든 플랫폼에서 MessageDialog -> GenericMessageDialog로 강제
_orig_MessageDialog = wx.MessageDialog
def _GenericMessageDialogFactory(parent, message, caption=wx.MessageBoxCaptionStr,
								 style=wx.OK | wx.CENTRE, pos=wx.DefaultPosition):
	return wx.GenericMessageDialog(parent, message, caption, style, pos)

wx.MessageDialog = _GenericMessageDialogFactory


class Morinus(wx.App):
	def OnInit(self):
		try:
			progPath = os.path.dirname(sys.argv[0])
			os.chdir(progPath)
		except:
			pass

		#wx.SetDefaultPyEncoding('utf-8')
		opts = options.Options()
		mtexts.setLang(opts.langid)
		# ==== 1) 표준 메시지/확인창 버튼을 강제 현지화 ====
		import wx

		def _build_gmd(parent, msg, title, style):
			dlg = wx.GenericMessageDialog(parent, msg, title, style)
			try:
				if (style & wx.YES) and (style & wx.NO) and (style & wx.CANCEL):
					dlg.SetYesNoCancelLabels(mtexts.txts.get('Yes','Yes'),
											mtexts.txts.get('No','No'),
											mtexts.txts.get('Cancel','Cancel'))
				elif (style & wx.YES) and (style & wx.NO):
					dlg.SetYesNoLabels(mtexts.txts.get('Yes','Yes'),
									mtexts.txts.get('No','No'))
				elif (style & wx.OK):
					dlg.SetOKLabel(mtexts.txts.get('OK','OK'))
			except Exception:
				pass
			return dlg

		# wx.MessageDialog / MessageBox 대체
		def _MessageDialog(parent, message, caption, style):
			return _build_gmd(parent,
							mtexts.txts.get(message, message),
							mtexts.txts.get(caption, caption),
							style)

		def _MessageBox(message, caption='Message',
						style=wx.OK|wx.CENTRE, parent=None, x=wx.DefaultCoord, y=wx.DefaultCoord):
			dlg = _build_gmd(parent,
							mtexts.txts.get(message, message),
							mtexts.txts.get(caption, caption),
							style)
			try:
				return dlg.ShowModal()
			finally:
				dlg.Destroy()

		wx.MessageDialog = _MessageDialog
		wx.MessageBox    = _MessageBox

		# ==== 2) 모든 다이얼로그가 뜨기 직전에 OK/Cancel/Yes/No 라벨을 일괄 치환 ====
		_ID2KEY = {
			wx.ID_OK:'OK', wx.ID_CANCEL:'Cancel',
			wx.ID_YES:'Yes', wx.ID_NO:'No',
			wx.ID_APPLY:'Apply', wx.ID_CLOSE:'Close'
		}

		def _localize_stock_buttons(root):
			# 다이얼로그 트리에 있는 모든 버튼 라벨을 앱 언어로 통일
			stack = [root]
			while stack:
				w = stack.pop()
				try:
					for c in w.GetChildren():
						stack.append(c)
				except Exception:
					pass
				if isinstance(w, wx.Button):
					key = _ID2KEY.get(w.GetId())
					if key:
						desired = mtexts.txts.get(key, w.GetLabel())
						if w.GetLabel() != desired:
							try:
								w.SetLabel(desired)
							except Exception:
								pass
			try:
				root.Layout()
			except Exception:
				pass

		# 모든 다이얼로그에 자동 적용 (Show/ShowModal 훅)
		_orig_show_modal = wx.Dialog.ShowModal
		def _patched_show_modal(self, *a, **k):
			_localize_stock_buttons(self)
			return _orig_show_modal(self, *a, **k)
		wx.Dialog.ShowModal = _patched_show_modal

		_orig_show = wx.Dialog.Show
		def _patched_show(self, *a, **k):
			_localize_stock_buttons(self)
			return _orig_show(self, *a, **k)
		wx.Dialog.Show = _patched_show

		import dlgutils

		# wx.MessageDialog / MessageBox를 강제 현지화 버전으로 바꿔치기
		import wx
		def _MsgDialog(parent, message, caption, style):
			# message/caption 둘 다 mtexts 키 또는 생 텍스트를 허용
			msg   = mtexts.txts.get(message, message)
			title = mtexts.txts.get(caption, caption)
			return dlgutils._build_gmd(parent, msg, title, style)

		def _MessageBox(message, caption='Message', style=wx.OK|wx.CENTRE, parent=None, x=wx.DefaultCoord, y=wx.DefaultCoord):
			dlg = _MsgDialog(parent, message, caption, style)
			try:
				return dlg.ShowModal()
			finally:
				dlg.Destroy()

		wx.MessageDialog = _MsgDialog          # 클래스 대체
		wx.MessageBox    = _MessageBox         # 함수 대체

		frame = morin.MFrame(None, -1, mtexts.txts['Morinus'], opts)
		frame.Show(True)

		return True

 
app = Morinus(0)
app.MainLoop()



