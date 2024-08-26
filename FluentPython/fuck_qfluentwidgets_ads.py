import builtins


def do():
    BLOCK_CONTENT_ALERT = "\n\033[1;33m📢 Tips:\033[0m QFluentWidgets Pro is now released. Click \033[1;96mhttps://qfluentwidgets.com/pages/pro\033[0m to learn more about it.\n"

    old_print = builtins.print

    def new_print(*args, **kwargs):
        if len(args) == 1 and args[0] == BLOCK_CONTENT_ALERT:
            return
        old_print(*args, **kwargs)

    builtins.print = new_print

    return True
