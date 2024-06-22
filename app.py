from ldapiclient import LaunchDarklyAPIClient
from transformer import Transformer
from custom_utils import Utils
import streamlit as st

from roles_tab import RolesTab
from members_tab import MembersTab
from teams_tab import TeamsTab
from app_config import AppConfig
import random

class DetailsTab:
    def __init__(self, ld_data=None):
        teams_value, roles_value, members_value = ld_data.values()

        transformer = Transformer(
            save=app_config.save_data, roles=roles_value, members=members_value, teams=teams_value)

        transformer.process()

        self.roles = transformer.get_roles_df()
        self.members = transformer.get_members_df()
        self.teams = transformer.get_teams_df()
        self.metrics = transformer.get_summary_metrics()

        self.roles_tab = RolesTab(
            roles=self.roles, metrics=self.metrics, members=self.members, teams=self.teams)
        self.members_tab = MembersTab(
            roles=self.roles, metrics=self.metrics, members=self.members, teams=self.teams)
        self.teams_tab = TeamsTab(
            roles=self.roles, metrics=self.metrics, members=self.members, teams=self.teams)

    def show_roles_tab(self):
        self.roles_tab.render()

    def show_members_tab(self):
        self.members_tab.render()

    def show_teams_tab(self):
        self.teams_tab.render()


def _fetch_remote(app_config=None):
    client = LaunchDarklyAPIClient(app_config.access_token, app_config.debug)
    output_dir = 'output'

    ld_data = {
        "teams": client.list_teams(),
        "roles": client.list_custom_roles(),
        "members": client.list_members()
    }

    if not app_config.save_data:
        return ld_data
    
    teams_json = f"{output_dir}/teams.json"
    roles_json = f"{output_dir}/roles.json"
    members_json = f"{output_dir}/members.json"

    client.save_data_to_file(ld_data['teams'], teams_json)
    client.save_data_to_file(ld_data['roles'], roles_json)
    client.save_data_to_file(ld_data['members'], members_json)

    return ld_data


def _fetch_local():
    output_dir = 'output'

    ld_data = {
        "teams": Utils.read_json_file(f"{output_dir}/teams.json"),
        "roles":  Utils.read_json_file(f"{output_dir}/roles.json"),
        "members": Utils.read_json_file(f"{output_dir}/members.json")
    }
    return ld_data


def get_data(app_config=None):
    if app_config == None:
        st.error("app_config was not defind.")

    ld_data = None

    if app_config.read_local:
        # print("Reading locally")
        ld_data = _fetch_local()
    else:
        # print("Fetching data...")
        ld_data = _fetch_remote(app_config)

    return ld_data

def run_main(app_config=None):
    ld_data = None

    if app_config.access_token == None:
        st.warning("Please enter your access token.")
        return

    if app_config.debug:
        print(app_config)

    
    loading_message="Aligning our digital ducks in a row..."
    with st.spinner(loading_message):
        ld_data = get_data(app_config)

    roles_tab, members_tab, teams_tab = st.tabs(["Roles", "Members", "Teams"])
    detailsTab = DetailsTab(ld_data)
    with roles_tab:
        detailsTab.show_roles_tab()
    with members_tab:
        detailsTab.show_members_tab()
    with teams_tab:
        detailsTab.show_teams_tab()


if __name__ == "__main__":

    app_config = AppConfig()

    if app_config.debug:
        print(*vars(app_config).items(), sep="\n")

    st.set_page_config(layout="wide")
    input_container = st.container()
    content_container = st.empty()

    with input_container:
        st.header("Policy Analyzer")
        col1, col2 = st.columns(2)

        if app_config.read_local:
            with content_container.container():
                run_main(app_config)

        with col1:
            token_value = app_config.access_token
            if app_config.read_local:
                token_value = "Reading from local"

            app_config.access_token = st.text_input(label='API Access Token',
                                                    label_visibility="collapsed",
                                                    value=token_value,
                                                    key="access_token_input",
                                                    placeholder="API Access Token")

        with col2:
            if st.button("Analyze", key="execute_button"):
                with content_container.container():
                    analysis = run_main(app_config)
