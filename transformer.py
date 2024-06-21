import pandas as pd
from custom_utils import Utils
import datetime


class Transformer():
    def __init__(self, roles: dict = None, members: dict = None, teams: dict = None, save=False):
        self.roles_source = {} if roles is None else roles
        self.roles_df = None

        self.policies = {}

        self.teams_source = {} if teams is None else teams
        self.teams_df = None

        self.members_source = {} if members is None else members
        self.members_df = None

        self.summary_metrics = {}
        self.save = save

    def process(self):

        self._prep_roles()
        self._prep_members()
        self._prep_teams()

        self._update_members_assigned_roles()
        self._update_teams_assigned_roles()

        self._generate_summary_metrics()

        if self.save == True:
            self._save_data()

    def convert_role_id_to_key(self, arr_lookup):

        role_id_map = {item["_id"]: item["key"] for item in self.roles_source}
        result = [role_id_map.get(_id, None)
                  for _id in arr_lookup if _id in role_id_map]

        return [key for key in result if key is not None]

    def _generate_summary_metrics(self):
        user_assigned_custom_roles = [role for sublist in self.members_df['customRoles']
                                      for role in sublist]

        team_assigned_custom_roles = [role for sublist in self.teams_df['customRoleKeys']
                                      for role in sublist]
        total_custom_role = len(self.roles_df)

        distict_user_assigned_custom_roles = len(
            set(user_assigned_custom_roles))
        distict_team_assigned_custom_roles = len(
            set(team_assigned_custom_roles))

        # user_assigned_custom_roles = self.convert_role_id_to_key(
        #     user_assigned_custom_roles)

        distinct_combined_roles = set(
            user_assigned_custom_roles + team_assigned_custom_roles)

        total_assigned_distinct_role = len(distinct_combined_roles)

        orphaned_roles = total_custom_role - len(distinct_combined_roles)

        total_users = len(self.members_df)
        total_custom_role = len(self.roles_df)
        total_teams = len(self.teams_df)
        total_members_custom_roles_count = self.members_df['customRoles_count'].sum(
        )
        total_users_custom_roles_count = self.teams_df['customRoleKeys_count'].sum(
        )
        total_permissions_count = self.roles_df['permission_count'].sum()
        self.summary_metrics = {
            'role_to_user_ratio': total_members_custom_roles_count / total_users,
            'role_to_team_ratio': total_users_custom_roles_count / total_teams,
            'total_custom_role': total_custom_role,

            'orphaned_roles': orphaned_roles,

            'permission_to_role_ratio':  total_permissions_count / total_custom_role,

            'user_assigned_custom_roles': user_assigned_custom_roles,
            'team_assigned_custom_roles': team_assigned_custom_roles,
            'total_assigned_roles': total_assigned_distinct_role,
            'distict_user_assigned_custom_roles': distict_user_assigned_custom_roles,
            'distict_team_assigned_custom_roles': distict_team_assigned_custom_roles,

        }

        return self.summary_metrics

    def _update_members_assigned_roles(self):

        member_lookup = {m["_id"]: m["customRoles"]
                         for m in self.members_df.to_dict(orient="records")}
        role_lookup = {
            r["key"]: r for r in self.roles_df.to_dict(orient="records")}

        for role_key, role_data in role_lookup.items():
            for member_id, member_roles in member_lookup.items():
                if "members" not in role_data:
                    role_data['members'] = []
                    role_data['members_count'] = 0

                if role_key in member_roles:
                    role_data["members"].append(member_id)
                    role_data['members_count'] += 1

        self.roles_df = pd.DataFrame(role_lookup.values())

    def _update_teams_assigned_roles(self):

        team_lookup = {t["key"]: t["customRoleKeys"]
                       for t in self.teams_df.to_dict(orient="records")}
        role_lookup = {
            r["key"]: r for r in self.roles_df.to_dict(orient="records")}
        for role_key, role_data in role_lookup.items():
            for team_key, team_data in team_lookup.items():
                if "teams" not in role_data:
                    role_data['teams'] = []
                    role_data['teams_count'] = 0

                if role_key in team_data:
                    role_data["teams"].append(team_key)
                    role_data['teams_count'] += 1

        self.roles_df = pd.DataFrame(role_lookup.values())

    def _prep_roles(self):
        roles = []
        for iter in self.roles_source:

            _id = iter.get('_id')
            del iter['_links']

            policy = iter['policy']
            self.policies[_id] = policy
            # count numbe rof permission statements in the policy
            iter['permission_count'] = len(policy)

            roles.append(iter)

        self.roles_df = pd.DataFrame(roles)

    def _days_from_today(self, unix_time_ms):
        today = datetime.datetime.today()
        input_dte = datetime.datetime.fromtimestamp(unix_time_ms / 1000)
        return (today - input_dte).days

    def _prep_members_item(self, iter):
        del iter['_links']
        iter['quickstartStatus'] = ""
        iter['hasPermissionGrants'] = False
        iter['isTeamMaintainer'] = False
        iter['customRoles_count'] = 0
        iter['hasCustomRoles'] = False
        iter['isTeamMember'] = False
        iter['team_list'] = []
        iter['teams_count'] = 0

        if iter.get('permissionGrants') is not None and len(iter.get('permissionGrants')) > 0:
            iter['isTeamMaintainer'] = True
            iter['hasPermissionGrants'] = True
            del iter['permissionGrants']

        iter['customRoles'] = self.convert_role_id_to_key(iter['customRoles'])
        iter['customRoles_count'] = len(iter['customRoles'])
        iter['hasCustomRoles'] = iter['customRoles_count'] > 0

        if iter.get('teams') is not None and len(iter.get('teams')) > 0:
            iter['isTeamMember'] = True
            teams = iter['teams']
            iter['teams_count'] = len(teams)
            for team in teams:
                iter['team_list'].append(team['key'])
            del iter['teams']

        if iter['_lastSeen'] < iter['creationDate']:
            # handle invalid data
            iter['_lastSeen'] = iter['creationDate']

        iter['days_since_last_seen'] = self._days_from_today(iter['_lastSeen'])

    def _prep_members(self):
        members = []
        for iter in self.members_source:
            self._prep_members_item(iter)
            members.append(iter)

        self.members_df = pd.DataFrame(members)

    def _prep_teams(self):
        teams = []
        for iter in self.teams_source:
            _id = iter.get('_id')
            del iter['_links']
            iter['customRoleKeys_count'] = len(iter['customRoleKeys'])
            teams.append(iter)

        self.teams_df = pd.DataFrame(teams)

    def get_summary_metrics(self):
        return self.summary_metrics

    def get_members_df(self):
        return self.members_df

    def get_roles_df(self):
        return self.roles_df

    def get_teams_df(self):
        return self.teams_df

    def get_policies(self) -> dict:
        return self.policies

    def _save_data(self, msg=None):

        Utils.save_data_to_file(
            self.roles_df.to_dict(orient="records"), "./output/transformer-out-roles.json")

        Utils.save_data_to_file(
            self.teams_df.to_dict(orient="records"), "./output/transformer-out-teams.json")

        Utils.save_data_to_file(
            self.members_df.to_dict(orient="records"), "./output/transformer-out-members.json")

        Utils.save_data_to_file(
            self.policies, "./output/transformer-out-policies.json")


def main():

    roles = Utils.read_json_file("./output/roles.json")
    teams = Utils.read_json_file("./output/teams.json")
    members = Utils.read_json_file("./output/members.json")
    transformer = Transformer(roles=roles, members=members, teams=teams)
    transformer.process()

    Utils.save_data_to_file(
        transformer.roles, "./output/transformer-out-roles.json")

    Utils.save_data_to_file(
        transformer.teams, "./output/transformer-out-teams.json")

    Utils.save_data_to_file(
        transformer.members, "./output/transformer-out-members.json")

    members_df = transformer.member_df
    print(members_df['customRoles'])
    print(members_df['customRoles_count'].mean())


if __name__ == '__main__':
    main()
