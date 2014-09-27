from __future__ import print_function
import vim
import os
import sys
PY3K = sys.version_info >= (3, 0, 0)
if PY3K:
    from . import repl
else:
    import repl
    str = unicode

if sys.platform != 'win32':
    # Make sure /usr/local/bin is on the path
    exec_path = os.getenv('PATH', '').split(os.pathsep)
    if "/usr/local/bin" not in exec_path:
        os.environ["PATH"] = os.pathsep.join(exec_path + ["/usr/local/bin"])


def compatible_dict(vim_dict):
    # vim will pass int as string to python
    def vbool(string):
        return bool(int(string))

    for key, value in vim_dict.items():
        if key == 'timeout':
            vim_dict[key] = int(value)
        elif key == 'strip_echo':
            if isinstance(value, dict):
                vim_dict[key] = {k: vbool(v) for k, v in value.items()}
            else:
                vim_dict[key] = vbool(value)
        elif isinstance(value, dict):
            vim_dict[key] = compatible_dict(value)
    return vim_dict

# store source_buffer_id => WorksheetCommand
Cache = {}
default_setting = vim.eval('g:worksheet_repl_setting')
default_setting = compatible_dict(default_setting)


class WorksheetCommand():
    def __init__(self, input_buf, output_buf):
        self.input_buf = vim.buffers[input_buf]
        self.output_buf = vim.buffers[output_buf]
        self.load_settings()
        Cache[input_buf] = self

    def prepare(self):
        try:
            language = self.get_language()
            default_def = self.get_repl_settings()
            repl_defs = self.settings.get("worksheet_languages")
            project_repl_defs = self.project_settings.\
                get("worksheet_languages", {})
            proj_def = project_repl_defs.\
                get(language, repl_defs.get(language, {})).items()
            repl_def = dict(list(default_def) + list(proj_def))
            repl_def['prefix'] = ''
            filename = self.input_buf.name
            if filename is not None:
                repl_def["cwd"] = os.path.dirname(filename)
            self.repl = repl.get_repl(language, repl_def)
        except repl.ReplStartError as e:
            self.error(str(e))
            return
        self.remove_previous_results()

    def load_settings(self):
        self.settings = default_setting
        self.timeout = self.settings.get('worksheet_timeout')

    def get_repl_settings(self):
        default_def = self.settings.get("worksheet_defaults")
        if not hasattr(self, "project_settings"):
            self.project_settings = {}
        project_def = self.project_settings.get("worksheet_defaults", {})
        settings = []
        for key, setting in default_def.items():
            settings.append((key, project_def.get(key, setting)))
        return settings

    def get_language(self):
        return vim.eval('&ft').lower()

    def remove_previous_results(self):
        input_buf = self.input_buf
        output_buf = self.output_buf
        num = 0
        for line in output_buf:
            if num >= len(input_buf):
                break
            if len(line) and len(input_buf[num]) == 0:
                input_buf[num] = None
            else:
                num += 1
        output_buf[:] = None

    def make_sheet(self):
        self.remove_previous_results()
        self.prepare()
        input_buf = self.input_buf
        line = 0
        while line < len(input_buf):
            source = input_buf[line]
            ret = self.repl.correspond(source)
            output = str(ret).strip()
            self.insert(output, line)
            if ret.terminates:
                self.cleanup()
                break
            line += output.count('\n') + 1
        # remove initial white line
        self.output_buf[-1] = None
        self.cleanup()

    def insert(self, text, start):
        text = str(text)
        extra_lines = text.count('\n')
        if extra_lines:
            vim.command(
                '{0} normal {1}o'.format(start, extra_lines),
            )
        for i, t in enumerate(text.split('\n')):
            self.output_buf.append(t, start+i)

    def set_status(self, msg, key="Worksheet"):
            vim.command('echo "' + key + ':' + msg + '"')

    def error(self, msg):
        print(msg, file=sys.stderr)

    def cleanup(self):
        try:
            self.repl.close()
        except repl.ReplCloseError as e:
            self.error("Could not close the REPL:\n" + str(e))

    def end_session(self):
        self.cleanup()
        self.remove_previous_results()
        bufnum = self.output_buf.number
        vim.command('bd! %d' % bufnum)
        del Cache[self.input_buf.number]


class WorksheetEvalCommand(WorksheetCommand):
    def run(self):
        WorksheetCommand.prepare(self)
        self.make_sheet()
        self.cleanup()


class WorksheetClearCommand(WorksheetCommand):
    def run(self):
        WorksheetCommand.prepare(self)
