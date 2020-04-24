# pylint: disable=missing-class-docstring

class NotFound(Exception):
    pass


class StackNotFound(NotFound):
    pass


class StackOutputsNotFound(NotFound):
    pass


class StackCanNotBeProcessed(Exception):
    pass


class StackIsBeingProcessed(Exception):
    pass
