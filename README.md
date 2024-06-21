

# LaunchDarkly RBAC Policy Explorer

This Python-based Streamlit app enables users to analyze Role-Based Access Control (RBAC) policies in LaunchDarkly, generating comprehensive operational, security, and core RBAC metrics to evaluate their management and effectiveness. 

## Requirements

- Python 3.7 or higher
- Streamlit
- Pandas
- LaunchDarkly access token


## Installation

1. **Clone the repository**:
    ```sh
    git clone git@github.com:tanben/ld-rbac-explorer.git
    cd ld-rbac-explorer
    ```

2. **Install the required dependencies**:
    ```sh
    > python -m venv .venv
    > source .venv/bin/activate
    > pip install -r requirements.txt
    ```
    To deactivate
    ```sh
    > deactivate
    ```
    
3. **Set up your LaunchDarkly API credentials**:
    - Create a `.env` file in the root directory of the project.
    - Add your LaunchDarkly API key to the `.env` file:
        ```
        DEBUG=false
        SAVE_DATA=false
        READ_LOCAL=false
        LD_API_KEY=<your_launchdarkly_api_key> 
        ```
        *Configuration:*
        * *SAVE_DATA* - True, to save the LaunchDarkly payload and transformed data
        * *READ_LOCAL* 
          * True, read local transformed data. 
          * False, fetch data from Launchdarkly REST API endpoint
        * *LD_API_KEY* - (Optional) if defined prepopulate the API input field
  
4. Disable Streamlit usage stats (Optional).
 
   Create the config.toml in .streamlit, you can find available configurations [here](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)

        [browser]
        gatherUsageStats = false

## Usage

1. **Run the Streamlit application**:
    ```sh
    streamlit run app.py
    ```

2. **Access the application**:
    - Open your web browser and go to `http://localhost:8501`.


## Metrics Tracked

### Custom Roles
![](./img/rolesCharts.jpg)

| Metric       | Description     |
| ------------ | --------------- | 
| Custom roles | Total custom roles|
| Orphaned roles | Total unassigned custom roles|
| Assigned roles | Total assigned member and Teams roles|
|Role/User ratio | Average numbe rof roles assigned to member|
|Role/Team ratio | Average number of roles assigned to Teams|
|Permission/Policy ratio| Average naumber of permissions per policy|

### Members
![](./img/membersChart.jpg)

| Metric | Description |
| ------ | ----------- |
|Role Utilization Rate|Percentage of users actively utilizing the permissions granted by their roles. |
|Inactive User w/ Roles|Inactive users with active custom roles|
| Active Roles last 30 days| Show role activities in the last 30 days.  Y-Axis is the days since last seen.|
| Top 5 Roles|Total count per role assigned to members and inherited from Teams.|
|Active User|Total active users: 30,60,90,120, >120 days|


## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
