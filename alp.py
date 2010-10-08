#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime
import re
import time as time_module
try:
    import curses
except ImportError:
    curses = None
try:
    import termcolor
    colored_orig = termcolor.colored
    _normal_esc_seq = colored_orig('>', 'grey').split('>')[1]
    def _colored(color, typ):
        if color == 'black':
            color = 'grey'
        if typ == 'bg':
            fg_color = None
            bg_color = 'on_' + color
        elif typ == 'fg':
            fg_color = color
            bg_color = None
        return colored_orig('>', fg_color, bg_color).split('>')[0]

    def _formatted(typ):
        try:
            return colored_orig('>', attrs=[typ]).split('>')[0]
        except KeyError:
            if typ == 'normal':
                return _normal_esc_seq
            else:
                return ''
except ImportError:
    termcolor = None
    colored = lambda color, typ: ''
    formatted = lambda typ: ''

######################################################################

# Basic constants
_epoch = datetime(2009, 10, 8, 13, 1, 34)
_one_alp = 2 ** 18
_hexalp_divide = 2 ** 14
_qvalp_divide = 2 ** 12
_salp_divide = 2 ** 8
_talp_divide = 2 ** 4

class _AlpTime(object):
    """The Alp time object"""

    def __init__(self):
        self.speed = 1
        self.start_date = datetime.now()
        self.start_diff = self.start_date - _epoch
        self.update()

    def set_speed(self, speed):
        self.speed = speed

    def get_seconds_since_epoch(self, date=None):
        if date is None:
            date = datetime.now()
        diff = self.start_diff + (date - self.start_date) * self.speed
        return diff.days * 86400 + diff.seconds, diff

    def update(self, date=None):
        passed, diff = self.get_seconds_since_epoch(date)
        self.date = self.start_date + diff
        self.real_date = self.start_date + diff - self.start_diff

        seconds_total = passed % _one_alp
        alp = passed / _one_alp
        seconds_left = seconds_total
        hexalp = seconds_left / _hexalp_divide
        seconds_left -= hexalp * _hexalp_divide
        qvalp = seconds_left / _qvalp_divide
        seconds_left -= qvalp * _qvalp_divide
        salp = seconds_left / _salp_divide
        seconds_left -= salp * _salp_divide
        talp = seconds_left / _talp_divide
        seconds_left -= talp * _talp_divide
        second = seconds_left

        self.seconds_since_epoch = passed
        self.alp = alp
        self.seconds = seconds_total
        self.hexalp = hexalp
        self.qvalp = qvalp
        self.salp = salp
        self.talp = talp
        self.second = second

    def __str__(self):
        return 'AlpTime{alp: %d, hexalp: %d, qvalp: %d, \
salp: %d, talp: %d, second: %d}' % (self.alp, self.hexalp, self.qvalp,
                                 self.salp, self.talp, self.second)

time = _AlpTime()
update = time.update
set_speed = time.set_speed

######################################################################

# Using curses without initscr
_curses_colors = ('BLUE', 'GREEN', 'CYAN', 'RED', 'MAGENTA', 'YELLOW',
                  'WHITE', 'BLACK')

_curses_controls = {
    'bol': 'cr', 'up': 'cuu1', 'down': 'cud1', 'left': 'cub1',
    'right': 'cuf1', 'clear_screen': 'clear', 'clear_eol': 'el',
    'clear_bol': 'el1', 'clear_eos': 'ed', 'bold': 'bold', 'blink':
    'blink', 'dim': 'dim', 'reverse': 'rev', 'underline': 'smul',
    'normal': 'sgr0', 'hide_cursor': 'civis', 'show_cursor': 'cnorm'
}

_formatter_control_regex = re.compile(r'!\((.+?)\)')
_formatter_bg_color_regex = re.compile(r'#\((.+?)\)')
_formatter_fg_color_regex = re.compile(r'\$\((.+?)\)')
_formatter_codes_regex = re.compile(r'[!#\$]\(.+?\)')

def _no_formatting(text):
    return _formatter_codes_regex.sub('', text)

def _textlen(text):
    return len(_no_formatting(text).decode('utf-8'))

