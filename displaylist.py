"""Code for working with display lists"""

import re
from collections import namedtuple

import sysinfo
import datafilters

class DisplayListCommand:
    def __init__(self, command_name, contents="", css_classes=[], subcommands=[]):
        self.name = command_name
        self.subcommands = subcommands
        self.contents = contents
        self.css_classes = css_classes

class DisplayList(list):
    def __init__(self, display_list_path):
        processed_list = self._get_display_list(display_list_path)
        list.__init__(self, processed_list)

    def _get_display_list(self, display_list_path):
        commands = self._parse_display_list(display_list_path)
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
        ParsedArgument = namedtuple('ParsedArgument', ['type', 'value', 'funcargs', 'filter'])
        arguments = []

        # Pattern matching commas not inside of quotes or parentheses.
        # Explanation:
        #  (?=(?:(?:[^"]*"){2})*[^"]*$) - Lookahead matching an even number of quotes
        #  (?![^()]*\)) - Negative lookahead matching non-parens ending with a ')'
        # This will break with nested parentheses; for now, they are not
        # supported. If it is needed in the future, regexes will not work here.
        commapattern = ',(?=(?:(?:[^"]*"){2})*[^"]*$)(?![^()]*\))'
        rawargs = re.split(commapattern, argumentstring)
        for full_arg in rawargs:
            #TODO: Use a regex to split '|' like above
            arg, *arg_filter = full_arg.strip().split('|')
            arg_filter = arg_filter[0] if arg_filter != [] else None
            # If argument is a function
            if '(' in arg:
                #TODO: handle multiple arguments to functions
                funcname = argumentstring.split('(')[0].strip()
                funcargs = argumentstring.split('(')[1].split(')')[0]
                arguments.append(ParsedArgument('function', funcname, [funcargs], arg_filter))
            else:
                #TODO: This will not work right once escaped characters are added
                clean_arg = arg.strip().strip('"')
                arguments.append(ParsedArgument('string', clean_arg, [], arg_filter))

        return arguments

    def _process_list(self, parsed_config):
        current_list = []
        for command, arguments, subcommands in parsed_config:
            # Preprocess function arguments
            if arguments:
                arg = arguments[0]
                processed_args = []
                if arg.type == 'function':
                    value = sysinfo.displaylist_functions[arg.value](arg.funcargs[0])
                else:
                    value = arg.value

                if arg.filter:
                    value = datafilters.output_filters[arg.filter](value)

                processed_args.append(value)
            # Process command
            command_name = command
            contents = ""
            classes = []
            processed_subcommands = []
            if command == 'text':
                contents = processed_args[0]
            elif command == 'inline':
                processed_subcommands = self._process_list(subcommands)
                classes = ['inlinecontents']
            else:
                #TODO: Only do this if a debug variable is set, otherwise raise an error
                #TODO: Add formatting to errors in output
                command_name = 'error'
                contents = "ERROR: unknown command {}".format(command)
            processed_command = DisplayListCommand(command_name,
                                                   contents=contents,
                                                   css_classes=classes,
                                                   subcommands=processed_subcommands)
            current_list.append(processed_command)
        return current_list
