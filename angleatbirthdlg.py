# -*- coding: utf-8 -*-
import wx
import mtexts
class AngleAtBirthParamsDlg(wx.Dialog):
    def __init__(self, parent, default_minutes=10):
        wx.Dialog.__init__(self, parent, title=mtexts.txts["AngleatBirth"])
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        v = wx.BoxSizer(wx.VERTICAL)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, u"± "+mtexts.txts["Minutes"]+":"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 6)
        self.spin = wx.SpinCtrl(self, -1, "", wx.DefaultPosition, wx.Size(50, -1),
                                        style=0, initial=default_minutes)
        row.Add(self.spin, 0)
        self.spin.SetHelpText(mtexts.txts.get('HelpDay', u'Must be between 1 and 31'))
        # add
        self._last_valid = int(self.spin.GetValue())
        self.spin.Bind(wx.EVT_KILL_FOCUS, self._on_spin_kill_focus)
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
        self.spin.Bind(wx.EVT_TEXT, self._on_spin_text)
        self._error_shown = False
        self._squelch_reset = False  # SetValue로 되돌리는 동안엔 에러 플래그를 리셋하지 않음

        v.Add(row, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        btns = wx.StdDialogButtonSizer()
        btn_ok = wx.Button(self, wx.ID_OK, mtexts.txts["Calculate"])
        btn_ok.SetHelpText(mtexts.txts.get('HelpOk', u'Accept changes'))
        btn_cancel = wx.Button(self, wx.ID_CANCEL, mtexts.txts["Cancel"])
        btn_cancel.SetHelpText(mtexts.txts.get('HelpCancel', u'Discard changes'))
        btns.AddButton(btn_ok)
        btns.AddButton(btn_cancel)
        btns.Realize()
        v.Add(btns, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizerAndFit(v)
        self.CentreOnScreen() 

    def get_minutes(self):
        return int(self.spin.GetValue())
    def _validate_spin(self, show_msg=True):
        # 현재 값 파싱
        try:
            v = int(self.spin.GetValue())
        except Exception:
            v = None

        # 범위 검사
        if v is None or v < 1 or v > 31:
            if show_msg and not getattr(self, '_error_shown', False):
                wx.MessageBox(mtexts.txts['RangeError'], mtexts.txts['Error'],
                            wx.OK | wx.ICON_WARNING)  # 노란 삼각형 아이콘
            # 프로그램적 복구 동안 발생하는 EVT_TEXT에서 _error_shown이 리셋되지 않도록 보호
            self._squelch_reset = True
            self.spin.SetValue(self._last_valid)
            try:
                self.spin.SetSelection(0, len(str(self._last_valid)))
            except Exception:
                pass
            self._squelch_reset = False
            self.spin.SetFocus()
            return False

        # 유효하면 최신값 저장, 단 '프로그램적 복구 중'에는 에러 플래그를 해제하지 않음
        self._last_valid = v
        if not getattr(self, '_squelch_reset', False):
            self._error_shown = False
        return True

    def _on_spin_kill_focus(self, evt):
        # 포커스 이동으로 인한 중복 표시 방지: 여기서는 메시지를 띄우지 않음
        self._validate_spin(show_msg=False)
        evt.Skip()


    def _on_spin_text(self, evt):
        # 이미 한 번 경고를 띄운 상태면 텍스트 이벤트에서는 재표시 금지
        self._validate_spin(show_msg=(not self._error_shown))
        evt.Skip()

    def _on_ok(self, evt):
        # OK 버튼: 이미 알림이 떴다면 재표시는 안 함
        if self._validate_spin(show_msg=not self._error_shown):
            evt.Skip()
        else:
            return


