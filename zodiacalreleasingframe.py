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
        # L3/L4 다이얼로그 추적용
        self._open_drill_dialogs = []
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self.panel.set_start_sign(start_sign)
        self.panel.compute_and_draw()

        self.SetMinSize((200, 200))
        self.CentreOnScreen()
        self.Show()   # ← 여기서 처음 창을 보여줌
        # --- Drill dialog tracking & safe close ---
    def _register_drill(self, dlg):
        # 다이얼로그가 자체적으로 닫힐 때(사용자가 X 클릭) 목록에서 제거
        try:
            dlg.Bind(wx.EVT_WINDOW_DESTROY, lambda e: self._unregister_drill(dlg))
        except Exception:
            pass
        self._open_drill_dialogs.append(dlg)

    def _unregister_drill(self, dlg):
        try:
            if dlg in self._open_drill_dialogs:
                self._open_drill_dialogs.remove(dlg)
        except Exception:
            pass

    def _on_close(self, evt):
        # 부모(L1/L2) 창을 닫을 때, 열려있는 L3/L4 팝업을 모두 종료
        for d in list(self._open_drill_dialogs):
            try:
                # 모달이면 모달 루프부터 종료
                if hasattr(d, "IsModal") and d.IsModal():
                    try:
                        d.EndModal(wx.ID_CANCEL)
                    except Exception:
                        pass
                # 파괴 시도
                try:
                    d.Destroy()
                except Exception:
                    pass
            except Exception:
                pass
        self._open_drill_dialogs[:] = []
        evt.Skip()  # 프레임 기본 종료 계속 진행
