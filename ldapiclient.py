import requests
import json
from dotenv import load_dotenv
import os


class LaunchDarklyAPIClient:
    def __init__(self, api_key, debug=False,  base_url="https://app.launchdarkly.com/api/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": self.api_key}
        self.debug = debug

    def _fetch_data(self, endpoint):
        all_data = []
        offset = 0
        limit = 20
        url = f"{self.base_url}/{endpoint}"

        while True:
            params = {"limit": limit, "offset": offset}

            if self.debug:
                print(f"Calling {endpoint} url={url}, offset={offset}, data_len={len(all_data)}")

            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                break 

            data = response.json()
            all_data.extend(data["items"])

            if len(data["items"]) != limit:
                break
            offset += limit

        return all_data

    def save_data_to_file(self, data, filename):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Data saved successfully to {filename}")
        except Exception as e:
            print(f"Error saving data to file: {e}")

    def list_and_save_members(self, filename="members.json"):
        members = self.list_members()
        self.save_data_to_file(members, filename)
        return members

    def list_and_save_custom_roles(self, filename="custom_roles.json"):
        custom_roles = self.list_custom_roles()
        self.save_data_to_file(custom_roles, filename)
        return custom_roles

    def list_and_save_teams(self, filename="teams.json"):
        teams = self.list_teams()
        self.save_data_to_file(teams, filename)
        return teams

    def list_members(self):
        try:
            return self._fetch_data("members")
        except Exception as e:
            print(f"Error listing members: {e}")
            return []

    def list_custom_roles(self):
        try:
            return self._fetch_data("roles")

        except Exception as e:
            print(f"Error listing custom roles: {e}")
            return []

    def list_teams(self):
        try:
            teams = self._fetch_data("teams")
            for team in teams:
                team_roles_details = self._fetch_data(f'teams/{team["key"]}/roles')
                team['customRoleKeys'] = [role['key'] for role in team_roles_details]

            return teams

        except Exception as e:
            print(f"Error listing teams: {e}")
            return []

def main():
    load_dotenv()
    API_KEY = os.getenv("LAUNCHDARKLY_API_KEY")
    DEBUG = os.getenv("DEBUG") or False

    client = LaunchDarklyAPIClient(API_KEY, DEBUG)
    client.list_and_save_teams("output/teams.json")
    client.list_and_save_custom_roles("output/roles.json")
    client.list_and_save_members("output/members.json")


if __name__ == '__main__':
    main()
