# -*- coding: utf-8 -*-
import wx
import mtexts
import wx
import mtexts

def _build_gmd(parent, msg, title, style):
    dlg = wx.GenericMessageDialog(parent, msg, title, style)
    try:
        # Yes/No/Cancel 라벨 강제
        if (style & wx.YES) and (style & wx.NO) and (style & wx.CANCEL):
            dlg.SetYesNoCancelLabels(mtexts.txts.get('Yes', u'Yes'),
                                     mtexts.txts.get('No', u'No'),
                                     mtexts.txts.get('Cancel', u'Cancel'))
        elif (style & wx.YES) and (style & wx.NO):
            dlg.SetYesNoLabels(mtexts.txts.get('Yes', u'Yes'),
                               mtexts.txts.get('No',  u'No'))
        elif (style & wx.OK):
            dlg.SetOKLabel(mtexts.txts.get('OK', u'OK'))
    except Exception:
        # 일부 wx 버전에 Setter가 없으면 그냥 넘어가도 동작은 함
        pass
    return dlg

def message(parent, msg, title_key='Message', style=wx.OK|wx.ICON_INFORMATION):
    title = mtexts.txts.get(title_key, title_key)
    dlg = _build_gmd(parent, msg, title, style)
    try:
        return dlg.ShowModal()
    finally:
        dlg.Destroy()

def ask_yes_no(parent, msg_key_or_text, title_key='Confirm', default_yes=False, icon='question'):
    msg = mtexts.txts.get(msg_key_or_text, msg_key_or_text)
    style = wx.YES_NO
    if default_yes: style |= wx.YES_DEFAULT
    if icon == 'question': style |= wx.ICON_QUESTION
    elif icon == 'warning': style |= wx.ICON_WARNING
    dlg = _build_gmd(parent, msg, mtexts.txts.get(title_key, title_key), style)
    try:
        return dlg.ShowModal() == wx.ID_YES
    finally:
        dlg.Destroy()
        
def precreate_context_help_dialog(self, parent, title, style=wx.DEFAULT_DIALOG_STYLE):
    # MSW에서는 "?"가 뜨려면 리사이즈/최대/최소가 없어야 함
    if wx.Platform == '__WXMSW__':
        style &= ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)

    # 2-phase create: __init__만 먼저(아직 창 생성 X)
    wx.Dialog.__init__(self)

    # Extra style은 Create 전에 넣어야 함
    if hasattr(wx, "DIALOG_EX_CONTEXTHELP"):
        self.SetExtraStyle(self.GetExtraStyle() | wx.DIALOG_EX_CONTEXTHELP)

    # 이제 실제 생성
    self.Create(parent, -1, title,
                pos=wx.DefaultPosition, size=wx.DefaultSize, style=style)
    return self

