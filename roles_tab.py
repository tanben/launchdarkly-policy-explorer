import streamlit as st
import pandas as pd
import plotly.express as px
import json


class RolesTab:
    def __init__(self, roles, metrics, members, teams):
        self.roles = roles
        self.metrics = metrics
        self.members = members
        self.teams = teams

    def _roles_assigned_categories(self):

        metrics_df = pd.DataFrame.from_dict(self.metrics, orient='index', columns=[
            'count'])

        # Make the labels a column
        metrics_df['metric'] = metrics_df.index

        filter_metrics = ['distict_user_assigned_custom_roles',
                          'distict_team_assigned_custom_roles', 'orphaned_roles']
        label_mapping = {
            'distict_user_assigned_custom_roles': 'User-Assigned Roles',
            'distict_team_assigned_custom_roles': 'Team-Assigned Roles',
            'orphaned_roles': 'Orphaned Roles'
        }

        metrics_df_filtered = metrics_df.loc[metrics_df["metric"].isin(
            filter_metrics)].copy()

        metrics_df_filtered.loc[:, 'label'] = metrics_df_filtered['metric'].map(
            label_mapping)
        # print(metrics_df_filtered)
        fig = px.pie(metrics_df_filtered, values='count', names='label',
                     title='Custom Roles: Assigned v Orphaned',
                     hover_data=['count'], labels=label_mapping,
                     hole=0.5)
        fig.update_traces(textposition='inside', textinfo='percent+label')

        st.plotly_chart(fig, theme="streamlit")

    def _most_assigned_roles_chart(self):
        metrics_df = pd.DataFrame(self.roles,
                                  columns=['permission_count', 'members_count', 'teams_count'], )

        metrics_df.index = self.roles['key']
        metrics_df['total'] = metrics_df['members_count'] + \
            metrics_df['teams_count']

        top_5_df = metrics_df.nlargest(5, "total")
        top_5_df.sort_index(ascending=False, inplace=True)
        del top_5_df['total']

        fig = px.imshow(top_5_df, text_auto=False,
                        title='Top 5 Assigned Custom Roles',
                        y=top_5_df.index,
                        aspect="auto",
                        x=['Permissions', 'Members', 'Teams', ],

                        )
        # fig.update_xaxes(side="top")
        fig.update_layout(width=400, height=400,
                          margin=dict(b=0, t=100))
        fig.update_traces(
            hovertemplate="Category: %{x}<br>Role: %{y}<br>Count: %{z}<extra></extra>"
        )
        st.plotly_chart(fig, theme="streamlit", config={
                        'displayModeBar': False})

    def _render_roles_headsup_display(self):
        col1, col2, col3, col4 = st.columns([0.40, 0.35, 0.10, 0.15])

        with col1:
            self._roles_assigned_categories()
        with col2:
            self._most_assigned_roles_chart()

        with col3:
            total_custom_roles = self.metrics.get('total_custom_role')
            assigned_count = self.metrics.get('total_assigned_roles')

            st.metric('Custom Roles',
                      total_custom_roles)

            st.metric('Orphaned',
                      delta_color="inverse",
                      value=self.metrics.get('orphaned_roles'))
            st.metric(label='Assigned',
                      value=assigned_count,
                      delta_color="normal",
                      )

            st.metric(label='Teams',
                      value=len(self.teams),
                      delta_color="normal",
                      )

        with col4:
            permission_count_threshold = 5
            role_to_team_ratio_threshold = 5
            st.metric("Role-to-User Ratio",
                      round(self.metrics.get('role_to_user_ratio'), 2))
            st.metric(label="Role-to-Team Ratio",
                      value=round(self.metrics.get(
                            'role_to_team_ratio'), 2),
                      delta_color="inverse",
                      )

            st.metric(label="Permissions per Role",
                      value=round(self.metrics.get(
                            'permission_to_role_ratio'), 2),
                      delta_color="normal",
                      )

            # permisions_min = 5
            # permissions_max = 10
            # permissions_ratio = round(
            #     self.metrics.get('permission_to_role_ratio'), 2)
            # if permissions_ratio < permisions_min or permissions_ratio > permissions_max:
            #     value_text = f"<span style='color:red'>{permissions_ratio}</span>"
            # else:
            #     value_text = permissions_ratio

            # st.markdown(f"""
            # <div class="element-container st-emotion-cache-1byvqvl e1f1d6gn4">
            #     <div style="font-size: 14px; font-weight:400;">Permissions Per Role</div>
            #     <div style="font-size: 2.25rem;">{value_text}</div>
            # </div>
            # """, unsafe_allow_html=True)

            st.metric(label='Members',
                      value=len(self.members),
                      delta_color="normal",
                      )

    def render_roles_table(self):
        column_config = {
            'key': st.column_config.Column(
                "custom roles",
                help="",
                width="medium",

            ),

            'orphan': st.column_config.Column(
                "orphan",
                help="Roles not assigned to members nor Teams",
                width="small",

            ),
            'members_count': st.column_config.Column(
                "members",
                help="Total assigned to members.",
                width="small",

            ),
            'teams_count': st.column_config.Column(
                "teams",
                help="Total assigned to Teams.",
                width="small",

            )
        }

        roles_table_df = self.roles[[
            'key', 'members_count', 'teams_count', 'policy']].copy()

        roles_table_df['orphan'] = (roles_table_df['members_count'] == 0) & (
            roles_table_df['teams_count'] == 0)

        roles_table_df["permission_count"] = self.roles["policy"].apply(
            lambda x: len(x))
        roles_table_df["policy"] = roles_table_df["policy"].apply(
            lambda x: json.dumps(x, indent=2))

        st.markdown('##### Custom Roles')
        st.dataframe(roles_table_df.style.background_gradient(
            cmap='Blues'),
            use_container_width=True,
            column_order=["key", "orphan", "members_count",
                          "teams_count", "permission_count", "policy"],
            column_config=column_config
        )

    def render(self):
        self._render_roles_headsup_display()
        self.render_roles_table()
