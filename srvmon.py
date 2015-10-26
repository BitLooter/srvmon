#!/usr/bin/env python3

#from flask import Flask, render_template
import flask

from displaylist import DisplayList, DisplayListError

#TODO: Change this when a name for the program is decided
app = flask.Flask(__name__)
app.config.from_object('config.defaults')

@app.route("/")
def index():
    display_list = DisplayList(app.config['DISPLAYLIST'])
    return flask.render_template('index.html', render_items=display_list)

@app.errorhandler(DisplayListError)
def displaylist_error(error):
    return "Error loading display list '{}:{}' - {}".format(error.filename, error.line_number, error.message), 500

if __name__ == "__main__":
    app.debug = True
    #TODO: Define port with command line option
    app.run(host='0.0.0.0', port=app.config['PORT'])
