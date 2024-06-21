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

    def _fetch_data(self, endpoint, offset=0, all_data=None):

        if all_data is None:
            all_data = []
            offset = 0

        limit = 20
        params = {
            "limit": limit,
            "offset": offset
        }
        url = f"{self.base_url}/{endpoint}"

        if (self.debug):
            print(
                f"Calling {endpoint} url={url}, offset={offset}, allData={ 0 if all_data == None else len(all_data)}")

        response = requests.get(url=url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data['items'])
            if len(data['items']) == limit:
                return self._fetch_data(endpoint, offset + limit, all_data)
            else:

                return all_data
        else:
            print(f"Failed to fetch members: {response.status_code}")
            print(response.json())
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
                team_roles_details = self._fetch_data(
                    f'teams/{team.get("key")}/roles')

                team_roles = []
                for role_detail in team_roles_details:
                    team_roles.append(role_detail['key'])
                team['customRoleKeys'] = team_roles
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
