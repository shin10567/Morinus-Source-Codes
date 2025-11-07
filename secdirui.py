
# -*- coding: utf-8 -*-
import wx
import mtexts

class SecDirDialog(wx.Dialog):
    """
    Secondary Progressions dialog.
    - Inputs: Year/Month/Day (real-world date entry)
    - Labels: Age (years), Progressed (astrological progressed date)
    - Buttons: Calculate, Close
    API:
        SecDirDialog(parent, on_calculate, on_step_year=None)
        set_snapshot(age_int, real_tuple, progressed_tuple=None)
        set_calendar(is_julian: bool)  # no-op, for compatibility
    """
    def __init__(self, parent, on_calculate, on_step_year=None):
        wx.Dialog.__init__(self, parent, title=mtexts.txts["SecondaryProgressions"],
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.on_calculate = on_calculate
        self.on_step_year = on_step_year

        # Title
        title = wx.StaticText(self, wx.ID_ANY, mtexts.txts["PositionForDate"])
        f = title.GetFont(); f.SetPointSize(f.GetPointSize()+2); f.SetWeight(wx.FONTWEIGHT_BOLD); title.SetFont(f)

        # Labels
        self.lbl_age  = wx.StaticText(self, wx.ID_ANY, mtexts.txts["Age"]+": 0")
        self.lbl_prog = wx.StaticText(self, wx.ID_ANY, mtexts.txts["Progressed"]+": ----.--.--")

        # Date inputs
        grid = wx.FlexGridSizer(2, 6, 6, 6)   # ← 빠진 생성줄 복구(중요)

        # (Growable 열 제거: 입력칸이 가로로 퍼지지 않게)
        grid.Add(wx.StaticText(self, wx.ID_ANY, mtexts.txts["Year"]+":"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.year = wx.SpinCtrl(self, wx.ID_ANY, min=-5000, max=5000, initial=2000); self.year.SetMinSize((60, -1))
        grid.Add(self.year, 0, 0)

        grid.Add(wx.StaticText(self, wx.ID_ANY, mtexts.txts["Month"]+":"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.month = wx.SpinCtrl(self, wx.ID_ANY, min=1, max=12, initial=1); self.month.SetMinSize((48, -1))
        grid.Add(self.month, 0, 0)

        grid.Add(wx.StaticText(self, wx.ID_ANY, mtexts.txts["Days"]+":"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.day = wx.SpinCtrl(self, wx.ID_ANY, min=1, max=31, initial=1); self.day.SetMinSize((48, -1))
        grid.Add(self.day, 0, 0)
        # Help texts aligned with PersonalDataDlg
        try:
            self.year.SetHelpText(mtexts.txts["HelpYear"])
            self.month.SetHelpText(mtexts.txts["HelpMonth"])
            self.day.SetHelpText(mtexts.txts["HelpDay"])
        except Exception:
            pass

        btns = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_calc = wx.Button(self, wx.ID_ANY, mtexts.txts["Calculate"])
        btn_close     = wx.Button(self, wx.ID_CLOSE, mtexts.txts["Close"])
        # Button helps
        try:
            self.btn_calc.SetHelpText(mtexts.txts["HelpOk"])
            btn_close.SetHelpText(mtexts.txts["HelpCancel"])
        except Exception:
            pass

        btns.AddStretchSpacer(1)
        btns.Add(self.btn_calc, 0, 0, 0)
        btns.Add(btn_close, 0, wx.LEFT, 8)

        # Layout
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(title, 0, wx.ALL, 8)

        hdr = wx.BoxSizer(wx.HORIZONTAL)
        hdr.Add(self.lbl_age,  0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 12)
        hdr.Add(self.lbl_prog, 0, wx.ALIGN_CENTER_VERTICAL)
        root.Add(hdr,  0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)

        root.Add(grid, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)  # EXPAND 제거
        root.Add(btns, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)

        self.SetSizerAndFit(root)
        self.Layout()

        # Bindings
        self.btn_calc.Bind(wx.EVT_BUTTON, self._on_calc)
        btn_close.Bind(wx.EVT_BUTTON, self._on_close_click)
        self.SetAffirmativeId(wx.ID_CLOSE)

    def set_snapshot(self, age_int, real_tuple, progressed_tuple=None):
        """Update labels and inputs.
           age_int: integer years
           real_tuple: (Y,M,D) real-world date to keep inputs in sync
           progressed_tuple: (Y,M,D) progressed astrologic date to display (optional)
        """
        try:
            self.lbl_age.SetLabel(mtexts.txts["Age"]+": %d," % int(age_int))
        except Exception:
            pass
        try:
            if real_tuple and len(real_tuple) == 3:
                y, m, d = [int(x) for x in real_tuple]
                self.year.SetValue(y)
                self.month.SetValue(m)
                self.day.SetValue(self._snap_day(y, m, d))
        except Exception:
            pass
        try:
            if progressed_tuple and len(progressed_tuple) == 3:
                py, pm, pd = [int(x) for x in progressed_tuple]
                self.lbl_prog.SetLabel(mtexts.txts["Progressed"]+": %04d.%02d.%02d" % (py, pm, pd))
        except Exception:
            pass

    def set_calendar(self, is_julian):
        return  # compatibility no-op

    def _on_calc(self, evt):
        y = int(self.year.GetValue())
        m = int(self.month.GetValue())
        d = int(self.day.GetValue())
        if callable(self.on_calculate):
            try:
                self.on_calculate(y, m, d)
            except Exception:
                pass
    def _safe_close(self):
        try:
            if hasattr(self, "IsModal") and self.IsModal():
                self.EndModal(wx.ID_CLOSE)
            else:
                self.Destroy()
        except Exception:
            try:
                self.Destroy()
            except Exception:
                pass

    def _on_close_click(self, evt):
        self._safe_close()

    # Helpers
    def _is_leap_greg(self, y):
        try:
            if y <= 0: y = 1 - y
        except Exception:
            pass
        return (y % 4 == 0) and (y % 100 != 0 or y % 400 == 0)

    def _snap_day(self, y, m, d):
        if m in (1,3,5,7,8,10,12): mdays = 31
        elif m == 2: mdays = 29 if self._is_leap_greg(y) else 28
        else: mdays = 30
        if d < 1: d = 1
        if d > mdays: d = mdays
        return d
