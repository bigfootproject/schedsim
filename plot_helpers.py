from itertools import cycle

import matplotlib


def config_paper(font_size=22):
    matplotlib.rc('font', **{'family': 'serif', 'serif': ['Palatino']})
    matplotlib.rc('text', usetex=True)
    if font_size:
        # 22 looks good for IEEE double-column figures
        matplotlib.rcParams.update({'font.size': font_size})

line_styles = "- -- -. :".split()


def cycle_styles(marker=''):
    return cycle(s + marker for s in line_styles)
