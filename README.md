# What is Termchart
Termchart is a simple Python script that takes data from standard input,
and draws a barchart on the terminal using ncurses.

# Installation
You just need to copy the `termchart.py` file.

The requirements are:
* Python curses library
* Linux (as the script uses special file like `/dev/tty`)

Note: this script has not been tested with Python 3

# Usage
```
termchart.py [--no-keep]
```

The script wait for data coming from standard input. It can be passed using pipes, like `cat data.txt | termchart.py`.

The script must receive data consisting of numbers, with only one number per line. Everything else will be ignored.

Each time the script receive data, it displays a bar on the terminal with a height relative to the value received. The
Y scale is automatically adjusted. If there are more data to display than the width of the terminal, then the data
received first is discarded (like a FIFO).

Regarding the `--no-keep` option, we must consider two cases:
* the stream of data input is finished (example: `cat datat.txt | termchart.py`)
  * by default, the chart stays on the terminal ; any key will exit
  * with the `--no-keep` option, the program will exit immediately after the end of the stream, and clear the screen ;
so you will not see anything, this option is not useful in that case
* the stream of data is not finished, the chart is updated live, and pressing on `CTRL-C` will exit the program
  * by default, the chart stays on the terminal ; any key will then exit
  * with the `--no-keep` option, the program will exit immediately after pressing `CTRL-C`

# Examples
## Display user CPU Usage
```
vmstat 1 | awk '{print $13; fflush(stdout)}' | termchart.py
```

Note: it is important to use `fflush(stdout)` in `awk` to force it to flush immediately.

![CPU usage chart](https://raw.githubusercontent.com/stephane-deraco/Termchart/gh-pages/images/cpu.png "CPU usage chart")

## Ping time
```
ping www.google.fr | awk 'BEGIN {FS="[=]|[ ]"} NR > 1 {print $11; lush(stdout)}' | termchart.py
```

![Ping chart](https://raw.githubusercontent.com/stephane-deraco/Termchart/gh-pages/images/ping.png "Ping chart")

## Java Memory Eden space usage
```
jstat -gc <vmid> 1000 | awk 'NR > 1 { gsub(",", ".", $6); print $6; fflush(stdout); }' | termchart.py
```

![Java memory chart](https://raw.githubusercontent.com/stephane-deraco/Termchart/gh-pages/images/java.png "Java memory chart")
