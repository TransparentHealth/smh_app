from social_django.middleware import SocialAuthExceptionMiddleware
from django.shortcuts import redirect
from django.urls import reverse
from social_core.exceptions import AuthCanceled


class AuthCanceledMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        """If AuthCanceled, redirect to home"""
        if isinstance(exception, AuthCanceled):
            return redirect(reverse('home'))
        else:
            return super().process_exception(request, exception)
