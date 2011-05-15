#!/usr/bin/env python
version = "0.95"
import sys
import os
import shutil
if sys.platform == 'win32': 
    dest = os.getenv('USERPROFILE') + "\\My Documents\\My Music"; conf = ''
    try: os.makedirs(conf)
    except: pass
    try: 
        os.remove("_groove.exe")
        os.remove("_python27.dll")
        shutil.rmtree("_modules")
    except: pass
    sys.stdout = open("groove.exe.out", "w")
    sys.stderr = open("groove.exe.err", "w")
elif sys.platform == 'linux2': 
    dest = os.getenv('HOME') + '/Music'; conf = os.getenv('HOME') + '/.groove'
    try: os.makedirs(conf)
    except: pass
import wx
import wx.lib.newevent
import base64
import groove
import threading
import httplib
import time
import subprocess
import ConfigParser
import tempfile
from urllib import urlretrieve
from ObjectListView import ObjectListView, ColumnDefn

def SetStatus(frame, event): frame.frame_statusbar.SetStatusText(event.attr1)
def EnableFrame(frame, event):
    frame.txt_query.Enable(event.attr1)
    frame.lst_artists.Enable(event.attr1)
def UpdateItem(frame, event): frame.lst_downloads.RefreshObject(event.attr1)
def SetFocus(frame, event): event.attr1.SetFocus()

evtExecFunc, EVT_EXEC_FUNC = wx.lib.newevent.NewEvent()
ID_DOWNLOAD = wx.NewId()
ID_REMOVE = wx.NewId()

def strip(value, deletechars):
    for c in deletechars:
        value = value.replace(c,'')
    return value;

class Album:
    def __init__(self):
        self.name = ""
        self.Songs = []
        self.id = 0
class Artist:
    def __init__(self):
        self.name = ""
        self.Albums = []
        self.gotalbums = False
        self.isVer = 0
        self.id = 0
