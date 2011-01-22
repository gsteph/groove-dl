#!/usr/bin/env python

import wx
import wx.lib.newevent
import groove
import threading

def SetStatus(frame, event): frame.frame_statusbar.SetStatusText(event.attr1)
def EnableFrame(frame, event): frame.Enable(event.attr1)
def ClearResults(frame, event): frame.lst_results.DeleteAllItems() if frame.lst_results.GetItemCount() > 0 else None
def AddResult(frame, event):
        frame.lst_results.InsertStringItem(frame.lst_results.GetItemCount(), str(frame.lst_results.GetItemCount()+1))
        frame.lst_results.SetStringItem(frame.lst_results.GetItemCount()-1, 1, event.attr1)
        frame.lst_results.SetStringItem(frame.lst_results.GetItemCount()-1, 2, event.attr2)
        frame.lst_results.SetStringItem(frame.lst_results.GetItemCount()-1, 3, event.attr3)
        frame.lst_results.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        frame.lst_results.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        frame.lst_results.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        frame.lst_results.SetColumnWidth(4, wx.LIST_AUTOSIZE)

evtExecFunc, EVT_EXEC_FUNC = wx.lib.newevent.NewEvent()

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.cb_type = wx.ComboBox(self, -1, choices=["Songs", "Artists", "Albums"], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.txt_query = wx.TextCtrl(self, 1, "", style=wx.TE_PROCESS_ENTER)
        self.lst_results = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.frame_statusbar = self.CreateStatusBar(1, 0)
        self.__set_properties()
        self.__do_layout()
        self.Bind(EVT_EXEC_FUNC, self._ExecFunc)

    def __set_properties(self):
        self.SetTitle("JTR's Grooveshark Downloader")
        self.SetSize((600, 400))
        self.cb_type.SetMinSize((100, 23))
        self.cb_type.SetSelection(0)
        self.frame_statusbar.SetStatusWidths([-1])
        frame_statusbar_fields = [""]
        for i in range(len(frame_statusbar_fields)):
            self.frame_statusbar.SetStatusText(frame_statusbar_fields[i], i)

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        #sizer_2.Add(self.cb_type, 0, wx.EXPAND, 0)
        sizer_2.Add(self.txt_query, 2, 0, 0)
        sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
        sizer_1.Add(self.lst_results, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()

    def _ExecFunc(self, event):
        event.func(self, event)

class t_search(threading.Thread):
    def __init__ (self, _frame, _query, _type):
        threading.Thread.__init__(self)
        self.frame = _frame
        self.query = _query
        self.type = _type
    def run(self):
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1='Searching for \"' + self.query + '\"...'))
        results = groove.getSearchResultsEx(self.query, self.type)
        wx.PostEvent(self.frame, evtExecFunc(func=ClearResults))
        for l in results:
            wx.PostEvent(self.frame, evtExecFunc(func=AddResult, attr1=l["SongName"], attr2=l["AlbumName"], attr3=l["ArtistName"]))
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))
class t_init(threading.Thread):
    def __init__ (self, _frame):
        threading.Thread.__init__(self)
        self.frame = _frame
    def run(self):
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Initializing..."))
        groove.init()
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Getting Token..."))
        groove.getToken()
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = MyFrame(None, -1, "")
    frame.Disable()
    app.SetTopWindow(frame)

    frame.lst_results.InsertColumn(-1, "ID")
    frame.lst_results.InsertColumn(-1, "Title")
    frame.lst_results.InsertColumn(-1, "Album")
    frame.lst_results.InsertColumn(-1, "Artist")

    init_thread = t_init(frame)
    init_thread.start()
    frame.Show()
    app.MainLoop()
