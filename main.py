import csv
wbi_prefix = 'World-Bank-Data-by-Indicators'
wbi_cats = [
    "agriculture-and-rural-development",
    "aid-effectiveness",
    "climate-change",
    "economy-and-growth",
    "education",
    "energy-and-mining",
    "environment",
    "external-debt",
    "financial-sector",
    "gender",
    "health",
    "infrastructure",
    "poverty",
    "private-sector",
    "public-sector",
    "science-and-technology",
    "social-development",
    "social-protection-and-labor",
    "trade",
    "urban-development"
]

# ISO country codes
with open('country-codes.csv') as fd:
    ccs = fd.readlines()
parsed_ccs = [r for r in csv.reader(ccs)]
# list of country code -> name mappings
african_ccs = list(map(lambda x: (x[2], x[0]), filter(lambda x: x[5] == 'Africa', parsed_ccs)))
african_codes = set(map(lambda x: x[0], african_ccs))

# world data
# country code is at 2nd position of each line
# indicator name is 3rd position of each line
# row 4 is the legend
#print(indicators_parsed[4])
string_escaper = lambda ls: list(map(lambda x: '"' + x + '"', ls))
# escape 1960-1999 and 2020, inclusive
# this leaves us data for the period 2000 - 2019
row_transformer = lambda ls: ls[0:4] + ls[44:-2]
# how many years present 
how_many_years_present = lambda row: sum(map(lambda _: 1, filter(lambda entry: entry != '""' and entry != '', row[4:])))
# form a file path
path = lambda l: '/'.join(l)
# get file name representing a WBI category
wbi_fn = lambda i: i + '-raw-2021.csv'
# canonicalize list of indicators inside a file containing a category of indicators
def canonicalize_indicators(cat_file, cat_name):
    with open(cat_file) as fd:
        indicators = fd.readlines()
    indicators_parsed = [r for r in csv.reader(indicators)]
    african_indicators = list(filter(lambda x: x[1] in african_codes, indicators_parsed[5:]))
    african_indicators = list(map(lambda row: string_escaper(row), african_indicators))
    african_indicators = list(map(row_transformer, african_indicators))
    african_indicators_header = row_transformer(indicators_parsed[4])
    return cat_name, [ african_indicators_header ] + african_indicators



canonicalized_indicators = [canonicalize_indicators(path([wbi_prefix, i, wbi_fn(i)]), i) for i in wbi_cats]

# big flattened dict of indicators
indicators = {}

for category in canonicalized_indicators:
    category = category[1]
    for row in category:
        indicators[row[2]] = []
    for row in category:
        # row[1] is 3-digit ISO country code
        # print('how many years present for ', row[1], ': ', how_many_years_present(row))
        indicators[row[2]].append((row[1], how_many_years_present(row)))

# rank indicators by quality of data (i.e. less # entries missing the better)
indicator_score = {}

for indicator in indicators:
    # indicator scoring scheme for indicators selection:
    # we are looking at 20 years worth of data.
    # each year present per country contributes 1/20 towards the score
    # the max score a country contributes is 1
    indicator_score[indicator] = sum(map(lambda x: x[1] * 1/20, indicators[indicator]))
paired_indicators = [(i, indicator_score[i]) for i in indicator_score]
paired_indicators.sort(key = lambda x: x[1], reverse=True)

# print("top 30 indicators: ")
# print(' name, score')
# for i in range(30):
#    print(paired_indicators[i][0], paired_indicators[i][1])

with open('indicators-scored-africa-sorted.csv', 'w') as fd:
    fd.writelines([', '.join(['"indicator name", "score"']) + '\n'])
    fd.writelines(list(map(lambda x: (', '.join([x[0], str(x[1])]) + '\n'), paired_indicators)))

for category in canonicalized_indicators:
    with open('african-data-since2000-' + category[0] + '.csv', 'w') as fd:
        fd.writelines(list(map(lambda x: (', '.join(x)) + '\n', category[1])))


###
# graphing of indicators we selected
# economic indicators
# -------------------------
# indicator 1: GDP per capita
# indicator 2: GNI per capita
# indicator 3: GDP total, current USD
# indicator 4: GNI total, current USD
# indicator 5: access to electricity, % of population
# indicator 6: direct foreign investment 
# political indicators
# -------------------------
# indicator A: life expectancy at birth (cumulative)
# indicator B: access to education 

#import plotly.express as px
#df = px.data.gapminder().query("country=='Canada'")
#fig = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')
#fig.show()
import plotly.graph_objects as go

