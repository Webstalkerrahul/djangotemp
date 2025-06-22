from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


def dashboard(request):
    print("Dashboard page accessed")
    return render(request, "base.html")