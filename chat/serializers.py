from rest_framework import serializers
from .models import ChatHistory

class ChatHistorySerializer(serializers.ModelSerializer):
    history = serializers.ReadOnlyField()
    products = serializers.ListField(read_only=True)

    class Meta:
        model = ChatHistory
        fields = ['session_key', 'email', 'input', 'history', 'products']
