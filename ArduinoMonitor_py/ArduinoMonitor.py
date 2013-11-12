from Tkinter import *
from readSerials import SerialPins
import collections

root = Tk()




pin_list_frame = Frame(root)
pin_list_frame.pack(fill = BOTH, expand = True)

pin_widgets = {} # name : widget

def cmp_pins(p1, p2):
    if p1.isdigit() and p2.isdigit():
        return cmp(int(p1), int(p2))
    return cmp(p1, p2)

def sort_pins():
    for row, pin_name in enumerate(sorted(pin_widgets, cmp = cmp_pins)):
        widgets = pin_widgets[pin_name][0]
        for column, widget in enumerate(widgets):
            widget.grid_configure(row = row, column = column)

COORDS = 250 # maximum number of coords for each polygon
COORDS = COORDS // 2

ROW_HEIGHT = 30

def new_pin_widget(name):
    f = pin_list_frame
    name_label = Label(f, text = name)
    name_label.grid_configure(sticky = W)
    current_value_label = Label(f, text = '-')
    height = ROW_HEIGHT
    means_canvas = Canvas(f, height = height, width = 0, borderwidth = 0, background = 'white')
    means_canvas.grid_configure(sticky = W)
    occurrences_canvas = Canvas(f, height = height, width = 0, borderwidth = 0, background = 'white')
    occurrences_canvas.grid_configure(sticky = W)
    occurrences_canvas_polygon = occurrences_canvas.create_polygon(0,0,0,0, fill = 'black')
    minima = []
    means = []
    maxima = []
    last_interval = [-1]
    val2coordy = lambda min_value, max_value: (\
        lambda height, min_value, delta, max_value: lambda value: height - height * (value - min_value + delta) / (max_value - min_value + delta * 2) + 1
        )(int(means_canvas['height']), min_value, (5 if max_value - min_value > 5 else 1), max_value)
    def update_timeline(statistics):
        if int(means_canvas['width']) < len(statistics.means):
            means_canvas.configure(width = len(statistics.means))
        for i in range(len(minima) // COORDS, len(statistics.means) // COORDS + 1):
            minima.append(means_canvas.create_polygon(0,0,0,0, width = 1, fill = 'black'))
            means.append(means_canvas.create_line(0,0,0,0, width = 1, fill = 'red'))
            maxima.append(means_canvas.create_polygon(0,0,0,0, width = 1, fill = 'black'))
        index = 0
        min_coords = [0, height + 2]
        mean_coords = []
        max_coords = [0, 0]
        val2coord = val2coordy(statistics.minimum, statistics.maximum)
        assert 0 <= val2coord(statistics.maximum) <= val2coord(statistics.minimum) <= height + 2, (val2coord(statistics.maximum), val2coord(statistics.minimum))
        for x, min_value, max_value, mean_value in zip(range(1, len(statistics.means) + 1), statistics.minima, statistics.maxima, statistics.means):
            if not (0 <= val2coord(max_value) <= val2coord(mean_value) <= val2coord(min_value) <= height + 2):
                raise ValueError(statistics.maximum, max_value, mean_value, min_value, statistics.minimum)
            min_coords.extend([x, val2coord(min_value)])
            mean_coords.extend([x, val2coord(mean_value)])
            max_coords.extend([x, val2coord(max_value)])
            if len(min_coords) >= COORDS:
                max_coords.extend([x, 0])
                min_coords.extend([x, height + 2])
                means_canvas.coords(minima[index], *min_coords)
                means_canvas.coords(means[index], *mean_coords)
                means_canvas.coords(maxima[index], *max_coords)
                index += 1
                min_coords = [x, height + 2, min_coords[-4], min_coords[-3]] 
                mean_coords = [mean_coords[-2], mean_coords[-1]]
                max_coords = [x, 0, max_coords[-4], max_coords[-3]]
        max_coords.extend([x, 0])
        min_coords.extend([x, height + 2])
        means_canvas.coords(minima[index], *min_coords)
        if len(mean_coords) >= 4:
            means_canvas.coords(means[index], *mean_coords)
        means_canvas.coords(maxima[index], *max_coords)

    def update_occurrences(statistics):
        assert COORDS > ROW_HEIGHT
        occurrences = statistics.occurrences
        val2coord_y = val2coordy(min(occurrences), max(occurrences))
        ycoords = map(int, map(val2coord_y, occurrences))
        d = collections.defaultdict(list)
        for i, o in enumerate(occurrences):
            d[ycoords[i]].append(occurrences[o])
        coords = [0,0]
        for y in range(0, height + 2):
            x = sum(d[y]) + 1
            if int(occurrences_canvas['width']) < x:
                occurrences_canvas['width'] = x
            coords.extend([x, y])
        coords.extend([0, int(occurrences_canvas['height']) + 2])
        occurrences_canvas.coords(occurrences_canvas_polygon, *coords)
        

    def update(statistics):
        ## current value
        current_value_label['text'] = str(statistics.last_value)
        ## time line
        if last_interval != [statistics.interval_number]:
           last_interval[:] = [statistics.interval_number]
           update_timeline(statistics)
           update_occurrences(statistics)
           
        
    pin_widgets[name] = [name_label, current_value_label, means_canvas,
                         occurrences_canvas], update
    sort_pins()

def update_pin_widgets():
    for pin_name in serial_pins:
        if pin_name not in pin_widgets:
            new_pin_widget(pin_name)
        update = pin_widgets[pin_name][1]
        update(serial_pins[pin_name])

ports_frame = Frame(root)
ports_frame.pack(fill = X)
ports_label = Label(ports_frame)
ports_label.pack(side = LEFT)
connected = True
def switch_connected():
    global connected
    connected = not connected
    if connected:
        connect_button['text'] = 'Disconnect'
    else:
        connect_button['text'] = 'Connect'
        serial_pins.stop()
connect_button = Button(ports_frame, text = 'Disconnect', command = switch_connected)
connect_button.pack(side = RIGHT)
port_count = 0

def update_port_widgets():
    global port_count
    if connected:
        serial_pins.update_ports()
    if not serial_pins.ports:
        port_count += 1
        port_count %= 40
        if port_count > 20: i = 40 - port_count
        else: i = port_count
        if connected: animation_text = ' ' * i + '...' + ' ' * (20 - i)
        else: animation_text = '.' + ' ' * 22
        ports_label['text'] = 'No Serial Ports connected' + animation_text
    else:
        ports_label['text'] = 'Ports: ' + ', '.join(map(str, serial_pins.ports))
        

def update():
    update_pin_widgets()
    update_port_widgets()

def _update():
    try:
        update()
    finally:
        root.after(33, _update)

serial_pins = SerialPins()

root.after(0, _update)
root.mainloop()
serial_pins.stop()

