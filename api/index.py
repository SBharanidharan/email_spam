import sys
import os

# Add root folder and backend folder to python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.append(root_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from backend.app.main import app
