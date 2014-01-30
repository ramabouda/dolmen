class CannotPay(Exception):
    pass

class TechnologyNeeded(Exception):
    def __init__(self, value):
        self.value = value

class InhabitantsError(Exception):
    pass
