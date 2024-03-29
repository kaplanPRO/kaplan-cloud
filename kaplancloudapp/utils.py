from pathlib import Path

from lxml import etree
import regex

def get_kpp_path(instance, filename):
    return str(Path(instance.project.directory) / 'packages' / filename)
def get_project_directory(instance):
    return str(Path('kaplancloudapp/projects/', str(instance.id)))
def get_reference_file_path(instance, filename):
    return Path(instance.project.directory, 'reference', filename)
def get_source_file_path(instance, filename):
    return Path(instance.project.directory, instance.project.source_language.iso_code, filename)
def get_target_file_path(instance, filename):
    return Path(instance.project.directory, instance.project.target_language.iso_code, filename)
def trim_segment(source_or_target_segment):
    source_or_target_segment = etree.tostring(source_or_target_segment, encoding='UTF-8') \
                                .decode()
    if regex.match('<[^<>]+/>', source_or_target_segment):
        return ''
    else:
        return regex.match('<[^<>]+>(.*)</[^<>]+>', source_or_target_segment).group(1)
