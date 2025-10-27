import wx
import profectionsmonwnd


class ProfsTableMonFrame(wx.Frame):
	def __init__(self, parent, title, pchrts, dates, opts, mainsigs, age):
		wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, wx.Size(640, 400))

		self.parent = parent
		self.mainsigs = mainsigs
		self.sw = profectionsmonwnd.ProfectionsMonWnd(self, age, pchrts, dates, opts, parent, mainsigs)
		# register to parent so main Profections can close us together
		if hasattr(self.parent, "register_monthly_child"):
			self.parent.register_monthly_child(self)
		# unregister on manual close
		self.Bind(wx.EVT_CLOSE, self._on_close_unregister)
		# also close this monthly window when the Profections TABLE parent closes/destroys
		if isinstance(self.parent, wx.Window):
			self.parent.Bind(wx.EVT_CLOSE, self._on_parent_close)
			self.parent.Bind(wx.EVT_WINDOW_DESTROY, self._on_parent_destroy)
		self.SetMinSize((200,200))
	def _on_parent_close(self, evt):
		# parent (Profections TABLE) is closing -> ensure this monthly closes too
		try:
			try:
				self.Destroy()
			except Exception:
				pass
		finally:
			evt.Skip()

	def _on_parent_destroy(self, evt):
		# if the destroyed window is the parent, self-destroy
		try:
			obj = evt.GetEventObject()
		except Exception:
			obj = None
		if obj is self.parent:
			try:
				self.Destroy()
			except Exception:
				pass
		evt.Skip()

	def _on_close_unregister(self, evt):
		try:
			if hasattr(self.parent, "unregister_monthly_child"):
				self.parent.unregister_monthly_child(self)
		finally:
			evt.Skip()