class _BaseControls(object):
    """A generic text formatting generator"""

    def _generate_part(self, attr, obj):
        return ''

    def generate(self, text, put=False):
        text = _formatter_control_regex.sub(
            lambda obj: self._generate_part('controls', obj), text)
        text = _formatter_bg_color_regex.sub(
            lambda obj: self._generate_part('bg_colors', obj), text)
        text = _formatter_fg_color_regex.sub(
            lambda obj: self._generate_part('fg_colors', obj), text)
        if put:
            sys.stdout.write(text)
        return text

    def clear(self):
        self.generate('!(clear_eol)', True)

    def end(self):
        pass

class _CursesControls(_BaseControls):
    """
    A text formatting generator and a container of curses escape
    sequences
    """

    def __init__(self):
        if not sys.stdout.isatty():
            return
        try:
            curses.setupterm()
        except Exception, e:
            print e
        bg_seq = curses.tigetstr('setab') or curses.tigetstr('setb') or ''
        fg_seq = curses.tigetstr('setaf') or curses.tigetstr('setf') or ''

        self.bg_colors = {}
        self.fg_colors = {}
        self.controls = {}

        # Get escape sequences
        for color in _curses_colors:
            index = getattr(curses, 'COLOR_%s' % color)
            color = color.lower()
            self.bg_colors[color] = curses.tparm(bg_seq, index)
            self.fg_colors[color] = curses.tparm(fg_seq, index)
        for control in _curses_controls:
            self.controls[control] = curses.tigetstr(_curses_controls[control]) or ''

        self.cols = curses.tigetnum('cols')
        self.lines = curses.tigetnum('lines')

    def _generate_part(self, attr, obj):
        return self.__getattribute__(attr)[obj.groups(1)[0]]

    def end(self):
        print formatter.generate('!(normal)!(show_cursor)!(up)')

class _FakeCursesControls(_BaseControls):
    """A text formatting generator without curses"""

    def _generate_part(self, attr, obj):
        obj = obj.groups(1)[0]
        if attr == 'bg_colors':
            return _colored(obj, 'bg')
        elif attr == 'fg_colors':
            return _colored(obj, 'fg')
        elif attr == 'controls':
            return _formatted(obj)
        # Else
        return ''

    def end(self):
        print formatter.generate('!(normal)')

formatter = None
def start_formatter(use_curses=True):
    global formatter, start_formatter
    if curses is None or not use_curses:
        formatter = _FakeCursesControls()
    else:
        formatter = _CursesControls()
    start_formatter = lambda *arg: True
    return formatter

######################################################################

# Date formats
## a '#' in the end returns the number in hex
## an '_' in the end followed by a number prepends
 # (<number> - len(str(number)) zeroes to the number
## Available "units":
### seconds, seconds_since_epoch, alp, hexalp, qvalp, salp, talp, second

_default_hex_date_format = '\
!(bold)#(black)$(yellow)ALP\
#(cyan)$(yellow)&(alp_4)\
#(blue)$(white)/\
#(black)$(green)&(hexalp#)\
$(cyan)&(qvalp)\
$(red)&(salp#)\
&(talp#)\
$(white)&(second#)'
         # e.g. 2403/93EC2

_default_dec_date_format = '\
!(bold)#(black)$(yellow)ALP\
#(cyan)$(yellow)&(alp_4)\
#(blue)$(white)/\
#(black)$(green)&(hexalp_2)\
$(cyan)&(qvalp)\
$(red)&(salp_2)\
&(talp_2)\
$(white)&(second_2)'
         # e.g. 2403/093141202

_date_format_unit_regex = re.compile(r'&\((.+?)\)')

def _format_replace(obj):
    unit = obj.groups(1)[0]
    zero_prepend = '_' in unit
    as_hex = unit.endswith('#')
    if zero_prepend:
        spl = unit.split('_')
        unit = spl[0]
        z_num = spl[1]
    elif as_hex:
        unit = unit[:-1]
    value = time.__dict__[unit]
    if zero_prepend:
        return ('%0' + z_num + 'd') % value
    elif as_hex:
        return hex(value)[2:].upper()
    else:
        return str(value)

