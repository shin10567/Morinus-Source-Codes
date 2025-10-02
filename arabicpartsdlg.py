# -*- coding: utf-8 -*-
import sys
import wx
import intvalidator
import chart
import arabicparts
import options
import mtexts
import copy

#---------------------------------------------------------------------------
# Create and set a help provider.  Normally you would do this in
# the app's OnInit as it must be done before any SetHelpText calls.
provider = wx.SimpleHelpProvider()
wx.HelpProvider.Set(provider)

#---------------------------------------------------------------------------
# daimon = 原等于守护神

class PartsListCtrl(wx.ListCtrl):
    def _deg_to_text(self, absdeg):
        try:
            absdeg = int(absdeg) % 360
        except:
            return u'?'
        signs = [u'Ari',u'Tau',u'Gem',u'Can',u'Leo',u'Vir',u'Lib',u'Sco',u'Sag',u'Cap',u'Aqu',u'Pis']
        sg = absdeg // 30
        dg = absdeg % 30
        return u'%d\u00B0%s' % (dg, signs[sg])

    def _render_token_text(self, code, idxABC, triplet):
        # 1) 인덱스 경로
        try:
            label = mtexts.partstxts[code]
        except Exception:
            # 2) 상수값 경로: 역매핑 캐시 사용
            rev = getattr(mtexts, '_conv_rev_cache', None)
            if not isinstance(rev, dict):
                try:
                    rev = dict((v, k) for (k, v) in mtexts.conv.items())
                except Exception:
                    rev = {}
                mtexts._conv_rev_cache = rev
            label = rev.get(code)
            if label is None:
                # conv 갱신 이후 캐시가 구버전일 수 있음 → 재구축
                try:
                    rev = dict((v, k) for (k, v) in mtexts.conv.items())
                except Exception:
                    rev = {}
                mtexts._conv_rev_cache = rev
                label = rev.get(code, u'?')

        txt = label
        want_lord = False
        if txt.endswith(u'!'):
            want_lord = True
            txt = txt[:-1]

        if txt == mtexts.txts.get('DE', u'DE'):
            out = self._deg_to_text(triplet[idxABC])
            return out + (u'!' if want_lord else u'')
        if txt == mtexts.txts.get('RE', u'RE'):
            rn = int(triplet[idxABC])
            if rn == 0:
                return u'R0(LoF)' + (u'!' if want_lord else u'')
            return (u'R%d' % rn) + (u'!' if want_lord else u'')

        return label

    def _format_formula_text(self, f1, f2, f3, triplet):
        return u'%s + %s - %s' % (self._render_token_text(f1,0,triplet), self._render_token_text(f2,1,triplet), self._render_token_text(f3,2,triplet))
    INDEXCOL = 0
    ACTIVE = 1
    NAME = 2
    FORMULA = 3
    DIURNAL = 4

    DIURNALTXT = u'*'

    MAX_ARABICPARTS_NUM = 40

    def __init__(self, parent, ID, parts, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)

        self.partsdata = {}
        self.parts_codes = {}
        self.parts_refdeg = {}
        self.parts_active = {}
        self.load(parts)

        self.Populate()
        self.Id = ID
        self.changed = False
        self.removed = False


    def Populate(self):
        self.InsertColumn(PartsListCtrl.INDEXCOL, u'#', format=wx.LIST_FORMAT_CENTER)
        self.InsertColumn(PartsListCtrl.ACTIVE, mtexts.txts['Active'], format=wx.LIST_FORMAT_CENTER)
        self.InsertColumn(PartsListCtrl.NAME, mtexts.txts['Name'])
        self.InsertColumn(PartsListCtrl.FORMULA, mtexts.txts['Formula'])
        self.InsertColumn(PartsListCtrl.DIURNAL, mtexts.txts['Diurnal'], format=wx.LIST_FORMAT_CENTER)
        
        items = self.partsdata.items()
        for key, data in items:
            index = self.InsertItem(sys.maxsize, data[0])
            self.SetItem(index, PartsListCtrl.NAME, data[0])
            self.SetItem(index, PartsListCtrl.FORMULA, data[1])
            self.SetItem(index, PartsListCtrl.DIURNAL, data[2])
            self.SetItemData(index, key)
            # Active/Index 표시
            active = self.parts_active.get(key, True)
            self.SetItem(index, PartsListCtrl.ACTIVE, mtexts.txts['On'] if active else mtexts.txts['Off'])
            self.SetItem(index, PartsListCtrl.INDEXCOL, u'R%d' % (index+1))
        self.SetColumnWidth(PartsListCtrl.INDEXCOL, 50)
        self.SetColumnWidth(PartsListCtrl.ACTIVE, 65)
        self.SetColumnWidth(PartsListCtrl.NAME, 160)#wx.LIST_AUTOSIZE)
        self.SetColumnWidth(PartsListCtrl.FORMULA, 140)
        self.SetColumnWidth(PartsListCtrl.DIURNAL, 65)

        self.currentItem = -1
        if len(self.partsdata):
            self.currentItem = 0
            self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)


    def GetListCtrl(self):
        return self


    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()


    def OnItemSelected(self, event):
        # Phoenix/Classic 모두 안전하게
        try:
            idx = event.GetIndex()
        except AttributeError:
            idx = getattr(event, 'm_itemIndex', -1)

        if idx is None:
            idx = -1
        self.currentItem = idx

        if idx >= 0:
            try:
                key = self.GetItemData(idx)
                self.GetParent().activeckb.SetValue(self.parts_active.get(key, True))
            except Exception:
                pass

        event.Skip()

    def OnColClick(self,event):
        event.Skip()

    def _renumber_rows(self):
        # 현재 표시 순서대로 R번호 갱신
        for row in range(self.GetItemCount()):
            self.SetItem(row, PartsListCtrl.INDEXCOL, u'R%d' % (row+1))

    def _refresh_active_for_row(self, row):
        if row < 0 or row >= self.GetItemCount():
            return
        key = self.GetItemData(row)
        active = self.parts_active.get(key, True)
        self.SetItem(row, PartsListCtrl.ACTIVE, mtexts.txts['On'] if active else mtexts.txts['Off'])

    def AddFullItem(self, name, disp_formula, diurnal, codes, triplet, active=True):
        num = self.GetItemCount()
        if num >= PartsListCtrl.MAX_ARABICPARTS_NUM:
            return False
        index = self.InsertItem(num, name)
        self.SetItem(index, PartsListCtrl.NAME, name)
        self.SetItem(index, PartsListCtrl.FORMULA, disp_formula)
        self.SetItem(index, PartsListCtrl.DIURNAL, diurnal)
        key = (max(self.partsdata.keys())+1) if len(self.partsdata) else 1
        self.SetItemData(index, key)
        self.partsdata[key] = (name, disp_formula, diurnal)
        self.parts_codes[key] = codes
        self.parts_refdeg[key] = triplet
        self.parts_active[key] = bool(active)
        self.SetItem(index, PartsListCtrl.ACTIVE, mtexts.txts['On'] if active else mtexts.txts['Off'])
        self.SetItem(index, PartsListCtrl.INDEXCOL, u'R%d' % (index+1))
        self.currentItem = index
        self.EnsureVisible(self.currentItem)
        self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.changed = True
        self._renumber_rows()
        return True

    def OnAdd(self, item):

        name = self.name.GetValue()
        if not name or not name.strip():
            wx.MessageBox(mtexts.txts['ArabicPartNameEmpty'], mtexts.txts['Confirm'])
            return

        num = self.GetItemCount()
        if num >= PartsListCtrl.MAX_ARABICPARTS_NUM:
            txt = mtexts.txts['MaxArabicPartsNum']+str(PartsListCtrl.MAX_ARABICPARTS_NUM)+u'!'
            dlgm = wx.MessageDialog(self, txt, '', wx.OK|wx.ICON_INFORMATION)
            dlgm.ShowModal()
            dlgm.Destroy()#
            return

        if self.checkName(item[PartsListCtrl.NAME]):
            dlgm = wx.MessageDialog(self, mtexts.txts['ArabicPartAlreadyExists'], '', wx.OK|wx.ICON_INFORMATION)
            dlgm.ShowModal()
            dlgm.Destroy()#
            return

        if item[PartsListCtrl.NAME] == '':
            dlgm = wx.MessageDialog(self, mtexts.txts['ArabicPartNameEmpty'], '', wx.OK|wx.ICON_INFORMATION)
            dlgm.ShowModal()
            dlgm.Destroy()#
            return

        self.InsertItem(num, item[PartsListCtrl.NAME])
        for i in range(1, len(item)):
            self.SetItem(num, i, item[i])

        self.currentItem = num
        self.EnsureVisible(self.currentItem) #This scrolls the list to the added item at the end
        self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

        self.changed = True

    def checkName(self, name):
        for i in range(self.GetItemCount()):
            if name == self.getColumnText(i, PartsListCtrl.NAME):
                return True

        return False

    def OnRemove(self):
        if self.currentItem != -1:
            dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
            val = dlg.ShowModal()
            if val == wx.ID_YES:
                key = self.GetItemData(self.currentItem)
                name = self.getColumnText(self.currentItem, PartsListCtrl.NAME)
                self.DeleteItem(self.currentItem)
                try:
                    self.GetParent().refdeg_by_name.pop(name, None)
                except:
                    pass
                try:
                    self.partsdata.pop(key, None)
                    self.parts_codes.pop(key, None)
                    self.parts_refdeg.pop(key, None)
                except:
                    pass
                if self.GetItemCount() == 0:
                    self.currentItem = -1
                elif self.currentItem >= self.GetItemCount():
                    self.currentItem = self.GetItemCount() - 1
                    self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
                else:
                    self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
                self.changed = True
                self.removed = True
                self._renumber_rows()
            dlg.Destroy()

    def OnRemoveAll(self):
        if self.currentItem != -1:
            dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
            val = dlg.ShowModal()
            if val == wx.ID_YES:
                self.DeleteAllItems()
            try:
                self.GetParent().refdeg_by_name = {}
            except:
                pass

            self.currentItem = -1
            self.partsdata = {}
            self.parts_codes = {}
            self.parts_refdeg = {}

            self.changed = True
            self.removed = True
            self.parts_active = {}
            dlg.Destroy()

    def load(self, parts):
        if parts is not None:
            idx = 1
            num = len(parts)
            for i in range(num):
                # Diurnal 표시문자
                diurnal = PartsListCtrl.DIURNALTXT if parts[i][2] else u''

                # 코드 3개(A,B,C)
                f1, f2, f3 = parts[i][1]

                # RE/DE 트리플렛
                trip = (0, 0, 0)
                try:
                    if len(parts[i]) > 3 and isinstance(parts[i][3], (list, tuple)):
                        trip = tuple(parts[i][3])
                except:
                    pass
                # 활성 상태(옵션 포맷에 없으므로 기본 True)
                self.parts_active[idx] = True

                # 내부 저장
                self.parts_codes[idx] = (f1, f2, f3)
                self.parts_refdeg[idx] = trip
                try:
                    active = bool(parts[i][4]) if len(parts[i]) > 4 else True
                except:
                    active = True
                self.parts_active[idx] = active
                # 표시용 포뮬러(실제값 반영: R0/R1.., 18°Ari 등)
                disp = self._format_formula_text(f1, f2, f3, trip)
                self.partsdata[idx] = (parts[i][0], disp, diurnal)

                idx += 1

    def save(self, opts):
        if not self.changed:
            return self.changed, self.removed

        if opts.arabicparts != None:
            del opts.arabicparts

        parts = []
        for row in range(self.GetItemCount()):
            name = self.getColumnText(row, PartsListCtrl.NAME)
            key = self.GetItemData(row)
            f1, f2, f3 = self.parts_codes.get(key, (0,0,0))
            trip = self.parts_refdeg.get(key, (0,0,0))
            diurnal = self.getColumnText(row, PartsListCtrl.DIURNAL)
            diur = (diurnal != '')
            active = self.parts_active.get(key, True)
            # 5-튜플로 저장: (name, (A,B,C), diur, (refA,refB,refC), active)
            parts.append((name, (f1, f2, f3), diur, trip, active))

        opts.arabicparts = copy.deepcopy(parts)
        return self.changed, self.removed


    def getFormula(self, txt, num):
        if num == 1:
            idx = txt.find(u'+')
            f = txt[0:idx]
        elif num == 2:
            idx = txt.find(u'+')
            idx2 = txt.find(u'-')
            f = txt[idx+1:idx2]
        else:
            idx = txt.find(u'-')
            f = txt[idx+1:]

        #remove whitespaces
        f = f.strip()

        return mtexts.conv[f]
            
