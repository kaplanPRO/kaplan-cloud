from pathlib import Path

from lxml import etree
import regex

def get_kpp_path(instance, filename):
    return str(Path(instance.project.directory) / 'packages' / filename)
def get_source_file_path(instance, filename):
    return instance.get_source_directory() / filename
def get_target_file_path(instance, filename):
    return instance.get_target_directory() / filename
def trim_segment(source_or_target_segment):
    source_or_target_segment = etree.tostring(source_or_target_segment, encoding='UTF-8') \
                                .decode()
    if regex.match('<[^<>]+/>', source_or_target_segment):
        return ''
    else:
        return regex.match('<[^<>]+>(.*)</[^<>]+>', source_or_target_segment).group(1)
