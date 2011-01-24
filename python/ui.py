#!/usr/bin/env python

import wx
import wx.lib.newevent
import groove
import threading
import urllib

def SetStatus(frame, event): frame.frame_statusbar.SetStatusText(event.attr1)
def EnableFrame(frame, event): frame.Enable(event.attr1)
def ClearResults(frame, event): frame.lst_results.DeleteAllItems() if frame.lst_results.GetItemCount() > 0 else None
def ShowDownloader(frame, event):
    frame.lst_downloads.Show(event.attr1)
    frame.sizer_1.Layout()
def AddResult(frame, event):
    frame.lst_results.InsertStringItem(frame.lst_results.GetItemCount(), str(frame.lst_results.GetItemCount()+1))
    frame.lst_results.SetStringItem(frame.lst_results.GetItemCount()-1, 1, event.attr1)
    frame.lst_results.SetStringItem(frame.lst_results.GetItemCount()-1, 2, event.attr2)
    frame.lst_results.SetStringItem(frame.lst_results.GetItemCount()-1, 3, event.attr3)
    frame.lst_results.SetColumnWidth(1, wx.LIST_AUTOSIZE)
    frame.lst_results.SetColumnWidth(2, wx.LIST_AUTOSIZE)
    frame.lst_results.SetColumnWidth(3, wx.LIST_AUTOSIZE)
    frame.lst_results.SetColumnWidth(4, wx.LIST_AUTOSIZE)
def UpdateProgress(frame, event):
    id = frame.lst_downloads.FindItemData(0, event.attr1)
    frame.lst_downloads.SetStringItem(id, 1, event.attr2)

evtExecFunc, EVT_EXEC_FUNC = wx.lib.newevent.NewEvent()

ID_DOWNLOAD = wx.NewId()
ID_REMOVE = wx.NewId()

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.cb_type = wx.ComboBox(self, -1, choices=["Songs", "Artists", "Albums"], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.txt_query = wx.TextCtrl(self, 1, "", style=wx.TE_PROCESS_ENTER)
        self.lst_results = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.lst_downloads = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.frame_statusbar = self.CreateStatusBar(1, wx.SB_RAISED)
        self.__set_properties()
        self.__do_layout()
        self.Bind(EVT_EXEC_FUNC, self._ExecFunc)
        self.Bind(wx.EVT_TEXT_ENTER, self._TextEnter, self.txt_query)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._ResultsContext, self.lst_results)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._DownloadsContext, self.lst_downloads)
        self.Bind(wx.EVT_SIZE, self._Resize)

        self.menu_results = {}
        self.menu_downloads = {}
        self.menu_results[ID_DOWNLOAD] = "Download"
        self.menu_downloads[ID_REMOVE] = "Remove"

    def __set_properties(self):
        self.SetTitle("JTR's Grooveshark Downloader")
        self.SetSize((600, 400))
        self.cb_type.SetMinSize((100, 23))
        self.cb_type.SetSelection(0)
        self.frame_statusbar.SetStatusWidths([-1])
        frame_statusbar_fields = [""]
        self.lst_results.InsertColumn(-1, "ID")
        self.lst_results.InsertColumn(-1, "Title")
        self.lst_results.InsertColumn(-1, "Album")
        self.lst_results.InsertColumn(-1, "Artist")
        self.lst_downloads.InsertColumn(-1, "Song Title")
        self.lst_downloads.InsertColumn(-1, "Progress")
        for i in range(len(frame_statusbar_fields)):
            self.frame_statusbar.SetStatusText(frame_statusbar_fields[i], i)
        self.frame_statusbar.SetStatusStyles([wx.SB_FLAT])

    def __do_layout(self):
        self.sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        #self.sizer_2.Add(self.cb_type, 0, wx.EXPAND, 0)
        self.sizer_2.Add(self.txt_query, 2, 0, 0)
        self.sizer_1.Add(self.sizer_2, 0, wx.EXPAND, 0)
        self.sizer_1.Add(self.lst_results, 2, wx.EXPAND, 0)
        self.sizer_1.Add(self.lst_downloads, 1, wx.EXPAND, 0)
        self.SetSizer(self.sizer_1)
        self.Layout()

    def _TextEnter(self, event):
        search_thread = t_search(self, event.GetString(), self.cb_type.GetValue())
        search_thread.start()

    def _ExecFunc(self, event):
        event.func(self, event)

    def _Resize(self, event):
        self.lst_downloads.SetColumnWidth(0, self.lst_downloads.GetSize()[0] - self.lst_downloads.GetColumnWidth(1))
        self.Layout()

    def _ResultsContext(self, event):
        menu = wx.Menu()
        menu.Append(ID_DOWNLOAD, "Download")
        wx.EVT_MENU( menu, ID_DOWNLOAD, self._ContextSelection )
        self.PopupMenu(menu, event.GetPoint() + self.lst_results.GetPosition())
        menu.Destroy()
    def _DownloadsContext(self, event):
        menu = wx.Menu()
        for (id,title) in self.menu_downloads.items():
            menu.Append(id,title)
            wx.EVT_MENU( menu, id, self._ContextSelection )
        self.PopupMenu(menu, event.GetPoint() + self.lst_downloads.GetPosition())
        menu.Destroy()

    def _ContextSelection(self, event):
        if event.GetId() == ID_DOWNLOAD:
            id = wx.NewId()
            song = self.results[self.lst_results.GetFirstSelected()]
            filename = "%s - %s.mp3" % (song["ArtistName"], song["SongName"])
            self.lst_downloads.InsertStringItem(self.lst_downloads.GetItemCount(), filename)
            self.lst_downloads.SetItemData(self.lst_downloads.GetItemCount()-1, id)
            self.lst_downloads.SetStringItem(self.lst_downloads.GetItemCount()-1, 1, "Initializing")
            t = t_download(self, filename, song["SongID"], id)
            t.start()
        if event.GetId() == ID_REMOVE:
            _id = self.lst_downloads.GetItemData(self.lst_downloads.GetFirstSelected())
            for t in threading.enumerate():
                try:
                    if (t.id is not None) and (_id == t.id): t.cancelled = True
                except: pass

