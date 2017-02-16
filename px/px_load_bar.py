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
    pass
