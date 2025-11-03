# -*- coding: utf-8 -*-
import wx
from decennialswnd import DecWnd, DecStartDlg

class DecennialsFrame(wx.Frame):
    XSIZE = 380
    YSIZE = 480
    def __init__(self, parent, title, chrt, opts):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition,
                          wx.Size(DecennialsFrame.XSIZE, DecennialsFrame.YSIZE))
        self.fpathimgs = u""
        self._parent = parent
        self._chrt   = chrt
        self._opts   = opts
        # 선택 팝업을 이벤트 큐에서 띄우고(커서 꼬임 방지), 선택 후에 화면 생성
        self.Hide()
        wx.CallAfter(self._ask_and_build)

    def _ask_and_build(self):
        # 프레임 자신을 부모로 모달을 띄워 포커스 문제 방지
        dlg = DecStartDlg(self)
        dlg.CentreOnScreen()
        rc = dlg.ShowModal()
        if rc != wx.ID_OK:
            dlg.Destroy()
            self.Destroy()
            return
        token = dlg.get_token()
        dlg.Destroy()

        # 이제 패널 생성 + 계산
        self.w = DecWnd(self, self._chrt, self._opts, self._parent)
        self.w.set_start_selector(token)
        self.w.compute_and_draw()

        self.SetMinSize((200, 200))
        self.Show(True)
        self.Raise()

