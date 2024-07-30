from django.db import models
import uuid
class ChatHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session_key = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=False, null=False)
    input = models.TextField()
    history = models.JSONField(default=list, blank=True)
