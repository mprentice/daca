class InputTape:
    """A read-only input tape.

    The input tape is a sequence of squares each of which holds an integer. The
    only operation is to read a single symbol from the input tape, upon which
    the tape is moved one square to the right.

    """
    def __init__(self, seq=None):
        """Initialize a read-only input tape.

        seq is a sequence of integers. The InputTape instance will create a
        copy of this sequence for internal use. If no sequence is given, an
        empty tape is created.

        """
        if seq is None:
            self.seq = []
        else:
            self.seq = [item for item in seq]
        self.index = 0
    def __iter__(self):
        return self
    def next(self):
        """Read the next symbol from the input tape.

        Move one square to the right. Raises StopIteration if reading past the
        end of the tape.

        read is another alias for next.

        """
        if self.index >= len(self.seq):
            raise StopIteration
        item = self.seq[self.index]
        self.index += 1
        return item
    read = next