def get_date_text(date_format=None):
    if date_format is None:
        date_format = _default_hex_date_format
    return _date_format_unit_regex.sub(_format_replace, date_format)

######################################################################

# Virtual LEDs
_led_letters = 'abcdefghijklmnopqrs'

_default_led_layout = '''\
   a  b  c  d
e  g  h  i  j
f  k  l  m  n
o  p  q  r  s\
'''

_default_led_controls = '#(yellow)'

class _Container(object):
    pass

class _Led(object):
    """A simulation of a LED lamp"""
    def __init__(self, **kwds):
        self.items = {
            True: _Container(), False: _Container()}
        for key, val in kwds.iteritems():
            if key[-1] in ('0', '1'):
                key_vals = bool(int(key[-1])),
                key = key[:-1]
            else:
                key_vals = True, False

            for x in key_vals:
                self.items[x].__setattr__(key, val)
        for x in self.items.values():
            d = x.__dict__
            if not 'letter' in d:
                x.letter = 'o'
            if not 'fg' in d:
                x.fg = None
            if not 'bg' in d:
                x.bg = None
            if not 'controls' in d:
                x.controls = None

    def generate(self, state):
        info = self.items[state]
        text = info.letter
        pre_esc = ''
        if info.bg:
            pre_esc += '#(%s)' % info.bg
        if info.fg:
            pre_esc += '$(%s)' % info.fg
        if info.controls:
            for x in info.controls:
                pre_esc += '!(' + x + ')'
        text = pre_esc + text
        if pre_esc:
            text += '!(normal)'
        return text

_led_formatting = {
    'a': _Led(bg='yellow', fg='green', letter0='·', letter1='O', controls=['bold']),
    'b': _Led(bg='yellow', fg='green', letter0='·', letter1='O', controls=['bold']),
    'c': _Led(bg='yellow', fg='green', letter0='·', letter1='O', controls=['bold']),
    'd': _Led(bg='yellow', fg='green', letter0='·', letter1='O', controls=['bold']),
    'e': _Led(bg='magenta', fg='cyan', letter0='.', letter1='0', controls=['bold']),
    'f': _Led(bg='magenta', fg='cyan', letter0='.', letter1='0', controls=['bold']),
    'g': _Led(bg='black', fg='red', letter0=',', letter1='o', controls=['bold']),
    'h': _Led(bg='black', fg='red', letter0=',', letter1='o', controls=['bold']),
    'i': _Led(bg='black', fg='red', letter0=',', letter1='o', controls=['bold']),
    'j': _Led(bg='black', fg='red', letter0=',', letter1='o', controls=['bold']),
    'k': _Led(bg='blue', fg='red', letter0=',', letter1='o', controls=['bold']),
    'l': _Led(bg='blue', fg='red', letter0=',', letter1='o', controls=['bold']),
    'm': _Led(bg='blue', fg='red', letter0=',', letter1='o', controls=['bold']),
    'n': _Led(bg='blue', fg='red', letter0=',', letter1='o', controls=['bold']),
    'o': _Led(bg='yellow', fg='white', letter0='·', letter1='>', controls=['bold']),
    'p': _Led(bg='yellow', fg='white', letter0='·', letter1='>', controls=['bold']),
    'q': _Led(bg='yellow', fg='white', letter0='·', letter1='>', controls=['bold']),
    'r': _Led(bg='yellow', fg='white', letter0='·', letter1='>', controls=['bold']),
    's': _Led(bg='yellow', fg='white', letter0='·', letter1='>', controls=['bold']),
    '*': _Led(letter0='.', letter1='o') # For eventual non-defined letters
}

_led_states = {}

def _set_states_from_hex(unit_time, *var):
    global _led_states
    for i in range(len(var) - 1, -1, -1):
        t = unit_time / 2**i
        unit_time -= t * 2**i
        _led_states[var[i]] = bool(t)

def _get_states_from_hex(unit_time, w=4):
    num = []
    for i in range(w - 1, -1, -1):
        t = unit_time / 2**i
        unit_time -= t * 2**i
        num.append(bool(t))
    num.reverse()
    return num

