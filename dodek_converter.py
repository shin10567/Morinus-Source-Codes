# -*- coding: utf-8 -*-
from __future__ import division
import wx
import mtexts
import math

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
    def __init__(self, parent=None, id=wx.ID_ANY, title = mtexts.txts[u"DodecatemoriaCalculator"]):
        wx.Dialog.__init__(self, parent, id, title,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        # input mode
        self.rb_mode1 = wx.RadioButton(self, label=mtexts.txts["InputSignandDegree"], style=wx.RB_GROUP)
        self.rb_mode2 = wx.RadioButton(self, label=mtexts.txts["InputEclipticLongitude"])

        # mode 1 widgets
        ZODIAC_SIGNS = [mtexts.txts["Aries"], mtexts.txts["Taurus"], mtexts.txts["Gemini"], mtexts.txts["Cancer"],mtexts.txts["Leo"], mtexts.txts["Virgo"], mtexts.txts["Libra"], mtexts.txts["Scorpio"],mtexts.txts["Sagittarius"], mtexts.txts["Capricornus"], mtexts.txts["Aquarius"], mtexts.txts["Pisces"]]
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
        btn_convert = wx.Button(self, wx.ID_OK, mtexts.txts["Convert"])
        btn_close = wx.Button(self, wx.ID_CANCEL, mtexts.txts["Close"])

        # layout
        g1 = wx.FlexGridSizer(8, 2, 6, 110) # 行,列,行间距,列间距
        g1.Add(self.rb_mode1, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL); g1.Add((5,5))
        g1.Add(wx.StaticText(self, label=mtexts.txts["SignDegMinSec"]), 0, wx.ALIGN_CENTER_VERTICAL)
        h_dms = wx.BoxSizer(wx.HORIZONTAL)
        h_dms.Add(self.choice_sign, 0, wx.RIGHT, 6)
        h_dms.Add(self.tc_deg, 0, wx.RIGHT, 4)
        h_dms.Add(self.tc_min, 0, wx.RIGHT, 4)
        h_dms.Add(self.tc_sec, 0)
        g1.Add(h_dms, 0, wx.EXPAND)

        #g1 = wx.FlexGridSizer(3, 2, 6, 110)
        g1.Add(self.rb_mode2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL); g1.Add((5,5))
        g1.Add(wx.StaticText(self, label=mtexts.txts["EclipticLongitude"]), 0, wx.ALIGN_CENTER_VERTICAL)
        g1.Add(self.tc_lon, 0)

        g2 = wx.FlexGridSizer(4, 2, 7, 120)
        g2.Add(wx.StaticText(self, label=mtexts.txts["DodecatemorionSign"]), 0, wx.ALIGN_CENTER_VERTICAL); g2.Add(self.out_sign, 1, wx.EXPAND)
        g2.Add(wx.StaticText(self, label=mtexts.txts["DodecatemorionPosition"]), 0, wx.ALIGN_CENTER_VERTICAL); g2.Add(self.out_dms, 1, wx.EXPAND)
        g2.Add(wx.StaticText(self, label=mtexts.txts["DodecatemorionAbsoluteLongitude"]), 0, wx.ALIGN_CENTER_VERTICAL); g2.Add(self.out_abs, 1, wx.EXPAND)
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
        self.Bind(wx.EVT_BUTTON, self.on_close, btn_close)
        self.update_mode_ui()
        self.rb_mode1.Bind(wx.EVT_RADIOBUTTON, lambda e: self.update_mode_ui())
        self.rb_mode2.Bind(wx.EVT_RADIOBUTTON, lambda e: self.update_mode_ui())

    def on_close(self, evt):
        self.Destroy()
        self._dlg_dodek = None

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
                    raise ValueError(mtexts.txts.get('CheckDMSRanges', u'Check D/M/S ranges.'))
                L_dodek, s2, d2, m2, s2sec = dodekatemoria_from_ecliptic(sidx, d, m, s)
            else:
                val_txt = (self.tc_lon.GetValue() or u"0").replace(',', '.')
                L_in = float(val_txt)
                if not (0.0 <= L_in < 360.0):
                    raise ValueError(mtexts.txts.get('CheckAbsDegRange', u'Absolute degree must be between 0° and 360° (exclusive).'))
                L = L_in  # 여기서는 normalize_deg로 강제 보정하지 않음 (범위 패스 시 그대로 사용)
                sidx0, d0, m0, s0 = decimal_to_dms_in_sign(L)
                L_dodek, s2, d2, m2, s2sec = dodekatemoria_from_ecliptic(sidx0, d0, m0, s0)

            ZODIAC_SIGNS = [mtexts.txts["Aries"], mtexts.txts["Taurus"], mtexts.txts["Gemini"], mtexts.txts["Cancer"],mtexts.txts["Leo"], mtexts.txts["Virgo"], mtexts.txts["Libra"], mtexts.txts["Scorpio"],mtexts.txts["Sagittarius"], mtexts.txts["Capricornus"], mtexts.txts["Aquarius"], mtexts.txts["Pisces"]]
            self.out_sign.SetValue("%s" % ZODIAC_SIGNS[s2])
            self.out_dms.SetValue("%02d:%02d'%02d\"" % (d2, m2, s2sec))
            self.out_abs.SetValue("%.6f" % (normalize_deg(s2*30.0 + d2 + m2/60.0 + s2sec/3600.0)))
        except ValueError as e:
            wx.MessageBox(str(e), mtexts.txts.get('Error', u'Error'), wx.OK|wx.ICON_EXCLAMATION)
            return
        except Exception:
            msg = mtexts.txts.get('InputError', u'Input error: %s') % mtexts.txts.get('SignDegMinSec', u'Sign/DMS')
            wx.MessageBox(msg, mtexts.txts.get('Error', u'Error'), wx.OK|wx.ICON_EXCLAMATION)
            return