class MyFrame(wx.Frame):
    results=[]
    downloads=[]
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        font = wx.Font(9, wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
        self.lbl_query = wx.StaticText(self, -1, "  Song:  ", style=wx.ALIGN_CENTRE)
        self.lbl_query.SetFont(font)
        self.txt_query = wx.TextCtrl(self, 1, "", style=wx.TE_PROCESS_ENTER)
        self.folder_chooser = wx.Button(self, -1, "Choose Destination", size=[-1, self.txt_query.GetSize().GetHeight()])
        self.lst_results = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.lst_downloads = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.lst_artists = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.lst_albums = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.lst_songs = ObjectListView(self, -1, style=wx.LC_REPORT)
        self.frame_statusbar = self.CreateStatusBar(1, wx.SB_RAISED)
        self.__set_properties()
        self.__do_layout()
        self.Bind(EVT_EXEC_FUNC, self._ExecFunc)
        self.Bind(wx.EVT_TEXT_ENTER, self._TextEnter, self.txt_query)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._ResultsContext, self.lst_results)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._DoubleClick, self.lst_results)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._DoubleClick, self.lst_songs)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._DoubleClick, self.lst_downloads)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._DownloadsContext, self.lst_downloads)
        self.Bind(wx.EVT_BUTTON, self._ChooseFolder, self.folder_chooser)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._ObjectSelected, self.lst_artists)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._ObjectSelected, self.lst_albums)
        self.txt_query.Bind(wx.EVT_KEY_DOWN, self._Tab)
        self.Bind(wx.EVT_CLOSE, self._Close)
        self.menu_results = {}
        self.menu_downloads = {}
        self.menu_results[ID_DOWNLOAD] = "Download"
        self.menu_downloads[ID_REMOVE] = "Remove"
        self.artists = []
        if sys.platform == 'win32':
            self.SetIcon(wx.Icon(sys.executable, wx.BITMAP_TYPE_ICO))
        else:
            if os.path.exists("groove.ico"): self.SetIcon(wx.Icon("groove.ico", wx.BITMAP_TYPE_ICO))
    def __set_properties(self):
        self.SetTitle("JTR's Grooveshark Downloader v" + version)
        self.SetSize((600, 400))
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
        self.lst_results.SetEmptyListMsg("Type into above text field to search.\nTab to switch modes.")
        self.lst_results._ResizeSpaceFillingColumns()
        self.lst_results.useAlternateBackColors = False
        columns = [
        ColumnDefn("Title", "left", 160, valueGetter = "filename", isSpaceFilling=True),
        ColumnDefn("Bitrate", "center", 60, valueGetter = "bitrate"),
        ColumnDefn("Speed", "center", 75, valueGetter = "speed"),
        ColumnDefn("Done/Total", "center", 100, valueGetter = "size"),
        ColumnDefn("Progress", "center", 80, valueGetter = "progress")]
        self.lst_downloads.SetColumns(columns)
        self.lst_downloads.SetObjects(self.downloads)
        self.lst_downloads.SetEmptyListMsg("N/A")
        self.lst_downloads.SortBy(0)
        self.lst_downloads.useAlternateBackColors = False
        columns = [ColumnDefn("Artist", "center", 100, valueGetter = "name", isSpaceFilling=True)]
        self.lst_artists.SetColumns(columns)
        self.lst_artists.SetEmptyListMsg("N/A")
        self.lst_artists.useAlternateBackColors = False
        columns = [ColumnDefn("Album", "center", 100, valueGetter = "name", isSpaceFilling=True)]
        self.lst_albums.SetColumns(columns)
        self.lst_albums.SetEmptyListMsg("N/A")
        self.lst_albums.useAlternateBackColors = False
        columns = [ColumnDefn("Song", "center", 100, valueGetter = "Name", isSpaceFilling=True)]
        self.lst_songs.SetColumns(columns)
        self.lst_songs.SetEmptyListMsg("N/A")
        self.lst_songs.useAlternateBackColors = False
        for i in range(len(frame_statusbar_fields)):
            self.frame_statusbar.SetStatusText(frame_statusbar_fields[i], i)
        self.frame_statusbar.SetStatusStyles([wx.SB_FLAT])
        self.list_by_mode = self.lst_results
    def __do_layout(self):
        self.sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_2.Add(self.lbl_query, 0, wx.ALIGN_CENTER, 0)
        self.sizer_2.Add(self.txt_query, 2, 0, 0)
        self.sizer_2.Add(self.folder_chooser, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.sizer_2, 0, wx.EXPAND, 0)
        self.sizer_1.Add(self.lst_results, 2, wx.EXPAND, 0)
        self.sizer_1.Add(self.sizer_3, 2, wx.EXPAND, 0)
        self.sizer_1.Add(self.lst_downloads, 1, wx.EXPAND, 0)
        self.sizer_3.Add(self.lst_artists, 1, wx.EXPAND, 0)
        self.sizer_3.Add(self.lst_albums, 1, wx.EXPAND, 0)
        self.sizer_3.Add(self.lst_songs, 2, wx.EXPAND, 0)
        self.SetSizer(self.sizer_1)
        self.sizer_1.Show(self.sizer_3, False)
        self.Layout()
    def _TextEnter(self, event):
        self.artists = []
        if self.lbl_query.GetLabel() == "  Artist:  ":
            self.lst_albums.DeleteAllItems()
            self.lst_songs.DeleteAllItems()
            search_thread = t_search_object(self, _query=event.GetString())
        elif self.lbl_query.GetLabel() == "  Song:  ":
            search_thread = t_search_flat(self, event.GetString())
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
        if event.GetEventObject() == self.lst_results or event.GetEventObject() == self.lst_songs:
            self._ContextSelection(ID_DOWNLOAD)
        elif event.GetEventObject() == self.lst_downloads:
            path = os.path.join(dest, self.lst_downloads.GetSelectedObjects()[0]["filename"])
            if sys.platform == 'win32': os.startfile(path)
            elif sys.platform == 'linux2': subprocess.Popen(['xdg-open', path])
    def _ContextSelection(self, event, flag=None):
        if (event == ID_DOWNLOAD) or (event.GetId() == ID_DOWNLOAD):
            if self.lbl_query.GetLabel() == "  Song:  ":
                lst = self.lst_results
            elif self.lbl_query.GetLabel() == "  Artist:  ":
                lst = self.lst_songs
            for song in lst.GetSelectedObjects():
                filename = "%s - %s.mp3" % (strip(song["ArtistName"], "<>:\"/\|?*"), strip(song["Name"], "<>:\"/\|?*"))
                t = t_download(self, song)
                t.download = {"progress":"Initializing", "thread":t, "filename":filename}
                self.downloads.append(t.download)
                self.lst_downloads.SetObjects(self.downloads)
                t.start()
        elif (flag != None and flag.flag == ID_REMOVE) or (event.GetId() == ID_REMOVE):
            for d in self.lst_downloads.GetSelectedObjects():
                d["thread"].cancelled = True
                self.downloads.remove(d)
            self.lst_downloads.RemoveObjects(self.lst_downloads.GetSelectedObjects())
    def _ChooseFolder(self, event):
        global dest
        dialog = wx.DirDialog(None, "Please choose the destination directory:", os.getenv('USERPROFILE') if sys.platform == 'win32' else os.getenv('HOME'))
        if dialog.ShowModal() == wx.ID_OK:
            dest = dialog.GetPath()
        dialog.Destroy()
    def _Tab(self, event):
        if event.GetKeyCode() == 9:
            if self.lbl_query.GetLabel() == "  Song:  ":
                self.sizer_1.Show(self.sizer_3, True)
                self.sizer_1.Show(self.lst_results, False)
                self.sizer_1.Layout()
                self.lbl_query.SetLabel("  Artist:  ")
                self.list_by_mode = self.lst_artists
            elif self.lbl_query.GetLabel() == "  Artist:  ":
                self.sizer_1.Show(self.sizer_3, False)
                self.sizer_1.Show(self.lst_results, True)
                self.sizer_1.Layout()
                self.lbl_query.SetLabel("  Song:  ")
                self.list_by_mode = self.lst_results
        event.Skip()
    def _ObjectSelected(self, event):
        if event.GetEventObject() == self.lst_artists:
            self.lst_albums.DeleteAllItems()
            self.lst_songs.DeleteAllItems()
            obj = self.lst_artists.GetSelectedObject()
            artist_thread = t_search_object(self, obj)
            artist_thread.start()
        elif event.GetEventObject() == self.lst_albums:
            self.lst_songs.SetObjects(self.lst_albums.GetSelectedObject().Songs)
    def _Close(self, event):
        sys.stdout.close()
        sys.stderr.close()
        os._exit(0)

