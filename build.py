import os
import subprocess
import sys
import nepali_datetime

def build():
    print("Starting Medi-Track Build Process...")
    
    # 1. Resolve nepali_datetime data path dynamically to avoid hardcoding site-packages
    nd_data_path = os.path.join(os.path.dirname(nepali_datetime.__file__), "data")
    print(f"Resolved nepali_datetime data path: {nd_data_path}")

    # 2. Get OS specific separator (; for Windows, : for Mac/Linux)
    sep = ';' if os.name == 'nt' else ':'
    add_data_arg = f"{nd_data_path}{sep}nepali_datetime/data"

    # 3. Construct flet pack command
    # Flet pack inherently understands flet and flet_desktop intricacies.
    # We only need to tell it about our custom views and dynamic data.
    import shutil
    flet_exe = shutil.which("flet")
    if not flet_exe:
        print("Error: flet command not found in PATH")
        sys.exit(1)
        
    cmd = [
        flet_exe, "pack", "main.py",
        "--name", "MediTrackNepal-Windows",
        "--add-data", add_data_arg,
        "--hidden-import", "views.dashboard",
        "--hidden-import", "views.inventory",
        "--hidden-import", "views.pos",
        "--hidden-import", "views.reports",
        "--hidden-import", "views.suppliers",
        "--hidden-import", "views.settings",
        "--hidden-import", "nepali_datetime",
        "--hidden-import", "nepali_date",
        "-y"
    ]

    print("Running command:", " ".join(cmd))
    
    # 4. Execute build
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("Build failed with return code", result.returncode)
        sys.exit(result.returncode)
        
    print("Build completed successfully!")

if __name__ == "__main__":
    build()
