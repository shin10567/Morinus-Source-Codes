# -*- coding: utf-8 -*-
import wx
import mtexts
import eclipseswnd  # 방금 만든 Wnd

class EclipsesFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options):
        wx.Frame.__init__(self, parent, -1,
                          u"%s" % (mtexts.menutxts.get('Eclipses', u'Eclipses')),
                          wx.DefaultPosition, wx.Size(720, 380))
        self.fpathimgs = u""
        self.horoscope = horoscope
        self.options   = options

        panel = eclipseswnd.EclipsesWnd(self, horoscope, options, mainfr=self)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(panel, 1, wx.EXPAND)
        self.SetSizer(s)

        self.SetMinSize((200, 200))
        self.CentreOnScreen()
        self.Show()
        self.Raise()
