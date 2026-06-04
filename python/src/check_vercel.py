import json
import os
import sys
import urllib.request

token = os.environ.get("VERCEL_TOKEN")
if not token:
    print("Error: VERCEL_TOKEN environment variable not set.")
    sys.exit(1)

team_id = "team_fseDuby6ZsscVe9UOUhpXODr"

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode()), res.status
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode()
            return {"error": str(e), "body": err_body}, e.code
        except Exception:
            return {"error": str(e)}, e.code
    except Exception as e:
        return {"error": str(e)}, 500

print("=== Fetching Projects under Team ===")
url = f"https://api.vercel.com/v9/projects?teamId={team_id}"
projects_res, status = fetch(url)

if status == 200:
    projects = projects_res.get("projects", [])
    print(f"Found {len(projects)} projects.")
    for p in projects:
        print("\n-------------------------------------------")
        print(f"Project Name: {p.get('name')}")
        print(f"Project ID:   {p.get('id')}")

        # Git settings
        link = p.get("link", {})
        print(f"Repo:         {link.get('org')}/{link.get('repo') if link else 'N/A'}")
        print(f"Prod Branch:  {link.get('productionBranch') if link else 'N/A'}")

        # Ignored build steps
        print(f"Ignored Build Step Command: {p.get('commandForIgnoringBuildStep')}")

        # Environment variables summary
        envs = p.get("env", [])
        env_keys = [e.get("key") for e in envs]
        print(f"Env Variables ({len(env_keys)}): {', '.join(env_keys)}")
else:
    print(f"Failed to fetch projects. Status: {status}")
    print(json.dumps(projects_res, indent=2))
