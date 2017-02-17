class PxLoadBar(object):
    """
    Visualizes system load in a horizontal bar.

    Inputs are:
    * System load
    * Number of physical cores
    * Number of logical cores
    * How many columns wide the horizontal bar should be

    The output is a horizontal bar string.

    Load below the number of physical cores is visualized in green.

    Load between the number of physical cores and logical cores is visualized in
    yellow.

    Load above of the number of logical cores is visualized in red.

    As long as load is below the number of physical cores, it will use only the
    first half of the output string.

    Load up to twice the number of physical cores will go up to the end of the
    string.
    """

    def __init__(self, physical=None, logical=None):
        if physical is None or physical < 1:
            raise ValueError("Physical must be a positive integer")

        if logical is None or logical < physical:
            raise ValueError("Logical must be a positive integer >= physical (%r)" % physical)

        self._physical = physical
        self._logical = logical

        CSI = b"\x1b["
        self.normal = CSI + b"m"
        self.inverse = CSI + b"7m"
        self.red = CSI + b"41m"
        self.yellow = CSI + b"43m"
        self.green = CSI + b"42m"

    def get_bar(self, load=None, columns=None):
        if load is None:
            raise ValueError("Missing required parameter load=")

        if columns is None:
            raise ValueError("Missing required parameter columns=")

        return b''
