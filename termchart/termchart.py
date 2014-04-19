#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Termchart - plot live charts in your terminal
import math
import argparse

__appname__ = 'termchart'
__version__ = "0.1"
__author__ = "Stéphane Deraco <stephane@deraco.fr>"
__licence__ = "GPL"

import sys
import os
import curses

LEFT_MARGIN = 8
BOTTOM_MARGIN = 2


def main(options):
    """
    Retrieve the channel containing the data, and call curses to do the drawing
    :param options: arguments passed to the program
    """

    # There are some problems reading data coming from pipe (stdin) and curses that wants to write on the tty.
    # We cheat by duplicating the file descriptor of stdin to 9 ...
    os.dup2(sys.stdin.fileno(), 9)
    fd9 = os.fdopen(9)

    # ... and duplicating the file descriptor of the tty to 0.
    ftty = open("/dev/tty")
    os.dup2(ftty.fileno(), 0)

    # We then pass the file descriptor 9 (so stdin) to curses
    curses.wrapper(curses_work, fd9, options)
    fd9.close()
    ftty.close()


def curses_work(scr, fd9, options):
    """
    Do the curses work: retrieve size of terminal, get date, and call method to draw
    :param scr: the curses screen
    :param fd9: file descriptor of data input
    :param options: arguments passed to the program
    """

    # Some cleanup
    scr.erase()
    scr.border(0)
    scr.refresh()

    # Terminal and chart size
    terminal_height, terminal_width = scr.getmaxyx()
    graph_width, graph_height = (terminal_width - LEFT_MARGIN, terminal_height - BOTTOM_MARGIN)

    # 'data' array will contain all the data to be drawn. The data is rolling: when the number of date is greater than
    # what can be drawned, then the data at the beginning is dropped.
    data = []

    while 1:
        try:
            # Get data from input
            line = fd9.readline()
        except KeyboardInterrupt:
            break

        if not line:
            break

        val = line.strip()

        try:
            # Note: date must be a valid Python number
            y = float(val)

            # We have our new value, we redraw everythin
            scr.erase()
            plot_border(scr, terminal_width, terminal_height)
            scr.addstr(0, LEFT_MARGIN + 1, "Last value: %9.4G" % y)
            update_data(data, y, graph_width)
            plot(scr, data, graph_height)
            scr.refresh()
        except ValueError:
            # If the source data cannot be parsed as a Python float, then nothing is done: no data is drawn.
            pass

    if options.keep:
        # By default, the chart stays displyed at the end (otherwise, it disappears). This can be changed with the
        # '--no-keep' option
        scr.getch()


def plot_border(scr, terminal_width, terminal_height):
    """
    Plot the border of the chart
    :param scr: the curses screen
    :param terminal_width: width of termminal
    :param terminal_height: height of terminal
    """

    # Top line
    scr.hline(0, LEFT_MARGIN + 1, curses.ACS_HLINE, terminal_width - LEFT_MARGIN - 2)

    # Bottom line
    scr.hline(terminal_height - BOTTOM_MARGIN, LEFT_MARGIN + 1, curses.ACS_HLINE, terminal_width - LEFT_MARGIN - 2)

    # Left line
    scr.vline(1, LEFT_MARGIN, curses.ACS_VLINE, terminal_height - BOTTOM_MARGIN - 1)

    # Right line
    scr.vline(1, terminal_width - 1, curses.ACS_VLINE, terminal_height - BOTTOM_MARGIN - 1)

    # Corners
    scr.addch(0, LEFT_MARGIN, curses.ACS_ULCORNER)
    scr.addch(0, terminal_width - 1, curses.ACS_URCORNER)
    scr.addch(terminal_height - BOTTOM_MARGIN, LEFT_MARGIN, curses.ACS_LLCORNER)
    scr.addch(terminal_height - BOTTOM_MARGIN, terminal_width - 1, curses.ACS_LRCORNER)


def update_data(data, val, width):
    """
    Update the array containing data to plot. When the number of elements in the array is greater than the terminal
    size minus margin, then the first elements are discarded until all the elements can be plotted.

    :param data: the array containing the date to be plotted
    :param val: the new element to add to the array
    :param width: the width of the chart (terminal width minus left margin)
    """
    data.append(val)

    # We check with 'width - 2' because of the border left and right
    while len(data) > width - 2:
        data.pop(0)


