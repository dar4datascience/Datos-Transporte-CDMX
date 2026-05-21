import json
from pathlib import Path

class AppConfig:
    def __init__(self, metadata_path):
        self.BASE_DIR = Path(metadata_path).parent
        self.METADATA_PATH = metadata_path
        self.AUTH_URL = "https://metrobus-gtfs.sinopticoplus.com/gtfs-api/partnerValidation"
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        
        self.LINES = sorted(self.metadata["lines"].keys(), key=lambda x: int(x))
        self.LINE_CHOICES = {line: f"Línea {line}" for line in self.LINES}
        
        self.ROUTE_TO_LINE = {}
        self.ROUTE_ID_TO_NAME = {}
        for line_num, line_data in self.metadata["lines"].items():
            for route in line_data["routes"]:
                rid_str = str(route["route_id"])
                self.ROUTE_TO_LINE[rid_str] = line_num
                self.ROUTE_ID_TO_NAME[rid_str] = route["name"]
