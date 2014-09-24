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
            print(self.repl.correspond('val a = 1'))
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

    # def ensure_trailing_newline(self):
        # pass
        # eof = self.input_buf[-1]
        # if not eof.endswith('\n'):
        #     self.insert("\n", len(self.input_buf))

    def process_line(self, start):
        line_text = self.input_buf[start]
        if start != len(self.input_buf):
            self.set_status("Sending 1 line to REPL.")
            print(line_text)
            ret = self.repl.correspond(line_text)
            print(ret)
        else:
            self.cleanup()

    def queue_thread(self, thread, start):
        while self.handle_thread(thread, start):
            print('waiting')
            time.sleep(5)

    def handle_thread(self, thread, next_start):
        if thread.is_alive():
            self.set_status("Waiting for REPL.")
            return True
        else:
            self.handle_finished_thread(thread, next_start)
            return False

    def handle_finished_thread(self, thread, next_start):
        result = thread.result
        print(result)
        self.insert(str(result), next_start)
        next_start += len(result)
        if not result.terminates:
            self.process_line(next_start)
        else:
            self.cleanup()

    def insert(self, text, start):
        text = str(text)
        lines = text.count('\n') - 1
        self.output_buf.append(text, start)
        self.input_buf.append('\n'*lines, start)

    def set_status(self, msg, key="Worksheet"):
        print(key + ':' + msg)

    def error(self, msg):
        print(msg, file=sys.stderr)

    def cleanup(self):
        self.set_status('')
        try:
            self.repl.close()
        except repl.ReplCloseError as e:
            self.error("Could not close the REPL:\n" + str(e))

    def get_line(self, linenum):
        return self.input_buf[linenum]


class WorksheetEvalCommand(WorksheetCommand):
    def run(self):
        WorksheetCommand.run(self)
        self.process_line(0)


class WorksheetClearCommand(WorksheetCommand):
    def run(self):
        WorksheetCommand.run(self)