def plot(scr, data, graph_height):
    """
    Do the plot of the chart on the terminal
    :param scr: the curses screen
    :param data: data to be drawn
    :param graph_height: height of graph
    """

    # Get min and max values
    (min_y, max_y) = (min(data), max(data))
    if min_y == max_y:
        # In case of min == max, then we force them to be different, and the date will be in the middle
        min_y -= 1
        max_y += 1

    x = 1
    for d in data:
        # Get the value in the Y axis coordinate
        y = linear_interpolation(max_y, 1, min_y, graph_height - 1, d)
        y_pos = int(y + 0.5)

        # Plot a bar chart
        plot_bar(scr, y_pos, x, graph_height)
        x += 1

    # Plot the legend no the left axis
    plot_y_axis(scr, min_y, max_y, graph_height)


def plot_y_axis(scr, min_y, max_y, graph_height):
    """
    Plot the legend of the left axis. Algorithm inspirated by:
    http://stackoverflow.com/questions/8506881/nice-label-algorithm-for-charts-with-minimum-ticks

    :param scr:
    :param data:
    :param min_y:
    :param max_y:
    :param graph_height:
    """

    # By default, we roughly display HEIGHT / 5 ticks
    n_ticks = int(graph_height / 5 + 0.5)

    for i in range(0, n_ticks):
        # j is the Y coordinate of the tick
        j = int(linear_interpolation(0, 1, n_ticks - 1, graph_height - 1, i))

        # v is the Y value associated at this Y coordinate
        v = linear_interpolation(0, max_y, n_ticks - 1, min_y, i)

        # Display this value
        scr.addstr(j, 0, "%s" % format_number(v, 7))


def nice_num(rge, rnd):
    """
    Get a nice number (1, 2, 5, 10, ...)
    :param rge: range
    :param rnd: round or not
    :return: a nice number
    """
    exponent = math.floor(math.log10(rge))
    fraction = rge / math.pow(10, exponent)

    if rnd:
        if fraction < 1.5:
            nice_fraction = 1
        elif fraction < 3:
            nice_fraction = 2
        elif fraction < 7:
            nice_fraction = 5
        else:
            nice_fraction = 10
    else:
        if fraction <= 1:
            nice_fraction = 1
        elif fraction <= 2:
            nice_fraction = 2
        elif fraction <= 5:
            nice_fraction = 5
        else:
            nice_fraction = 10

    return nice_fraction * math.pow(10, exponent)


def plot_dot(scr, y, x):
    """
    Plot a 'dot' (in fact a blank character in reverse) at (x,y)
    :param scr: curses screen
    :param y: y position, from top
    :param x: x position
    """
    scr.addstr(y, x + LEFT_MARGIN, ' ', curses.A_REVERSE)


def plot_bar(scr, y, x, graph_height):
    """
    Plot a vertical bar from the botton of graph to the desired position
    :param scr: curses screen
    :param y: y position, from top
    :param x: x position
    :param graph_height: height of graph
    """
    for i in range(y, graph_height):
        plot_dot(scr, i, x)


def format_number(n, max_length):
    """
    Get number in String, in a format fitting in the max_length specified
    :param n: number to transform in String
    :param max_length: maximum length authorized to display that number
    :return: a String representing this number fitting in the desired size
    """

    # First, we round the number
    s = str(int(n + 0.5))
    if len(s) > max_length or abs(n) < 1:
        # If the String of the rounded number is bigger than max_length,
        # or of the absolute value is < 1, then we return the number using an exponent
        return format(n, str(max_length - 3) + ".2G")
    else:
        # otherwise, we return the rounded number in text
        return s


def linear_interpolation(x1, y1, x2, y2, x):
    """
    Just linear interpolation
    """
    return (x - x1) * (y2 - y1) / (x2 - x1) + y1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot a chart from stantdard input')
    parser.add_argument('--no-keep', dest='keep', action='store_false',
                        help='Do not keep the chart plotted at the end of stream')
    parser.set_defaults(keep=True)
    args = parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        pass

