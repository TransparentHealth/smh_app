from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from .forms import DismissNotificationForm
from .models import Notification


class DismissNotificationView(LoginRequiredMixin, View):
    http_method_names = ['post', 'get']

    def get(self, request, **kwargs):
        return self.post(request, **kwargs)

    def post(self, request, **kwargs):
        form = DismissNotificationForm(kwargs)
        if not form.is_valid():
            # Notification.pk missing or invalid
            return HttpResponse(status=422)
        else:
            try:
                notification = Notification.objects.get(
                    pk=form.cleaned_data.get('pk'))

                # the request.user must be the notify user, or an agent of the
                # notify org.
                if (
                    'user' in str(notification.notify_content_type)
                    and notification.notify_id != request.user.id
                ) or (
                    'organization' in str(notification.notify_content_type)
                    and notification.notify_id
                    not in [org.pk for org in request.user.agent_organizations.all()]
                ):
                    raise Notification.DoesNotExist()

                notification.dismissed = True
                notification.save()

            except Notification.DoesNotExist:
                raise Http404("Notification does not exist")

        if request.GET.get('next'):
            return redirect(request.GET.get('next'))
        else:
            return redirect(reverse('home'))
