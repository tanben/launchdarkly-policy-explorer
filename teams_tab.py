import streamlit as st
import pandas as pd
import plotly.express as px


class TeamsTab:
    def __init__(self, roles, metrics, members, teams):
        self.roles = roles
        self.metrics = metrics
        self.members = members
        self.teams = teams

    def _render_teams_headsup_display(self):
        col1, col2 = st.columns([0.50, 0.50])
        with col1:
            self._most_assigned_roles_chart()

        with col2:
            self._assigned_team_roles_chart()

    def _most_assigned_roles_chart(self):
        df = pd.DataFrame(self.roles)
        top_5 = 5
        top_df = df.nlargest(top_5, "teams_count")
        top_df.index = top_df['teams_count']

        top_df.sort_index(ascending=True, inplace=True)

        fig = px.bar(top_df, x='teams_count', y='key', orientation='h',
                     labels={"key": "Custom Roles", "teams_count": "Teams"},
                     title=f"Top {top_5} Assigned Team Roles"
                     )
        st.plotly_chart(fig, theme="streamlit")

    def _assigned_team_roles_chart(self):
        fig = px.scatter(self.teams,
                         title="Roles per Team",
                         y="customRoleKeys_count", x="key",
                         color="key", size="customRoleKeys_count",
                         labels={"customRoleKeys_count": "Roles", "key": "Teams"}
                         )
        # fig.update_xaxes(showticklabels=False)
        st.plotly_chart(fig, theme="streamlit")

    def _render_teams_table(self):
        column_config = {
            '_lastModified': st.column_config.DatetimeColumn(
                format="YYYY-MMM-D, h:mm a",

            ),
        }

        st.markdown(f'##### Total Teams:{len(self.teams)}')

        st.dataframe(self.teams, hide_index=True, on_select="ignore", selection_mode="single-row", column_order=[
            "key", "name", "descripton", "customRoleKeys", "customRoleKeys_count", "_lastModified"],
            column_config=column_config)

        # st.help(self.teams)

    def render(self):
        self._render_teams_headsup_display()
        self._render_teams_table()
