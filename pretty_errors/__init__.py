import sys, re, colorama, os, time, linecache
colorama.init()


name = "pretty_errors"

FILENAME_COMPACT  = 0
FILENAME_EXTENDED = 1
FILENAME_FULL     = 2

reset_color = '\033[m'



class PrettyErrorsConfig():
    def __init__(self):
        self.line_length            = 0
        self.full_line_newline      = False
        self.filename_display       = FILENAME_COMPACT
        self.display_timestamp      = False
        try:
            self.timestamp_function = time.perf_counter
        except AttributeError:
            self.timestamp_function = time.time
        self.display_link           = False
        self.separator_character    = '-'
        self.line_number_first      = False
        self.top_first              = False
        self.always_display_bottom  = True
        self.stack_depth            = 0
        self.exception_above        = False
        self.exception_below        = True
        self.trace_lines_before     = 0
        self.trace_lines_after      = 0
        self.lines_before           = 0
        self.lines_after            = 0
        self.display_locals         = False
        self.display_trace_locals   = False
        self.truncate_locals        = True
        self.truncate_code          = False
        self.header_color           = '\033[1;30m'
        self.timestamp_color        = '\033[1;30m'
        self.line_color             = '\033[1;38m'
        self.code_color             = '\033[1;30m'
        self.filename_color         = '\033[1;36m'
        self.line_number_color      = '\033[1;32m'
        self.function_color         = '\033[1;34m'
        self.link_color             = '\033[1;30m'
        self.local_name_color       = '\033[1;35m'
        self.local_value_color      = '\033[m'
        self.local_len_color        = '\033[1;30m'
        self.exception_color        = '\033[1;31m'
        self.exception_arg_color    = '\033[1;33m'
        self.prefix                 = None
        self.infix                  = None
        self.postfix                = None
        self.whitelist_paths        = []
        self.blacklist_paths        = []
        self.reset_stdout           = False


    def configure(self, **kwargs):
        """Configure settings governing how exceptions are displayed."""
        for setting in kwargs:
            if kwargs[setting] is not None: setattr(self, setting, kwargs[setting])


config = PrettyErrorsConfig()
default_config = PrettyErrorsConfig()


def configure(
        always_display_bottom = None,
        code_color = None,
        display_link = None,
        display_locals = None,
        display_timestamp = None,
        display_trace_locals = None,
        exception_above = None,
        exception_arg_color = None,
        exception_below = None,
        exception_color = None,
        filename_color = None,
        filename_display = None,
        full_line_newline = None,
        function_color = None,
        header_color = None,
        infix = None,
        line_color = None,
        line_length = None,
        line_number_color = None,
        line_number_first = None,
        lines_after = None,
        lines_before = None,
        link_color = None,
        local_len_color = None,
        local_name_color = None,
        local_value_color = None,
        postfix = None,
        prefix = None,
        reset_stdout = None,
        separator_character = None,
        stack_depth = None,
        timestamp_color = None,
        timestamp_function = None,
        top_first = None,
        trace_lines_after = None,
        trace_lines_before = None,
        truncate_code = None,
        truncate_locals = None
        ):
    """Configure settings governing how exceptions are displayed."""
    config.configure(
        always_display_bottom  = always_display_bottom,
        code_color             = code_color,
        display_link           = display_link,
        display_locals         = display_locals,
        display_timestamp      = display_timestamp,
        display_trace_locals   = display_trace_locals,
        exception_above        = exception_above,
        exception_arg_color    = exception_arg_color,
        exception_below        = exception_below,
        exception_color        = exception_color,
        filename_color         = filename_color,
        filename_display       = filename_display,
        full_line_newline      = full_line_newline,
        function_color         = function_color,
        header_color           = header_color,
        infix                  = infix,
        line_color             = line_color,
        line_length            = line_length,
        line_number_color      = line_number_color,
        line_number_first      = line_number_first,
        lines_after            = lines_after,
        lines_before           = lines_before,
        link_color             = link_color,
        local_len_color        = local_len_color,
        local_name_color       = local_name_color,
        local_value_color      = local_value_color,
        postfix                = postfix,
        prefix                 = prefix,
        reset_stdout           = reset_stdout,
        separator_character    = separator_character,
        stack_depth            = stack_depth,
        timestamp_color        = timestamp_color,
        timestamp_function     = timestamp_function,
        top_first              = top_first,
        trace_lines_after      = trace_lines_after,
        trace_lines_before     = trace_lines_before,
        truncate_code          = truncate_code,
        truncate_locals        = truncate_locals
    )


