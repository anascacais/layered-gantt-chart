# third-party
import pandas as pd
import plotly.express as px

# built-in
from datetime import datetime
import calendar

# local
from constants import YEARLY_QUARTERS_START, YEARLY_QUARTERS_END

# ========================== GANTT ========================== #


class GanttTimeline():

    def __init__(self, projects_dict, color_palette, task_name='Project', subtask_name='Task'):
        self.task_name = task_name
        self.subtask_name = subtask_name

        self.df = self.fill_base_df(projects_dict)
        self.df_background = self.df.dropna()
        self.start_date, self.end_date = self.get_start_end_dates()

        self.quarter_color_code = self.get_quarter_color(color_palette)

    def fill_base_df(self, projects_dict):

        gantt_df = pd.DataFrame(
            columns=['task', 'project', 'start', 'end', 'description', 'status'])

        for p, project in enumerate(projects_dict):

            # Add empty line to separate projects
            gantt_df.loc[len(gantt_df)] = [
                f'{self.task_name} {p+1}'] + [None] * (len(gantt_df.columns)-1)

            for t, task in enumerate(projects_dict[project]):

                att = []
                for key in projects_dict[project][task]:
                    att += [projects_dict[project][task][key]]

                gantt_df.loc[len(gantt_df)] = [
                    f'{self.subtask_name} {p+1}.{t+1}', f'{self.task_name} {p+1}'] + att

        # get yearly quarter
        gantt_df['quarter'] = gantt_df['start'].apply(
            lambda x: get_quarter_from_strdate(x)).values

        return gantt_df

    def get_start_end_dates(self):
        # get start and end of timeline
        start_date = self.df['start'].dropna().min()
        end_date = self.df['end'].dropna().max()

        self.df['first'] = start_date
        self.df['last'] = end_date

        self.df_background['first'] = start_date
        self.df_background['last'] = end_date

        return start_date, end_date

    def get_quarter_color(self, color_palette):
        quarter_color_code = {}

        cp_iter = iter(color_palette)
        self.color_palette = []
        for quarter in self.df['quarter'].unique():
            if quarter != 'None':
                quarter_color_code[quarter] = next(cp_iter)
                self.color_palette += [quarter_color_code[quarter]]
            else:
                quarter_color_code[quarter] = None

        self.df_background['color'] = '#F4F4F4'
        self.df['quarter_color'] = self.df['quarter'].apply(
            lambda x: quarter_color_code[x]).values
        # set as categorical to be used for plot category
        self.df['quarter_color'] = pd.Categorical(self.df['quarter_color'])

        return quarter_color_code

    def get_quarter_info(self):
        quarter_info = {}

        for quarter in self.df['quarter'].unique():
            if quarter != 'None':
                quarter_info[quarter] = {
                    'start': YEARLY_QUARTERS_START[quarter],
                    'end': YEARLY_QUARTERS_END[quarter],
                    'color': self.quarter_color_code[quarter]
                }

        return quarter_info

    def get_month_info(self):

        month_info = {}

        for quarter in self.df['quarter'].unique():

            if quarter != 'None':
                for month_start_end in get_months(YEARLY_QUARTERS_START[quarter], YEARLY_QUARTERS_END[quarter]):
                    month_name = calendar.month_name[pd.to_datetime(
                        month_start_end[0]).month]

                    month_info[month_name] = {
                        'start': month_start_end[0],
                        'end': month_start_end[1],
                        'color': self.quarter_color_code[quarter]
                    }

        return month_info

    def get_fig_timeline(self, quarters, months):

        fig = px.timeline(
            self.df_background,
            x_start='first', x_end='last',
            y='task',
            category_orders={'task': self.df["task"]}
        )

        fig.add_trace(px.timeline(
            self.df,
            x_start='start', x_end='end',
            y='task',
            custom_data=['description'],
            # color_discrete_sequence=self.color_palette, color='quarter_color',
            category_orders={'task': self.df["task"]}
        ).data[0])

        margin = dict(l=50, r=50, b=100, t=100, pad=4)
        pos, width = get_header_pos(fig, margin)

        if months:
            month_info = self.get_month_info()
            for month in month_info.keys():
                fig.add_shape(
                    type="rect",
                    x0=month_info[month]['start'], x1=month_info[month]['end'],
                    y0=pos, y1=pos+width,
                    xref='x', yref='paper',
                    line=dict(color=hex_to_rgba('#F4F4F4', 1)),
                    fillcolor=hex_to_rgba('#F4F4F4', 1),
                    opacity=1
                )
                fig.add_annotation(
                    text=month,
                    x=get_midpoint_date(
                        max([month_info[month]['start'], self.start_date]),
                        min([month_info[month]['end'], self.end_date])
                    ),
                    y=(pos+width),
                    yref='paper',
                    showarrow=False,
                    font=dict(color="#0A4074"),
                )
            pos += width + 0.04

        if quarters:
            quarter_info = self.get_quarter_info()
            for quarter in quarter_info.keys():
                fig.add_shape(
                    type="rect",
                    x0=quarter_info[quarter]['start'], x1=quarter_info[quarter]['end'],
                    y0=pos, y1=pos+width,
                    xref='x', yref='paper',
                    line=dict(color=hex_to_rgba(
                        quarter_info[quarter]['color'], 1)),
                    fillcolor=hex_to_rgba(
                        quarter_info[quarter]['color'], 1),
                    opacity=1
                )
                fig.add_annotation(
                    text=f'Q{quarter}',
                    x=get_midpoint_date(
                        max([quarter_info[quarter]['start'], self.start_date]),
                        min([quarter_info[quarter]['end'], self.end_date])),
                    y=(pos+width),
                    yref='paper',
                    showarrow=False,
                    font=dict(color="#FFFFFF"),
                )

        fig.update_yaxes(
            title='', visible=True, showticklabels=True)
        fig.update_xaxes(visible=False, showticklabels=False, range=[
                         self.start_date, self.end_date])
        fig.update_traces(hovertemplate="%{customdata[0]}", marker=dict(
            color=self.df_background['color']), selector=0)
        fig.update_traces(marker=dict(
            color=self.df['quarter_color']), selector=1)
        fig.update_layout(
            yaxis_type='category',
            plot_bgcolor='white',
            coloraxis_showscale=False,
            showlegend=False,
            barmode='overlay',
            margin=margin,
        )

        return fig


def get_header_pos(fig, margin):
    layout_height = fig.layout.height
    if not layout_height:
        layout_height = 450
    width = ((layout_height - margin['t'] - margin['b']) /
             len(fig.to_dict()['data'][0]['y'])) / (layout_height * 0.8)
    return 1.1, width


def get_quarter_from_strdate(strdate):
    try:
        date = pd.to_datetime(strdate)
        quarter = ((date.month-1)//3 + 1)
        return quarter
    except:
        return 'None'


def get_months(start_date, end_date):
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Create a date range with monthly frequency
    months = pd.date_range(start=start, end=end, freq='MS')

    month_days = []
    for month_start in months:
        first_day = month_start
        last_day = month_start + pd.offsets.MonthEnd(0)
        month_days.append((first_day.strftime('%Y-%m-%d'),
                          last_day.strftime('%Y-%m-%d')))

    return month_days


def get_midpoint_date(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    midpoint = start_date + (end_date - start_date) / 2
    return midpoint.strftime('%Y-%m-%d')


def hex_to_rgba(h, alpha):
    '''
    converts color value in hex format to rgba format with alpha transparency
    '''
    return 'rgba' + str(tuple([int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)] + [alpha]))
