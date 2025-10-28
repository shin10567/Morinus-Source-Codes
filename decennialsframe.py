# -*- coding: utf-8 -*-
import wx
from decennialswnd import DecWnd

class DecennialsFrame(wx.Frame):
    XSIZE = 380
    YSIZE = 480
    def __init__(self, parent, title, chrt, opts):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, wx.Size(DecennialsFrame.XSIZE, DecennialsFrame.YSIZE))
        self.w = DecWnd(self, chrt, opts, parent)
        self.SetMinSize((200,200))
