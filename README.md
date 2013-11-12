Arduino-Monitor
===============

Ever wondered what your Arduino does? Use this monitor to see the values the Arduino works with and the check for own outputs.

Install
-------

Download the sources from [github](https://github.com/niccokunzmann/Arduino-Monitor/archive/master.zip).
Install [Python 2](http://python.org/download/releases/2.7.6/).
Install [PySerial](https://pypi.python.org/pypi/pyserial).

Run
---

Run the ArduinoMonitor.pyw in the folder ArduinoMonitor_py. It checks for Arduinos connected.

Now whenever your arduino prints a line like

`value=4` or `pin0 = 25` 

the monitor updates the statistics.

There is an example program that outputs the values of all pins of the Arduino located in the folder ArduinoMonitor_ino.

