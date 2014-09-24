from __future__ import print_function
import vim
import os
import sys
import time
PY3K = sys.version_info >= (3, 0, 0)
if PY3K:
    from . import repl
else:
    import repl
    import repl_setting

if sys.platform != 'win32':
    # Make sure /usr/local/bin is on the path
    exec_path = os.getenv('PATH', '').split(os.pathsep)
    if "/usr/local/bin" not in exec_path:
        os.environ["PATH"] = os.pathsep.join(exec_path + ["/usr/local/bin"])


class WorksheetCommand():
    def __init__(self, input_buf, output_buf):
        self.input_buf = vim.buffers[input_buf]
        self.output_buf = vim.buffers[output_buf]

    def run(self):
        self.load_settings()
        try:
            language = self.get_language()
            default_def = self.get_repl_settings()
            repl_defs = self.settings.get("worksheet_languages")
            project_repl_defs = self.project_settings.\
                get("worksheet_languages", {})
            proj_def = project_repl_defs.\
                get(language, repl_defs.get(language, {})).items()
            repl_def = dict(list(default_def) + list(proj_def))
            self.prefix = repl_def.get('prefix')
            filename = self.input_buf.name
            if filename is not None:
                repl_def["cwd"] = os.path.dirname(filename)
            self.repl = repl.get_repl(language, repl_def)
        except repl.ReplStartError as e:
            self.error(str(e))
            return
        self.remove_previous_results()

    def load_settings(self):
        self.settings = repl_setting.default_setting
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
        for num, line in enumerate(output_buf):
            if len(line) and len(input_buf[num]) == 0:
                output_buf[num] = None
                input_buf[num] = None

    def make_sheet(self):
        line = 0
        input_buf = self.input_buf
        while line < len(input_buf):
            source = input_buf[line]
            ret = self.repl.correspond(source)
            output = str(ret).strip()
            self.insert(output, line)
            if ret.terminates:
              self.cleanup()
              break
            line += output.count('\n') + 1

    def insert(self, text, start):
        text = str(text)
        extra_lines = text.count('\n')
        if extra_lines:
            vim.command(
                '{0} normal {1}o'.format(start, extra_lines),
            )
        print('the out put is: ' + text)
        print('has extra_lines: ' + str(extra_lines))
        for i, t in enumerate(text.split('\n')):
          self.output_buf.append(t, start+i)

    def set_status(self, msg, key="Worksheet"):
        vim.command('echo "' + key + ':' + msg+ '"')

    def error(self, msg):
        print(msg, file=sys.stderr)

    def cleanup(self):
        self.set_status('')
        try:
            self.repl.close()
        except repl.ReplCloseError as e:
            self.error("Could not close the REPL:\n" + str(e))


class WorksheetEvalCommand(WorksheetCommand):
    def run(self):
        WorksheetCommand.run(self)
        self.make_sheet()
        self.cleanup()

class WorksheetClearCommand(WorksheetCommand):
    def run(self):
        WorksheetCommand.run(self)
