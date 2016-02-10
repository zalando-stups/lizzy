
class ObjectNotFoundException(Exception):
    def __init__(self, uid):
        self.uid = uid
