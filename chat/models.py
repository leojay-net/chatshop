from django.db import models

class ChatHistory(models.Model):
    session_key = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=False, null=False)
    input = models.TextField()
    history = models.JSONField(default=list, blank=True)
