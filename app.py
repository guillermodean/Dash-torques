import pandas as pd
import numpy as np
import matplotlib as plt
import plotly.express as px
import plotly.graph_objs as go
from Classes.Filterdata import Filtrar
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

external_scripts = [
    'https://www.google-analytics.com/analytics.js',
    {'src': 'https://cdn.polyfill.io/v2/polyfill.min.js'},
    {
        'src': 'https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.10/lodash.core.js',
        'integrity': 'sha256-Qqd/EfdABZUcAxjOkMi8eGEivtdTkh3b65xCZL4qAQA=',
        'crossorigin': 'anonymous'
    }
]
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
        'crossorigin': 'anonymous'
    }
]
# ----------------------------------------------------------------------------
# importar data y tratar

df = pd.read_csv('Results_TTM.csv', sep=";", header=0)
df = df.drop(
    columns=["Controlling transducer", "Current min (A)", "Current max (A)", "Current min (%)", "Current max (%)",
             "Current (%)", "Torque rate", "Current (A)"])
# df = Filterdata.Filtrar(df)
df = df.drop(
    columns=["Step status", "Current trend", "Torque rate min", "Torque rate max", "Torque rate trend", "CVILOGIX",
             "Identifier6", "Identifier7", "Identifier8", "Identifier9", "Identifier10",
             "Second transducer torque deviation", "Second transducer angle deviation", "Result type", "Pulse counter",
             "Angle offset", "AO torque rate"])
df = df.rename(
    columns={"Result number": "Result_number", "Pset ID": "Pset_ID", "Step ID": "Step_ID", "Torque min": "Torque_min",
             "Torque max": "Torque_max", "Angle min": "Angle_min", "Angle max": "Angle_max",
             "Controller serial no.": "Controller_serial_no.", "Pset name": "Pset_name",
             'Controller name': 'Controller_name', 'Error code': 'Error_code', 'Result status': 'Result_status'})
df = df[~df["Pset_name"].str.contains("Poka", na=False)]
df.astype({'Time result': 'datetime64[ns, US/Eastern]'}).dtypes
df.reset_index(inplace=True)


# ----------------------------------------------------------------------------


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def generate_nok(dataframe):
    dataframe = dataframe[['Result_status', 'Result_number']].groupby(by='Result_status').count().reset_index()
    fig = px.pie(dataframe, values='Result_number', names='Result_status', title='% of torques not ok filtered by pset',
                 color='Result_status',
                 color_discrete_map={'OK': 'green',
                                     'NOK': 'red'})
    return fig


app = dash.Dash(__name__, external_scripts=external_scripts,
                external_stylesheets=external_stylesheets)

#Para facilitar el entendimiento he separado por bloques el layout html

LEFT_COLUMN = dbc.Jumbotron(
    [
        html.H4(children="Select Pset & dates", className="display-5"),
        html.Hr(className="my-2"),
        html.Label("Select a bank", style={"marginTop": 50}, className="lead"),
        html.P(
            "(You can use the dropdown or click the barchart on the right)",
            style={"fontSize": 10, "font-weight": "lighter"},
        ),
        dcc.Dropdown(id='dropdown', clearable=False, options=[
            {'label': str(i), 'value': str(i)} for i in df['Pset_name'].unique()
        ], multi=True, placeholder='Filter by Pset...', style={"marginBottom": 50, "font-size": 12}),
        html.Label("Select time frame", className="lead"),
        html.Div(dcc.RangeSlider(id="time-window-slider"), style={"marginBottom": 50}),  #TODO populate the slider => callback abajo ejemplo => https://github.com/plotly/dash-sample-apps/blob/master/apps/dash-nlp/app.py
        html.P(
            "(You can define the time frame down to month granularity)",
            style={"fontSize": 10, "font-weight": "lighter"},
        ),
    ]
)

RIGHTCOLUM=dcc.Graph(id='general_nok')


NAVBAR = dbc.Navbar(children=[
    html.A(
        # Use row and col to control vertical alignment of logo / brand
        dbc.Row(
            [
                dbc.Col(html.Img(src='Classes/ISRI.png', height="30px")),  #TODO hacer que se vea la imagen que no la pilla => JPG
                dbc.Col(
                    dbc.NavbarBrand("ISRI Torque tool managemento dashboard", className="ml-2")
                ),
            ],
            align="center",
            no_gutters=True,
        ),
        href="https://isri.de",
    )
], color="dark", dark=True, sticky="top")

BODY = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(LEFT_COLUMN, md=4, align="center"),
                dbc.Col(dbc.Card(RIGHTCOLUM), md=8),
            ],
            style={"marginTop": 30},
        ),
        dbc.Row([
            html.Br(),
            dbc.Card(html.Div(id='table-container'))  #TODO o encoger la tabla o meterla de alguna manera en vereda dentro de una card
        ])
    ],
    className="mt-12",
)

app.layout = html.Div(children=[NAVBAR, BODY])


@app.callback(
    Output(component_id='table-container', component_property='children'),
    Input(component_id='dropdown', component_property='value'))
def display_table(dropdown_value):
    if dropdown_value is None:
        return generate_table(df)
    else:
        dff = df[df['Pset_name'].str.contains('|'.join(dropdown_value), na=False)]
        return generate_table(dff)


@app.callback(
    Output(component_id='general_nok', component_property='figure'),
    Input(component_id='dropdown', component_property='value'))
def display_nok_graph(dropdown_value):
    if dropdown_value is None:
        return generate_nok(df)
    else:
        dff = df[df['Pset_name'].str.contains('|'.join(dropdown_value), na=False)]
    return generate_nok(dff)

@app.callback(
    [
        Output("time-window-slider", "marks"),
        Output("time-window-slider", "min"),
        Output("time-window-slider", "max"),
        Output("time-window-slider", "step"),
        Output("time-window-slider", "value"),
    ],
    [Input("n-selection-slider", "value")],
)
def populate_time_slider(value):
    """
    Depending on our dataset, we need to populate the time-slider
    with different ranges. This function does that and returns the
    needed data to the time-window-slider.
    """
    value += 0
    min_date = GLOBAL_DF["Date received"].min()
    max_date = GLOBAL_DF["Date received"].max()

    marks = make_marks_time_slider(min_date, max_date)
    min_epoch = list(marks.keys())[0]
    max_epoch = list(marks.keys())[-1]

    return (
        marks,
        min_epoch,
        max_epoch,
        (max_epoch - min_epoch) / (len(list(marks.keys())) * 3),
        [min_epoch, max_epoch],
    )


if __name__ == '__main__':
    app.run_server(debug=True)
