from django.db import models

import json
import logging
import requests


class WebHook(models.Model):
  target = models.URLField()
  header = models.JSONField()

  class Meta:
    abstract = True

  def fire_hook(self, body: dict):
    try:
      requests.post(self.target, data=json.dumps(body), headers=self.header)
    except Exception as e:
      logging.error(e)


class ProjectWebHook(WebHook):
  project = models.ForeignKey('kaplancloudapp.Project', on_delete=models.CASCADE)

  def fire_hook(self):
    return super().fire_hook({'id': self.project.id, 'status': self.project.get_status()})


class ProjectFileWebHook(WebHook):
  project_file = models.ForeignKey('kaplancloudapp.ProjectFile', on_delete=models.CASCADE)

  def fire_hook(self):
    return super().fire_hook({'id': self.project_file.id, 'status': self.project_file.get_status()})
