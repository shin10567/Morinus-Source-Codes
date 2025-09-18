# -*- coding: utf-8 -*-
from __future__ import division
import wx
import math

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer",
                "Leo", "Virgo", "Libra", "Scorpio",
                "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def normalize_deg(x):
    x = float(x) % 360.0
    if x < 0:
        x += 360.0
    return x

def dms_to_decimal(deg, minute, second):
    d = float(deg or 0)
    m = float(minute or 0)
    s = float(second or 0)
    return d + m/60.0 + s/3600.0

def decimal_to_dms_in_sign(total_deg):
    total_deg = normalize_deg(total_deg)
    sign_idx = int(total_deg // 30.0) % 12
    deg_in_sign = total_deg - 30.0 * sign_idx

    d = int(deg_in_sign // 1)
    mF = (deg_in_sign - d) * 60.0
    m = int(mF // 1)
    s = round((mF - m) * 60.0)

    # carry
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    if d >= 30:
        d = 0
        sign_idx = (sign_idx + 1) % 12

    return sign_idx, int(d), int(m), int(s)

def dodekatemoria_from_ecliptic(sign_idx, deg, minute, second):
    """
    Rule: position-in-sign × 12, projected in the same direction
    L_dodek = (sign_idx*30 + (deg+min/60+sec/3600)*12) mod 360
    """
    pos_in_sign = dms_to_decimal(deg, minute, second)
    L_dodek = normalize_deg(sign_idx * 30.0 + pos_in_sign * 12.0)
    s2, d2, m2, s2sec = decimal_to_dms_in_sign(L_dodek)
    return L_dodek, s2, d2, m2, s2sec

class DodekConverterDialog(wx.Dialog):
    """
    Convert ecliptic longitude or sign+DMS to dodekatemoria.
    """
    def __init__(self, parent=None, id=wx.ID_ANY, title="Dodecatemoria Calculator"):
        wx.Dialog.__init__(self, parent, id, title,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        # input mode
        self.rb_mode1 = wx.RadioButton(self, label="Input: Sign and Degree", style=wx.RB_GROUP)
        self.rb_mode2 = wx.RadioButton(self, label="Input: Ecliptic Longitude (0–360°)")

        # mode 1 widgets
        self.choice_sign = wx.Choice(self, choices=ZODIAC_SIGNS)
        self.choice_sign.SetSelection(0)
        self.tc_deg = wx.TextCtrl(self, value="0", size=(40, -1))
        self.tc_min = wx.TextCtrl(self, value="0", size=(40, -1))
        self.tc_sec = wx.TextCtrl(self, value="0", size=(40, -1))

        # mode 2 widgets
        self.tc_lon = wx.TextCtrl(self, value="0.0", size=(87, -1))

        # outputs
        self.out_sign = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.out_dms  = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.out_abs  = wx.TextCtrl(self, style=wx.TE_READONLY)

        # buttons
        btn_convert = wx.Button(self, wx.ID_OK, "Convert")
        btn_close = wx.Button(self, wx.ID_CANCEL, "Close")

        # layout
        g1 = wx.FlexGridSizer(2, 2, 5, 4)
        g1.Add(self.rb_mode1, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL); g1.Add((5,5))
        g1.Add(wx.StaticText(self, label="Sign / Deg. / Min. / Sec."), 0, wx.ALIGN_CENTER_VERTICAL)
        h_dms = wx.BoxSizer(wx.HORIZONTAL)
        h_dms.Add(self.choice_sign, 0, wx.RIGHT, 6)
        h_dms.Add(self.tc_deg, 0, wx.RIGHT, 4)
        h_dms.Add(self.tc_min, 0, wx.RIGHT, 4)
        h_dms.Add(self.tc_sec, 0)
        g1.Add(h_dms, 0, wx.EXPAND)

        g1.Add(self.rb_mode2, 0, wx.TOP, 10); g1.Add((5,5))
        g1.Add(wx.StaticText(self, label="Ecliptic Longitude (0–360°)"), 0, wx.ALIGN_CENTER_VERTICAL)
        g1.Add(self.tc_lon, 0)

        g2 = wx.FlexGridSizer(3, 2, 6, 110)
        g2.Add(wx.StaticText(self, label="Dodecatemorion Sign"), 0, wx.ALIGN_CENTER_VERTICAL); g2.Add(self.out_sign, 1, wx.EXPAND)
        g2.Add(wx.StaticText(self, label="Dodecatemorion Position (D/M/S)"), 0, wx.ALIGN_CENTER_VERTICAL); g2.Add(self.out_dms, 1, wx.EXPAND)
        g2.Add(wx.StaticText(self, label="Dodecatemorion Absolute Longitude (°)"), 0, wx.ALIGN_CENTER_VERTICAL); g2.Add(self.out_abs, 1, wx.EXPAND)
        #g2.AddGrowableCol(1, 1)

        h_btn = wx.BoxSizer(wx.HORIZONTAL)
        h_btn.Add(btn_convert, 0, wx.RIGHT, 6)
        h_btn.Add(btn_close, 0)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(g1, 0, wx.ALL|wx.EXPAND, 10)
        root.Add(wx.StaticLine(self), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        root.Add(g2, 0, wx.ALL|wx.EXPAND, 10)
        root.Add(h_btn, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        self.SetSizerAndFit(root)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_convert, btn_convert)
        self.update_mode_ui()
        self.rb_mode1.Bind(wx.EVT_RADIOBUTTON, lambda e: self.update_mode_ui())
        self.rb_mode2.Bind(wx.EVT_RADIOBUTTON, lambda e: self.update_mode_ui())

    def update_mode_ui(self):
        m1 = self.rb_mode1.GetValue()
        self.choice_sign.Enable(m1); self.tc_deg.Enable(m1); self.tc_min.Enable(m1); self.tc_sec.Enable(m1)
        self.tc_lon.Enable(not m1)

    def on_convert(self, evt):
        try:
            if self.rb_mode1.GetValue():
                sidx = self.choice_sign.GetSelection()
                if sidx < 0: sidx = 0
                d = float(self.tc_deg.GetValue() or 0)
                m = float(self.tc_min.GetValue() or 0)
                s = float(self.tc_sec.GetValue() or 0)
                if not (0 <= d < 30) or not (0 <= m < 60) or not (0 <= s < 60):
                    raise ValueError("Check D/M/S ranges.")
                L_dodek, s2, d2, m2, s2sec = dodekatemoria_from_ecliptic(sidx, d, m, s)
            else:
                L = normalize_deg(float(self.tc_lon.GetValue() or 0.0))
                sidx0, d0, m0, s0 = decimal_to_dms_in_sign(L)
                L_dodek, s2, d2, m2, s2sec = dodekatemoria_from_ecliptic(sidx0, d0, m0, s0)

            self.out_sign.SetValue("%s" % ZODIAC_SIGNS[s2])
            self.out_dms.SetValue("%02d° %02d′ %02d″" % (d2, m2, s2sec))
            self.out_abs.SetValue("%.6f" % (normalize_deg(s2*30.0 + d2 + m2/60.0 + s2sec/3600.0)))
        except Exception as e:
            wx.MessageBox("Input error: %s" % e, "Error", wx.ICON_ERROR|wx.OK)
