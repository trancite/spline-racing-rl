from entities.roads import SplineRoad


class RoadMakerRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.preview_road = None
        self.min_points_for_spline = 2

    def update_visuals(self, road_data):
        if self.preview_road:
            self.preview_road.destroy()
            self.preview_road = None
        
        # Only create spline preview if we have enough points
        if road_data and len(road_data.get("points", [])) >= self.min_points_for_spline:
            self.preview_road = SplineRoad(self.canvas, road_data)

    def draw(self, wv):
        if self.preview_road:
            self.preview_road.show(wv)

    def clear(self):
        if self.preview_road:
            self.preview_road.destroy()
            self.preview_road = None