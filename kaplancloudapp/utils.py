from pathlib import Path

def get_source_file_path(instance, filename):
    return str(Path(instance.project.directory) / instance.source_language / filename)
def get_target_file_path(instance, filename):
    return str(Path(instance.project.directory) / instance.target_language / filename)
