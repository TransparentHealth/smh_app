from django.shortcuts import reverse
from apps.notifications.models import Notification


def dismiss_connect_notification(backend, user, response, *args, **kwargs):
    if backend.name in ['sharemyhealth']:
        notification = Notification.objects.filter(
                notify_id=user.id, 
                actor_id=user.id, 
                actions__contains=f'''"url": "{reverse('social:begin', args=[backend.name])}"'''
            ).first()
        if notification:
            notification.dismissed = True
            notification.save()
