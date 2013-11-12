from readSerials import *


def test_pin_line_matches():
    assert SerialMonitor.line_is_about_pins('pin0=123')
    assert SerialMonitor.line_is_about_pins('pin A0 = 0')
    assert SerialMonitor.line_is_about_pins('pin 13    = 4000008\n')
    assert SerialMonitor.line_is_about_pins('asdf= 123')
    assert not SerialMonitor.line_is_about_pins('')
    assert not SerialMonitor.line_is_about_pins('pinA1= 123 asd  ')
    assert SerialMonitor.line_is_about_pins('pina1=4')

def test_pin_values():
    assert SerialMonitor.pin_and_value('pina1=4') == ('A1', 4)
    assert SerialMonitor.pin_and_value('pinA0 = 55') == ('A0', 55)
    assert SerialMonitor.pin_and_value('pin 0 = 3000') == ('0', 3000)

def test_non_pins():
    assert SerialMonitor.pin_and_value('asdef = 23') == ('asdef', 23)