def mono():
    global reset_color
    reset_color = ''
    configure(
        infix = '\n---\n',
        line_number_first = True,
        code_color = '| ',
        exception_arg_color = '',
        exception_color = '',
        filename_color = '',
        function_color = '',
        header_color = '',
        line_color = '> ',
        line_number_color = '',
        link_color = '',
        local_len_color = '',
        local_name_color = '= ',
        local_value_color = '',
        timestamp_color = '',
    )


def whitelist(*paths):
    """If the whitelist has any entries, then only files which begin with
    one of its entries will be included in the stack trace.
    """
    for path in paths:
        config.whitelist_paths.append(os.path.normpath(path).lower())


def blacklist(*paths):
    """Files which begin with a path on the blacklist will not be
    included in the stack trace.
    """
    for path in paths:
        config.blacklist_paths.append(os.path.normpath(path).lower())



def excepthook(exception_type, exception_value, traceback):
    "Replaces sys.excepthook to output pretty errors."


    def get_terminal_width():
        try:
            return os.get_terminal_size()[0]
        except Exception:
            return 79


    def get_line_length():
        if config.line_length == 0:
            return get_terminal_width()
        else:
            return config.line_length


    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')


    def visible_length(s):
        return len(ansi_escape.sub('', s))


    def output_text(texts):
        if not isinstance(texts, (list, tuple)):
            texts = [texts]
        count = 0
        for text in texts:
            text = str(text)
            sys.stderr.write(text)
            count += visible_length(text)
        line_length = get_line_length()
        if count == 0 or count % line_length != 0 or config.full_line_newline:
            sys.stderr.write('\n')
        sys.stderr.write(reset_color)
        if config.reset_stdout:
            sys.stdout.write(reset_color)


    def write_header():
        if not config.separator_character: return
        line_length = get_line_length()
        if config.display_timestamp:
            timestamp = str(config.timestamp_function())
            separator = (line_length - len(timestamp)) * config.separator_character + timestamp
        else:
            separator = line_length * config.separator_character
        output_text('')
        output_text([config.header_color, separator])


    def write_location(path, line, function):
        line_number = str(line) + ' '
        output_text('')
        if config.filename_display == FILENAME_FULL:
            filename = ""
            output_text([config.filename_color, path])
            output_text([config.line_number_color, line_number, config.function_color, function])
        else:
            if config.filename_display == FILENAME_EXTENDED:
                line_length = get_line_length()
                filename = path[-(line_length - len(line_number) - len(function) - 4):]
                if filename != path:
                    filename = '...' + filename
            else:
                filename = os.path.basename(path)
            if config.line_number_first:
                output_text([
                    config.line_number_color, line_number,
                    config.function_color,    function + ' ',
                    config.filename_color,    filename
                ])
            else:
                output_text([
                    config.filename_color,    filename + ' ',
                    config.line_number_color, line_number,
                    config.function_color,    function
                ])
        if config.display_link:
            output_text([config.link_color, '"%s", line %s' % (path, line)])


    def write_code(filepath, line, module_globals, is_final):
        if is_final:
            target_line = config.lines_before
            start = line - config.lines_before
            end   = line + config.lines_after
        else:
            target_line = config.trace_lines_before
            start = line - config.trace_lines_before
            end   = line + config.trace_lines_after

        if start < 1:
            target_line -= (1 - start)
            start = 1

        lines = []
        for i in range(start, end + 1):
            lines.append(linecache.getline(filepath, i, module_globals).rstrip())

        min_lead = 9999
        for line in lines:
            if line.strip() == '': continue
            c = 0
            while c < len(line) and line[c] in (' ', '\t'):
                c += 1
            if c < min_lead: min_lead = c
        if min_lead > 0:
            lines = [line[min_lead:] for line in lines]

        if config.truncate_code:
            line_length = get_line_length()

        for i, line in enumerate(lines):
            if i == target_line:
                color = config.line_color
            else:
                color = config.code_color
            prefix_length = visible_length(color)
            if config.truncate_code and len(line) + prefix_length > line_length:
                line = line[:line_length - prefix_length + 3] + '...'
            output_text([color, line])

        return '\n'.join(lines)


    def exception_name(exception):
        label = str(exception)
        if label.startswith("<class '"):
            label = label[8:-2]
        return label


    def write_exception(exception_type, exception_value):
        if exception_value and len(exception_value.args) > 0:
            output_text([
                config.exception_color, exception_name(exception_type), ':\n',
                config.exception_arg_color, '\n'.join((str(x) for x in exception_value.args))
            ])
        else:
            output_text([config.exception_color, exception_name(exception_type)])


    write_header()

    if config.prefix != None:
        sys.stderr.write(config.prefix)

    syntax_error_info = None
    if exception_type == SyntaxError:
        syntax_error_info = exception_value.args[1]
        exception_value.args = [exception_value.args[0]]

    if config.exception_above:
        output_text('')
        write_exception(exception_type, exception_value)

    if syntax_error_info:
        write_location(syntax_error_info[0], syntax_error_info[1], '')
        write_code(syntax_error_info[0], syntax_error_info[1], [], True)
    else:
        tracebacks = []
        while traceback != None:
            path = os.path.normpath(traceback.tb_frame.f_code.co_filename).lower()
            if traceback.tb_next == None or (config.always_display_bottom and tracebacks == []):
                tracebacks.append(traceback)
            else:
                if config.whitelist_paths:
                    for white in config.whitelist_paths:
                        if path.startswith(white): break
                    else:
                        traceback = traceback.tb_next
                        continue
                for black in config.blacklist_paths:
                    if path.startswith(black): break
                else:
                    tracebacks.append(traceback)
            traceback = traceback.tb_next

        if config.top_first:
            tracebacks.reverse()
            if config.stack_depth > 0:
                if config.always_display_bottom and len(tracebacks) > 1:
                    tracebacks = tracebacks[:config.stack_depth] + tracebacks[-1:]
                else:
                    tracebacks = tracebacks[:config.stack_depth]
            final = 0
        else:
            if config.stack_depth > 0:
                if config.always_display_bottom and len(tracebacks) > 1:
                    tracebacks = tracebacks[:1] + tracebacks[-config.stack_depth:]
                else:
                    tracebacks = tracebacks[-config.stack_depth:]
            final = len(tracebacks) - 1

        for count, traceback in enumerate(tracebacks):
            if config.infix != None and count != 0:
                sys.stderr.write(config.infix)

            frame = traceback.tb_frame
            code = frame.f_code
            write_location(code.co_filename, traceback.tb_lineno, code.co_name)
            code_string = write_code(code.co_filename, traceback.tb_lineno, frame.f_globals, count == final)

            if (config.display_locals and count == final) or (config.display_trace_locals and count != final):
                local_variables = [(code_string.find(x), x) for x in frame.f_locals]
                local_variables.sort()
                local_variables = [x[1] for x in local_variables if x[0] >= 0]
                if local_variables:
                    output_text('')
                    spacer = ': '
                    len_spacer = '... '
                    line_length = get_line_length()
                    for local in local_variables:
                        value = str(frame.f_locals[local])
                        output = [config.local_name_color, local, spacer, config.local_value_color]
                        if config.truncate_locals and len(local) + len(spacer) + len(value) > line_length:
                            length = '[' + str(len(value)) + ']'
                            value = value[:line_length - (len(local) + len(spacer) + len(len_spacer) + len(length))]
                            output += [value, len_spacer, config.local_len_color, length]
                        else:
                            output += [value]
                        output_text(output)

    if config.exception_below:
        output_text('')
        write_exception(exception_type, exception_value)

    if config.postfix != None:
        sys.stderr.write(config.postfix)


