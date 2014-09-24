default_setting = {
    "worksheet_defaults": {
        "timeout": 10,
        "ignore": [],
        "prefix": "// > ",
        "error": ["[A-Z][a-z]+Error:"],
        "strip_echo": {
            "windows": False,
            "osx": True,
            "linux": True
        }
    },
    "worksheet_languages": {
        "elixir": {
            "cmd": "iex",
            "prompt": ["iex\\([\\d]+\\)> ", "\\.\\.\\.\\([\\d]+\\)> "],
            "prefix": "# > ",
            "error": ["\\*\\* \\([A-Z][a-zA-Z]+Error\\)"]
        },
        "javascript": {
            "cmd": "node -e \"require('repl').start('node> ')\"",
            "prompt": ["node> ", "\\.\\.+ "],
            "ignore": ["^\\n"]
        },
        "perl": {
            "cmd": "re.pl --rcfile=\"{repl_base}/perl/perl.rc\" --profile Minimal",
            "prompt": [">>> "],
            "prefix": "# > ",
            "error": ["[A-Z][a-z]+error:"]
        },
        "php": {
            "cmd": "php -a",
            "prompt": ["(php|>>>) [>{\\('\"] "],
            "error": ["PHP Parse error:", "PHP Fatal error"],
            "ignore": ["<\\?php", "\\?>"]
        },
        "python": {
            "cmd": "python -i",
            "prompt": [">>> ", "\\.\\.+ "],
            "prefix": "# > ",
            "error": ["Traceback ", "  File \"<stdin>\","]
        },
        "racket": {
            "cmd": "guile",
            "prompt": ["guile>"],
            "prefix": ";; > ",
            "error": ["ERROR:"],
            "ignore": ["^[\\s]*\n", "^[\\s]*;;"]
        },
        "ruby": {
            "cmd": {
                "windows": "irb.bat --prompt simple",
                "linux": "irb --prompt simple",
                "osx": "irb --prompt simple"
            },
            "prompt": [">> ", "\\?>"],
            "prefix": "# =",
            "strip_echo": True
        },
        "scala": {
            "cmd": {
                "windows": "scala.bat -i",
                "linux": "scala",
                "osx": "scala"
            },
            "prompt": ["scala> ", "     \\| "],
            "error": ["<console>:[0-9]+: error:"],
            "env": {
                "windows": {"EMACS": 1}
            }
        }
    }
}
