#!/usr/bin/env python3

from flask import Flask, render_template

from displaylist import DisplayList

#TODO: Change this when a name for the program is decided
app = Flask(__name__)

@app.route("/")
def index():
    display_list = DisplayList("displaylist")

    return render_template('index.html', render_items=display_list)

if __name__ == "__main__":
    app.debug = True
    #TODO: Define port with command line option
    app.run(host='0.0.0.0', port=8080)
