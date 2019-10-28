from django.shortcuts import reverse

from apps.notifications.models import Notification


def connection_notifications(backend, user, response, *args, **kwargs):
    if backend.name in ['sharemyhealth']:
        print(type(backend), backend)
        # Dismiss the notification prompting the user to connect
        notifications = Notification.objects.filter(
            notify_id=user.id,
            actor_id=user.id,
            actions__contains=f'''"url": "{reverse('social:begin', args=[backend.name])}"''',
        )
        for notification in notifications:
            notification.dismissed = True
            notification.save()

        # Dismiss any notifications related to this backend
        action_url = reverse('social:disconnect', args=[backend.name])
        notifications = Notification.objects.filter(
            notify_id=user.id,
            actor_id=user.id,
            actions__contains=f'''"url": "{action_url}"''',
        )
        for notification in notifications:
            notification.dismissed = True
            notification.save()

        # Create a notification that the user connected to the backend
        Notification.objects.create(
            notify=user,
            actor=user,
            actions=[{'url': action_url, 'text': 'Disconnect'}],
            message=f'You connected to <b>{backend.name}</b>',
        )


def disconnection_notifications(backend, user, *args, **kwargs):
    if backend.name in ['sharemyhealth']:
        # Dismiss any notifications related to this backend
        action_url = reverse('social:disconnect', args=[backend.name])
        notifications = Notification.objects.filter(
            notify_id=user.id,
            actor_id=user.id,
            actions__contains=f'''"url": "{action_url}"''',
        )
        for notification in notifications:
            notification.dismissed = True
            notification.save()
