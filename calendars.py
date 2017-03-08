from __future__ import absolute_import, print_function

from calendar import Calendar, day_abbr as day_abbrs, month_name as month_names

from bokeh.layouts import gridplot
from bokeh.models import Plot, ColumnDataSource, FactorRange, CategoricalAxis, HoverTool
from bokeh.models.glyphs import Text, Rect
from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.resources import INLINE
from bokeh.util.browser import view
from bokeh.sampledata.us_holidays import us_holidays

import pandas as pd

def read_data(filename):
    df = pd.read_csv(filename)
    df['year'] = df.apply(lambda x: x.date[:4], 1)
    df['month'] = df.apply(lambda x: x.date[5:7], 1)
    df['day'] = df.apply(lambda x: x.date[8:10], 1)
    return df

def get_DAU(dataframe, m, m_d):
    subdf = dataframe[pd.to_numeric(dataframe.month)==m]
    d = dict(zip([day.lstrip("0") for day in subdf.day], ["{:,}".format(dau) for dau in pd.to_numeric(subdf.DAU)]))
    d[None]=''
    return [d[day] for day in m_d]

def make_calendar(filename, year, month, firstweekday="Mon"):
    firstweekday = list(day_abbrs).index(firstweekday)
    calendar = Calendar(firstweekday=firstweekday)

    month_days  = [ None if not day else str(day) for day in calendar.itermonthdays(year, month) ]
    month_weeks = len(month_days)//7

    df = read_data(filename)
    DAU = get_DAU(df, month, month_days)

    workday = "linen"
    weekend = "lightsteelblue"

    def weekday(date):
        return (date.weekday() - firstweekday) % 7

    def pick_weekdays(days):
        return [ days[i % 7] for i in range(firstweekday, firstweekday+7) ]

    day_names = pick_weekdays(day_abbrs)
    week_days = pick_weekdays([workday]*5 + [weekend]*2)

    all_days = list(day_names)*month_weeks
    all_weeks = sum([ [str(week)]*7 for week in range(month_weeks) ], [])
    all_backgrounds = sum([week_days]*month_weeks, [])

    source = ColumnDataSource(data=dict(
        days            = [all_days[i] for i in range(len(month_days)) if month_days[i] is not None],
        weeks           = [all_weeks[i] for i in range(len(month_days)) if month_days[i] is not None],
        month_days      = [month_days[i] for i in range(len(month_days)) if month_days[i] is not None],
        day_backgrounds = [all_backgrounds[i] for i in range(len(month_days)) if month_days[i] is not None],
        dau             = [DAU[i] for i in range(len(month_days)) if month_days[i] is not None],
    ))

    holidays = [ (date, summary.replace("(US-OPM)", "").strip()) for (date, summary) in us_holidays
        if date.year == year and date.month == month and "(US-OPM)" in summary ]

    holidays_source = ColumnDataSource(data=dict(
        holidays_days  = [ day_names[weekday(date)] for date, _ in holidays ],
        holidays_weeks = [ str((weekday(date.replace(day=1)) + date.day) // 7) for date, _ in holidays ],
        month_holidays = [ summary for _, summary in holidays ],
        dau            = [DAU[month_days.index(str(date.day))] for date, __ in holidays],
    ))

    nulldays_source = ColumnDataSource(data=dict(
        null_days = [all_days[i] for i in range(len(month_days)) if month_days[i] is None],
        null_weeks = [all_weeks[i] for i in range(len(month_days)) if month_days[i] is None],
    ))

    xdr = FactorRange(factors=list(day_names))
    ydr = FactorRange(factors=list(reversed([ str(week) for week in range(month_weeks) ])))

    plot = Plot(x_range=xdr, y_range=ydr, plot_width=300, plot_height=300, outline_line_color=None)
    plot.title.text = month_names[month]
    plot.title.text_font_size = "12pt"
    plot.title.text_color = "darkolivegreen"
    plot.title.offset = 25
    plot.min_border_left = 0
    plot.min_border_bottom = 5

    rect = Rect(x="days", y="weeks", width=0.9, height=0.9, fill_color="day_backgrounds", line_color="silver")
    plot.add_glyph(source, rect)
    rect_renderer = plot.add_glyph(source, rect)

    rect = Rect(x="holidays_days", y="holidays_weeks", width=0.9, height=0.9, fill_color="pink", line_color="indianred")
    plot.add_glyph(holidays_source, rect)
    rect_renderer_holidays = plot.add_glyph(holidays_source, rect)

    rect = Rect(x="null_days", y="null_weeks", width=0.9, height=0.9, fill_color="white", line_color="white")
    plot.add_glyph(nulldays_source, rect)
    rect_renderer_nulldays = plot.add_glyph(nulldays_source, rect)

    text = Text(x="days", y="weeks", text="month_days", text_align="center", text_baseline="middle")
    plot.add_glyph(source, text)

    xaxis = CategoricalAxis()
    xaxis.major_label_text_font_size = "8pt"
    xaxis.major_label_standoff = 0
    xaxis.major_tick_line_color = None
    xaxis.axis_line_color = None
    plot.add_layout(xaxis, 'above')

    hover_tool = HoverTool(plot=plot, renderers=[rect_renderer], tooltips=[("DAU", "@dau")])
    plot.tools.append(hover_tool)
    hover_tool = HoverTool(plot=plot, renderers=[rect_renderer_holidays], tooltips=[("DAU", "@dau"), ("Holiday", "@month_holidays")])
    plot.tools.append(hover_tool)

    return plot

filename = 'sample_DAU.csv'
months = [ [ make_calendar(filename, 2016, 3*i + j + 1, "Mon") for j in range(3) ] for i in range(4) ]
grid = gridplot(toolbar_location=None, children=months)

doc = Document()
doc.add_root(grid)

if __name__ == "__main__":
    doc.validate()
    filename = "calendars.html"
    with open(filename, "w") as f:
        f.write(file_html(doc, INLINE, "Calendar"))
    print("Wrote %s" % filename)
    view(filename)

