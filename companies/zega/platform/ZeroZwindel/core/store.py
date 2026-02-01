import os
import requests
import json
import hashlib
from dotenv import load_dotenv

# Load variables from the root .env file
load_dotenv()

class ZegaCloudManager:
    def __init__(self):
        self.base_url = "https://getgameszerozwindel.netlify.app"
        self.api_url = "https://api.netlify.com/api/v1"
        self.token = os.getenv("NETLIFY_AUTH_TOKEN")
        self.site_id = os.getenv("NETLIFY_SITE_ID")
        
        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
            print("ZEGA Security Alert: NETLIFY_AUTH_TOKEN not found in .env")

    def get_cloud_catalog(self):
        """Fetches and parses the {'games': [...]} dictionary format."""
        try:
            resp = requests.get(f"{self.base_url}/games.json", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                slugs = data.get("games", []) if isinstance(data, dict) else data
                return [{"id": s, "name": s.replace("_", " ").title()} for s in slugs if s.lower() != "games"]
        except Exception as e:
            print(f"ZZ Cloud Sync Error: {e}")
        return []

    def download_game(self, slug):
        """Downloads assets from /games/<slug>/ into local storage."""
        local_dir = os.path.join("games", slug)
        os.makedirs(local_dir, exist_ok=True)
        assets = ["manifest.json", "main.py", "displayimage.png"]
        
        for file_name in assets:
            asset_url = f"{self.base_url}/games/{slug}/{file_name}"
            try:
                r = requests.get(asset_url, stream=True, timeout=15)
                if r.status_code == 200:
                    with open(os.path.join(local_dir, file_name), 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    print(f"404: {file_name} missing at {asset_url}")
            except Exception as e:
                print(f"Network Failure: {e}")
        return True

    def deploy_new_game(self, local_path):
        """Executive Atomic Deploy: Syncs ALL games to prevent 404s."""
        if not self.token or not self.site_id:
            print("ZEGA Error: Credentials missing in .env")
            return False

        print("ZZ Platform: Initializing Full-State Cloud Sync...")

        # 1. Update the Master Index locally
        new_slug = os.path.basename(local_path)
        catalog_data = self._fetch_raw_catalog()
        if new_slug not in catalog_data["games"]:
            catalog_data["games"].append(new_slug)
        
        with open("games.json", "w") as f:
            json.dump(catalog_data, f)

        # 2. Map EVERYTHING in the local 'games/' directory
        file_map = {"/games.json": self._sha1("games.json")}
        actual_paths = {"/games.json": "games.json"}
        
        base_games_dir = "games" 
        for root, dirs, files in os.walk(base_games_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # Map to cloud path style
                rel_path = "/" + os.path.relpath(full_path, ".").replace("\\", "/")
                file_map[rel_path] = self._sha1(full_path)
                actual_paths[rel_path] = full_path

        # 3. Handshake & Upload
        try:
            endpoint = f"{self.api_url}/sites/{self.site_id}/deploys"
            resp = requests.post(endpoint, json={"files": file_map}, headers=self.headers)
            
            if resp.status_code in [200, 201]:
                deploy_data = resp.json()
                deploy_id = deploy_data['id']
                required_hashes = deploy_data.get('required', [])
                
                print(f"ZZ Cloud: Syncing {len(required_hashes)} assets...")

                for rel_path, file_hash in file_map.items():
                    if file_hash in required_hashes:
                        with open(actual_paths[rel_path], "rb") as f:
                            content = f.read()
                        upload_url = f"{self.api_url}/deploys/{deploy_id}/files{rel_path}"
                        requests.put(upload_url, data=content, 
                                     headers={**self.headers, "Content-Type": "application/octet-stream"})
                
                print(f"ZZ Cloud: Atomic Sync Complete. Site is LIVE.")
                return True
            else:
                print(f"Handshake Error: {resp.status_code}")
                return False
        except Exception as e:
            print(f"Sync Failure: {e}")
            return False

    def _fetch_raw_catalog(self):
        """Standard helper for JSON catalog state."""
        try:
            r = requests.get(f"{self.base_url}/games.json", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "games" in data:
                    return data
        except:
            pass
        return {"games": []}

    def _sha1(self, path):
        """Generates SHA1 hash for Netlify verification."""
        with open(path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()