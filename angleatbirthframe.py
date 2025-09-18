# angleatbirthframe.py
# -*- coding: utf-8 -*-
import wx
import angleatbirthdlg
import angleatbirthwnd

class AngleAtBirthFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options):
        # 시작 크기: 가로 좁게
        wx.Frame.__init__(self, parent, -1, title,
                          wx.DefaultPosition, wx.Size(480, 200))

        # 공통 저장 메뉴에서 참조하는 경로 필드(없으면 AttributeError)
        self.fpathimgs = u""

        self.horoscope = horoscope
        self.options   = options

        # 1) 파라미터 다이얼로그(± Minute)
        dlg = angleatbirthdlg.AngleAtBirthParamsDlg(self, default_minutes=10)
        dlg.CentreOnScreen()
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            self.Destroy()
            return
        minutes = dlg.get_minutes()
        dlg.Destroy()

        # 2) 결과 패널 생성  ← 반드시 sizer보다 먼저!
        self.panel = angleatbirthwnd.AngleAtBirthWnd(
            self, horoscope, options, mainfr=self, minutes=minutes
        )

        # 3) 레이아웃
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(s)

        # 4) 최소 크기: fixed stars와 동일
        self.SetMinSize((200, 200))     # (= SetSizeHints(200,200)과 동일효과)

        self.CentreOnScreen()
        self.Show()
