from django import forms


class DismissNotificationForm(forms.Form):
    pk = forms.IntegerField(required=True, min_value=1)
