function dlSong(song){
  url =  "http://listen.grooveshark.com/more.php?";
  sessid = GS.service.sessionID;
  ctoken = GS.service.currentToken;

  method = "getStreamKeyFromSongIDEx";
  token = GS.service.lastRandomizer + hex_sha1(method + ":" + ctoken + ":quitStealinMahShit:" + GS.service.lastRandomizer);
  data = '{"header": {"clientRevision": "20101012.37",';
  data += '"uuid": "' + GS.service.uuID + '", ';
  data += '"privacy": 0, "Country": {"CC4": "0", "CC1": "0", "ID": "1", "CC3": "0", "CC2": "0"}, "client": "jsqueue", ';
  data += '"token": "' + token + '", ';
  data += '"session": "' + sessid + '"}, ';
  data += '"method": "' + method + '", ';
  data += '"parameters": {"mobile": "false", "country": {"CC4": "0", "CC1": "0", "ID": "1", "CC3": "0", "CC2": "0"}, ';
  data += '"songID": "' + song.SongID + '", "prefetch": "false"}}\n\n';

  $.ajax({
    type: 'POST',
    url: url + method,
    data: data,
    dataType: "json",
    success: function(d, s, x){
       alert("wget --post-data=streamKey=" + d.result.streamKey + " \"http://" + d.result.ip + "/stream.php\" -O \"" + song.ArtistName + " - " + song.SongName + ".mp3\"");
    },
    contentType: "application/json"
  });
}

function dlCur(){
  dlSong(GS.player.getCurrentSong());
}