import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_init, post_save, pre_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe

from apps.common.models import CreatedModel

# We can either notify a User or an Organization
# -- we're building this dynamically because we have to refer to it by PK, which we don't know
# (but which shouldn't change for a given installation unless this definition is changed.)

NOTIFICATION_ENTITY_CONTENT_TYPE_CHOICES = models.Q(
    app_label='org', model='organization'
) | models.Q(app_label='auth', model='user')


class Notification(CreatedModel, models.Model):
    """A notification such as will be displayed on a Member's or Organization's dashboard
    * created = timestamp when the notification was created
    * actor = the entity who did something
    * notify = the entity to notify
    * target = an optional entity who is the target of the action
    * instance = an optional object that is related to the notification (e.g., a ResourceRequest)
    * message = the notification message template; formatted with notification=self
    * actions = a JSON-formatted list of actions, each with form {'url': string, 'text': string}
    * dismissed = flag to indicate when the notification has been dismissed
    """

    notify_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=NOTIFICATION_ENTITY_CONTENT_TYPE_CHOICES,
        related_name="+",
    )
    notify_id = models.PositiveIntegerField()
    notify = GenericForeignKey('notify_content_type', 'notify_id')

    actor_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=NOTIFICATION_ENTITY_CONTENT_TYPE_CHOICES,
        related_name="+",
    )
    actor_id = models.PositiveIntegerField()
    actor = GenericForeignKey('actor_content_type', 'actor_id')

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=NOTIFICATION_ENTITY_CONTENT_TYPE_CHOICES,
        related_name="+",
        null=True,
    )
    target_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey('target_content_type', 'target_id')

    instance_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+", null=True
    )
    instance_id = models.PositiveIntegerField(null=True)
    instance = GenericForeignKey('instance_content_type', 'instance_id')

    type = models.TextField(null=True)

    message = models.TextField()
    picture_url = models.TextField(null=True)
    actions = models.TextField(default='[]')
    dismissed = models.BooleanField(default=False)

    # The GenericForeignKey fields should enable, e.g., notication.instance to return
    # the instance object. But they're not working, and that is throwing errors when
    # calling render_message (below). So we use the *_content_type object directly in
    # each of the get_* methods.

    def get_notify(self):
        if self.notify_id is not None and self.notify_content_type is not None:
            return self.notify_content_type.get_object_for_this_type(id=self.notify_id)

    def get_actor(self):
        if self.actor_id is not None and self.actor_content_type is not None:
            return self.actor_content_type.get_object_for_this_type(id=self.actor_id)

    def get_instance(self):
        if self.instance_id is not None and self.instance_content_type is not None:
            return self.instance_content_type.get_object_for_this_type(
                id=self.instance_id
            )

    def get_target(self):
        if self.target_id is not None and self.target_content_type is not None:
            return self.target_content_type.get_object_for_this_type(id=self.target_id)

    def render_message(self, **kwargs):
        return mark_safe(
            self.message.format(
                notify=self.get_notify(),
                actor=self.get_actor(),
                instance=self.get_instance(),
                target=self.get_target(),
                **kwargs,
            )
        )


# Notification.actions should be a list, but we can't use the postgres
# JSONField, so we do it here.


@receiver(pre_save, sender=Notification)
def notification_actions_to_json_string(sender, instance, **kwargs):
    """make sure instance.actions is a string before we try to save it."""
    if not isinstance(instance.actions, str):
        instance.actions = json.dumps(instance.actions)


@receiver([post_init, post_save], sender=Notification)
def notification_actions_from_json_string(sender, instance, **kwargs):
    """make sure instance.actions is data (list) after we initialize or save it."""
    if isinstance(instance.actions, str):
        instance.actions = json.loads(instance.actions)