class t_download(threading.Thread):
    def __init__(self, _frame, _filename, _songid, _id):
        threading.Thread.__init__(self)
        self.frame = _frame
        self.songid = _songid
        self.filename = _filename
        self.id = _id
        self.cancelled = False
    def run(self):
        key = groove.getStreamKeyFromSongIDEx(self.songid)
        try:
            urllib.urlretrieve("http://" + key["result"]["ip"] + "/stream.php", self.filename, self.hook, "streamKey="+key["result"]["streamKey"])
        except Exception, ex:
            if ex.args[0] == "Cancelled":
                frame.lst_downloads.DeleteItem(frame.lst_downloads.FindItemData(0, self.id))
                os.remove(self.filename)
    def hook(self, countBlocks, Block, TotalSize):
        if self.cancelled: raise Exception("Cancelled")
        progress = float(countBlocks*Block) / float(TotalSize) * 100
        wx.PostEvent(self.frame, evtExecFunc(func=UpdateProgress, attr1=self.id,
            attr2=("%.0f%%" % progress if progress < 100 else "Completed")))

class t_search(threading.Thread):
    def __init__ (self, _frame, _query, _type):
        threading.Thread.__init__(self)
        self.frame = _frame
        self.query = _query
        self.type = _type
    def run(self):
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1='Searching for \"' + self.query + '\"...'))
        self.frame.results = groove.getSearchResultsEx(self.query, self.type)
        wx.PostEvent(self.frame, evtExecFunc(func=ClearResults))
        for l in self.frame.results:
            wx.PostEvent(self.frame, evtExecFunc(func=AddResult, attr1=l["SongName"], attr2=l["AlbumName"], attr3=l["ArtistName"]))
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))

class t_init(threading.Thread):
    def __init__ (self, _frame):
        threading.Thread.__init__(self)
        self.frame = _frame
    def run(self):
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
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
    app.SetTopWindow(frame)

    init_thread = t_init(frame)
    init_thread.start()
    frame.Show()
    app.MainLoop()