class t_download(threading.Thread):
    def __init__(self, frame, song):
        threading.Thread.__init__(self)
        self.frame = frame
        self.songid = song["SongID"]
        self.duration = float(song["EstimateDuration"])
        self.cancelled = False
    def run(self):
        try: os.makedirs(dest)
        except: pass
        try:
            key = groove.getStreamKeyFromSongIDEx(self.songid)
            self.t = time.time()
            self.beg = self.t
            self.lastCount = 0
            urlretrieve("http://" + key["result"]["ip"] + "/stream.php", os.path.join(dest, self.download["filename"]), self.hook, "streamKey="+key["result"]["streamKey"])
        except Exception, ex:
            if ex.args[0] == "Cancelled":
                os.remove(os.path.join(dest, self.download["filename"]))
            else:
                def f(frame, event): frame.lst_results.SetObjects(frame.results)
                wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Failed to retreive song. Please try another.."))
                wx.PostEvent(self.frame, evtExecFunc(func=self.frame._ContextSelection, flag=ID_REMOVE))
                
    def hook(self, countBlocks, Block, TotalSize):
        if self.cancelled: raise Exception("Cancelled")
        progress = float(countBlocks*Block) / float(TotalSize) * 100
        if countBlocks == 0:
            if self.duration != 0: self.download["bitrate"] = "%ukbps" % (TotalSize*8 / self.duration / 1000)
            else: self.download["bitrate"] = "-"
        self.download["progress"] = "%.0f%%" % progress if progress < 100 else "Completed"
        if time.time() - self.t > 0.2:
            self.download["size"] = "%.02f/%.02f MB" % (float(countBlocks*Block) / 1024**2, float(TotalSize) / 1024**2)
            self.download["speed"] = "%.02f KB/s" % ((countBlocks - self.lastCount)*Block / (time.time() - self.t) / 1024)
            self.t = time.time()
            self.lastCount = countBlocks
        if countBlocks*Block >= TotalSize:
            self.download["size"] = "%.02f/%.02f MB" % (float(TotalSize) / 1024**2, float(TotalSize) / 1024**2)
            self.download["speed"] = self.download["speed"] = "~%.02f KB/s" % (countBlocks*Block / (time.time() - self.beg) / 1024)
        wx.PostEvent(self.frame, evtExecFunc(func=UpdateItem, attr1=self.download))

