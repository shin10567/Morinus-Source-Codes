import wx
import fixstarsparallelswnd

class FixStarsParallelsFrame(wx.Frame):
    def __init__(self, parent, title, chrt, options):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, wx.Size(510, 610))
        wnd = fixstarsparallelswnd.FixStarsParallelsWnd(self, chrt, options, parent)
        self.SetMinSize((200, 200))
