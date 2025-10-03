import copy
import wx
import chart
import mtexts


class TriplicitiesDlg(wx.Dialog):

	def __init__(self, parent, options):
		wx.Dialog.__init__(self, parent, -1, mtexts.txts['Triplicities'], pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

		self.trips = [[None, None, None],
						[None, None, None],
						[None, None, None],
						[None, None, None]]

		self.tripsval = copy.deepcopy(options.trips)

		#main vertical sizer
		mvsizer = wx.BoxSizer(wx.VERTICAL)

		self.cb = wx.ComboBox(self, -1, mtexts.triplicityList[options.seltrip], size=(150, -1), choices=mtexts.triplicityList, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		self.cb.SetSelection(options.seltrip)
		mvsizer.Add(self.cb, 0, wx.ALIGN_LEFT|wx.TOP|wx.LEFT, 5)

		strips =wx.StaticBox(self, label='')
		tripssizer = wx.StaticBoxSizer(strips, wx.VERTICAL)
		num = len(self.trips)
		subnum = len(self.trips[0])
		gsizer = wx.FlexGridSizer(0, 4, 0, 0)

		# Caption row: [blank] [Primary] [Secondary] [Particip.]
		blank = wx.StaticText(self, -1, "")
		gsizer.Add(blank, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		for i in range(subnum):
			cap = wx.StaticText(self, -1, mtexts.triptypes[i])
			gsizer.Add(cap, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		for i in range(num):
			row_label = wx.StaticText(self, -1, mtexts.triplicities[i]+':')
			gsizer.Add(row_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

			for j in range(subnum):
				chstxt = mtexts.pls if j != 2 else mtexts.pls3
				self.trips[i][j] = wx.ComboBox(
					self, -1,
					chstxt[self.tripsval[options.seltrip][i][j]],
					size=(90, -1), choices=chstxt,
					style=wx.CB_DROPDOWN|wx.CB_READONLY
				)
				self.trips[i][j].SetSelection(self.tripsval[options.seltrip][i][j])
				gsizer.Add(self.trips[i][j], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)


		tripssizer.Add(gsizer, 0, wx.ALIGN_LEFT|wx.TOP, 2)

		mvsizer.Add(tripssizer, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT, 5)

		self.oldidx = options.seltrip

		btnsizer = wx.StdDialogButtonSizer()

		btnOk = wx.Button(self, wx.ID_OK, mtexts.txts['Ok'])
		btnsizer.AddButton(btnOk)
		btnOk.SetHelpText(mtexts.txts['HelpOk'])
		btnOk.SetDefault()

		btn = wx.Button(self, wx.ID_CANCEL, mtexts.txts['Cancel'])
		btnsizer.AddButton(btn)
		btn.SetHelpText(mtexts.txts['HelpCancel'])

		btnsizer.Realize()

		mvsizer.Add(btnsizer, 0, wx.GROW|wx.ALL, 10)
		self.SetSizer(mvsizer)
		mvsizer.Fit(self)

		self.Bind(wx.EVT_COMBOBOX, self.onSelect, id=self.cb.GetId())
		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)

		btnOk.SetFocus()


	def onSelect(self, event):
		idx = event.GetSelection()
		#save the old and display the new
		num = len(self.trips)
		subnum = len(self.trips[0])
		for i in range(num):
			for j in range(subnum):
				self.tripsval[self.oldidx][i][j] = self.trips[i][j].GetCurrentSelection()

				self.trips[i][j].SetSelection(self.tripsval[idx][i][j])

		self.oldidx = idx


	def onOK(self, event):
		num = len(self.trips)
		subnum = len(self.trips[0])
		curridx = self.cb.GetCurrentSelection()
		#save
		for i in range(num):
			for j in range(subnum):
				self.tripsval[curridx][i][j] = self.trips[i][j].GetCurrentSelection()

		self.Close()
		self.SetReturnCode(wx.ID_OK)


	def check(self, options):
		changed = False

		if options.seltrip != self.cb.GetCurrentSelection():
			options.seltrip = self.cb.GetCurrentSelection()
			changed = True

		typnum = len(mtexts.triplicityList)

		num = len(self.trips)
		subnum = len(self.trips[0])
		for typ in range(typnum):
			for i in range(num):
				for j in range(subnum):
					if self.tripsval[typ][i][j] != options.trips[typ][i][j]:
						options.trips[typ][i][j] = self.tripsval[typ][i][j] 
						changed = True
						
		return changed






