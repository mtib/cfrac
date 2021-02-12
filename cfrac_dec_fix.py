from decimal import getcontext, Decimal

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


def main():
    sb_iter = fractions()
    for i in range(10000000):
        sb = next(sb_iter)
        base_extension = sb.to_base(10)
        cfrac = sb.to_cfrac()
        #print(i+1, sb, base_extension, cfrac)
        if cfrac.sequence[1:] == base_extension.frac_digits:
            print(i+1, "found a match!", sb, base_extension, cfrac)


if __name__ == '__main__':
    main()
