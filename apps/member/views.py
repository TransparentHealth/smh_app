from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def member_dashboard(request, subject=None):
    return render(request, 'member-dashboard.html', context={})

