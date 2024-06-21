import streamlit as st
import pandas as pd
import plotly.express as px


class MembersTab:
    def __init__(self, roles, metrics, members, teams):
        self.roles = roles
        self.metrics = metrics
        self.members = members
        self.teams = teams

    def _render_members_headsup_display(self):
        last_30_days = 30
        self._create_utilization_metrics(last_30_days)

        col1, col2 = st.columns([0.75, 0.25])

        with col1:
            self._assigned_roles_chart(last_30_days)

        with col2:
            self._render_lastseen()

    def _get_unique_roles(self, member):
        all_roles = set(member['customRoles'])
        for team in member['team_list']:
            matching_team = self.teams[self.teams['key'] == team]
            if not matching_team.empty:
                all_roles.update(matching_team['customRoleKeys'].iloc[0])
        return list(all_roles)

    def _get_active_members_with_combined_roles(self, last_days_ago=0):

        if last_days_ago == 0:
            active_members_with_roles = pd.DataFrame(self.members)
        else:
            active_members_with_roles = self.members[self.members['days_since_last_seen']
                                                     <= last_days_ago].copy()
        active_members_with_roles.loc[:, 'unique_roles'] = active_members_with_roles.apply(
            self._get_unique_roles, axis=1)

        return active_members_with_roles

    def _get_inactive_members_with_combined_roles(self, older_than=30):

        inactive_members_with_roles = self.members[self.members['days_since_last_seen']
                                                   > older_than].copy()
        inactive_members_with_roles.loc[:, 'unique_roles'] = inactive_members_with_roles.apply(
            self._get_unique_roles, axis=1)

        return inactive_members_with_roles

    def _compute_role_utilization(self, last_days_ago):

        members_df = self._get_active_members_with_combined_roles(
            last_days_ago)

        df_exploded = members_df.explode('unique_roles')
        df_exploded = df_exploded.dropna(subset=['unique_roles'])

        all_roles = df_exploded['unique_roles'].unique()
        total_users = df_exploded['_id'].nunique()
        role_counts = df_exploded['unique_roles'].value_counts()

        utilization_rates = pd.DataFrame({'role': all_roles})
        utilization_rates['utilization_rate'] = utilization_rates['role'].apply(
            lambda x: role_counts.get(x, 0) / total_users * 100)
        utilization_rates['utilization_rate'] = utilization_rates['utilization_rate'].round(
            2)
        return utilization_rates

    def _get_role_count(self, last_days_ago):
        # todo: there got to be a better way to do this

        members_df = self._get_active_members_with_combined_roles(
            last_days_ago)

        exploded_df = members_df.explode('unique_roles')
        role_counts = exploded_df.groupby(
            ['unique_roles', 'days_since_last_seen']).size().reset_index(name='count')

        return role_counts

    def _create_active_role_heatmap(self,  role_counts, last_days_ago=30):
        heatmap_data = role_counts.pivot(
            index='unique_roles', columns='days_since_last_seen', values='count').fillna(0)

        unique_roles = heatmap_data.index
        days_since_last_seen = heatmap_data.columns
        fig = px.imshow(heatmap_data,
                        x=days_since_last_seen,
                        y=unique_roles,
                        aspect="auto",
                        labels={"unique_roles": "Roles"},
                        color_continuous_scale='brwnyl',
                        )
        # fig.update_xaxes(showticklabels=False)
        fig.update_layout(margin=dict(b=0, t=100))
        fig.update_layout(
            title=f'Active Roles last {last_days_ago} days',
            xaxis_title='Days Since Last Seen',
            yaxis_title='Roles',
            xaxis=dict(tickmode='linear', dtick=5),
            yaxis=dict(showticklabels=True),
        )
        fig.update_traces(
            hovertemplate="Role: %{y}<br>Count: %{z}<br>Days Last seen: %{x}<extra></extra>"
        )
        return fig

    def _create_top_roles_since(self,  role_counts,  top_limit=5):

        # print(role_counts.info())
        top_df = role_counts.nlargest(top_limit, "count")
        top_df.sort_index(ascending=True, inplace=True)

        fig = px.bar(top_df, x='count', y='unique_roles', orientation='h',
                     labels={"unique_roles": "Roles",
                             "count": "count"},
                     title=f"Top {top_limit} Roles",
                     color="count",
                     )
        # fig.update_yaxes(showticklabels=False)
        return fig

    def _create_utilization_metrics(self, last_days_ago):

        st.markdown(f"### Utilization Rate last {last_days_ago} days")
        util_mean = 45  # 50% utilization

        col1, col2, col3, col4 = st.columns(4)

        hide_arrow_style = """
                        <style>
                        [data-testid="stMetricDelta"] svg {
                            display: none;
                        }
                        </style>
                        """
        st.write(hide_arrow_style, unsafe_allow_html=True)

        utilization_rates_df = self._compute_role_utilization(
            last_days_ago=last_days_ago)

        overall_utilization_rate = utilization_rates_df['utilization_rate'].mean(
        )

        with col1:
            st.metric(f"Utilization Rate",
                      f"{overall_utilization_rate: .2f}%", f"{ (overall_utilization_rate- util_mean): .2f}%")
        with col2:
            entry_max_row = utilization_rates_df.loc[utilization_rates_df['utilization_rate'].idxmax(
            )]
            st.metric(
                "Max", f"{utilization_rates_df['utilization_rate'].max()}", f"{entry_max_row['role']}")
        # with col3:
        #     st.metric(
        #         "Median", f"{utilization_rates_df['utilization_rate'].median()}")
        with col3:
            entry_min_row = utilization_rates_df.loc[utilization_rates_df['utilization_rate'].idxmin(
            )]
            st.metric(
                "Min", f"{utilization_rates_df['utilization_rate'].min()}",  f"{entry_min_row['role']}", delta_color="inverse",)

        with col4:
            older_30_days = 30
            inactive_members_df = self._get_inactive_members_with_combined_roles(
                older_than=older_30_days)
            filtered_df = inactive_members_df[inactive_members_df['unique_roles'].apply(
                lambda x: len(x) > 0)]
            st.metric(
                "Inactive Users w/ Roles", f"{len(filtered_df)}",  f"older than {older_30_days} days", delta_color="inverse",)

    def _assigned_roles_chart(self, last_days_ago=30):

        role_counts = self._get_role_count(last_days_ago)

        col1, col2 = st.columns(2)
        with col1:
            fig = self._create_active_role_heatmap(
                role_counts=role_counts, last_days_ago=last_days_ago)
            st.plotly_chart(fig, theme="streamlit")
        with col2:
            # print(role_counts)
            aggregate_df = role_counts.groupby("unique_roles")[
                "count"].sum().reset_index()

            fig2 = self._create_top_roles_since(
                role_counts=aggregate_df,  top_limit=5)
            st.plotly_chart(fig2, theme="streamlit")

    def _render_lastseen(self):
        df = pd.DataFrame(self.members, columns=[
            "_lastSeen", "days_since_last_seen", ])

        bins = [0, 30, 60, 90, 120, float("inf")]
        labels = ["0-30", "31-60", "61-90", "91-120", ">120"]
        df["dayLastSeenBinned"] = pd.cut(
            df["days_since_last_seen"], bins=bins, labels=labels, right=False)

        fig = px.histogram(df, x="dayLastSeenBinned", title="Acitve User: [30,60,90, 120] Days",
                           labels={"dayLastSeenBinned": "Days"},
                           color="dayLastSeenBinned",
                           color_discrete_sequence=px.colors.qualitative.Set2,
                           category_orders={"dayLastSeenBinned": labels})

        st.plotly_chart(fig, theme="streamlit")

    def _render_members_table(self):
        column_config = {
            'unique_roles': st.column_config.Column(
                "Inherited Roles",
                help="Assigned and inherted Teams role",
                width="small",

            ),
            'team_list': st.column_config.Column(
                "teams",
                help="",
                width="small",

            ),

            'days_since_last_seen': st.column_config.Column(
                "days",
                help="Last Seen in Days",
                width="small",

            ),
            '_lastSeen': st.column_config.DatetimeColumn(
                label="last seen",
                format="YYYY-MMM-D, h:mm a",

            ),
        }

        active_members_roles = self._get_active_members_with_combined_roles()
        merged_df = self.members.merge(
            active_members_roles[["_id", "unique_roles"]], on="_id", how="left")
        merged_df['unique_roles'] = merged_df['unique_roles'].apply(
            lambda x: [] if isinstance(x, float) and pd.isna(x) else x,
        )
        merged_df['num_inherited'] = merged_df['unique_roles'].apply(
            lambda x: len(x),
        )

        # print(merged_df)

        st.markdown(f'##### Total Members:{len(self.members)}')
        st.dataframe(merged_df,  on_select="ignore", column_order=[
                     "_id", "firstName", "lastName",  "email", "role", "customRoles", "unique_roles", 'num_inherited', "team_list", "isTeamMember", "isTeamMaintainer", "_pendingInvite",  "days_since_last_seen", "_lastSeen"],
                     column_config=column_config,
                     use_container_width=True,)

    def _active_members_assigned_roles_chart(self):
        fig = px.scatter(self.members,
                         title="",
                         y="customRoleKeys_count", x="key",
                         color="key", size="customRoleKeys_count",
                         labels={
                             "customRoleKeys_count": "Roles", "key": "Teams"}
                         )
        fig.update_xaxes(showticklabels=False)
        st.plotly_chart(fig, theme="streamlit")

    def render(self):
        self._render_members_headsup_display()
        self._render_members_table()
