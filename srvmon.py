#!/usr/bin/env python3

import os
from collections import namedtuple
from flask import Flask, render_template
app = Flask(__name__)

class BaseCommand:
    def __init__(self, subcommands=[]):
        self.subcommands = subcommands
        self.text=""
        self.classes = []

class TextCommand(BaseCommand):
    """Display list command that simply prints a string."""
    def __init__(self, text):
        BaseCommand.__init__(self)
        self.text = text

class InlineCommand(BaseCommand):
    def __init__(self, subcommands):
        BaseCommand.__init__(self, subcommands=subcommands)
        self.classes = ['inlinecontents']

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

#TODO: Test setup, properly handle display list functions
def volume_free_space(volume):
    return VolumeInfo(volume).free_space

displaylist_functions = {'VolumeFreeSpace': volume_free_space}

class DisplayList(list):
    def __init__(self, display_list_path):
        processed_list = self._get_display_list(display_list_path)
        list.__init__(self, processed_list)

    def _get_display_list(self, display_list_path):
        commands = self._parse_display_list(display_list_path)
        #print(repr(commands))
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

        ParsedCommand = namedtuple('ParsedCommand', ['command', 'arguments', 'subcommands'])
        IndentStackItem = namedtuple('IndentStackItem', ['indent_level', 'block'])

        list_file = open(display_list_path, 'r')

        #TODO: assumes first line has no indent, will break if not true
        root_block = current_block = []
        indent_stack = [ IndentStackItem(0, current_block) ]

        for line in list_file:
            # Ignore comments
            if line.lstrip().startswith("#"):
                continue
            # Ignore blank lines
            if not line.strip():
                continue

            indent_level = len(line) - len(line.lstrip())
            last_indent = indent_stack[-1].indent_level
            if indent_level > last_indent:
                current_block = indent_stack[-1].block[-1].subcommands
                indent_stack.append( IndentStackItem(indent_level, current_block) )
            elif indent_level < last_indent:
                while True:
                    indent_stack.pop()
                    if indent_level == indent_stack[-1].indent_level:
                        current_block = indent_stack[-1].block
                        break
                #TODO: exception is raised here if a matching indent level is
                # not found. This is a malformed config file, catch and show error

            command, *data = line.strip().split(None, 1)
            if data:
                parameters = self._parse_command_arguments(data[0])
            else:
                parameters = None

            current_block.append( ParsedCommand(command, parameters, []) )

        return root_block

    def _parse_command_arguments(self, argumentstring):
        """Parsed the argments given to a command"""
        ParsedArgument = namedtuple('ParsedArgument', ['type', 'value', 'funcargs'])
        arguments = []
        #TODO: do this right
        if '(' in argumentstring:
            funcargs = argumentstring.split('(')[1].split(')')[0]
            arguments.append(ParsedArgument('function', 'VolumeFreeSpace', [funcargs]))
        else:
            arguments.append(ParsedArgument('string', argumentstring, []))
        return arguments

    def _process_list(self, parsed_config):
        current_list = []
        for command, arguments, subcommands in parsed_config:
            # Preprocess function arguments
            if arguments:
                arg = arguments[0]
                processed_args = []
                if arg.type == 'function':
                    processed_args.append(displaylist_functions[arg.value](arg.funcargs[0]))
                else:
                    processed_args.append(arg.value)
            # Process command
            if command == 'text':
                current_list.append(TextCommand(processed_args[0]))
            elif command == 'inline':
                processed_commands = self._process_list(subcommands)
                current_list.append(InlineCommand(processed_commands))
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
