class level(str):

    def __gt__(self, other):
        return PRECEDENCE_LOOKUP[self] > PRECEDENCE_LOOKUP[other]

    def __ge__(self, other):
        print("ge", PRECEDENCE_LOOKUP[self], PRECEDENCE_LOOKUP[other])
        return PRECEDENCE_LOOKUP[self] >= PRECEDENCE_LOOKUP[other]

    def __lt__(self, other):
        print("lt", PRECEDENCE_LOOKUP[self], PRECEDENCE_LOOKUP[other])
        return PRECEDENCE_LOOKUP[self] < PRECEDENCE_LOOKUP[other]

    def __le__(self, other):
        print("le", PRECEDENCE_LOOKUP[self], PRECEDENCE_LOOKUP[other])
        return PRECEDENCE_LOOKUP[self] <= PRECEDENCE_LOOKUP[other]


PRECEDENCE = ("QUIET", "LOW", "MEDIUM", "HIGH")
PRECEDENCE_LOOKUP = dict(zip(PRECEDENCE, range(0, len(PRECEDENCE))))
QUIET, LOW, MEDIUM, HIGH = map(level, PRECEDENCE)
