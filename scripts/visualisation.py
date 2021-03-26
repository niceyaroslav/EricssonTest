import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scripts.analysis import Analysis
import seaborn as sns


analysis = Analysis()


usage = analysis.evaluate_robot_usage()
fail = analysis.evaluate_failure_rate()
qf = analysis.quantify_and_analyze_fails()
map_aborted_failures = analysis.prepare_df_for_fail_mapping(aborted=True)
map_other_failures = analysis.prepare_df_for_fail_mapping(aborted=False)
proc_ab = analysis.get_pct_aborted()
total_usage = analysis.get_total_usage_by_robot()


def plot_pie(df, title, show):
    fig = px.pie(df, values='Value', names='Type',
                 color_discrete_sequence=['Orange', '#36688D'],
                 template="simple_white")
    fig.update_layout(
        font_family="Rockwell",
        # legend=dict(
        #     title=None, orientation="h", y=1, yanchor="bottom", x=0.5, xanchor="right"
        # )
        title_text=f'{title}',
        margin=dict(l=20, r=20, t=100, b=100, pad=100),
        title_x=0.5,
        legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01),
        font_size=20,
        autosize=False,
        width=800,
        height=800

    )
    fig.update_traces(textfont_size=30, pull=[0.02, 0])
    if show:
        fig.show(renderer="browser")
    else:
        fig.write_image(engine='kaleido', file=f'imgs/{title}.png')


def plot_bars(df, title, show):
    fig = px.bar(df, x=df['Problems'], y=df['Occurence'], color_discrete_sequence=['#36688D'])
    fig.update_layout(xaxis_tickangle=-30,
                      font_family="Rockwell",
                      height=800,
                      width=800,
                      showlegend=True,
                      title_text=f'{title}',
                      title_x=0.6,
                      )
    fig.update_traces(textfont_size=40)
    fig.layout.title.font.size = 30
    fig.layout.xaxis.title.font.size = 20
    fig.layout.yaxis.title.font.size = 20
    if show:
        fig.show(renderer="browser")
    else:
        fig.write_image(engine='kaleido', file=f'imgs/{title}.png')


def plot_bars_mapped(df, title, show):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Robot'],
                         y=df['Share of Day missions'],
                         name="Day",
                         marker_color="Orange",
                         ))
    fig.add_trace(go.Bar(x=df['Robot'],
                         y=df['Share of Night missions'],
                         name='Night',
                         marker_color='#36688D',
                         ))
    fig.update_layout(xaxis_tickangle=-30,
                      font_family="Rockwell",
                      height=800,
                      width=1000,
                      showlegend=True,
                      title_text=f'{title}',
                      title_x=0.5,
                      )

    fig.update_traces(textfont_size=40)
    fig.layout.title.font.size = 30
    # fig.layout.xaxis.ticks = 20
    fig.layout.font.size = 20
    fig.layout.yaxis = {'range': [0, 100]}
    fig.layout.xaxis.title.text = 'Robot'
    fig.layout.yaxis.title.text = 'Share of failures, %'
    # fig.layout.yaxis.ticks.font.size = 20
    if show:
        fig.show(renderer="browser")
    else:
        fig.write_image(engine='kaleido', file=f'imgs/{title}.png')


plot_pie(usage, title="Total distribution of orders", show=False)
plot_pie(fail, title="Fail rate for missions", show=False)
plot_bars(qf, title='Distribution of fails by type', show=False)
plot_pie(proc_ab, title='Share of aborted missions', show=False)
plot_bars_mapped(map_aborted_failures, title='Share of aborted missions by shift and robot', show=False)
plot_bars_mapped(map_other_failures, title='Share of other failures by shift and robot', show=False)
plot_bars_mapped(total_usage, title='Share of all missions by shift and robot', show=False)