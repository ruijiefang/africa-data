import csv
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

with open('all-data.csv') as fd:
    indicators = fd.readlines()
indicators_parsed = [r for r in csv.reader(indicators)]
# row 4 is the legend
#print(indicators_parsed[4])
string_escaper = lambda ls: list(map(lambda x: '"' + x + '"', ls))
# escape 1960-1999 and 2020-2021, inclusive
# this leaves us data for the period 2000 - 2019
row_transformer = lambda ls: ls[0:4] + ls[44:-3]
african_indicators = list(filter(lambda x: x[1] in african_codes, indicators_parsed[5:]))
african_indicators = list(map(lambda row: string_escaper(row), african_indicators))
african_indicators = list(map(row_transformer, african_indicators))
african_indicators_header = row_transformer(indicators_parsed[4])
indicators = {}

def how_many_years_present(row):
    # after row transformation,
    # year 2000 starts on col 5 which means index 4 in zero indexing
    cnt = 0
    for x in row[4:]:
        if x != '""':
            cnt += 1
    return cnt

for row in african_indicators:
    indicators[row[2]] = []

for row in african_indicators:
    # row[1] is 3-digit ISO country code
    indicators[row[2]].append((row[1], how_many_years_present(row)))

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

#with open('african-data-since2000.csv', 'w') as fd:
#    fd.writelines([', '.join(african_indicators_header) + '\n'])
#    fd.writelines(list(map(lambda x: (', '.join(x)) + '\n', african_indicators)))

