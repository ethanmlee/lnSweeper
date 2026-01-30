#!/bin/python3
import xmlrpc.client
# used to be called xmlrpclib (python 2: import xmlrpclib)
import subprocess
import os
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()

# p much the only documentation I could find, but I am also lazy
# https://mdevaev.github.io/emonoda/rTorrent-XMLRPC-Reference/

server_url = os.getenv('SERVERURL')
server = xmlrpc.client.Server(server_url)

# list of all torrents in torrent client
alltorrents = server.download_list("", "main")

# returns the number of hardlinks into
def numln (self):
  if ".mp4" in self or ".mkv" in self or ".avi" in self or ".vob" in self:
    return subprocess.getoutput("stat " + self + " | grep -i inode | awk -vn=1 '{print substr($0,length($0)-n+1)}'")
  else:
    # need to set up to omit Sample folders and other folders that would not have been hardlinked
    return subprocess.getoutput("stat " + self + "/* | grep -i inode | awk -vn=1 '{print substr($0,length($0)-n+1)}' | sort -k2 -r | head -1")

# and now for some nested if statement garbage
for torrent in alltorrents:
  # only run on these labels
  label = unquote(server.d.get_custom1(torrent) or "")
  if label in ("*sonarr", "*radarr", "*anime-sonarr"):
    # only completed torrents (not torrents that are still downloading)
    if server.d.get_complete(torrent) == 1:
      # set name as the torrents name
      name = server.d.name(torrent)
      # set dir as the directory of the torrent
      thisdir = server.d.base_path(torrent)
      # set filename as the filename of the torrent
      filename = server.d.base_filename(torrent)
      # set label as the torrent's label
      label = server.d.custom1(torrent)
      # set tracker as the torrents tracker domain
      tracker = server.d.tracker_domain(torrent)
      # fixes path format
      thisdir = thisdir.replace(filename, '"' + filename + '"')
      thisdir = "~" + thisdir
      # need to set up to only run if torrent is seeding (not downloading)
      # if there is not a hardlink then procede
      try:
        num_lines = int(numln(thisdir))
        if num_lines <= 1:
          # need to add print how old the torrent is and from which tracker
          print("")
          print(name + " | " + label + " | " + tracker)
          print( thisdir )
          print( num_lines )
          # label acts as an inbox to look through and confirm before deleting or adding to ratio group
          server.d.custom1.set(torrent, "*lnsweep")
        else:
          pass
      except ValueError:
        print(name + " | " + "numln did not return an integer.")

  if server.d.get_custom1(torrent) == "cross-seed":
    if server.d.get_complete(torrent) == 1:
      name = server.d.name(torrent)
      thisdir = server.d.base_path(torrent)
      filename = server.d.base_filename(torrent)
      label = server.d.custom1(torrent)
      tracker = server.d.tracker_domain(torrent)
      thisdir = thisdir.replace(filename, '"' + filename + '"')
      thisdir = "~" + thisdir
      if 'No such file or directory' in numln(thisdir):
        print("")
        print(name + " is a dead torrent, deleting")
        server.d.erase(torrent)

