from ldapiclient import LaunchDarklyAPIClient
from transformer import Transformer
from custom_utils import Utils
import streamlit as st

from roles_tab import RolesTab
from members_tab import MembersTab
from teams_tab import TeamsTab
from app_config import AppConfig
from zipfile import ZipFile
import io
import json
from faker import Faker


class DetailsTab:
    def __init__(self, transformer):
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


@st.cache_data(show_spinner=False, ttl=300)
def _fetch_remote(_app_config=None):
    client = LaunchDarklyAPIClient(_app_config.access_token, _app_config.debug)
    output_dir = _app_config.output_dir

    ld_data = {
        "teams": client.list_teams(),
        "roles": client.list_custom_roles(),
        "members": client.list_members(),
    }

    if not _app_config.save_data:
        return ld_data

    teams_json = f"{output_dir}/teams.json"
    roles_json = f"{output_dir}/roles.json"
    members_json = f"{output_dir}/members.json"

    client.save_data_to_file(ld_data['teams'], teams_json)
    client.save_data_to_file(ld_data['roles'], roles_json)
    client.save_data_to_file(ld_data['members'], members_json)

    return ld_data


def _fetch_local(_app_config=None):
    output_dir = _app_config.output_dir

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
        ld_data = _fetch_local(app_config)
    else:
        # print("Fetching data...")
        ld_data = _fetch_remote(app_config)

    return ld_data


def anonymize_data(data):
    fake = Faker()
    cp_data = data.copy()
    for item in cp_data:
        item['firstName'] = fake.first_name(
        ) if item.get('firstName') else None
        item['lastName'] = fake.last_name() if item.get('lastName') else None
        item['email'] = fake.email() if item.get('email') else None

    return cp_data


def run_main(app_config=None):
    st.session_state.ld_data = None

    if app_config.access_token == None and app_config.read_local is False:
        st.warning("Please enter your access token.")
        return

    loading_message = "Aligning our digital ducks in a row..."
    with st.spinner(loading_message):
        st.session_state.ld_data = get_data(app_config)

    transformer = Transformer(
        save=app_config.save_data, ld_data=st.session_state.ld_data)

    transformer.process(output_dir=app_config.output_dir)

    roles_tab, members_tab, teams_tab = st.tabs(["Roles", "Members", "Teams"])
    detailsTab = DetailsTab(transformer)
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
        st.header("Policy Explorer")
        col1, col2 = st.columns([0.5, 1])

        if app_config.read_local or st.session_state.get('download_clicked', False):
            with content_container.container():
                run_main(app_config)
                if 'download_clicked' in st.session_state:
                    del st.session_state['download_clicked']

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
            subcol1, subcol2 = st.columns([0.2, 1])

            with subcol1:
                if st.button("Analyze", key="execute_button",  on_click=lambda: st.session_state.update({'ld_data': None})):
                    with content_container.container():
                        analysis = run_main(app_config)

            with subcol2:
                if st.session_state.get('ld_data', None) is not None:
                    zip_buffer = io.BytesIO()
                    with ZipFile(zip_buffer, "w") as zipf:
                        for key, value in st.session_state.ld_data.items():
                            tmp_data = value

                            if app_config.anonymous_export and key == 'members':
                                tmp_data = anonymize_data(value)

                            zipf.writestr(
                                f"{key}.json", json.dumps(tmp_data, indent=4))

                    st.download_button(
                        label="export",
                        data=zip_buffer,
                        file_name="policies.zip",
                        mime="application/zip",
                        on_click=lambda: st.session_state.update(
                            {'download_clicked': True})
                    )
