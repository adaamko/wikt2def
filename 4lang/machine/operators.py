from machine import Machine

class Operator(object):
    """The abstract superclass of the operator hierarchy."""
    def __init__(self, working_area=None):
        """The working area is that of the enclosing Construction."""
        self.working_area = working_area

    def act(self, seq):
        """
        Acts on the machines in the randomly accessible sequence @p seq.
        @note The indices of the machines affected by the operation must be
              specified in the constructor.
        """
        pass


class AppendOperator(Operator):
    """Appends a machine to another's partition: <tt>X, Y -> X[Y]</tt>."""
    def __init__(self, X, Y, part=0, working_area=None):
        """
        @param X index of the machine to whose partition Y will be appended.
        @param Y index of the machine to be appended.
        @param part the partition index.
        """
        Operator.__init__(self, working_area)
        self.X = X
        self.Y = Y
        self.part = part

    def act(self, seq):
        seq[self.X].append(seq[self.Y], self.part)
        return [seq[self.X]]

class AppendToBinaryOperator(Operator):
    """appends two machines to the partitions of a binary relation"""

    def __init__(self, bin_rel, first_pos, second_pos, reverse=False,
                 working_area=None):
        # TODO type checking of what to be binary
        Operator.__init__(self, working_area)
        self.bin_rel = bin_rel
        if not reverse:
            self.first_pos = first_pos
            self.second_pos = second_pos
        else:
            self.first_pos = second_pos
            self.second_pos = first_pos

    def __str__(self):
        return "{0}: {1}({2}, {3})".format(
            type(self), self.bin_rel, self.first_pos, self.second_pos)

    def act(self, seq):
        #logging.info("appending machines {0} and {1} to binary {2}".format(
        #    seq[self.first_pos], seq[self.second_pos], self.bin_rel))
        self.bin_rel.append(seq[self.first_pos], 1)
        self.bin_rel.append(seq[self.second_pos], 2)
        return [self.bin_rel]

class AppendToNewBinaryOperator(AppendToBinaryOperator):
    """will create a new binary machine every time it's used"""

    def act(self, seq):
        # logging.info(
        #    "appending machines {0} and {1} to new binary {2}".format(
        #        seq[self.first_pos], seq[self.second_pos], self.bin_rel))
        rel_machine = Machine(self.bin_rel)
        rel_machine.append(seq[self.first_pos], 1)
        rel_machine.append(seq[self.second_pos], 2)
        return [rel_machine]
