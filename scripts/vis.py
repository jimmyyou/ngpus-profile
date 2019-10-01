import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.path import Path as mPath


def default_marker_begin():
    return mPath([
        (-0.5, 0.866),
        (0, 0),
        (0, 1.0),
        (0, -1.0),
        (0, 0),
        (-0.5, -0.866),
        (0, 0),
    ])


def default_marker_end():
    return mPath([
        (0.5, 0.866),
        (0, 0),
        (0, 1.0),
        (0, -1.0),
        (0, 0),
        (0.5, -0.866),
        (0, 0),
    ])


def figure_legend(fig, **kwargs):
    fig.legend(bbox_to_anchor=(0.5, 0.86), loc="lower center", **kwargs)
    fig.subplots_adjust(top=0.86)


def job_timeline(workers, begin, end, groupby=None, label=None,
              ax=None,
              marker_begin=None, marker_end=None,
              markersize=None,
              group_num=2, group_radius=.3):
    '''
        Args:
            workers: list
            begin: list
            end: list
            groupby: list
    '''
    if marker_begin is None:
        marker_begin = default_marker_begin()
    if marker_end is None:
        marker_end = default_marker_end()
    
    if int(group_num) <= 0:
        raise ValueError(f'group_num should be a positive integer, but got {group_num}')
    group_num = int(group_num)
    
    if groupby is None:
        if not len(workers) == len(begin) == len(end):
            raise ValueError('Length of workers, begin, end should be equal,'
                             f' but got ({len(workers)}, {len(begin)}, {len(end)})')
    else:
        if not len(workers) == len(begin) == len(end) == len(groupby):
            raise ValueError('Length of workers, begin, end, groupby should be equal,'
                             f' but got ({len(workers)}, {len(begin)}, {len(end)}, {len(groupby)})')

    # create y_pos according to workers, so workers doesn't has to be numeric
    y_values, y_pos = np.unique(workers, return_inverse=True)
    y_pos = y_pos.astype(np.float64)
    
    # adjust y_pos according to a wave like shape around original y_pos,
    # the offset should be changing based on the index within a particular y_value
    offset_pattern = np.concatenate([
        np.arange(0, group_num),
        np.arange(group_num, -group_num, step=-1),
        np.arange(-group_num, 0)
    ])
    for worker in y_values:
        mask = workers == worker
        l = len(workers[mask])
        offset = np.tile(offset_pattern, (l + len(offset_pattern) - 1) // len(offset_pattern))[:l]
        y_pos[mask] += offset * group_radius / group_num

    if ax is None:
        _, ax = plt.subplots()
    
    def draw_group(y, xmin, xmax, key=None):
        # cycle color
        c = next(ax._get_lines.prop_cycler)['color']
        # label
        if key is None:
            l = label
        else:
            l = (label or '{key}').format(key=key) if key is not None else l
        # draw lines
        ax.hlines(y, xmin, xmax, label=l, color=c)
        # draw markers
        ax.plot(xmin, y, color=c,
                marker=marker_begin, markersize=markersize,
                linestyle='None', fillstyle='none')
        ax.plot(xmax, y, color=c,
                marker=marker_end, markersize=markersize,
                linestyle='None', fillstyle='none')
    
    if groupby is None:
        draw_group(y_pos, begin, end)
    else:
        for grp_key in np.unique(groupby):
            mask = groupby == grp_key
            y = y_pos[mask]
            xmin = begin[mask]
            xmax = end[mask]
            draw_group(y, xmin, xmax, key=grp_key)
    
    # fix ticks to categorical
    ax.yaxis.set_major_formatter(mticker.IndexFormatter(y_values))
    
    # set a default title
    ax.set_ylabel('Worker')
    ax.set_xlabel('Time')

    return ax