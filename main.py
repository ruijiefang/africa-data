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
with open('all-data.csv') as fd:
    indicators = fd.readlines()
indicators_parsed = [r for r in csv.reader(indicators)]
# row 4 is the legend
#print(indicators_parsed[4])
african_indicators =list(filter(lambda x: len(x) >= 2 and x[1] in african_codes, indicators_parsed[5:]))

with open('african-data.csv', 'w') as fd:
    fd.writelines([', '.join(indicators_parsed[4]) + '\n'])
    fd.writelines(list(map(lambda x: (', '.join(x)) + '\n', african_indicators)))

    