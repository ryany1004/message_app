from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from messaging_app.messaging.signals import message_sent


class Thread(models.Model):

    subject = models.CharField(max_length=150)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="UserThread")

    @classmethod
    def inbox(cls, user):
        return cls.objects.filter(userthread__user=user, userthread__deleted=False, userthread__is_sender=False)

    @classmethod
    def sent(cls, user):
        return cls.objects.filter(userthread__user=user, userthread__deleted=False, userthread__is_sender=True)

    @classmethod
    def deleted(cls, user):
        return cls.objects.filter(userthread__user=user, userthread__deleted=True)

    @classmethod
    def unread(cls, user):
        return cls.objects.filter(
            userthread__user=user,
            userthread__deleted=False,
            userthread__unread=True
        )

    def __str__(self):
        return f"{self.subject}: {', '.join([str(user) for user in self.users.all()])}"

    def get_absolute_url(self):
        return reverse("pinax_messages:thread_detail", args=[self.pk])

    def first_message(self):
        return self.messages.all()[0]

    def latest_message(self):
        return self.messages.order_by("-sent_at")[0]

    @classmethod
    def ordered(cls, objs):
        """
        Returns the iterable ordered the correct way, this is a class method
        because we don"t know what the type of the iterable will be.
        """
        objs = list(objs)
        objs.sort(key=lambda o: o.latest_message.sent_at, reverse=True)
        return objs


class UserThread(models.Model):

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_sender = models.BooleanField(default=False)
    unread = models.BooleanField()
    deleted = models.BooleanField()


class Message(models.Model):

    thread = models.ForeignKey(Thread, related_name="messages", on_delete=models.CASCADE)

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
    sent_at = models.DateTimeField(default=timezone.now)

    content = models.TextField()

    @classmethod
    def new_reply(cls, thread, user, content):
        """
        Create a new reply for an existing Thread.
        Mark thread as unread for all other participants, and
        mark thread as read by replier.
        """
        msg = cls.objects.create(thread=thread, sender=user, content=content)
        thread.userthread_set.exclude(user=user).update(deleted=False, unread=True)
        thread.userthread_set.filter(user=user).update(deleted=False, unread=False)
        message_sent.send(sender=cls, message=msg, thread=thread, reply=True)
        return msg

    @classmethod
    def new_message(cls, from_user, to_users, subject, content):
        """
        Create a new Message and Thread.
        Mark thread as unread for all recipients, and
        mark thread as read and deleted from inbox by creator.
        """
        thread = Thread.objects.create(subject=subject)
        for user in to_users:
            thread.userthread_set.create(user=user, deleted=False, unread=True)
        thread.userthread_set.create(user=from_user, deleted=False, unread=False, is_sender=True)
        msg = cls.objects.create(thread=thread, sender=from_user, content=content)
        message_sent.send(sender=cls, message=msg, thread=thread, reply=False)
        return msg

    class Meta:
        ordering = ("sent_at",)

    def get_absolute_url(self):
        return self.thread.get_absolute_url()
