# -*- coding: utf-8 -*-
import wx
# (필요 시) mtexts를 쓰면 프레임 타이틀/사인 이름을 현지화 가능
try:
    import mtexts
except:
    mtexts = None

from zodiacalreleasingwnd import ZRWnd, ZRStartDlg

class ZRFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options):
        # 프레임은 일단 '비가시' 상태로 생성 (Show는 나중에)
        t = title
        if mtexts:
            try:
                t = title.replace(mtexts.typeList[horoscope.htype], mtexts.txts["ZodiacalReleasing"])
            except:
                t = u"Zodiacal Releasing"
        wx.Frame.__init__(self, parent, -1, t, wx.DefaultPosition, wx.Size(380, 480))

        self.fpathimgs = u""          # 저장 기능에서 참조
        self.horoscope = horoscope
        self.options   = options

        # 1) 먼저 Start sign 팝업을 띄운다 (프레임은 아직 Show 안 함)
        if mtexts and 'zodiac' in mtexts.txts:
            sign_names = [mtexts.txts['zodiac'][i] for i in range(12)]
        else:
            sign_names = [mtexts.txts["Aries"], mtexts.txts["Taurus"], mtexts.txts["Gemini"], mtexts.txts["Cancer"], mtexts.txts["Leo"], mtexts.txts["Virgo"],
                          mtexts.txts["Libra"], mtexts.txts["Scorpio"], mtexts.txts["Sagittarius"], mtexts.txts["Capricornus"], mtexts.txts["Aquarius"], mtexts.txts["Pisces"]]

        dlg = ZRStartDlg(self, sign_names)
        dlg.CentreOnScreen()
        rc = dlg.ShowModal()
        if rc != wx.ID_OK:
            dlg.Destroy()
            # 취소 또는 X → 아무것도 띄우지 말고 프레임 제거
            self.Destroy()
            return

        start_sign = dlg.get_sign_index()
        dlg.Destroy()

        # 2) OK일 때만 패널 생성 + compute + Show
        self.panel = ZRWnd(self, horoscope, options, mainfr=self)
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(s)

        self.panel.set_start_sign(start_sign)
        self.panel.compute_and_draw()

        self.SetMinSize((200, 200))
        self.CentreOnScreen()
        self.Show()   # ← 여기서 처음 창을 보여줌