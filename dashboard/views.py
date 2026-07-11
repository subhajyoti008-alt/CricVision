from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return HttpResponse("""
                        <h1>Welcome to CricVision</h1>
                        <p> Your local cricket platform is running.</p>
                        """)