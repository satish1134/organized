import os
import logging
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from datetime import datetime, time
from flask import Blueprint, render_template, current_app
from typing import Dict, List, Optional

# Initialize Blueprint and logger
bp = Blueprint('trend', __name__)
logger = logging.getLogger(__name__)

# Custom HTML template for Dash
index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Trend Analysis</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        {%css%}
        <style>
            body {
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

@bp.route('/trend-analysis', endpoint='trend')
def trend() -> str:
    """
    Route handler for trend analysis page.
    Returns: Rendered template or error page
    """
    try:
        logger.info('Rendering trend analysis page')
        return render_template('trend.html')
    except Exception as e:
        logger.error(f"Error loading trend analysis: {str(e)}", exc_info=True)
        return render_template('error.html',
                             error_title='Trend Analysis Error',
                             error='Failed to load trend analysis'), 500

def process_data(csv_path: str) -> pd.DataFrame:
    """
    Process the CSV file containing DAG execution data.
    Args:
        csv_path: Path to the CSV file
    Returns:
        Processed DataFrame
    """
    try:
        logger.info(f"Reading data from {csv_path}")
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found at {csv_path}")
            return pd.DataFrame()

        df = pd.read_csv(csv_path)
        df['exe_date'] = pd.to_datetime(df['exe_date'], format='%d-%m-%Y')
        df['max_batch_end_dt'] = pd.to_datetime(df['max_batch_end_dt'], format='%d-%m-%Y %H:%M')
        df['end_time'] = df['max_batch_end_dt'].dt.time
        df['end_hour_float'] = df['max_batch_end_dt'].dt.hour + df['max_batch_end_dt'].dt.minute/60

        logger.info(f"Successfully processed {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}", exc_info=True)
        return pd.DataFrame()

# Initialize DataFrame
df = process_data('dag_data.csv')

# Get unique dates for x-axis
unique_dates = sorted(df['exe_date'].unique())
date_strings = [d.strftime('%d-%m-%y') for d in unique_dates]

# Define time intervals for y-axis
time_intervals = [
    time(0, 0), time(3, 0), time(6, 0), time(9, 0),
    time(12, 0), time(15, 0), time(18, 0), time(21, 0), time(23, 59)
]
time_labels = [t.strftime('%H:%M') for t in time_intervals[:-1]] + ['24:00']

# Define thresholds for each application
thresholds = {
    'east': 7 + 0/60,  # 7:00 AM
    'north': 22 + 10/60,  # 22:10
    'south': 14 + 0/60,  # 14:00
    'west': 21 + 0/60  # 21:00
}

layout = html.Div(className='main-container', children=[
    # Dropdowns Container
    html.Div(className='dropdown-container backdrop-blur-sm bg-white/80 rounded-xl shadow-lg p-4 border border-blue-100', children=[
        html.Div([
            html.Label(
                'Select Application:', 
                className='block text-sm font-semibold text-gray-700 mb-2'
            ),
            html.Div(
                dcc.Dropdown(
                    id='app-dropdown',
                    options=[{'label': 'All Applications', 'value': 'all'}] +
                            [{'label': app, 'value': app} for app in df['application_name'].unique()],
                    value='all',
                    clearable=False,
                    className='dash-dropdown'
                ),
                className='relative'
            )
        ], className='w-[48%] inline-block'),
        
        html.Div([
            html.Label(
                'Select DAG:', 
                className='block text-sm font-semibold text-gray-700 mb-2'
            ),
            html.Div(
                dcc.Dropdown(
                    id='dag-dropdown',
                    options=[],
                    clearable=False,
                    className='dash-dropdown'
                ),
                className='relative'
            )
        ], 
        className='w-[48%] inline-block ml-[4%]',
        id='dag-dropdown-container',
        style={'visibility': 'hidden'})
    ]),
    
    # Graph Container
    html.Div(className='graph-container backdrop-blur-sm bg-white/80 rounded-xl shadow-lg p-4 border border-blue-100', children=[
        dcc.Graph(
            id='time-series-graph',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                'responsive': True
            }
        )
    ])
])

def init_dash(server) -> Dash:
    """
    Initialize the Dash application.
    Args:
        server: Flask server instance
    Returns:
        Initialized Dash server
    """
    try:
        logger.info("Initializing Dash app")
        app = Dash(
            __name__,
            server=server,
            url_base_pathname='/trend/dash/',
            external_stylesheets=['/static/css/trend.css'],
            index_string=index_string
        )

        app.layout = layout
        register_callbacks(app)
        
        logger.info("Dash app initialized successfully")
        return app.server
    except Exception as e:
        logger.error(f"Error initializing Dash app: {str(e)}", exc_info=True)
        raise

