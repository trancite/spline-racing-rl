from worldview.WPoint import *
from worldview.VPoint import *
import numpy as np

class WorldView:

    def __init__(self, wMin, wMax, vMin, vMax):
        self.wMin = wMin
        self.wMax = wMax
        self.vMin = vMin
        self.vMax = vMax
        self.scale_x = 1.0
        self.scale_y = 1.0
        self._update_scale()
       
    def __repr__(self) :
        s = f"World=({self.wMin.x},{self.wMin.y}) to ({self.wMax.x},{self.wMax.y}) "
        s += f"View=({self.vMin.x},{self.vMin.y}) to ({self.vMax.x},{self.vMax.y})"
        return s


    def _update_scale(self):
        wx = self.wMax.p[0] - self.wMin.p[0]
        wy = self.wMax.p[1] - self.wMin.p[1]
        vx = self.vMax.p[0] - self.vMin.p[0]
        vy = self.vMax.p[1] - self.vMin.p[1]

        self.scale_x = vx / wx if wx != 0 else 0.0
        self.scale_y = vy / wy if wy != 0 else 0.0

    def center(self, world_x, world_y, width, height):
        self.wMin.p = np.array([world_x - width/2, world_y - height/2])
        self.wMax.p = np.array([world_x + width/2, world_y + height/2])
        
        self.wMin.x, self.wMin.y = self.wMin.p
        self.wMax.x, self.wMax.y = self.wMax.p
        
        self._update_scale()


    def worldToView(self, Wp: WPoint) -> VPoint:
        x, y = Wp.p
        vx = (x - self.wMin.p[0]) * self.scale_x + self.vMin.p[0]
        vy = (self.wMax.p[1] - y) * self.scale_y + self.vMin.p[1]
        return VPoint(int(vx), int(vy))

    def worldToViewXY(self, x: float, y: float) -> VPoint:      
        return self.worldToView(WPoint(x, y))
    

    def centre_around_points(self, p1, p2, padding=100):
        centre_x = (p1[0] + p2[0]) / 2
        centre_y = (p1[1] + p2[1]) / 2
        dist_x = abs(p1[0] - p2[0]) + padding
        dist_y = abs(p1[1] - p2[1]) + padding
        distance = max(dist_x, dist_y, 0)
        self.center(centre_x, centre_y, distance, distance)

    def viewToWorld(self, Vp):
        x, y = Vp.p

        wx = (x - self.vMin.p[0]) / self.scale_x + self.wMin.p[0] if self.scale_x != 0 else self.wMin.p[0]

        wy = self.wMax.p[1] - ((y - self.vMin.p[1]) / self.scale_y) if self.scale_y != 0 else self.wMin.p[1]

        return WPoint(wx, wy)

    def viewToWorldXY(self, x: int, y: int) -> WPoint:
        return self.viewToWorld(VPoint(x, y))
    
    def translateWindow(self, dx, dy):
        self.wMin.p += [dx, dy]
        self.wMax.p += [dx, dy]
