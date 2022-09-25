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

print("top 30 indicators: ")
print(' name, score')
for i in range(30):
    print(paired_indicators[i][0], paired_indicators[i][1])

with open('indicators-scored-africa-sorted.csv', 'w') as fd:
    fd.writelines([', '.join(['"indicator name", "score"']) + '\n'])
    fd.writelines(list(map(lambda x: (', '.join([x[0], str(x[1])]) + '\n'), paired_indicators)))

for category in canonicalized_indicators:
    with open('african-data-since2000-' + category[0] + '.csv', 'w') as fd:
        fd.writelines(list(map(lambda x: (', '.join(x)) + '\n', category[1])))



