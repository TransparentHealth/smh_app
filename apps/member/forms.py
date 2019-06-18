from django import forms
from apps.org.models import ResourceRequest


class ResourceRequestForm(forms.ModelForm):

    class Meta:
        model = ResourceRequest
        fields = '__all__'
