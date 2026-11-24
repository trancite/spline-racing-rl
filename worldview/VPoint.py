import numpy as np

class VPoint:   
    def __init__(self,x = 0, y = 0):
        self.x=x
        self.y=y
        self.p = np.array([x,y])

    def __repr__(self):
        return f"({self.x},{self.y})"
    