"""
import plotly.graph_objects as go

# Create random data with numpy
import numpy as np
np.random.seed(1)

N = 100
random_x = np.linspace(0, 1, N)
random_y0 = np.random.randn(N) + 5
random_y1 = np.random.randn(N)
random_y2 = np.random.randn(N) - 5

fig = go.Figure()

# Add traces
fig.add_trace(go.Scatter(x=random_x, y=random_y0,
                    mode='markers',
                    name='markers'))
fig.add_trace(go.Scatter(x=random_x, y=random_y1,
                    mode='lines+markers',
                    name='lines+markers'))
fig.add_trace(go.Scatter(x=random_x, y=random_y2,
                    mode='lines',
                    name='lines'))

fig.show()

"""

class WBIndicator(object):
    """
        The category of world bank indicators.
    """
    def __init__(self, name):
        self.name = name
        self.countries = {}
    
    def add(self, country_name, country_years):
        self.countries[country_name] = country_years
    
    def plot(self):
        fig = go.Figure() #layout_title_text=self.name) 
        years = ['200' + str(x) for x in range(2020)]
        for country in self.countries:
            cs = go.Scatter(x = years, y = self.countries[country], mode='lines+markers', name=country.strip('"'))
            fig.add_trace(cs)

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), xaxis_title = self.name.strip('"')) # hack to display title at the bottom
        fig.show()
        #ig.show(renderer="png", width=8000, height=4000)

    def __str__(self):
        acc = self.name + ' {\n'
        for country in self.countries:
            acc += '[ ' + country + ', ' + str(self.countries[country]) + ' ]\n'
        acc += '}\n'
        return acc 

class CombineOperator(object):
    """
        The abstract product operation (X) on a pair of WBIndicators.
    """
    def __init__(self, name, op):
        self.name = name 
        self.op = op

    def __str__(self):
        return self.name

    def __call__(self, r1, r2):
        return self.op(r1, r2)

class CombinedWBIndicator(WBIndicator):

    """
        The product functor on WBIndicators.

        WBIndicator            WBIndicator
                \               /
                 \             /
                 CombineOperator
                        |
                    WBIndicator
    """
    def __init__(self, ind1, ind2, combine_op):
        self.ind1 = ind1 
        self.ind2 = ind2 
        self.combine_op = combine_op
        self.name = (ind1.name + combine_op.name + ind2.name)
        super().__init__(self.name)
        for country in ind1.countries:
            ind1_row = ind1.countries[country]
            ind2_row = ind2.countries[country] if country in ind2.countries else None
            self.countries[country] = (self.combine_op(ind1_row, ind2_row))

indicator1 = WBIndicator('"GDP per capita (current US$)"')
indicator2 = WBIndicator('"GNI per capita, Atlas method (current US$)"')
indicator3 = WBIndicator('"GDP (current US$)"')
indicator4 = WBIndicator('"GNI, Atlas method (current US$)"')
indicator5 = WBIndicator('"Access to electricity (% of population)"')
indicator6 = WBIndicator('"Foreign direct investment, net (BoP, current US$)"')

indicatorA = WBIndicator('"Life expectancy at birth, total (years)"')
#indicatorB_numerator = WBIndicator('"Primary education, pupils"')
#indicatorB_denominator = WBIndicator('"Population ages 0-14 (% of total population)"')
indicatorC = WBIndicator('"School enrollment, primary (% gross)"')


# some helper operations
safety = lambda x, y, z:    \
    x if y == None else     \
        y if x == None else \
            z(x, y)

wbi_divider = CombineOperator("/", 
    lambda x, y: safety(x, y, lambda x, y: [safety(x[i], y[i], lambda a, b: a / b) for i in range(len(x))]))

# pipeline of indicators to process
indicator_pipeline = [
    indicator1, indicator2, indicator3,
    indicator4, indicator5, indicator6, 
    indicatorA, indicatorC]

wbi_row_canonicalizer = lambda ls: list(map(lambda x: None if x == '""' else float(x.strip('"')), ls))

for ind in indicator_pipeline:
    for category in canonicalized_indicators:
        category = category[1]
        for row in category:
            # row[2] is the category name
            if row[2] == ind.name:
                ind.add(row[0], wbi_row_canonicalizer(row[4:]))

# compute indicatorB last as we do eager computation
#indicatorB = CombinedWBIndicator(indicatorB_numerator, indicatorB_denominator, wbi_divider)
#indicatorB.name = "Number of primary education pupils normalized by population aged 0-14"
#indicatorB.plot()
#indicator_pipeline[-1].plot()
#indicator_pipeline[0].plot()
#indicator_pipeline[1].plot()
for ind in indicator_pipeline:
    ind.plot()
#for ind in indicator_pipeline:
#    print(ind)

