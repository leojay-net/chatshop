from rest_framework import serializers
from .models import ChatHistory

class ChatHistorySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    history = serializers.ReadOnlyField()
    products = serializers.ListField(read_only=True)

    class Meta:
        model = ChatHistory
        fields = '__all__'
