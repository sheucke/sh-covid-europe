import dash  # you need Dash version 1.15.0 or higher
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px


# Code source from Dash Plotly
def data_bars(df, column):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min()
        for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append({
            'if': {
                'filter_query': (
                    '{{{column}}} >= {min_bound}' +
                    (' && {{{column}}} < {max_bound}' if (
                        i < len(bounds) - 1) else '')
                ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                'column_id': column
            },
            'background': (
                """
                    linear-gradient(90deg,
                    #0074D9 0%,
                    #0074D9 {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(max_bound_percentage=max_bound_percentage)
            ),
            'paddingBottom': 2,
            'paddingTop': 2
        })

    return styles

# Get today's date
presentday = datetime.now()  # or presentday = datetime.today()

# Get Yesterday
yesterday = presentday - timedelta(1)


# strftime() is to format date according to
# the need by converting them to string
print("Yesterday = ", yesterday.strftime('%d-%m-%Y'))
print("Today = ", presentday.strftime('%d-%m-%Y'))


# ---------------------------------------------------------------
# Taken from https://www.ecdc.europa.eu/en/geographical-distribution-2019-ncov-cases
df = pd.read_csv(
    "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv")

df_original = df.copy()

df_overall = df.groupby('countriesAndTerritories', as_index=False)[
    ['deaths', 'cases']].sum()

print(df_overall.head())


df['dateRep'] = pd.to_datetime(df['dateRep'])
df = df[df['dateRep'].dt.strftime(
    '%d-%m-%Y') == yesterday.strftime('%d-%m-%Y')]

print(df.shape)

result = pd.merge(df, df_overall, how='outer', on='countriesAndTerritories')
df_tidy = result.rename(columns={'cases_x': 'cases', 'deaths_x': 'deaths',
                                 'cases_y': 'overall_cases', 'deaths_y': 'overall_deaths'}, inplace=False)

print(df_tidy.head())

df_europe = df_tidy[df_tidy['continentExp'] == "Europe"]

print(df_europe)

df_europe = df_europe.groupby('countriesAndTerritories', as_index=False).agg(
    {'countryterritoryCode': 'first', 'popData2019': 'first', 'deaths': 'sum', 'overall_deaths': 'first', 'cases': 'sum', 'overall_cases': 'first'})
df_europe['id'] = df_europe['countryterritoryCode']
df_europe.set_index('id', inplace=True, drop=False)
df_europe['severity'] = df_europe['cases'].apply(lambda x:
                                                 '😷😷😷😷😷' if x > 6000 else (
                                                     '😷😷😷😷' if x > 3000 else (
                                                         '😷😷😷' if x > 1500 else (
                                                             '😷😷' if x > 750 else (
                                                                 '😷' if x > 375 else '')))))

print(df_europe.head())

if df.shape[0] == 0:
    status = 'Data from yesterday not available yet.'
else:
    status = 'Data filtered for yesterday.'

print(status)

app = dash.Dash(__name__, prevent_initial_callbacks=True)
server = app.server

app.layout = html.Div([
    html.H1("Covid cases in europe"),
    html.H4("The data csv.file you can get at https://opendata.ecdc.europa.eu/covid19/casedistribution/csv"),
    html.H5(status),
    dash_table.DataTable(
        id='mydatatable',
        columns=[
            {'name': 'Country', 'id': 'countriesAndTerritories',
                'type': 'text', 'editable': True},
            # {'name': 'Country Code', 'id': 'countryterritoryCode',
            #    'type': 'text', 'editable': False},
            {'name': 'Population', 'id': 'popData2019'},
            {'name': 'Daily cases', 'id': 'cases'},
            {'name': 'Overall cases', 'id': 'overall_cases'},
            {'name': 'Daily deaths', 'id': 'deaths'},
            {'name': 'Overall deaths', 'id':'overall_deaths'},
            {'name': 'Severity', 'id': 'severity'}
        ],
        data=df_europe.to_dict('records'),
        filter_action="native",
        # enables data to be sorted per-column by user or not ('none')
        sort_action="native",
        column_selectable="multi",
        row_selectable="multi",
        selected_rows=[16, 18, 27, 49, 53],
        page_action="native",
        page_current=0,             # page number that user is on
        page_size=20,                # number of rows visible per page
        style_as_list_view=True,
        style_cell={'padding': '5px'},
        style_header={
            'backgroundColor': 'lightgrey',
            'fontWeight': 'bold',
            'text_align': 'center',
            'font_size': '15px'
        },
        style_data_conditional=(
            [
                # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
                # filter_query ****************************************
                {
                    'if': {
                        'filter_query': '{cases} > 500 && {cases} < 15000',
                        'column_id': 'cases'
                    },
                    'backgroundColor': 'hotpink',
                    'color': 'red'
                },
                {
                    'if': {
                        'filter_query': '{countriesAndTerritories} = Germany'
                    },
                    'backgroundColor': '#FFFF00',
                },
                # Align text to the left ******************************
                {
                    'if': {
                        'column_type': 'text'
                        # 'text' | 'any' | 'datetime' | 'numeric'
                    },
                    'textAlign': 'left'
                },
                # Align text to the left ******************************
                {
                    'if': {
                        'column_id': 'popData2019'
                        # 'text' | 'any' | 'datetime' | 'numeric'
                    },
                    'textAlign': 'left'
                },
            ]
            +

            [   # Highlighting bottom three values in a column ********
                {
                    'if': {
                        'filter_query': '{{deaths}} = {}'.format(i),
                        'column_id': 'deaths',
                    },
                    'backgroundColor': '#7FDBFF',
                    'color': 'white'
                }
                for i in df['deaths'].nsmallest(3)
            ]
            +

            # Adding data bars to numerical columns *******************
            data_bars(df, 'cases'))
    ),
    html.Br(),
    html.Br(),
    html.Div(id='bar-container'),
    html.Br(),
    html.Div(id='choromap-container'),
    html.Div([
        html.Div([
            dcc.Dropdown(id='linedropdown',
                         options=[
                             {'label': 'Deaths', 'value': 'deaths'},
                             {'label': 'Cases', 'value': 'cases'}
                         ],
                         value='deaths',
                         multi=False,
                         clearable=False
                         ),
        ], className='six columns'),

        html.Div([
            dcc.Dropdown(id='piedropdown',
                         options=[
                             {'label': 'Deaths', 'value': 'deaths'},
                             {'label': 'Cases', 'value': 'cases'}
                         ],
                         value='cases',
                         multi=False,
                         clearable=False
                         ),
        ], className='six columns'),

    ], className='row'),

    html.Div([
        html.Div([
            dcc.Graph(id='linechart'),
        ], className='six columns'),

        html.Div([
            dcc.Graph(id='piechart'),
        ], className='six columns'),

    ], className='row'),
])

# -------------------------------------------------------------------------------------
# Create bar chart


@app.callback(
    Output(component_id='bar-container', component_property='children'),
    [Input(component_id='mydatatable', component_property="derived_virtual_data"),
     Input(component_id='mydatatable',
           component_property='derived_virtual_selected_rows'),
     Input(component_id='mydatatable',
           component_property='derived_virtual_selected_row_ids'),
     Input(component_id='mydatatable',
           component_property='selected_rows'),
     Input(component_id='mydatatable',
           component_property='derived_virtual_indices'),
     Input(component_id='mydatatable',
           component_property='derived_virtual_row_ids'),
     Input(component_id='mydatatable',
           component_property='active_cell'),
     Input(component_id='mydatatable', component_property='selected_cells')]
)
def update_bar(all_rows_data, slctd_row_indices, slct_rows_names, slctd_rows,
               order_of_rows_indices, order_of_rows_names, actv_cell, slctd_cell):
    print('***************************************************************************')
    print('Data across all pages pre or post filtering: {}'.format(all_rows_data))
    print('---------------------------------------------')
    print("Indices of selected rows if part of table after filtering:{}".format(
        slctd_row_indices))
    print("Names of selected rows if part of table after filtering: {}".format(
        slct_rows_names))
    print("Indices of selected rows regardless of filtering results: {}".format(slctd_rows))
    print('---------------------------------------------')
    print("Indices of all rows pre or post filtering: {}".format(
        order_of_rows_indices))
    print("Names of all rows pre or post filtering: {}".format(order_of_rows_names))
    print("---------------------------------------------")
    print("Complete data of active cell: {}".format(actv_cell))
    print("Complete data of all selected cells: {}".format(slctd_cell))

    dff = pd.DataFrame(all_rows_data)

    # used to highlight selected countries on bar chart
    colors = ['#7FDBFF' if i in slctd_row_indices else '#0074D9'
              for i in range(len(dff))]

    if "countryterritoryCode" in dff and "cases" in dff:
        return [
            dcc.Graph(id='bar-chart',
                      figure=px.bar(
                          data_frame=dff,
                          x="countriesAndTerritories",
                          y='cases',
                          log_y=True,
                          labels={'countriesAndTerritories': 'Countries',
                                  'cases': 'Cases'},
                      ).update_layout(title="Yesterday's covid cases in europe", xaxis={'categoryorder': 'total ascending'})
                      .update_traces(marker_color=colors, hovertemplate="<b>%{y}</b><extra></extra>")
                      )
        ]

# -------------------------------------------------------------------------------------
# Highlight selected column


@app.callback(
    Output('mydatatable', 'style_data_conditional'),
    [Input('mydatatable', 'selected_columns')]
)
def update_styles(selected_columns):
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns]


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# Create choropleth map
@app.callback(
    Output(component_id='choromap-container', component_property='children'),
    [Input(component_id='mydatatable', component_property="derived_virtual_data"),
     Input(component_id='mydatatable', component_property='derived_virtual_selected_rows')]
)
def update_map(all_rows_data, slctd_row_indices):
    dff = pd.DataFrame(all_rows_data)

    # highlight selected countries on map
    borders = [5 if i in slctd_row_indices else 1
               for i in range(len(dff))]

    colors = [
        'lightskyblue' if i in slctd_row_indices else 'midnightblue' for i in range(len(dff))]

    if "countryterritoryCode" in dff:
        return [
            dcc.Graph(id='choropleth',
                      style={'height': 700},
                      figure=px.choropleth(
                          data_frame=dff,
                          locations="countryterritoryCode",
                          scope="europe",
                          color="cases",
                          title=f"Cases from {yesterday.strftime('%d-%m-%Y')} in european countries",
                          template='seaborn',
                          hover_data=['countriesAndTerritories', 'cases'],
                      ).update_layout(showlegend=False, title=dict(font=dict(size=28), x=0.5, xanchor='center'))
                      .update_traces(marker_line_width=borders, marker_line_color=colors,  hovertemplate="<b>%{customdata[0]}</b><br><br>" +
                                     "%{customdata[1]}")
                      )

        ]


@app.callback(
    [Output('piechart', 'figure'),
     Output('linechart', 'figure')],

    [
        Input('piedropdown', 'value'),
        Input('linedropdown', 'value')]
)
def update_data(piedropval, linedropval):
    df_filterd = df[df['countriesAndTerritories'].isin(
        ['Germany', 'France', 'Spain', 'Italy', 'United_Kingdom'])]

    pie_chart = px.pie(
        data_frame=df_filterd,
        names='countriesAndTerritories',
        values=piedropval,
        hole=.3,
        labels={'countriesAndTerritories': 'Countries'}
    )

    # extract list of chosen countries
    list_chosen_countries = df_filterd['countriesAndTerritories'].tolist()
    # filter original df according to chosen countries
    # because original df has all the complete dates
    df_line = df_original[df_original['countriesAndTerritories'].isin(
        list_chosen_countries)]

    line_chart = px.line(
        data_frame=df_line,
        x='dateRep',
        y=linedropval,
        color='countriesAndTerritories',
        labels={'countriesAndTerritories': 'Countries', 'dateRep': 'date'},
    )
    line_chart.update_layout(uirevision='foo')

    return (pie_chart, line_chart)


if __name__ == '__main__':
    app.run_server(debug=False)
