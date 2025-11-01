# -*- coding: utf-8 -*-
import wx
import mtexts
class AngleAtBirthParamsDlg(wx.Dialog):
    def __init__(self, parent, default_minutes=10):
        wx.Dialog.__init__(self, parent, title=mtexts.txts["AngleatBirth"])
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        v = wx.BoxSizer(wx.VERTICAL)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, u"± "+mtexts.txts["Minute"]+":"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 6)
        self.spin = wx.SpinCtrl(self, -1, "", wx.DefaultPosition, wx.DefaultSize,
                                style=0, min=1, max=12, initial=default_minutes)
        row.Add(self.spin, 0)
        self.spin.SetHelpText(mtexts.txts.get('HelpLessThanTwelve', u'Must be between 0 and 12'))
        v.Add(row, 0, wx.ALL, 10)

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
