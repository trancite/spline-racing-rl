import math
import numpy as np

class WPoint:
    def __init__(self, x=0.0, y=0.0):   
        self.x = x
        self.y = y
        self.p = np.array([x,y])

    def distance(self, other):
        return np.linalg.norm(self.p - other.p)

    def __repr__(self):
        return f"({self.x},{self.y})"