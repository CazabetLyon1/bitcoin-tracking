
"""

"""


class Transaction:
    """

    """
    def __init__(self, inputs, outputs, timestamp):
        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = timestamp


class Address:
    """

    """
    def __init__(self, hash):
        self.hash = hash


class TransactionInput:
    """

    """
    def __init__(self, address, value):
        self.address = address
        self.value = value


class TransactionOutput:
    """

    """
    def __init__(self, address, value):
        self.address = address
        self.value = value
