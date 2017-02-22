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
            raise ValueError("Physical must be a positive integer, was: %r" % (physical,))

        if logical is None or logical < physical:
            raise ValueError("Logical must be >= physical, was: %r (vs %r)" % (logical, physical))

        self._physical = physical
        self._logical = logical

        CSI = b"\x1b["
        self.normal = CSI + b"m"
        self.inverse = CSI + b"0;7m"
        self.red = CSI + b"27;1;37;41m"
        self.yellow = CSI + b"27;1;37;43m"
        self.green = CSI + b"27;1;37;42m"

    def _get_colored_bytes(self, load=None, columns=None, text=""):
        "Yields pairs, with each pair containing a color and a byte"

        maxlength = columns - 2  # Leave room for a starting and an ending space
        if len(text) > maxlength:
            text = text[0:(maxlength - 1)]
        text = text + ' ' * (maxlength - len(text))
        text = " " + text + " "
        assert len(text) == columns

        max_value = self._physical
        if load > max_value:
            max_value = 1.0 * load

        UNUSED = 1000 * max_value
        if load < self._physical:
            yellow_start = UNUSED
            red_start = UNUSED
            inverse_start = load
            normal_start = self._physical
        else:
            yellow_start = self._physical
            red_start = self._logical
            inverse_start = UNUSED
            normal_start = load

        # Scale the values to the number of columns
        yellow_start = yellow_start * columns / max_value - 0.5
        red_start = red_start * columns / max_value - 0.5
        inverse_start = inverse_start * columns / max_value - 0.5
        normal_start = normal_start * columns / max_value - 0.5

        for i in range(columns):
            # We always start out green
            color = self.green

            if i >= yellow_start:
                color = self.yellow
            if i >= red_start:
                color = self.red
            if i >= inverse_start:
                color = self.inverse
            if i >= normal_start:
                color = self.normal

            yield (color, text[i].encode('utf-8'))

    def get_bar(self, load=None, columns=None, text=""):
        if load is None:
            raise ValueError("Missing required parameter load=")

        if columns is None:
            raise ValueError("Missing required parameter columns=")

        return_me = b''
        color = self.normal
        for color_and_byte in self._get_colored_bytes(load=load, columns=columns, text=text):
            if color_and_byte[0] != color:
                return_me += color_and_byte[0]
                color = color_and_byte[0]
            return_me += color_and_byte[1]

        if color != self.normal:
            return_me += self.normal

        return return_me
