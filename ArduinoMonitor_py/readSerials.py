import serial
import re
import threading
import collections
import time

## got the code from
## http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
import os
from serial.tools import list_ports

def list_serial_ports():
    # Windows
    if os.name == 'nt':
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append('COM'+str(i + 1))
                s.close()
            except serial.SerialException:
                pass
        return available
    else:
        # Mac / Linux
        return [port[0] for port in list_ports.comports()]

class SerialMonitor(object):

    line_is_about_pins_regex = re.compile('^(?:pin\\s*(?=(A|a)?\\d+))?\\s*(?P<pin>(A|a)?\\d+|\\w+)\\s*=\\s*(?P<value>\\d+)\\s*$')

    @classmethod
    def line_is_about_pins(cls, line):
        """=> whether the line can be passed to pin_and_value"""
        return bool(cls.line_is_about_pins_regex.match(line))

    @classmethod
    def pin_and_value(cls, line):
        """=> the pin name and the value of that pin as described by the line"""
        match = cls.line_is_about_pins_regex.match(line)
        pin = match.group('pin')
        if pin and pin[0] == 'a' and pin[1:].isdigit():
            pin = pin.upper()
        value = int(match.group('value'))
        return pin, value

    def __init__(self, serial, statistics):
        self.serial = serial
        self.thread = threading.Thread(target = self.monitor)
        self.stopped = False
        self.values = None
        self.statistics = statistics

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped = True

    def monitor(self):
        while not self.stopped:
            try:
                line = self.serial.readline()
            except serial.SerialException:
                if self.stopped:
                    break
                raise
            if self.line_is_about_pins(line):
                pin, value = self.pin_and_value(line)
                self.add_pin_value(pin, value)

    def add_pin_value(self, pin, value):
        self.statistics.add_pin_value(pin, value)

class PinEntry(object):
    def __init__(self, statistics):
        self._last_values = []
        self._sample_means = []
        self._sample_minima = []
        self._sample_maxima = []
        self._occurrences = collections.defaultdict(lambda: 0)
        self._occurence_timeline = []
        self.statistics = statistics
        self._lock = threading.Lock()
        
    def add_value(self, value):
        with self._lock:
            self._last_values.append(value)
            self._occurrences[value] += 1

    def restart_samples(self, max_size):
        with self._lock:
            # add values
            if self._last_values:
                self._sample_means.append(sum(self._last_values) / len(self._last_values))
                self._sample_minima.append(min(self._last_values))
                self._sample_maxima.append(max(self._last_values))
                self._occurence_timeline.append(self._last_values[:])
            elif self._sample_means:
                self._sample_means.append(0)
                self._sample_minima.append(0)
                self._sample_maxima.append(0)
            # clean up
            while len(self._sample_means)  > max_size: self._sample_means.pop(0)
            while len(self._sample_minima) > max_size: self._sample_minima.pop(0)
            while len(self._sample_maxima) > max_size: self._sample_maxima.pop(0)
            while len(self._occurence_timeline) > max_size:
                for value in self._occurence_timeline.pop(0):
                    self._occurrences[value] -= 1
            self._last_values = []

    def snapshot(self):
        with self._lock:
            return PinSnapshot(self)