sys.excepthook = excepthook



def install(find = False, add_to_user = False, add_to_site = False, pth = False, path = None):
    """Install pretty_errors so that it is imported whenever you run a python file."""
    import re, site
    check = re.compile(r'^\s*import\s+\bpretty_errors\b', re.MULTILINE)

    def readfile(path):
        try:
            return ''.join((x for x in open(path)))
        except IOError:
            return ''

    def find_install(quiet = False):
        found = False
        for path in site.getsitepackages() + [site.getusersitepackages()]:
            for filename in 'usercustomize.py', 'sitecustomize.py', 'pretty_errors.pth':
                filepath = os.path.join(path, filename)
                if check.search(readfile(filepath)):
                    if not found:
                        print('\npretty_errors found in:')
                        found = True
                    print(filepath)
        if not found and not quiet:
            print('\npretty_errors not currently installed in any expected locations.')
        return found

    if find:
        find_install()
        return

    if add_to_user:
        path = site.getusersitepackages()
        filename = 'pretty_errors.pth' if pth else 'usercustomize.py'
    elif add_to_site:
        path = site.getsitepackages()[0]
        filename = 'pretty_errors.pth' if pth else 'sitecustomize.py'
    else:

        def get_choice(query, choices, default = None):
            options = {}
            for i in range(len(choices)):
                options[str(i + 1)] = i
            while True:
                print()
                print(' ' + query)
                print()
                for option, choice in enumerate(choices):
                    print('%d: %s' % ((option + 1), choice))
                print('0: Exit')
                if default is None:
                    print('\nOption: ', end='')
                else:
                    print('\nOption: [default: %d] ' % (default + 1), end='')
                choice = input()
                if choice == '' and default is not None:
                    choice = str(default + 1)
                if choice == '0':
                    sys.exit(0)
                elif choice in options:
                    return options[choice]

        print("""\
To have pretty_errors be used when you run any python file you may add it to your \
usercustomize.py (user level) or sitecustomize.py (system level), or to pretty_errors.pth.

(just hit <enter> to accept the defaults if you are unsure)
 """)

        found = find_install(True)

        paths = site.getsitepackages() + [site.getusersitepackages()]
        path = paths[get_choice('Choose folder to install into:', paths, -1 if found else len(paths) - 1)]

        filenames = ['usercustomize.py', 'sitecustomize.py', 'pretty_errors.pth']
        filename = filenames[get_choice('Choose file to install into:', filenames, 0)]

        if filename.endswith('.pth'):
            output = (os.path.dirname(os.path.dirname(os.path.normpath(__file__))) +
                '\nimport pretty_errors; ' +
                '#pretty_errors.configure()  ' +
                '# keep on one line, for options see ' +
                'https://github.com/onelivesleft/PrettyErrors/blob/master/README.md'
            )
        else:
            output = []
            output.append('''

###########################################################################

# pretty-errors package to make exception reports legible.
import pretty_errors

# Use if you do not have a color terminal:
#pretty_errors.mono()

# Use to hide frames whose file begins with these paths:
#pretty_errors.blacklist('/path/to/blacklist', '/other/path/to/blacklist', ...)

# Use to only show frames whose file begins with these paths:
#pretty_errors.whitelist('/path/to/whitelist', '/other/path/to/whitelist', ...)

# Use to configure output:
"""pretty_errors.configure(
    ''')

            options = []
            colors = []
            parameters = []
            max_length = 0
            for option in dir(config):
                if len(option) > max_length:
                    max_length = len(option)
                if (option not in ('configure', 'mono', 'whitelist_paths', 'blacklist_paths') and
                        not option.startswith('_')):
                    if option.endswith('_color'):
                        colors.append(option)
                    else:
                        options.append(option)
            for option in sorted(options):
                if option == 'filename_display':
                    parameters.append('    ' + option.ljust(max_length) + ' = pretty_errors.FILENAME_COMPACT,  # FILENAME_EXTENDED | FILENAME_FULL')
                elif option == 'timestamp_function':
                    parameters.append('    ' + option.ljust(max_length) + ' = time.perf_counter')
                else:
                    parameters.append('    ' + option.ljust(max_length) + ' = ' + repr(getattr(config, option)))
            for option in sorted(colors):
                parameters.append('    ' + option.ljust(max_length) + ' = ' + repr(getattr(config, option)))

            output.append(',\n'.join(parameters))
            output.append(')"""\n')
            output.append('###########################################################################\n')
            output = '\n'.join(output)

        print('\n--------------')

    filepath = os.path.join(path, filename)
    if check.search(readfile(filepath)):
        print('\npretty_errors already present in:\n\n ' + filepath +
            '\n\nEdit it to set config options.\n')
        return

    try:
        os.makedirs(path)
    except Exception:
        pass
    try:
        out = open(filepath, 'a')
        out.write(output)
        out.close()
    except Exception:
        print('\nFailed to write to:\n' + filepath)
    else:
        print('\npretty_errors added to:\n\n %s\n\nEdit it to set config options.\n' % filepath)



if __name__ == "__main__":
    configure(
        lines_after=1, lines_before=1,
        trace_lines_after=1, trace_lines_before=1,
        display_locals=True,
        postfix='\n'
    )
    mono()
    raise KeyError("Testing testing")
