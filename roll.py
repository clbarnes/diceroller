#!/usr/bin/env python
import re
from random import random
from math import ceil, floor
from collections import namedtuple
from tkinter import Tk
import argparse
from datetime import datetime
from abc import ABCMeta, abstractmethod
from itertools import combinations_with_replacement
from math import inf

DEFAULT_SIDES = 10

UP_ARROW = chr(8593)
DOWN_ARROW = chr(8595)

# QUICK_ENUMERATE_REPS = 1000
QUICK_ENUMERATE_REPS = inf

round_args = {'': '', 'up': UP_ARROW, 'down': DOWN_ARROW}


def roll_die(n_sides):
    return ceil(random()*n_sides)


def mean(lst):
    total = sum(lst)
    return total/len(lst)


def var(lst):
    mu = mean(lst)
    sqdev = [(item - mu)**2 for item in lst]
    return mean(sqdev)


def std(lst):
    return var(lst)**(1/2)


class DiceRoll:
    # name, number, sides, modifier, rounding
    DICE_RE = re.compile('(.*:)?(\d*)d(\d*)(p\d*[hl])?([\d\+\-\*/]*)([\^_]?)')
    PICK_RE = re.compile('p(\d*)([hl])')
    rounding_types = {'^': 'up', '_': 'down', '': ''}
    arg_count = 1
    DiceResult = namedtuple('DiceResult',
                            ['name', 'argument', 'results', 'subtotal', 'total']
                            )
    DiceDistribution = namedtuple('DiceDistribution',
                                  ['name', 'argument', 'distribution']
                                  )

    def __init__(self, sides=DEFAULT_SIDES, count=1, pick_str='', modifier_str='', rounding='', name='', arg=''):
        self.sides = sides
        self.count = count
        self.modifier = lambda x: eval(str(x) + modifier_str)

        self.pick = self._parse_pick_str(pick_str)

        self.rounding = rounding

        if not name:
            name = str(self.__class__.arg_count)
        self.name = name
        self.__class__.arg_count += 1

        self.argument = arg if arg else '{}d{}{}{}{}'.format(
            count if count > 1 else '', sides, pick_str, modifier_str, round_args[self.rounding]
        )

    @classmethod
    def from_string(cls, s):
        m = cls.DICE_RE.match(s)
        name_, count_, sides_, pick_str, modifier_str, rounding_ = m.groups()
        return cls(
            int(sides_),
            int(count_) if count_ else 1,
            lambda x: eval(str(x) + modifier_str),
            cls.rounding_types[rounding_],
            name_[:-1] if name_ else ''
        )

    def _round(self, number):
        rounding_fns = {'up': ceil, 'down': floor, '': lambda x: x}
        return rounding_fns[self.rounding](number)

    def _results_to_output(self, results_lst):
        subtotal = sum(results_lst)
        modified_subtotal = eval(str(subtotal)+self.modifier)
        total = self._round(modified_subtotal)

        return self.__class__.DiceResult(
            name=self.name,
            argument=self.argument,
            results=results_lst,
            subtotal=subtotal,
            total=total
        )

    def roll(self):
        results = [roll_die(self.sides) for _ in range(self.count)]
        return self._results_to_output(results)

    def enumerate(self):
        if self.sides * self.count > QUICK_ENUMERATE_REPS:
            return self._quick_enumerate()
        else:
            return self._full_enumerate()

    def _full_enumerate(self):
        possible_results = combinations_with_replacement(range(1, self.sides+1), self.count)
        totals = [self._results_to_output(results).total for results in possible_results]
        return self.__class__.DiceDistribution(
            name=self.name,
            argument=self.argument,
            distribution=FullDistribution(totals)
        )

    def _quick_enumerate(self, reps=QUICK_ENUMERATE_REPS):
        totals = [self.roll().total for _ in range(reps)]
        return self.__class__.DiceDistribution(
            name=self.name,
            argument=self.argument,
            distribution=NormalDistribution(totals)
        )

    def _parse_pick_str(self, pick_str):
        if not pick_str:
            return lambda x: x

        m = self.PICK_RE.match(pick_str)
        count, direction = m.groups()
        count = 1 if count is None else int(count)

        def pick_fn(lst):
            sorted_lst = sorted(lst)
            if direction == 'l':
                return sorted_lst[:count]
            elif direction == 'h':
                return sorted_lst[-count:]

        return pick_fn


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


class Distribution(metaclass=ABCMeta):
    """
    Interface for distributions
    """
    @abstractmethod
    def p_val(self, actual):
        pass

    @abstractmethod
    @property
    def expected(self):
        pass

class FullDistribution(Distribution):
    def __init__(self, possibles):
        self.possibles = sorted(possibles)
        self._rev_possibles = list(reversed(self.possibles))

    def p_val(self, actual):
        lower_or_equal_actual = len(self.possibles) - self._rev_possibles.index(actual)
        higher_or_equal_actual = len(self.possibles) - self.possibles.index(actual)
        return min(lower_or_equal_actual, higher_or_equal_actual)/len(self.possibles)

    # algorithmically slower
    # def _p_val_unsorted(self, actual):
    #     lower_than_actual = 0
    #     higher_than_actual = 0
    #     for possible in self.possibles:
    #         lower_than_actual += actual <= possible
    #         higher_than_actual += actual >= possible
    #
    #     return min(lower_than_actual, higher_than_actual)/len(self.possibles)

    @property
    def expected(self):
        return mean(self.possibles)


# todo: may not be statistically valid?
class NormalDistribution(Distribution):
    def __init__(self, sample):
        self.mu = mean(sample)
        self.sigma = std(sample)

    def p_val(self, actual):
        raise NotImplementedError
        # todo

    @property
    def expected(self):
        return self.mu


def to_clipboard(table_str):
    timestamp = datetime.now().isoformat()
    clipboard_str = '{}\nRolled at {}'.format(table_str, timestamp)
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(clipboard_str)
    r.update()
    print(table_str)
    input('Result copied to clipboard! Press enter when you have pasted it to continue (clipboard will be cleared).')
    r.destroy()


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
parser.add_argument('-c', '--clipboard', dest='clipboard', action='store_true')
parser.add_argument('-s', '--statistics', dest='statistics', action='store_true')
parser.add_argument('roll_command', nargs='+', default='d10', help='Tell the parser what sort of dice you want to roll')


if __name__ == '__main__':
    args = parser.parse_args()

    result_table = ResultTable([DiceRoll.from_string(arg).roll() for arg in args.roll_command])
    table_str = result_table.to_string()
    if args.clipboard:
        to_clipboard(table_str)
    else:
        print(table_str)
