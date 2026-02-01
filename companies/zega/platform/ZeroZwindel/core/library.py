import os
import json
import subprocess
import sys

class LibraryManager:
    """
    ZEGA Executive Library Manager
    Engineered for Python 3.11. Handles game discovery, 
    nested dependency injection, and process execution.
    """
    def __init__(self, games_dir="games"):
        self.games_dir = games_dir
        # Ensure the executive directory exists
        if not os.path.exists(self.games_dir):
            os.makedirs(self.games_dir, exist_ok=True)

    def get_installed_games(self):
        """
        Scans the local storage for valid ZEGA projects.
        Returns metadata for the UI grid.
        """
        installed = []
        if not os.path.exists(self.games_dir):
            return installed

        for folder in os.listdir(self.games_dir):
            path = os.path.join(self.games_dir, folder)
            manifest_path = os.path.join(path, "manifest.json")
            
            if os.path.isdir(path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        installed.append({
                            "id": folder, 
                            "name": data.get("name", folder), 
                            "version": data.get("version", "1.0.0"),
                            "entry": data.get("entry", "main.py"),
                            # Correctly navigate to nested libs
                            "libs": data.get("requirements", {}).get("libs", [])
                        })
                except Exception as e:
                    print(f"ZEGA Library Error: Could not parse {folder}: {e}")
        return installed

    def install_dependencies(self, libs):
        """
        Executes a blocking 'py -3.11 -m pip install'.
        Returns True only if all libraries are secured.
        """
        if not libs:
            return True

        print(f"ZZ Platform: Synchronizing executive libraries: {', '.join(libs)}...")
        
        try:
            # We use 'py -3.11' to ensure compatibility with your preferred engine
            executable = "py"
            args = ["-3.11", "-m", "pip", "install"] + libs
            
            # Non-Windows support just in case
            if sys.platform != "win32":
                executable = "python3.11"
                args = ["-m", "pip", "install"] + libs

            # This is a blocking call. The app waits until pip finishes.
            result = subprocess.run(
                [executable] + args, 
                capture_output=True, 
                text=True, 
                check=True
            )
            print("ZZ Platform: Environment secured successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"ZEGA Critical: Dependency sync failed.")
            print(f"Pip Error Output:\n{e.stderr}")
            return False
        except Exception as e:
            print(f"ZEGA Critical: Unexpected error during sync: {e}")
            return False

    def launch_game(self, game_id):
        """
        Safety-Gated Launch Sequence:
        1. Parse Manifest requirements.
        2. Sync environment via pip.
        3. Boot project in isolated process.
        """
        game_path = os.path.abspath(os.path.join(self.games_dir, game_id))
        manifest_path = os.path.join(game_path, "manifest.json")
        
        if not os.path.exists(manifest_path):
            print(f"Launch Error: Project '{game_id}' is missing its manifest.json.")
            return

        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Targeting your specific nested structure
            requirements = data.get("requirements", {})
            libs = requirements.get("libs", [])
            entry_file = data.get("entry", "main.py")

        # PHASE 1: Dependency Gate
        if libs:
            print(f"ZZ Platform: Inspecting environment for {data.get('name')}...")
            success = self.install_dependencies(libs)
            if not success:
                print(f"ZZ Platform: ABORTING launch for {game_id} to prevent crash.")
                return 

        # PHASE 2: Execution
        entry_point = os.path.join(game_path, entry_file)
        
        if not os.path.exists(entry_point):
            print(f"Launch Error: Entry point '{entry_file}' not found in {game_id}.")
            return

        try:
            executable = "py -3.11" if os.name == 'nt' else "python3.11"
            print(f"ZZ Platform: Booting {game_id} via {executable}...")
            
            # CRITICAL: cwd=game_path allows the game to find its own files
            subprocess.Popen(
                f"{executable} \"{entry_point}\"", 
                shell=True, 
                cwd=game_path
            )
        except Exception as e:
            print(f"Critical Boot Failure: {e}")