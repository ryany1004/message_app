from rest_framework import serializers

from messaging_app.messaging.models import Thread, Message, UserThread
from messaging_app.users.api.serializers import UserSerializer


class UserThreadSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserThread
        fields = ['unread', 'deleted', 'user', 'id', 'is_sender']


class ThreadSerializer(serializers.ModelSerializer):
    users = UserThreadSerializer(source='userthread_set', many=True)
    message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['subject', 'users', 'message', 'id']

    def get_message(self, obj):
        return MessageSerializer(obj.first_message()).data


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'sent_at']