class PinSnapshot(object):
    
    def __init__(self, pinEntry):
        self._last_values = pinEntry._last_values[:]
        self._sample_means = pinEntry._sample_means[:]
        self._sample_minima = pinEntry._sample_minima[:]
        self._sample_maxima = pinEntry._sample_maxima[:]
        self._occurrences = pinEntry._occurrences.copy()
        self.statistics = pinEntry.statistics
        
    @property
    def last_value(self):
        """=> the last value read from the sensor"""
        v = self._last_values
        if v: return v[-1]
        return self.current_value
    latest_value = last_value

    @property
    def current_value(self):
        """=> the mean of all last values within the sample_tim_interval"""
        v = self._last_values
        if v: return sum(v) / len(v)
        sm = self._sample_means
        if sm: return sm[-1]
        return 0

    @property
    def previous_values(self):
        """=> all previously recorded values without the current value"""
        return self._sample_means[:]

    @property
    def means(self):
        """=> the current knowledge about the pins means values"""
        v = self._last_values
        sm = self._sample_means
        if not v: return sm[:]
        return sm + [sum(v) / len(v)]

    @property
    def maxima(self):
        """=> the maxima of the values"""
        if self._last_values: return self._sample_maxima + [max(self._last_values)]
        return self._sample_maxima[:]
        
    @property
    def minima(self):
        """=> the maxima of the values"""
        if self._last_values: return self._sample_minima + [min(self._last_values)]
        return self._sample_minima[:]
        
    @property
    def sample_time_interval(self):
        """the sample mean time interval of the statistics"""
        return self.statistics.sample_time_interval
    @sample_time_interval.setter
    def sample_time_interval(self, value):
        self.statistics.sample_time_interval = value

    def has_values(self):
        """=> whether there were any values for the pin"""
        return bool(self._last_values) or bool(self._sample_means)

    @property
    def interval_number(self):
        """=> the number of the interval"""
        return self.statistics.interval_number

    @property
    def occurrences(self):
        """=> a dict of a value and how often it appeared"""
        d = collections.OrderedDict()
        for key in sorted(self._occurrences):
            value = self._occurrences[key]
            if value > 0:
                d[key] = value
            assert value >= 0, value
        return d

    @property
    def minimum(self):
        """=> the minimum of all the values"""
        return min(self.minima)
    
    @property
    def maximum(self):
        """=> the maximum of all the values"""
        return max(self.maxima)
    
class PinStatistics(object):

    def __init__(self, pin_values = 100, sample_time_interval = 1):
        self._pin_values = pin_values
        self._sample_time_interval = sample_time_interval
        self._pin_statistics = collections.defaultdict(lambda: PinEntry(self))
        self._restart_samples_time = 0
        self._interval_number = 0
        self._lock = threading.Lock()

    def add_pin_value(self, pin, value):
        now = time.time()
        with self._lock:
            restart_samples = self._restart_samples_time < now
            if restart_samples:
                self._restart_samples_time = now + self._sample_time_interval
                self._interval_number += 1
        if restart_samples:
            for pinEntry in self._pin_statistics.values():
                pinEntry.restart_samples(self._pin_values)
        self._pin_statistics[pin].add_value(value)

    def __iter__(self):
        """=> the pin names"""
        return iter(list(self._pin_statistics))

    def __getitem__(self, pin):
        """=> the statistical entry for the pin"""
        return self._pin_statistics[pin].snapshot()

    @property
    def sample_time_interval(self):
        """the sample mean time interval of the statistics"""
        return self.statistics.sample_time_interval
    @sample_time_interval.setter
    def sample_time_interval(self, value):
        self.statistics.sample_time_interval = value

    @property
    def interval_number(self):
        return self._interval_number

class SerialPins(object):

    newPinStatistics = PinStatistics
    newSerialMonitor = SerialMonitor

    def __init__(self):
        self.statistics = self.newPinStatistics()
        self._ports = {} # port name : (serial, monitor)
        self.update_ports()

    def update_ports(self):
        for port_name in list_serial_ports():
            if port_name not in self._ports:
                open_serial = serial.Serial(port_name)
                monitor = self.newSerialMonitor(open_serial, self.statistics)
                monitor.start()
                self._ports[port_name] = (open_serial, monitor)

    @property
    def serials(self):
        return [port[0] for port in self._ports.values()]

    @property
    def monitors(self):
        return [port[1] for port in self._ports.values()]

    @property
    def ports(self):
        return list(self._ports.keys())

    def stop(self):
        for serial in self.serials:
            serial.close()
        for monitor in self.monitors:
            monitor.stop()
        self._ports = {}

    def __del__(self):
        self.stop()

    def is_useful(self):
        """=> whether this object has any serial connection."""
        return bool(self.serials)

    def __iter__(self):
        """=> pin names"""
        return iter(self.statistics)

    def __getitem__(self, pin):
        """=> the statistical entry of the pin"""
        return self.statistics[pin]


if __name__ == '__main__':
    s = SerialPins()
    assert s.is_useful()
    r = s.serials[0]
