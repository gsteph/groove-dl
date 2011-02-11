#!/usr/bin/env python
import wx
import wx.lib.newevent
import groove
import threading
import urllib
import os
import ConfigParser
from ObjectListView import ObjectListView, ColumnDefn

def SetStatus(frame, event): frame.frame_statusbar.SetStatusText(event.attr1)
def EnableFrame(frame, event): 
  frame.txt_query.Enable(event.attr1)
  frame.cb_type.Enable(event.attr1)
def ClearResults(frame, event): frame.lst_results.DeleteAllItems() if frame.lst_results.GetItemCount() > 0 else None
def ShowDownloader(frame, event):
    frame.lst_downloads.Show(event.attr1)
    frame.sizer_1.Layout()
def UpdateItem(frame, event):
    frame.lst_downloads.RefreshObject(event.attr1)

evtExecFunc, EVT_EXEC_FUNC = wx.lib.newevent.NewEvent()
ID_DOWNLOAD = wx.NewId()
ID_REMOVE = wx.NewId()
dest = "Songs"

def strip(value, deletechars):
    for c in deletechars:
        value = value.replace(c,'')
    return value;

class MyFrame(wx.Frame):
    results=[]
    downloads=[]
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.cb_type = wx.ComboBox(self, -1, choices=["Songs", "Artists", "Albums"], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.txt_query = wx.TextCtrl(self, 1, "", style=wx.TE_PROCESS_ENTER)
        self.lst_results = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.lst_downloads = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.frame_statusbar = self.CreateStatusBar(1, wx.SB_RAISED)
        self.cb_type.Show(False)
        self.__set_properties()
        self.__do_layout()
        self.Bind(EVT_EXEC_FUNC, self._ExecFunc)
        self.Bind(wx.EVT_TEXT_ENTER, self._TextEnter, self.txt_query)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._ResultsContext, self.lst_results)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._DoubleClick, self.lst_results)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._DownloadsContext, self.lst_downloads)

        self.menu_results = {}
        self.menu_downloads = {}
        self.menu_results[ID_DOWNLOAD] = "Download"
        self.menu_downloads[ID_REMOVE] = "Remove"
        
        icon = wx.Icon("groove.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

    def __set_properties(self):
        self.SetTitle("JTR's Grooveshark Downloader")
        self.SetSize((600, 400))
        self.cb_type.SetMinSize((100, 23))
        self.cb_type.SetSelection(0)
        self.frame_statusbar.SetStatusWidths([-1])
        frame_statusbar_fields = [""]
        columns = [
        ColumnDefn("Title", "left", 0, valueGetter = "SongName", isSpaceFilling=True),
        ColumnDefn("Album", "center", 0, valueGetter = "AlbumName", isSpaceFilling=True),
        ColumnDefn("Artist", "center", 0, valueGetter = "ArtistName", isSpaceFilling=True)]
        columns[0].freeSpaceProportion = 2
        columns[1].freeSpaceProportion = columns[2].freeSpaceProportion = 1
        self.lst_results.SetColumns(columns)
        self.lst_results.SetObjects(self.results)
        self.lst_results.SetEmptyListMsg("Type into above text field to search.")
        self.lst_results._ResizeSpaceFillingColumns()
        columns = [
        ColumnDefn("Title", "left", 160, valueGetter = "filename", isSpaceFilling=True),
        ColumnDefn("Progress", "center", 160, valueGetter = "progress")]
        self.lst_downloads.SetColumns(columns)
        self.lst_downloads.SetObjects(self.downloads)
        self.lst_downloads.SetEmptyListMsg("N/A")
        self.lst_downloads.SortBy(0)

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
    def _DoubleClick(self, event):
        self._ContextSelection(ID_DOWNLOAD)

    def _ContextSelection(self, event):
        if (event == ID_DOWNLOAD) or (event.GetId() == ID_DOWNLOAD):
            for song in self.lst_results.GetSelectedObjects():
                filename = "%s - %s.mp3" % (strip(song["ArtistName"], "<>:\"/\|?*"), strip(song["SongName"], "<>:\"/\|?*"))
                t = t_download(self, song["SongID"])
                t.download = {"progress":"Initializing", "thread":t, "filename":filename}
                self.downloads.append(t.download)
                self.lst_downloads.SetObjects(self.downloads)
                t.start()
        elif event.GetId() == ID_REMOVE:
            for d in self.lst_downloads.GetSelectedObjects():
                d["thread"].cancelled = True
            for i in self.lst_downloads.GetSelectedObjects(): self.downloads.remove(i)
            self.lst_downloads.RemoveObjects(self.lst_downloads.GetSelectedObjects())

class t_download(threading.Thread):
    def __init__(self, frame, songid):
        threading.Thread.__init__(self)
        self.frame = frame
        self.songid = songid
        self.cancelled = False
    def run(self):
        key = groove.getStreamKeyFromSongIDEx(self.songid)
        try: os.makedirs(dest)
        except: pass
        try:
            urllib.urlretrieve("http://" + key["result"]["ip"] + "/stream.php", dest + "/" + self.download["filename"], self.hook, "streamKey="+key["result"]["streamKey"])
        except Exception, ex:
            if ex.args[0] == "Cancelled":
                os.remove(dest + "/" + self.download["filename"])
            else:
                print ex
    def hook(self, countBlocks, Block, TotalSize):
        if self.cancelled: raise Exception("Cancelled")
        progress = float(countBlocks*Block) / float(TotalSize) * 100
        self.download["progress"] = "%.0f%%" % progress if progress < 100 else "Completed"
        wx.PostEvent(self.frame, evtExecFunc(func=UpdateItem, attr1=self.download))

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
        def f(frame, event): frame.lst_results.SetObjects(frame.results)
        wx.PostEvent(self.frame, evtExecFunc(func=f))
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

def main():
    global dest
    config = ConfigParser.RawConfigParser()
    if not os.path.exists("settings.ini"):
        config.add_section("groove-dl")
        config.set("groove-dl", "dest", dest)
        config.write(open("settings.ini", "wb"))
    config.read("settings.ini")
    dest = config.get("groove-dl", "dest")
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = MyFrame(None, -1, "")
    app.SetTopWindow(frame)
    init_thread = t_init(frame)
    init_thread.start()
    frame.Show()
    app.MainLoop()
