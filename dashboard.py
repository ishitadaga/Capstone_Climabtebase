import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Sample data
counties = ['Kern', 'Santa Barbara', 'Lassen', 'Los Angeles', 'El Dorado', 'Santa Clara']
permit_types = ['NOP', 'MND', 'EIR', 'NEG', 'NOE', 'NOD']
years = list(range(1990, 2024))

# Generate more comprehensive sample data
df = pd.DataFrame({
    'County': np.random.choice(counties, 1000),
    'Year': np.random.choice(years, 1000),
    'Permit Type': np.random.choice(permit_types, 1000),
    'Permit Approvals (%)': np.random.randint(0, 100, 1000),
    'Number of Projects': np.random.randint(1, 10000, 1000),
    'Average Project Time (months)': np.random.randint(1, 24, 1000),
    'Acres': np.random.randint(10, 1000, 1000),
    'MegaWatt': np.random.randint(1, 100, 1000),
})

# Approximate coordinates for the counties
coordinates = {
    'Kern': (35.3933, -118.9015),
    'Santa Barbara': (34.4208, -119.6982),
    'Lassen': (40.6739, -120.5917),
    'Los Angeles': (34.0522, -118.2437),
    'El Dorado': (38.7786, -120.5231),
    'Santa Clara': (37.3541, -121.9552)
}

df['Latitude'] = df['County'].map(lambda x: coordinates[x][0])
df['Longitude'] = df['County'].map(lambda x: coordinates[x][1])

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("California County Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Div([
            html.Label("Select Year Range:"),
            dcc.RangeSlider(
                id='year-slider',
                min=min(years),
                max=max(years),
                value=[min(years), max(years)],
                marks={str(year): str(year) for year in range(min(years), max(years)+1, 5)},
                step=1
            )
        ], style={'width': '50%', 'display': 'inline-block', 'paddingRight': '10px'}),
        
        html.Div([
            html.Label("Select County:"),
            dcc.Dropdown(
                id='county-dropdown',
                options=[{'label': county, 'value': county} for county in counties],
                value=None,
                style={'width': '100%'}
            )
        ], style={'width': '50%', 'display': 'inline-block'})
    ], style={'marginBottom': '20px'}),
    
    html.Div([
        html.Div([
            dcc.Graph(id='permit-approvals-chart')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='county-projects-map')
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),
    
    html.Div([
        html.Div([
            dcc.Graph(id='permit-journey-plot')
        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        html.Div([
            dash_table.DataTable(
                id='summary-table',
                columns=[
                    {'name': 'Metric', 'id': 'Metric'},
                    {'name': 'Value', 'id': 'Value'}
                ],
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_table={'height': '300px', 'overflowY': 'auto'}
            )
        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ])
])

@app.callback(
    [Output('permit-approvals-chart', 'figure'),
     Output('county-projects-map', 'figure'),
     Output('permit-journey-plot', 'figure'),
     Output('summary-table', 'data')],
    [Input('county-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_dashboard(selected_county, selected_years):
    # Filter by year for all sections
    year_filtered_df = df[(df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1])]
    
    # Section 1: Permit Approvals Chart (all counties)
    permit_chart = px.bar(year_filtered_df.groupby('County')['Permit Approvals (%)'].mean().reset_index(), 
                          x='County', y='Permit Approvals (%)', 
                          title='Average Permit Approvals by County',
                          color_discrete_sequence=['rgba(255, 165, 0, 0.7)'])  # Light orange color
    permit_chart.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    
    # Section 2: County Projects Map (all counties)
    map_data = year_filtered_df.groupby('County').agg({
        'Number of Projects': 'sum',
        'Average Project Time (months)': 'mean',
        'Latitude': 'first',
        'Longitude': 'first'
    }).reset_index()
    
    map_fig = px.scatter_mapbox(map_data,
                                lat="Latitude",
                                lon="Longitude",
                                size="Number of Projects",
                                color="Average Project Time (months)",
                                hover_name="County",
                                color_continuous_scale=px.colors.sequential.Oranges,
                                size_max=50,
                                zoom=5,
                                center={"lat": 37.2516, "lon": -119.7526},  # Center of California
                                mapbox_style="open-street-map")

    map_fig.update_layout(
        title='County Projects Overview',
        mapbox=dict(
            center=dict(lat=37.2516, lon=-119.7526),  # Center of California
            zoom=5
        ),
        height=600,  # Increase the height of the map
        margin={"r":0,"t":40,"l":0,"b":0}
    )
    
    # Section 3: Permit Journey Plot
    if selected_county:
        journey_data = year_filtered_df[year_filtered_df['County'] == selected_county]
    else:
        journey_data = year_filtered_df

    # Calculate the count of projects for each permit type
    permit_counts = journey_data['Permit Type'].value_counts()

    # Define the flow of permits
    permit_flow = {
        'NOP': ['MND', 'EIR', 'NEG', 'NOE', 'NOD'],
        'MND': ['EIR'],
        'EIR': ['NOD'],
        'NEG': ['NOD'],
        'NOE': ['NOD']
    }

    # Prepare data for Sankey diagram
    nodes = permit_types.copy()
    links = []
    for source, targets in permit_flow.items():
        source_index = nodes.index(source)
        for target in targets:
            target_index = nodes.index(target)
            value = min(permit_counts.get(source, 0), permit_counts.get(target, 0))
            if value > 0:
                links.append((source_index, target_index, value))

    # Create Sankey diagram
    journey_plot = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 10,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = nodes,
          color = "rgba(255, 165, 0, 0.7)"
        ),
        link = dict(
          source = [link[0] for link in links],
          target = [link[1] for link in links],
          value = [link[2] for link in links]
    ))])

    journey_plot.update_layout(
        title_text="Permit Process Flow",
        font_size=10,
        height=400
    )

    
    # Section 4: Summary Table
    if selected_county:
        county_filtered_df = year_filtered_df[year_filtered_df['County'] == selected_county]
    else:
        county_filtered_df = year_filtered_df

    summary_data = [
        {'Metric': 'Median Acres', 'Value': f"{county_filtered_df['Acres'].median():.2f}"},
        {'Metric': 'Median Approval Time (months)', 'Value': f"{county_filtered_df['Average Project Time (months)'].median():.2f}"},
        {'Metric': 'Median MegaWatt', 'Value': f"{county_filtered_df['MegaWatt'].median():.2f}"},
        {'Metric': 'Median Approval Rate (%)', 'Value': f"{county_filtered_df['Permit Approvals (%)'].median():.2f}"}
    ]
    
    return permit_chart, map_fig, journey_plot, summary_data

if __name__ == '__main__':
    app.run_server(debug=True)