class RefDegDlg(wx.Dialog):
    def __init__(self, parent, needA, needB, needC, maxref, init_triplet=(0,0,0)):
        wx.Dialog.__init__(self, parent, -1, 'Set RE/DE', style=(wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX))
        self.values = [init_triplet[0], init_triplet[1], init_triplet[2]]
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.rows = []
        self.signs = [mtexts.txts['Aries'], mtexts.txts['Taurus'], mtexts.txts['Gemini'], mtexts.txts['Cancer'], mtexts.txts['Leo'], mtexts.txts['Virgo'], mtexts.txts['Libra'], mtexts.txts['Scorpio'], mtexts.txts['Sagittarius'], mtexts.txts['Capricornus'], mtexts.txts['Aquarius'], mtexts.txts['Pisces']]
        for idx,need in enumerate([needA, needB, needC]):
            if not need:
                self.rows.append(None)
                continue
            hs = wx.BoxSizer(wx.HORIZONTAL)
            lbl = wx.StaticText(self, -1, ['A','B','C'][idx]+':')
            hs.Add(lbl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
            if need == 'DE':
                cb = wx.ComboBox(self, -1, self.signs[0], choices=self.signs, style=wx.CB_DROPDOWN|wx.CB_READONLY)
                sp = wx.SpinCtrl(self, -1, '', min=0, max=29)
                try:
                    absd = int(self.values[idx]) % 360
                    sg = absd // 30
                    dg = absd % 30
                    cb.SetSelection(sg)
                    sp.SetValue(dg)
                except:
                    pass
                hs.Add(cb, 0, wx.ALL, 5)
                hs.Add(wx.StaticText(self, -1, u' '), 0, wx.ALL, 2)
                hs.Add(sp, 0, wx.ALL, 5)
                self.rows.append(('DE', cb, sp))
            else:
                # R0(LoF), R1..R{maxref} 라벨 콤보
                choices = [u'R0(LoF)'] + [u'R%d' % k for k in range(1, maxref+1)]
                init_idx = 0
                try:
                    _n = int(self.values[idx])
                    if 0 <= _n <= maxref:
                        init_idx = _n
                except:
                    pass
                cb = wx.ComboBox(self, -1, choices[init_idx], choices=choices, style=wx.CB_DROPDOWN|wx.CB_READONLY)

                hs.Add(wx.StaticText(self, -1, mtexts.txts['RefColon']), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
                hs.Add(cb, 0, wx.ALL, 5)
                self.rows.append(('RE', cb))

            vsizer.Add(hs, 0, wx.ALL, 2)
        btns = self.CreateButtonSizer(wx.OK)
        vsizer.Add(btns, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        self.SetSizerAndFit(vsizer)

    def getValues(self):
        out=[0,0,0]
        for idx,row in enumerate(self.rows):
            if row is None:
                continue
            if row[0]=='DE':
                cb, sp = row[1], row[2]
                out[idx] = cb.GetSelection()*30 + sp.GetValue()
            else:
                cb = row[1]
                sel = cb.GetSelection()
                out[idx] = sel 
        return tuple(out)

class ArabicPartsDlg(wx.Dialog):

    def __init__(self, parent, options):#, inittxt):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI object using the Create
        # method.
#        pre = wx.PreDialog()
#        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
#        pre.Create(parent, -1, mtexts.txts['ArabicParts'], pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
#        self.PostCreate(pre)
        wx.Dialog.__init__(self, None, -1, mtexts.txts['ArabicParts'], size=wx.DefaultSize)
        #main vertical sizer
        mvsizer = wx.BoxSizer(wx.VERTICAL)
        #main horizontal sizer
        mhsizer = wx.BoxSizer(wx.HORIZONTAL)

        COMBOSIZE = 70

        #AscRef
        self.sascref =wx.StaticBox(self, label='')
        refsizer = wx.StaticBoxSizer(self.sascref, wx.HORIZONTAL)
        label = wx.StaticText(self, -1, mtexts.txts['Ascendant']+':')
        refsizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        self.refcb = wx.ComboBox(self, -1, mtexts.partsreftxts[0], size=(COMBOSIZE, -1), choices=mtexts.partsreftxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.refcb.SetStringSelection(mtexts.partsreftxts[0])
        refsizer.Add(self.refcb, 0, wx.ALL, 5)

        vsubsizer = wx.BoxSizer(wx.VERTICAL)
        vsubsizer.Add(refsizer, 1, wx.GROW|wx.ALIGN_LEFT|wx.RIGHT, 5)

        #DayNight Orb
        self.sorb =wx.StaticBox(self, label=mtexts.txts['DayNightOrb'])
        orbsizer = wx.StaticBoxSizer(self.sorb, wx.HORIZONTAL)
        self.orbdeg = wx.TextCtrl(self, -1, '', validator=intvalidator.IntValidator(0, 6), size=(40,-1))
        self.orbdeg.SetHelpText(mtexts.txts['HelpDayNightOrbDeg'])
        self.orbdeg.SetMaxLength(1)
        orbsizer.Add(self.orbdeg, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        label = wx.StaticText(self, -1, mtexts.txts['Deg'])
        orbsizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        self.orbmin = wx.TextCtrl(self, -1, '', validator=intvalidator.IntValidator(0, 59), size=(40,-1))
        self.orbmin.SetHelpText(mtexts.txts['HelpMin'])
        self.orbmin.SetMaxLength(2)
        orbsizer.Add(self.orbmin, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        label = wx.StaticText(self, -1, mtexts.txts['Min'])
        orbsizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

        vsubsizer.Add(orbsizer, 1, wx.GROW|wx.ALIGN_LEFT|wx.RIGHT, 5)

        # --- ensure RE/DE tokens exist in mtexts (safe, no override) ---
        def _ensure_re_de_tokens():
            if 'DE' not in mtexts.txts:
                mtexts.txts['DE'] = u'DE'
            if 'RE' not in mtexts.txts:
                mtexts.txts['RE'] = u'RE'
            need = [mtexts.txts['DE'], mtexts.txts['DE']+u'!', mtexts.txts['RE'], mtexts.txts['RE']+u'!']
            pts = list(mtexts.partstxts)
            for t in need:
                if t not in pts:
                    pts.append(t)
            mtexts.partstxts = tuple(pts)
            if mtexts.txts['DE'] not in mtexts.conv:
                mtexts.conv[mtexts.txts['DE']] = arabicparts.ArabicParts.DEG
            if (mtexts.txts['DE']+u'!') not in mtexts.conv:
                mtexts.conv[mtexts.txts['DE']+u'!'] = arabicparts.ArabicParts.DEGLORD
            if mtexts.txts['RE'] not in mtexts.conv:
                mtexts.conv[mtexts.txts['RE']] = arabicparts.ArabicParts.RE
            if (mtexts.txts['RE']+u'!') not in mtexts.conv:
                mtexts.conv[mtexts.txts['RE']+u'!'] = arabicparts.ArabicParts.REFLORD

        #이 줄을 실제로 추가
        _ensure_re_de_tokens()

        #Editor
        self.seditor =wx.StaticBox(self, label='')
        editorsizer = wx.StaticBoxSizer(self.seditor, wx.VERTICAL)
        label = wx.StaticText(self, -1, mtexts.txts['Name']+':')
        editorsizer.Add(label, 0, wx.LEFT, 5)
        self.name = wx.TextCtrl(self, -1, '', size=(200,-1))
        self.name.SetMaxLength(20)
        editorsizer.Add(self.name, 0, wx.ALL, 5)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.acb = wx.ComboBox(self, -1, mtexts.partstxts[0], size=(COMBOSIZE, -1), choices=mtexts.partstxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.acb.SetStringSelection(mtexts.partstxts[0])
        hsizer.Add(self.acb, 0, wx.ALL, 5)
        label = wx.StaticText(self, -1, '+(')
        hsizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        self.bcb = wx.ComboBox(self, -1, mtexts.partstxts[0], size=(COMBOSIZE, -1), choices=mtexts.partstxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.bcb.SetStringSelection(mtexts.partstxts[0])
        hsizer.Add(self.bcb, 0, wx.ALL, 5)
        label = wx.StaticText(self, -1, '-')
        hsizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        self.ccb = wx.ComboBox(self, -1, mtexts.partstxts[0], size=(COMBOSIZE, -1), choices=mtexts.partstxts, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.ccb.SetStringSelection(mtexts.partstxts[0])
        hsizer.Add(self.ccb, 0, wx.ALL, 5)
        label = wx.StaticText(self, -1, ')')
        hsizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        editorsizer.Add(hsizer, 0, wx.ALL, 5)
        self.pending_refdeg = [0, 0, 0]  # A,B,C 임시 RE/DE 값 (DE=절대경도 0..359, RE=정수 0=R0, 1=R1...)
        self.acb.Bind(wx.EVT_COMBOBOX, self._OnTokenChangedA)
        self.bcb.Bind(wx.EVT_COMBOBOX, self._OnTokenChangedB)
        self.ccb.Bind(wx.EVT_COMBOBOX, self._OnTokenChangedC)
        self.diurnalckb = wx.CheckBox(self, -1, mtexts.txts['Diurnal'])
        editorsizer.Add(self.diurnalckb, 0, wx.ALL, 5)
        vsubsizer.Add(editorsizer, 0, wx.ALIGN_LEFT|wx.RIGHT, 5)

        #buttons
        sbtns =wx.StaticBox(self, label='')
        btnssizer = wx.StaticBoxSizer(sbtns, wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        ID_Add = wx.NewId()
        btnAdd = wx.Button(self, ID_Add, mtexts.txts['Add'])
        vsizer.Add(btnAdd, 0, wx.GROW|wx.ALL, 5)
        ID_Modify = wx.NewId()
        btnModify = wx.Button(self, ID_Modify, mtexts.txts["Modify"])
        vsizer.Add(btnModify, 0, wx.GROW|wx.ALL, 5)
        ID_Remove = wx.NewId()
        btnRemove = wx.Button(self, ID_Remove, mtexts.txts['Remove'])
        vsizer.Add(btnRemove, 0, wx.GROW|wx.ALL, 5)
        ID_RemoveAll = wx.NewId()
        btnRemoveAll = wx.Button(self, ID_RemoveAll, mtexts.txts['RemoveAll'])
        vsizer.Add(btnRemoveAll, 0, wx.GROW|wx.ALL, 5)

        btnssizer.Add(vsizer, 0, wx.GROW|wx.ALL, 5)#
        vsubsizer.Add(btnssizer, 0, wx.GROW|wx.ALIGN_LEFT|wx.RIGHT, 5)

        mhsizer.Add(vsubsizer, 0, wx.ALIGN_LEFT|wx.ALL, 0)

        #parts
        sparts =wx.StaticBox(self, label='')
        partssizer = wx.StaticBoxSizer(sparts, wx.VERTICAL)
        ID_Parts = wx.NewId()
        self.li = PartsListCtrl(self, ID_Parts, options.arabicparts, size=(485,-1), style=wx.LC_VRULES|wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.li.Bind(wx.EVT_LIST_ITEM_SELECTED, self._OnRowSelected)
        self.refdeg_by_name = {}
        if options.arabicparts:
            for it in options.arabicparts:
                try:
                    name = it[0]
                    trip = it[3]
                    if isinstance(trip, (list, tuple)) and len(trip)==3:
                        self.refdeg_by_name[name] = tuple(trip)
                except:
                    pass

        partssizer.Add(self.li, 1, wx.GROW|wx.ALL, 5)
        # 현재 선택된 랏 활성/비활성 토글 박스
        self.activeckb = wx.CheckBox(self, -1, mtexts.txts.get('Active', 'Active'))
        self.activeckb.SetValue(True)
        partssizer.Add(self.activeckb, 0, wx.ALL, 5)
        self.activeckb.Bind(wx.EVT_CHECKBOX, self.OnToggleActive)

        mhsizer.Add(partssizer, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALL, 0)
        mvsizer.Add(mhsizer, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.OnAdd, id=ID_Add)
        self.Bind(wx.EVT_BUTTON, self.OnModify, id=ID_Modify)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, id=ID_Remove)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveAll, id=ID_RemoveAll)

        btnsizer = wx.StdDialogButtonSizer()

        if wx.Platform != '__WXMSW__':
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)

        btnOk = wx.Button(self, wx.ID_OK, mtexts.txts['Ok'])
        btnOk.SetHelpText(mtexts.txts['HelpOk'])
        btnOk.SetDefault()
        btnsizer.AddButton(btnOk)

        btn = wx.Button(self, wx.ID_CANCEL, mtexts.txts['Cancel'])
        btn.SetHelpText(mtexts.txts['HelpCancel'])
        btnsizer.AddButton(btn)

        btnsizer.Realize()

        mvsizer.Add(btnsizer, 0, wx.GROW|wx.ALL, 10)
        self.SetSizer(mvsizer)
        mvsizer.Fit(self)
        cur_h = self.GetSize().height
        self.SetMinSize((820, cur_h))    # 최소폭도 같이 잡아두면 Fit이 줄이지 못함
        self.SetSize((820, cur_h))
        self.Layout()
        btnOk.SetFocus()

    def OnToggleActive(self, event):
        row = getattr(self.li, 'currentItem', -1)
        if row < 0:
            return
        key = self.li.GetItemData(row)
        val = bool(self.activeckb.GetValue())
        self.li.parts_active[key] = val
        self.li._refresh_active_for_row(row)
        self.li.changed = True

    def _OnTokenChangedA(self, event):
        self._handle_token_click(0)

    def _OnTokenChangedB(self, event):
        self._handle_token_click(1)

    def _OnTokenChangedC(self, event):
        self._handle_token_click(2)

    def _handle_token_click(self, which):
        # which: 0(A)/1(B)/2(C)
        sels = [
            self.acb.GetCurrentSelection(),
            self.bcb.GetCurrentSelection(),
            self.ccb.GetCurrentSelection()
        ]
        tok = mtexts.partstxts[sels[which]]
        base = tok[:-1] if tok.endswith(u'!') else tok

        need = None
        if base == mtexts.txts.get('DE', u'DE'):
            need = 'DE'
        elif base == mtexts.txts.get('RE', u'RE'):
            need = 'RE'

        # RE/DE가 아니면 해당 칸 임시값만 리셋하고 종료
        if not need:
            self.pending_refdeg[which] = 0
            return

        needs = [None, None, None]
        needs[which] = need

        # 초기값: 현재 선택된 랏이 있으면 그 랏의 저장값, 없으면 임시버퍼
        init_triplet = tuple(self.pending_refdeg)
        selrow = getattr(self.li, 'currentItem', -1)
        if selrow is not None and selrow >= 0:
            selname = self.li.getColumnText(selrow, self.li.NAME)
            init_triplet = self.refdeg_by_name.get(selname, init_triplet)

        maxref = self.li.GetItemCount()  # R0..Rmaxref
        dlg = RefDegDlg(self, needs[0], needs[1], needs[2], maxref, init_triplet)
        if dlg.ShowModal() == wx.ID_OK:
            vals = dlg.getValues()
            v = int(vals[which])

            # 여기서는 "저장"하지 않는다! (다른 랏이 바뀌는 버그 방지)
            # 자기 자신 참조 방지는 Modify 시점에 처리
            self.pending_refdeg[which] = v
        dlg.Destroy()

    def _deg_to_text(self, absdeg):
        try:
            absdeg = int(absdeg) % 360
        except:
            return u'?'
        signs = [u'Ari',u'Tau',u'Gem',u'Can',u'Leo',u'Vir',u'Lib',u'Sco',u'Sag',u'Cap',u'Aqu',u'Pis']
        sg = absdeg // 30
        dg = absdeg % 30
        return u'%d\u00B0%s' % (dg, signs[sg])

    def _render_token_text(self, code, idxABC, triplet):
        """
        code: mtexts.partstxts 인덱스 (A/B/C용 선택값)
        idxABC: 0(A)/1(B)/2(C)
        triplet: (refA,refB,refC) ─ RE는 정수 Rn, DE는 절대경도(0..359)
        """
        txt = mtexts.partstxts[code]
        want_lord = False
        if txt.endswith(u'!'):
            want_lord = True
            txt = txt[:-1]

        if txt == mtexts.txts['DE']:
            t = self._deg_to_text(triplet[idxABC])
            return t + (u'!' if want_lord else u'')
        if txt == mtexts.txts['RE']:
            rn = int(triplet[idxABC])
            if rn < 0: rn = 0
            # RE는 R0=LoF, R1..=이미 만든 랏
            return (u'R%d' % rn) + (u'!' if want_lord else u'')

        # 그 외(ASC, SU, LOF 등)는 원래 문자열 그대로
        return mtexts.partstxts[code]

    def _format_formula_text(self, a_sel, b_sel, c_sel, triplet):
        a_txt = self._render_token_text(a_sel, 0, triplet)
        b_txt = self._render_token_text(b_sel, 1, triplet)
        c_txt = self._render_token_text(c_sel, 2, triplet)
        # 603 스타일 "A + B - C"
        return u'%s + %s - %s' % (a_txt, b_txt, c_txt)

    def _refreshRowDisplay(self, row, name, a_sel, b_sel, c_sel, triplet):
        # 리스트 컨트롤의 "Formula" 칼럼 텍스트를 실제값으로 교체
        formula_text = self._format_formula_text(a_sel, b_sel, c_sel, triplet)
        try:
            self.li.SetItem(row, self.li.NAME, name)
            self.li.SetItem(row, self.li.FORMULA, formula_text)
        except:
            # 칼럼 인덱스 이름이 다르면 네 파일의 상수에 맞춰 조정
            pass

    def OnAdd(self, event):
        name = self.name.GetValue().strip()
        if not name:
            dlgm = wx.MessageDialog(self, mtexts.txts.get('ArabicPartNameEmpty', u'Name is empty'), '',
                                    wx.OK | wx.ICON_INFORMATION)
            dlgm.ShowModal()
            dlgm.Destroy()
            return
        if self.li.checkName(name):
            dlgm = wx.MessageDialog(self, mtexts.txts.get('ArabicPartAlreadyExists', u'Already exists'), '',
                                    wx.OK | wx.ICON_INFORMATION)
            dlgm.ShowModal()
            dlgm.Destroy()
            return

        diurnal = ''
        if self.diurnalckb.GetValue():
            diurnal = PartsListCtrl.DIURNALTXT

        trip = tuple(getattr(self, 'pending_refdeg', [0,0,0]))  # 선택 즉시 정해둔 값 사용

        # compute codes (기존 그대로)
        f1 = mtexts.conv[mtexts.partstxts[self.acb.GetCurrentSelection()]]
        f2 = mtexts.conv[mtexts.partstxts[self.bcb.GetCurrentSelection()]]
        f3 = mtexts.conv[mtexts.partstxts[self.ccb.GetCurrentSelection()]]

        disp = self.li._format_formula_text(f1, f2, f3, trip)
        self.refdeg_by_name[name] = trip
        self.li.AddFullItem(name, disp, diurnal, (f1, f2, f3), trip)

        # 추가 후엔 임시버퍼 초기화
        self.pending_refdeg = [0,0,0]

        # 행 표시 갱신
        row = self.li.GetItemCount() - 1
        self._refreshRowDisplay(row, name, self.acb.GetCurrentSelection(), self.bcb.GetCurrentSelection(),
                                self.ccb.GetCurrentSelection(), trip)
        self.pending_refdeg = [0,0,0]

    def OnModify(self, event):
        # 선택된 행
        i = self.li.GetFirstSelected() if hasattr(self.li, 'GetFirstSelected') else getattr(self.li, 'currentItem', -1)
        if i is None or i < 0:
            return

        # 기존/신규 이름
        old_name = self.li.getColumnText(i, self.li.NAME)
        new_name = self.name.GetValue().strip() or old_name
        if new_name != old_name and self.li.checkName(new_name):
            dlgm = wx.MessageDialog(self, mtexts.txts.get('ArabicPartAlreadyExists', u'Already exists'), '',
                                    wx.OK | wx.ICON_INFORMATION)
            dlgm.ShowModal(); dlgm.Destroy()
            return

        # Diurnal 체크 상태 → 표시 문자
        diur_text = PartsListCtrl.DIURNALTXT if self.diurnalckb.GetValue() else u''

        # A/B/C 토큰 선택
        a_sel = self.acb.GetCurrentSelection()
        b_sel = self.bcb.GetCurrentSelection()
        c_sel = self.ccb.GetCurrentSelection()

        # RE/DE 값: 저장된 값 우선, 없으면 임시버퍼
        vals = self.refdeg_by_name.get(old_name, tuple(getattr(self, 'pending_refdeg', [0,0,0])))

        # 자기 자신을 RE로 가리키면 루프 방지(R0로 강등)
        self_index_1based = i + 1
        vals = list(vals)
        for idx, sel in enumerate((a_sel, b_sel, c_sel)):
            tok = mtexts.partstxts[sel]
            base = tok[:-1] if tok.endswith(u'!') else tok
            if base == mtexts.txts.get('RE', u'RE'):
                try:
                    if int(vals[idx]) == self_index_1based:
                        vals[idx] = 0
                except:
                    vals[idx] = 0
        vals = tuple(vals)

        # 내부 코드 갱신(실제 계산용)
        key = self.li.GetItemData(i)
        self.li.parts_codes[key] = (
            mtexts.conv[mtexts.partstxts[a_sel]],
            mtexts.conv[mtexts.partstxts[b_sel]],
            mtexts.conv[mtexts.partstxts[c_sel]],
        )
        self.li.parts_refdeg[key] = vals

        # 표시용 수식 갱신(리스트 칼럼 텍스트)
        disp_formula = self._format_formula_text(a_sel, b_sel, c_sel, vals)

        # 리스트 셀 텍스트 갱신: 이름/공식/Diurnal
        self.li.SetItem(i, self.li.NAME, new_name)
        self.li.SetItem(i, self.li.FORMULA, disp_formula)
        self.li.SetItem(i, self.li.DIURNAL, diur_text)

        # partsdata 튜플도 함께 갱신(저장 시 직렬화에 쓰임)
        self.li.partsdata[key] = (new_name, disp_formula, diur_text)

        # 이름 바뀐 경우 RE/DE 참조 저장 테이블 rename
        if new_name != old_name:
            try:
                self.refdeg_by_name.pop(old_name, None)
            except:
                pass
            self.refdeg_by_name[new_name] = vals
        else:
            # 이름 동일해도 최신 RE/DE 저장
            self.refdeg_by_name[new_name] = vals

        # 변경 플래그
        self.li.changed = True
        # 임시버퍼는 초기화(헷갈림 방지)
        self.pending_refdeg = [0, 0, 0]

    def OnRemove(self):
        # 아이템 없으면 그냥 리턴
        if self.GetItemCount() == 0:
            return
        # 선택이 풀려 있으면 첫 행 선택으로 가드
        if self.currentItem == -1:
            self.currentItem = 0
            self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

        dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
        val = dlg.ShowModal()
        if val == wx.ID_YES:
            key = self.GetItemData(self.currentItem)
            name = self.getColumnText(self.currentItem, PartsListCtrl.NAME)
            self.DeleteItem(self.currentItem)
            try:
                self.GetParent().refdeg_by_name.pop(name, None)
            except:
                pass
            try:
                self.partsdata.pop(key, None)
                self.parts_codes.pop(key, None)
                self.parts_refdeg.pop(key, None)
            except:
                pass
            if self.GetItemCount() == 0:
                self.currentItem = -1
            elif self.currentItem >= self.GetItemCount():
                self.currentItem = self.GetItemCount() - 1
                self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            else:
                self.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.changed = True
            self.removed = True
        dlg.Destroy()

    def _OnRowSelected(self, event):
        # (기존)
        i = getattr(self.li, 'currentItem', -1)
        try:
            i = event.GetIndex()
        except:
            pass
        if i is None or i < 0:
            return

        # ★ 핵심 1: 리스트의 현재 행을 직접 갱신
        self.li.currentItem = i

        # (기존) 이름/주야(diurnal) UI 싱크
        self.name.SetValue(self.li.getColumnText(i, self.li.NAME))
        self.diurnalckb.SetValue(bool(self.li.getColumnText(i, self.li.DIURNAL)))

        # ★ 핵심 2: Active 체크박스도 선택 행 상태로 동기화
        key = self.li.GetItemData(i)
        self.activeckb.SetValue(self.li.parts_active.get(key, True))

        # ★ 권장: 리스트의 자체 핸들러도 돌게 해 이벤트 전파
        event.Skip()


    def OnRemoveAll(self):
        if self.GetItemCount() == 0:
            return
        dlg = wx.MessageDialog(self, mtexts.txts['AreYouSure'], mtexts.txts['Confirm'], wx.YES_NO|wx.ICON_QUESTION)
        val = dlg.ShowModal()
        if val == wx.ID_YES:
            self.DeleteAllItems()
            try:
                self.GetParent().refdeg_by_name = {}
            except:
                pass
            self.currentItem = -1
            self.partsdata = {}
            self.parts_codes = {}
            self.parts_refdeg = {}
            self.changed = True
            self.removed = True
        dlg.Destroy()

    def OnRemove(self, event):
        self.li.OnRemove()

    def OnRemoveAll(self, event):
        self.li.OnRemoveAll()

    def fill(self, opts):
        self.refcb.SetStringSelection(mtexts.partsreftxts[opts.arabicpartsref])
        self.orbdeg.SetValue(str(opts.daynightorbdeg))
        self.orbmin.SetValue(str(opts.daynightorbmin))


    def check(self, opts):
        changed = False
        removed = False

        if self.refcb.GetCurrentSelection() != opts.arabicpartsref:
            opts.arabicpartsref = self.refcb.GetCurrentSelection()
            changed = True

        if int(self.orbdeg.GetValue()) != opts.daynightorbdeg:
            opts.daynightorbdeg = int(self.orbdeg.GetValue())
            changed = True

        if int(self.orbmin.GetValue()) != opts.daynightorbmin:
            opts.daynightorbmin = int(self.orbmin.GetValue())
            changed = True

        ch, rem = self.li.save(opts)
        if ch:
            changed = True
            if rem:
                removed = True

        return changed, removed





