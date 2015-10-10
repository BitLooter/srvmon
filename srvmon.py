#!/usr/bin/env python3

import os
from flask import Flask, render_template
app = Flask(__name__)

class BaseCommand:
    def __init__(self, subcommands=[]):
        self.subcommands = subcommands
        self.text="DUMMYTEXT"

class TextCommand(BaseCommand):
    """Display list command that simply prints a string."""
    def __init__(self, text):
        BaseCommand.__init__(self)
        self.text = text

class InlineCommand(BaseCommand):
    def __init__(self, subcommands):
        BaseCommand.__init__(self, subcommands=subcommands)
        self.text="[INLINE]"

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
        processed_list = self._get_display_list(display_list_path)
        list.__init__(self, processed_list)

    def _get_display_list(self, display_list_path):
        commands = self._parse_display_list(display_list_path)
        print(repr(commands))
        return self._process_list(commands)

    def _parse_display_list(self, display_list_path):
        """
        Reads in a display list file and parses its contents.

        Config file format:
        Every line begins with a command, usually a display object such as
        a label or a widget. Following the command are parameters to the
        object on the same line.

        Some lines make up blocks of commands, which start with one command and
        are followed by indented lines, similar to a Python block. Much like
        Python, each line must be at the same indentation as the others in the
        block, with the block ending once a line at a previous indentation is
        reached.

        This format is still in the early stages and may undergo significant
        changes in the future. Hopefully Dave has not been an idiot and
        remembered to update this information.
        """

        list_file = open(display_list_path, 'r')
        root_block = []
        current_block = root_block
        last_indent=0
        sb = None
        for line in list_file:
            # Ignore comments
            if line.lstrip().startswith("#"):
                continue
            # Ignore blank lines
            if not line.strip():
                continue

            indent_level = len(line) - len(line.lstrip())
            if indent_level > last_indent:
                parent_block = current_block
                current_block = last_subcommands
                last_indent = indent_level

            command, *data = line.strip().split(None, 1)
            parameters = data[0] if len(data) > 0 else None

            # If the next line is indented, this becomes the next current_block
            last_subcommands = []
            current_block.append( (command, parameters, last_subcommands) )

#            self.append(VolumeInfo(data))
        return root_block

    def _process_list(self, parsed_config):
        current_list = []
        for command, data, subcommands in parsed_config:
            if command == 'text':
                current_list.append(TextCommand(data))
            elif command == 'inline':
                subcommands = self._process_list(subcommands)
                current_list.append(InlineCommand(subcommands))
            else:
                #TODO: Only do this if a debug variable is set, otherwise raise an error
                #TODO: Create a special 'error' metacommand for special display
                current_list.append(TextCommand("ERROR: unknown command {}".format(command)))
        return current_list

@app.route("/")
def hello():
    display_list = DisplayList("displaylist")

    return render_template('index.html', render_items=display_list)

if __name__ == "__main__":
    app.debug = True
    #TODO: Define port with command line option
    app.run(host='0.0.0.0', port=8080)
