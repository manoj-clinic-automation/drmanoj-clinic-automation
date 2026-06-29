"""
WSGI entry point for production deployment.
For Hostinger / cPanel Python app setup.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application

# For direct WSGI servers (gunicorn, uWSGI)
if __name__ == "__main__":
    application.run()
