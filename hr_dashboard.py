import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime

# Load CSV
df = pd.read_csv("dataset.csv", delimiter=';')
df['Hiredate'] = pd.to_datetime(df['Hiredate'], dayfirst=True)
df['Termdate'] = pd.to_datetime(df['Termdate'], dayfirst=True, errors='coerce')
df['Birthdate'] = pd.to_datetime(df['Birthdate'], dayfirst=True)

# Enrich data
df['Age'] = ((pd.Timestamp('today') - df['Birthdate']).dt.days / 365.25).astype(int)
df['Status'] = df['Termdate'].apply(lambda x: 'Active' if pd.isnull(x) else 'Terminated')
df['HQ'] = df['City'].apply(lambda x: 'HQ' if x == 'New York City' else 'Branch')

# Start Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for deployment

# OVERVIEW TAB
total_hired = len(df)
active = len(df[df['Status'] == 'Active'])
terminated = total_hired - active
hires_by_year = df['Hiredate'].dt.year.value_counts().sort_index()
terms_by_year = df['Termdate'].dt.year.dropna().astype(int).value_counts().sort_index()
dept_counts = df['Department'].value_counts()
hq_branch = df['HQ'].value_counts()
city_state = df.groupby(['State', 'City']).size().reset_index(name='Employees')

overview_tab = [
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(total_hired, className="card-title"), html.P("Total Hired")])]), md=4),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(active, className="card-title"), html.P("Active")])]), md=4),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(terminated, className="card-title"), html.P("Terminated")])]), md=4),
    ]),
    html.Hr(),
    dcc.Graph(figure=px.bar(x=hires_by_year.index, y=hires_by_year.values, labels={'x': 'Year', 'y': 'Hires'}, title="Hires per Year")),
    dcc.Graph(figure=px.bar(x=terms_by_year.index, y=terms_by_year.values, labels={'x': 'Year', 'y': 'Terminations'}, title="Terminations per Year")),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=px.pie(names=dept_counts.index, values=dept_counts.values, title="Employees by Department")), md=6),
        dbc.Col(dcc.Graph(figure=px.pie(names=hq_branch.index, values=hq_branch.values, title="HQ vs Branches")), md=6)
    ]),
    dcc.Graph(figure=px.sunburst(city_state, path=['State', 'City'], values='Employees', title="Distribution by City & State"))
]

# DEMOGRAPHICS TAB
gender_counts = df['Gender'].value_counts()
age_bins = pd.cut(df['Age'], bins=[0, 25, 35, 45, 55, 65, 100], labels=["<25", "25-34", "35-44", "45-54", "55-64", "65+"])
age_counts = age_bins.value_counts().sort_index()
edu_counts = df['Education Level'].value_counts()
edu_perf = df.groupby(['Education Level', 'Performance Rating']).size().reset_index(name='Count')

demographics_tab = [
    dbc.Row([
        dbc.Col(dcc.Graph(figure=px.pie(names=gender_counts.index, values=gender_counts.values, title="Gender Ratio")), md=6),
        dbc.Col(dcc.Graph(figure=px.bar(x=age_counts.index, y=age_counts.values, title="Employees by Age Group")), md=6)
    ]),
    dcc.Graph(figure=px.bar(x=edu_counts.index, y=edu_counts.values, title="Employees by Education Level")),
    dcc.Graph(figure=px.sunburst(edu_perf, path=['Education Level', 'Performance Rating'], values='Count', title="Education vs Performance"))
]

# INCOME TAB
edu_gender_salary = df.groupby(['Education Level', 'Gender'])['Salary'].mean().reset_index()
income_tab = [
    dcc.Graph(figure=px.box(df, x='Education Level', y='Salary', color='Gender', title="Salary by Education & Gender")),
    dcc.Graph(figure=px.scatter(df, x='Age', y='Salary', color='Department', title="Age vs Salary by Department"))
]

# TABLE TAB
columns_to_show = ['Employee_ID', 'First Name', 'Last Name', 'Department', 'Job Title', 'Gender', 'Age', 'Education Level', 'Salary', 'Status']
emp_df = df[columns_to_show]

table_tab = dash_table.DataTable(
    id='emp-table',
    columns=[{"name": c, "id": c} for c in emp_df.columns],
    data=emp_df.to_dict('records'),
    page_size=15,
    sort_action='native',
    filter_action='native',
    style_cell={'textAlign': 'left', 'minWidth': '80px', 'width': '120px', 'maxWidth': '180px'},
    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
)

# LAYOUT
app.layout = dbc.Container([
    html.H1("HR Analytics Dashboard", className="mb-4"),
    dbc.Tabs([
        dbc.Tab(dbc.Container(overview_tab), label="Overview"),
        dbc.Tab(dbc.Container(demographics_tab), label="Demographics"),
        dbc.Tab(dbc.Container(income_tab), label="Income Analysis"),
        dbc.Tab(dbc.Container([table_tab]), label="Employee Records")
    ])
], fluid=True)

# RUN
if __name__ == '__main__':
    app.run(debug=True)
