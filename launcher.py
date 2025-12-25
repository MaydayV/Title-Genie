import sys
import os
# Ensure we can find the streamlit module even if frozen
from streamlit.web import cli as stcli

def resolve_path(path):
    """
    Finds the absolute path to resources.
    Works for dev (local) and frozen (PyInstaller) modes.
    """
    if getattr(sys, "frozen", False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS'.
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
        
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # 1. Set the environment variable to stop Streamlit from trying to watch files in prod
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    
    # 2. Construct the arguments for the streamlit run command
    # equivalent to: streamlit run app.py
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"), # This locates app.py inside the bundle
        "--global.developmentMode=false",
    ]
    
    # 3. Execute Streamlit
    sys.exit(stcli.main())
