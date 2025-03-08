from django.shortcuts import render, redirect, reverse
from django.conf import settings
from .models import *
from django.http import HttpResponse
from django.contrib import messages
import logging
import os

# Configure logging
log_file_path = os.path.join(settings.BASE_DIR, 'logs', 'app.log')  # Path to the log file
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)  # Ensure the directory exists

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'core/index.html')

def pricing(request):
    return render(request, 'core/pricing.html')