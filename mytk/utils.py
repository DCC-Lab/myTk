def package_app_script(filepath=None):
    from inspect import currentframe, getframeinfo

    frameinfo = getframeinfo(currentframe())

    script = ""
    with open(__file__, "r") as file:
        lines = file.readlines()
        embeddable_lines = lines[: frameinfo.lineno - 3]
        script += "".join(embeddable_lines)

    if filepath is not None:
        with open(filepath, "r") as file:
            lines = file.readlines()
            embeddable_lines = [
                line
                for line in lines
                if "from mytk import *" not in line and "app_script" not in line
            ]
            script += "".join(embeddable_lines)
    try:
        import pyperclip

        pyperclip.copy(script)
    except:
        pass
