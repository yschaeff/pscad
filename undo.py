from copy import deepcopy

class Undo():
    def __init__(self, limit):
        self.undo_history = []
        self.undo_index = 0

    def store(self, obj):
        while self.undo_index > 0:
            _ = self.undo_history.pop(0)
            self.undo_index -= 1
        self.undo_history.insert(0, deepcopy(obj))

    def undo(self):
        if self.undo_index+1 < len(self.undo_history):
            self.undo_index += 1
            node = deepcopy(self.undo_history[self.undo_index])
            return node
        else:
            return None

    def redo(self):
        if self.undo_index > 0:
            self.undo_index -= 1
            return deepcopy(self.undo_history[self.undo_index])
        else:
            return None
