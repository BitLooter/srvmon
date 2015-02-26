#!/usr/bin/env python3

import os
from flask import Flask, render_template
app = Flask(__name__)

class VolumeInfo:
    def __init__(self, volume):
        #TODO: Verify volume is valid
        self.volume = volume.strip()
        self._stat = os.statvfs(self.volume)

    @property
    def free_space(self):
        return self._stat.f_bavail * self._stat.f_frsize

    @property
    def total_size(self):
        return self._stat.f_blocks * self._stat.f_frsize

class DisplayList(list):
    def __init__(self, display_list_path):
        list.__init__(self)

        self._parse_display_list(display_list_path)

    def _parse_display_list(self, display_list_path):
        list_file = open(display_list_path, 'r')
        for line in list_file:
            self.append(VolumeInfo(line))

@app.route("/")
def hello():
    display_list = DisplayList("displaylist")

    return render_template('index.html', render_items=display_list)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
