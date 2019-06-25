from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Notification
from .forms import DismissNotificationForm


class DismissNotificationView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, **kwargs):
        form = DismissNotificationForm(kwargs)
        if not form.is_valid():
            # Notification.pk missing or invalid
            raise HttpResponse(status=422)
        else:
            try:
                notification = Notification.objects.get(pk=form.cleaned_data.get('pk'))

                # the request.user must be the notify user, or an agent of the notify org.
                if (
                    notification.notify_content_type == 'auth.user'
                    and notification.notify_id != request.user.id
                ) or (
                    notification.notify_content_type == 'org.organization'
                    and notification.notify_id
                    not in [org.pk for org in request.user.organization_set.all()]
                ):
                    raise Notification.DoesNotExist

                notification.dismissed = True
                notification.save()

            except Notification.DoesNotExist:
                raise Http404("Notification does not exist")

        if request.GET.get('next'):
            return redirect(request.GET.get('next'))
        else:
            return redirect(reverse('home'))
