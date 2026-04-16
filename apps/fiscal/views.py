"""Views do módulo Fiscal / NF-e."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    return render(request, "fiscal/list.html", {"title": "Fiscal / NF-e"})
