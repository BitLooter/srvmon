"""Code for working with display lists"""

import re
from collections import namedtuple

import sysinfo
import datafilters

IndentStackItem = namedtuple('IndentStackItem', ['indent_level', 'block'])
ParsedCommand = namedtuple('ParsedCommand', ['command', 'arguments', 'subcommands'])
ParsedArgument = namedtuple('ParsedArgument', ['type', 'value', 'funcargs', 'filter'])


class DisplayListCommand:
    def __init__(self, command_name, contents="", css_classes=[], subcommands=[]):
        self.name = command_name
        self.subcommands = subcommands
        self.contents = contents
        self.css_classes = css_classes

    def __str__(self):
        return "{}: {}{}".format(self.name,
                                 self.contents if self.contents else "<No contents>",
                                 " [Subcommands]" if self.subcommands else "")

class DisplayList(list):
    def __init__(self, display_list_path):
        self.variables = {}
        # Stores the parsed widgets, are processed when used
        self.widgets = {}

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

        list_file = open(display_list_path, 'r')

        #TODO: assumes first line has no indent, will break if not true
        root_block = current_block = []
        indent_stack = [ IndentStackItem(0, current_block) ]

        for line in list_file:
            # Ignore comments
            if line.lstrip().startswith('#'):
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

            line = line.strip()
            # If a variable assignment
            if line.startswith('$'):
                # Lines starting with '$' are a shortcut for setvariable
                # We will simply reformat the line for regular processing
                #TODO: check that the line is properly formatted
                #TODO: currently treats value as raw text, handle functions
                varname, varvalue = line.split('=', 1)
                varname = varname.strip().lstrip('$')
                line = "{} {}, {}".format('setvariable', varname, varvalue)

            command, *data = line.split(None, 1)
            if data:
                parameters = self._parse_command_arguments(data[0])
            else:
                parameters = []

            current_block.append( ParsedCommand(command, parameters, []) )

        return root_block

    def _parse_command_arguments(self, argumentstring):
        """Parsed the argments given to a command"""
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
            arg_filter = arg_filter[0].strip() if arg_filter != [] else None
            # If argument is a function
            if '(' in arg:
                #TODO: handle multiple arguments to functions
                # This will not properly handle nested function calls
                funcname = arg.split('(')[0].strip()
                funcargs = arg.split('(')[1].split(')')[0].strip()
                parsed_funcargs = self._parse_command_arguments(funcargs)
                arguments.append(ParsedArgument('function', funcname, parsed_funcargs, arg_filter))
            else:
                #TODO: This will not work right once escaped characters are added
                clean_arg = arg.strip().strip('"')
                arguments.append(ParsedArgument('string', clean_arg, [], arg_filter))
        return arguments

    def _process_list(self, parsed_config):
        """
        Takes a parsed display list and turns it into a list of DisplayListCommand

        This function calls itself to handle subcommand lists.
        """
        current_list = []
        for command, arguments, subcommands in parsed_config:
            # Preprocess command arguments - reduce all arguments to strings
            processed_args = []
            for arg in arguments:
                if arg.type == 'function':
                    call_func = sysinfo.displaylist_functions[arg.value]
                    call_args = [self._substitute_strings(x.value) for x in arg.funcargs]
                    value = call_func(*call_args)
                elif arg.type == 'string':
                    value = self._substitute_strings(arg.value)
                else:
                    #TODO: unkown argument type, raise an error
                    pass

                if arg.filter:
                    value = datafilters.output_filters[arg.filter](value)

                processed_args.append(value)
            processed_args = [str(a) for a in processed_args]
            # Process command
            command_name = command
            contents = ""
            classes = []
            processed_subcommands = []
            if command == 'text':
                #TODO: might need to tweak this when keyword args are added
                contents = " ".join(processed_args)
            elif command == 'inline':
                processed_subcommands = self._process_list(subcommands)
                classes = ['inlinecontents']
            elif command == 'setvariable':
                varname, varvalue = processed_args
                self.variables['$'+varname] = varvalue
                # This is not a rendered command, skip to the next
                continue
            elif command == 'widget':
                self.widgets[processed_args[0]] = subcommands
                # This is not a rendered command, skip to the next
                continue
            elif command in self.widgets:
                command_name = 'renderedwidget'
                processed_subcommands = self._process_list(self.widgets[command])
            else:
                #TODO: Only do this if a debug variable is set, otherwise raise an error
                command_name = 'error'
                contents = "ERROR: unknown command {}".format(command)
                classes = ['errormessage']
            processed_command = DisplayListCommand(command_name,
                                                   contents=contents,
                                                   css_classes=classes,
                                                   subcommands=processed_subcommands)
            current_list.append(processed_command)
        return current_list

    def _substitute_strings(self, string):
        """Performs string substitution"""
        while '$' in string:
            varname = re.search('\$\w*', string).group()
            if varname in self.variables:
                varvalue = self.variables[varname]
            else:
                #TODO: raise an error if the variable doesn't exist
                pass
            string = string.replace(varname, varvalue)
        return string
