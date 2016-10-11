#!/usr/bin/env python
import re
from random import random
from math import ceil, floor
import sys
from collections import namedtuple
from tkinter import Tk
import argparse
from datetime import datetime

DEFAULT_SIDES = 10

UP_ARROW = chr(8593)
DOWN_ARROW = chr(8595)

def roll_die(n_sides):
    return ceil(random()*n_sides)

round_args = {'': '', 'up': UP_ARROW, 'down': DOWN_ARROW}


class DiceRoll:
    # name, number, sides, modifier, rounding
    DICE_RE = re.compile('(.*:)?(\d*)d(\d*)([\d\+\-\*/]*)([\^_]?)')
    rounding_types = {'^': 'up', '_': 'down', '': ''}
    arg_count = 1
    DiceResult = namedtuple('DiceResult',
                            ['name', 'argument', 'results', 'subtotal', 'total']
                            )

    def __init__(self, sides=DEFAULT_SIDES, count=1, modifier='', rounding='', name=''):
        self.sides = sides
        self.count = count
        self.modifier = modifier

        self.rounding = rounding

        if not name:
            name = str(self.__class__.arg_count)
        self.name = name
        self.__class__.arg_count += 1

        self.argument = self.reconstruct_arg()

    @classmethod
    def from_string(cls, s):
        m = cls.DICE_RE.match(s)
        name_, count_, sides_, modifier_, rounding_ = m.groups()
        return cls(
            int(sides_),
            int(count_) if count_ else 1,
            modifier_,
            cls.rounding_types[rounding_],
            name_[:-1] if name_ else ''
        )

    def _round(self, number):
        rounding_fns = {'up': ceil, 'down': floor, '': lambda x: x}
        return rounding_fns[self.rounding](number)

    def roll(self):
        results = [roll_die(self.sides) for _ in range(self.count)]
        subtotal = sum(results)
        modified_subtotal = eval(str(subtotal) + self.modifier)
        total = self._round(modified_subtotal)

        return self.__class__.DiceResult(
            name=self.name,
            argument=self.argument,
            results=results,
            subtotal=subtotal,
            total=total
        )

    def reconstruct_arg(self):
        return '{}d{}{}{}'.format(
            self.count if self.count > 1 else '', self.sides, self.modifier, round_args[self.rounding]
        )


class ResultTable:
    def __init__(self, dice_results, vsep=' | ', hsep='=', outline=False, pad=1):
        self.results = dice_results
        self.results_strs = [self._stringify(dice_result) for dice_result in dice_results]

        self.vsep = vsep
        self.hsep = hsep
        self.outline = outline
        if outline:
            raise NotImplementedError('Outline not implemented yet')
        self.pad = pad

        self.headers = ['', 'Dice', 'Roll(s)', 'Raw sum', 'TOTAL']

    def _stringify(self, results):
        return DiceRoll.DiceResult(
            name=results.name,
            argument=results.argument,
            results=', '.join(str(result) for result in results.results),
            subtotal=str(results.subtotal),
            total=str(results.total)
        )

    def _get_widths(self):
        widths = [len(header) for header in self.headers]
        for result in self.results_strs:
            zipped = zip(widths, [len(s) for s in result])
            widths = [max(current, new) for current, new in zipped]

        return widths

    def to_string(self):
        widths = self._get_widths()
        rows = [
            self._make_justified_row(self.headers, widths),
            self._make_hline(widths)
            ]
        for result in self.results_strs:
            rows.append(self._make_justified_row(result, widths))

        return '\n'.join(rows)

    def print(self):
        print(self.to_string())

    def _make_justified_row(self, row, widths, filler=' '):
        return self.vsep.join(item.rjust(width, filler) for item, width in zip(row, widths))

    def _make_hline(self, widths, vsep='=+='):
        if len(vsep) != len(self.vsep):
            raise ValueError('Horizontal line vertical separator is a different length to cell separator')
        return vsep.join(self.hsep*width for width in widths)


parser = argparse.ArgumentParser('''\
Roll some dice!

The primary syntax of this tool is the roll command, designed to be colloquial and terse.
For example,
>>> roll.py attack:2d20+4
rolls 2 20-sided dice, adds 4 to the sum of the results, and labels this batch 'attack' in the output table.

You can choose not to label it, modifiers are optional, and results can be rounded up or down with ^ and _

>>> roll.py  # defaults to rolling 1d10, because I wrote this while playing Cyberpunk 2020.
>>> roll.py d6
>>> roll.py 2d12/3^  # roll 2d12, divide the sum by 3, and round up the result\
>>> roll.py d3 d4 d6 d8 d12 d20  # multiple batches at once!
''')
# parser.add_argument('-c', '--clipboard', dest='clipboard', action='store_true')
parser.add_argument('roll_command', nargs='+', default='d10', help='Tell the parser what sort of dice you want to roll')


if __name__ == '__main__':
    args = parser.parse_args()
    # try:
    #     args = sys.argv[1:]
    # except:
    #     args = ['d{}'.format(DEFAULT_SIDES)]

    # rolls = [DiceRoll.from_string(arg) for arg in args]
    # results = [roll.roll() for roll in rolls]
    # table = ResultTable(results)
    # s = table.to_string()

    result_table = ResultTable([DiceRoll.from_string(arg).roll() for arg in args.roll_command])
    table_str = result_table.to_string()
    # if args.clipboard:
        ## tkinter clears your clipboard when it closes so this doesn't work
        ## raise NotImplementedError('--clipboard option is not available')
        # timestamp = datetime.now().isoformat()
        # clipboard_str = '{}\nRolled at {}'.format(table_str, timestamp)
        # r = Tk()
        # r.withdraw()
        # r.clipboard_clear()
        # r.clipboard_append(table_str)
        # r.update()
        # r.destroy()
    print(table_str)
