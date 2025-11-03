# -*- coding: utf-8 -*-
import wx
import phasiswnd  # ← 새 Wnd 사용
import mtexts
class PhasisFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options):
        # 시작 크기: 가로를 좁게, 세로는 고정 최소 이상
        wx.Frame.__init__(self, parent, -1, mtexts.txts["HeliacalRisingsSettings"],
                          wx.DefaultPosition, wx.Size(450, 340))

        # CommonWnd "Save as bitmap" 이 참조하는 경로 필드 (없으면 AttributeError)
        self.fpathimgs = u""

        self.horoscope = horoscope
        self.options   = options

        # 결과 패널 (리스트 컨트롤 제거, CommonWnd+PIL 기반)
        self.panel = phasiswnd.PhasisWnd(self, horoscope, options, mainfr=self)

        # 레이아웃
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(s)

        # 최소 크기: fixed stars와 동일 정책(200x200)
        self.SetMinSize((200, 200))

        self.CentreOnScreen()
        self.Show()
        self.Raise()  #; // 置于最前面