class t_search_object(threading.Thread):
    def __init__ (self, _frame, _artist=None, _query=None):
        threading.Thread.__init__(self)
        self.frame = _frame
        self.artist = _artist
        self.query = _query
    def run(self):
        if self.artist == None:
            wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
            wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1='Searching for \"' + self.query + '\"...'))
            self.frame.results = groove.getSearchResultsEx(self.query, "Artists")
            for a in self.frame.results:
                b = Artist()
                b.name = a["ArtistName"]
                b.isVer = a["IsVerified"]
                b.id = a["ArtistID"]
                self.frame.artists.append(b)
            def f(frame, event): frame.lst_artists.SetObjects(frame.artists)
            wx.PostEvent(self.frame, evtExecFunc(func=f))
            wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
            wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))
            wx.PostEvent(self.frame, evtExecFunc(func=SetFocus, attr1=self.frame.lst_artists))
        else:
            if not self.artist.gotalbums:
                wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
                wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1='Retreiving artist\'s songs...'))
                self.frame.results = groove.artistGetSongsEx(self.artist.id, self.artist.isVer)
                #print len(self.frame.results['result'])
                for i in self.frame.results['result']:
                    flag = True
                    for a in self.artist.Albums:
                        if a.id == i["AlbumID"]:
                            flag = False
                            break
                    if flag:
                        a = Album()
                        a.name = i["AlbumName"]
                        a.id = i["AlbumID"]
                        self.artist.Albums.append(a)
                for i in self.frame.results['result']:
                    for a in self.artist.Albums:
                        if a.id == i["AlbumID"]:
                            a.Songs.append(i)
                            break
                self.artist.gotalbums = True
            def f(frame, event): frame.lst_albums.SetObjects(self.artist.Albums)
            wx.PostEvent(self.frame, evtExecFunc(func=f))
            wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
            wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))
        
class t_search_flat(threading.Thread):
    def __init__ (self, _frame, _query):
        threading.Thread.__init__(self)
        self.frame = _frame
        self.query = _query
    def run(self):
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1='Searching for \"' + self.query + '\"...'))
        self.frame.results = groove.getSearchResultsEx(self.query, "Songs")
        def f(frame, event): frame.lst_results.SetObjects(frame.results)
        wx.PostEvent(self.frame, evtExecFunc(func=f))
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
        wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))
        wx.PostEvent(self.frame, evtExecFunc(func=SetFocus, attr1=self.frame.lst_results))
        
class t_init(threading.Thread):
    def __init__ (self, _frame):
        threading.Thread.__init__(self)
        self.frame = _frame
    def updatehook(self, countBlocks, Block, TotalSize):
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Downloading v%s - %%%s..." % (self.new,int(float(countBlocks*Block)/TotalSize*100))))
    def update(self):
        wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Checking for updates..."))
        conn = httplib.HTTPConnection("www.groove-dl.co.cc")
        conn.request("GET", "/version")
        self.new = conn.getresponse().read()
        if self.new != version:
            dlg = wx.MessageDialog(self.frame, "There is a new version available. Do you wish to update ?", "Update found", wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Downloading v%s..." % self.new))
                filename = urlretrieve("https://github.com/downloads/jacktheripper51/groove-dl/groove-dl_%sall.exe" % self.new, reporthook=self.updatehook)[0]
                newfile = filename+"tmp.exe"
                o = open(newfile, "wb")
                for l in open(filename, "rb"):                                         ### Hack to replace the extract path
                    if "InstallPath" in l:                                              ### to the current directory
                        l = l[:12] + '"' + os.getcwd().replace('\\', '\\\\') + '"\n'  ### because the functionality doesn't
                    o.write(l)                                                          ### exist yet in 7zsfx through CLI
                o.close()
                os.rename("groove.exe", "_groove.exe")
                os.rename("modules", "_modules")
                os.rename("python27.dll", "_python27.dll")
                subprocess.Popen([newfile, '-ai', '-gm2', '-y'])
                os._exit(0)
    def run(self):
        while(True):
            try:
                wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=False))
                if sys.platform == "win32": self.update()
                wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Initializing..."))
                groove.init()
                wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Getting Token..."))
                groove.getToken()
                wx.PostEvent(self.frame, evtExecFunc(func=EnableFrame, attr1=True))
                wx.PostEvent(self.frame, evtExecFunc(func=SetFocus, attr1=self.frame.txt_query))
                wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Ready"))
                time.sleep(300)
            except Exception, e:
                if e.args[0] == 11004:
                    wx.PostEvent(self.frame, evtExecFunc(func=SetStatus, attr1="Failed to connect. Waiting (2)"))
                    time.sleep(2)
                else: print e.args

def main():
    global dest
    config = ConfigParser.RawConfigParser()
    if not os.path.exists(os.path.join(conf, "settings.ini")):
        config.add_section("groove-dl")
        config.set("groove-dl", "dest", dest)
        config.write(open(os.path.join(conf, "settings.ini"), "wb"))
    config.read(os.path.join(conf, "settings.ini"))
    dest = config.get("groove-dl", "dest")
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = MyFrame(None, -1, "")
    app.SetTopWindow(frame)
    init_thread = t_init(frame)
    init_thread.start()
    frame.Show()
    app.MainLoop()
