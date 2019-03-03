from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def organization_dashboard(request):
    return render(request, 'organization-dashboard.html', context={}) 
