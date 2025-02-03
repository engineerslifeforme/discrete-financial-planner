from pathlib import Path
from types import SimpleNamespace

from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor
from yaml import safe_dump

class PlanEditor:

    def __init__(self, data: dict):
        self.processor = self.get_processor(data)

    @property
    def data(self):
        return self.processor.data

    def get_processor(self, data: dict):
        temp_file = Path(".temp_data.yaml")
        temp_file.write_text(safe_dump(data))
        logging_args = SimpleNamespace(quiet=True, verbose=False, debug=False)
        log = ConsolePrinter(logging_args)
        yaml = Parsers.get_yaml_editor()
        #yaml_file = "your-file.yaml"
        (yaml_data, doc_loaded) = Parsers.get_yaml_data(yaml, log, temp_file)
        temp_file.unlink()
        if not doc_loaded:
            exit(1)
        return Processor(log, yaml_data)
    
    def set_value(self, yaml_path: str, new_value):
        self.processor.set_value(yaml_path, new_value)

    def get_value(self, yaml_path: str):
        results = list(self.processor.get_nodes(yaml_path, mustexist=True))
        assert(len(results) == 1)
        return results[0]
        