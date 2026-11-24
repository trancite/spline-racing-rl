from entities.RoadMaker.RoadMakerManager import RoadMakerManager
from entities.RoadMaker.RoadMakerRenderer import RoadMakerRenderer
import json


class RoadMaker:
    def __init__(self, canvas):
        self.manager = RoadMakerManager()
        self.renderer = RoadMakerRenderer(canvas)

    def on_click(self, world_x, world_y, current_selected_degree):
        self.manager.handle_input(world_x, world_y)
        self.manager.set_degree(current_selected_degree) 
        data = self.manager.get_road_data()
        self.renderer.update_visuals(data)

    def render(self, wv):
        self.renderer.draw(wv)

    def get_final_data(self):
        return self.manager.get_road_data()
    
    def save_to_file(self, filename: str):
        import numpy as np
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            else:
                return obj
        data = self.manager.return_data_to_saved()
        data = convert(data)
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def cleanup(self):
        self.manager.checkpoints = []
        self.manager.is_periodic = False
        self.renderer.checkpoints = []
        self.renderer.clear()
        