def register_callbacks(app: Dash) -> None:
    """
    Register callbacks for the Dash application.
    Args:
        app: Dash application instance
    """
    try:
        @app.callback(
            [Output('dag-dropdown', 'options'),
             Output('dag-dropdown-container', 'style')],
            [Input('app-dropdown', 'value')]
        )
        def update_dag_dropdown(selected_app: str) -> tuple:
            """Update DAG dropdown based on selected application"""
            base_style = {
                'width': '48%',
                'display': 'inline-block',
                'marginLeft': '4%',
                'transition': 'visibility 0.3s ease-in-out'
            }
            
            if selected_app == 'all':
                return [], {**base_style, 'visibility': 'hidden'}
            
            filtered_df = df[df['application_name'] == selected_app]
            return (
                [{'label': dag, 'value': dag} for dag in filtered_df['dag_name'].unique()],
                {**base_style, 'visibility': 'visible'}
            )

        @app.callback(
            Output('time-series-graph', 'figure'),
            [Input('app-dropdown', 'value'),
             Input('dag-dropdown', 'value')]
        )
        def update_graph(selected_app: str, selected_dag: Optional[str]) -> go.Figure:
            """Update graph based on selected application and DAG"""
            logger.info(f"Updating graph for app: {selected_app}, dag: {selected_dag}")
            
            try:
                # Filter data based on selections
                if selected_app == 'all':
                    filtered_df = df
                else:
                    filtered_df = df[df['application_name'] == selected_app]
                    if selected_dag:
                        filtered_df = filtered_df[filtered_df['dag_name'] == selected_dag]

                if filtered_df.empty:
                    logger.warning("No data available for the selected filters")
                    return go.Figure()

                # Get daily maximum values
                daily_max_indices = filtered_df.groupby('exe_date')['end_hour_float'].idxmax()
                daily_max = filtered_df.loc[daily_max_indices].reset_index(drop=True)

                fig = go.Figure()

                # Add trace
                fig.add_trace(go.Scatter(
                    x=[d.strftime('%d-%m-%y') for d in daily_max['exe_date']],
                    y=daily_max['end_hour_float'],
                    mode='lines+markers',
                    name='Max Batch End Time',
                    line=dict(color='#017cee', width=2),
                    marker=dict(
                        size=10,
                        symbol='circle',
                        line=dict(color='#fff', width=2)
                    ),
                    hovertemplate=(
                        'Date: %{x}<br>' +
                        'Time: %{text}<br>' +
                        'DAG: %{customdata[0]}<br>' +
                        'Batch: %{customdata[1]}<br>' +
                        '<extra></extra>'
                    ),
                    text=[t.strftime('%H:%M') for t in daily_max['max_batch_end_dt']],
                    customdata=list(zip(daily_max['dag_name'], daily_max['batch_name']))
                ))

                # Update layout
                fig.update_layout(
                    autosize=True,
                    margin=dict(l=60, r=20, t=40, b=100),
                    xaxis=dict(
                        title='Execution Date',
                        gridcolor='#e0e0e0',
                        showgrid=True,
                        ticktext=date_strings,
                        tickvals=date_strings,
                        tickangle=90,
                        tickmode='array',
                        type='category',
                        tickfont=dict(size=12)
                    ),
                    yaxis=dict(
                        title='Time of Day',
                        ticktext=time_labels,
                        tickvals=[0, 3, 6, 9, 12, 15, 18, 21, 24],
                        gridcolor='#e0e0e0',
                        showgrid=True,
                        range=[-0.5, 24.5],
                        tickfont=dict(size=12)
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    hovermode='x unified',
                    showlegend=False
                )

                # Add horizontal lines for hours
                for hour in [0, 3, 6, 9, 12, 15, 18, 21, 24]:
                    fig.add_hline(
                        y=hour,
                        line=dict(color='#e0e0e0', width=1, dash='dash'),
                        opacity=0.7
                    )

                # Add threshold line if applicable
                if selected_app != 'all' and selected_app in thresholds:
                    fig.add_hline(
                        y=thresholds[selected_app],
                        line=dict(color='red', width=2, dash='dash'),
                        annotation_text=f'Threshold: {time(int(thresholds[selected_app]), int((thresholds[selected_app] % 1) * 60)).strftime("%H:%M")}',
                        annotation_position='top left'
                    )

                logger.info("Graph updated successfully")
                return fig
            except Exception as e:
                logger.error(f"Error updating graph: {str(e)}", exc_info=True)
                return go.Figure()

        logger.info("Callbacks registered successfully")
    except Exception as e:
        logger.error(f"Error registering callbacks: {str(e)}", exc_info=True)
        raise
