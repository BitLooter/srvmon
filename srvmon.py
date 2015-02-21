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

@app.route("/")
def hello():
    display_list_file = open("displaylist", 'r')
    render_items = []
    for line in display_list_file:
        info = VolumeInfo(line)
        render_items.append(info)

    return render_template('index.html', render_items=render_items)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
