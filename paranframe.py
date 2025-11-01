# -*- coding: utf-8 -*-
from __future__ import division
import wx
import paranwnd

class ParanFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options):
        wx.Frame.__init__(self, parent, -1, "Paranatellonta" + title,
                          size=(530, 360))
        self.panel = paranwnd.ParanatellontaWnd(self, horoscope, options, mainfr=self)
        self.Centre()
