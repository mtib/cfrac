from decimal import getcontext, Decimal
import itertools
from multiprocessing import Pool
from typing import Iterator
import os

getcontext().prec = 500


class Cfrac():
    def __init__(self, sequence_gen, initial_digits=20):
        self.sequence_gen = sequence_gen
        self.sequence = []
        self.finalized = False

        self.add_digits(initial_digits)

    def add_digits(self, amount):
        if self.finalized:
            return
        try:
            for _ in range(amount):
                next_digit = next(self.sequence_gen)
                self.sequence.append(next_digit)
        except StopIteration:
            self.finalized = True

    def __repr__(self):
        if len(self.sequence) < 1:
            return "[...?]"
        elif len(self.sequence) == 1:
            return f"[{self.sequence[0]}]"
        elif self.finalized:
            return f"[{self.sequence[0]}; {', '.join(map(lambda x: '{:.0f}'.format(x), self.sequence[1:]))}]"
        else:
            return f"[{self.sequence[0]}; {', '.join(map(lambda x: '{:.0f}'.format(x), self.sequence[1:]))}, ...?]"


class BaseExpansion():
    def __init__(self, integer, expansion_gen, initial_digits=5, base=10):
        self.integer = integer  # int (floor(v))
        self.expansion_gen = expansion_gen  # sequence of decimal places
        self.frac_digits = []
        self.finalized = False
        self.base = base

        self.add_frac_digits(initial_digits)

    def add_frac_digits(self, amount):
        if self.finalized:
            return
        try:
            for _ in range(amount):
                next_digit = next(self.expansion_gen)
                self.frac_digits.append(next_digit)
        except StopIteration:
            self.finalized = True

    def __repr__(self):
        return f"{self.integer}_10 + 0.{''.join(map(lambda d: '{:.0f}'.format(d) if type(d) == Decimal else d, self.frac_digits))}{'...' if not self.finalized else ''}_{self.base}"


class Frac():
    def __init__(self, numerator, denominator):
        self.numerator = Decimal(numerator)
        self.denominator = Decimal(denominator)

    def __repr__(self):
        return f"{self.numerator}/{self.denominator}"

    def to_base(self, base=10):
        integer_part = self.numerator // self.denominator
        fractional_part = self.numerator/self.denominator -\
            integer_part  # This rounds to float precision

        def frac_places():
            frac_part = fractional_part
            while frac_part > 0:
                place = (frac_part * base) // 1
                new_frac_part = (frac_part * base) - place

                if Decimal(1.0) - new_frac_part < 1e-10:
                    yield place + 1
                    return
                if new_frac_part < 1e-10:
                    yield place
                    return

                yield place

                frac_part = new_frac_part

        return BaseExpansion(integer_part, frac_places(), base=base, initial_digits=20)

    def to_cfrac(self):

        def digi_gen():
            numerator = self.numerator
            denominator = self.denominator
            while denominator != 0:
                integer_part = numerator // denominator
                yield integer_part
                numerator, denominator = denominator, numerator - integer_part * denominator

        return Cfrac(digi_gen())


def fractions():
    sb_gen = stern_brocot()
    last = next(sb_gen)
    while True:
        new = next(sb_gen)
        yield Frac(last, new)
        last = new


def stern_brocot():
    queue = [1, 1]
    while True:
        next_val = queue[0] + queue[1]
        queue.append(next_val)
        queue.append(queue[1])
        retval = queue[0]
        queue = queue[1:]
        yield retval


def pretty_print(base_range: range, sb_range: range,
                 min_num_places: int):
    for i, sb in enumerate(itertools.islice(
            fractions(), sb_range.start, sb_range.stop)):
        for b in base_range:
            base_extension = sb.to_base(b)
            cfrac = sb.to_cfrac()
            if len(cfrac.sequence) > min_num_places and cfrac.sequence[1:] == base_extension.frac_digits and 0 == base_extension.integer:
                frac_part = "0."
                for fd in base_extension.frac_digits:
                    fd: Decimal
                    frac_part += "{:.0f}".format(fd)
                print(sb_range.start + i + 1, f"$\\nicefrac{{{sb.numerator}}}{{{sb.denominator}}}$", base_extension.integer, b,
                      frac_part, f"${cfrac}$ ", sep=" & ", end="\\\\\n")


CPU_COUNT = os.cpu_count()
MIN_COVERAGE = 1e4
CHUNK_LENGTH = int(MIN_COVERAGE // max(CPU_COUNT - 1, 1))


def main():
    with Pool(CPU_COUNT) as pool:

        print(f"Will now run parallelized with {CPU_COUNT} threads")
        base_range = range(2, 1000)

        pool.starmap(pretty_print, [(
            base_range, range(i * CHUNK_LENGTH, (i+1) * CHUNK_LENGTH), 1) for i in range(CPU_COUNT)])


if __name__ == '__main__':
    main()