def update_leds():
    global _led_states
    _set_states_from_hex(time.hexalp, 'a', 'b', 'c', 'd')
    _set_states_from_hex(time.qvalp, 'e', 'f')
    _set_states_from_hex(time.salp, 'g', 'h', 'i', 'j')
    _set_states_from_hex(time.talp, 'k', 'l', 'm', 'n')

    Q = _get_states_from_hex(time.second)
    O = Q[0] or Q[1]
    P = Q[2] ^ Q[3]
    R = not Q[2] and not Q[3]

    val_e = not Q[0] and Q[1] and P or Q[0] and\
        (Q[2] and Q[3] or not Q[1] and not Q[2] and not Q[3])
    val_d = Q[1] and (not Q[0] and not P or Q[0]\
                          and (not Q[2] and Q[3] or Q[2]))
    val_c = Q[3] and (Q[2] or not O) or Q[0] and Q[1] and R
    val_b = not O and Q[2] and not Q[3] or Q[3] and (O or Q[2])
    val_a = Q[3] or Q[2] and O

    _led_states['o'] = val_e
    _led_states['p'] = val_d
    _led_states['q'] = val_c
    _led_states['r'] = val_b
    _led_states['s'] = val_a

def _get_led_formatting(obj):
    obj = obj.groups(1)[0]
    try:
        return _led_formatting[obj].generate(_led_states[obj])
    except KeyError:
        return _led_formatting['*'].generate(_led_states[obj])

def get_led_text(led_layout=None):
    if led_layout is None:
        led_layout = _default_led_layout

    led_layout = re.sub(r'([' + _led_letters + '])',
                        lambda obj: _get_led_formatting(obj) \
                            + _default_led_controls, led_layout)

    text = _default_led_controls + led_layout.replace(
        '\n', '!(normal)\n' + _default_led_controls) + '!(normal)'
    return formatter.generate(text), _no_formatting(led_layout)

update_leds()

######################################################################

# Gregorian calendar compatibility

# Format (using strftime)
_default_gregorian_date_format = '\
!(bold)#(red)$(white)GR\
#(yellow) \
!(bold)#(cyan)$(yellow)%Y\
#(blue)$(white)-\
#(cyan)$(yellow)%m\
#(blue)$(white)-\
#(cyan)$(yellow)%d\n\
!(bold)#(red)$(white)EGOR\
#(yellow) \
#(black)$(cyan)%H\
#(blue)$(white):\
#(black)$(green)%M\
#(blue)$(white):\
#(black)$(red)%S'

def get_gregorian_date_text(date_format=None):
    if date_format is None:
        date_format = _default_gregorian_date_format
    return time.real_date.strftime(date_format)

######################################################################

# Convenience functions

def update_all(date=None):
    update(date)
    update_leds()

def print_time_continously(date_format=None, greg_date_format=None,
                           led_layout=None):
    start_formatter()
    formatter.generate('!(hide_cursor)', True)
    update()
    prev = time.seconds_since_epoch

    go_up = 0
    try:
        while True:
            update()
            now = time.seconds_since_epoch
            if now > prev:
                date_text = get_date_text(date_format)
                greg_date_text = get_gregorian_date_text(greg_date_format)
                update_leds()
                led_text, led_pure_text = get_led_text(led_layout)
                # ' ' *
                #     (_textlen(led_pure_text.split('\n', 1)[0]) - _textlen(date_text))
                text = \
                    '!(up)' * go_up + '!(up)\n' + date_text \
                    + '!(normal)\n' + greg_date_text + '!(normal)\n' + led_text
                formatter.generate(text, True)
                go_up = (date_text + greg_date_text +
                         led_text).count('\n') + 2

                prev = now
            sleep_time = 0.5 / time.speed
            if sleep_time < 0.01:
                sleep_time = 0.01
            time_module.sleep(sleep_time)
    except KeyboardInterrupt:
        formatter.generate('\n!(up)' + '!(clear_eol)!(up)' * go_up, True)
        raise KeyboardInterrupt()

######################################################################

if __name__ == '__main__':
    set_speed(128)
    start_formatter(True)
    try:
        print_time_continously()
    except (KeyboardInterrupt, EOFError):
        formatter.end()

