from datetime import date, timedelta
from random import uniform

start = date(2016,1,1)
end = date(2016,12,31)
dates = [start + timedelta(days=x) for x in range((end-start).days + 1)]
DAU = [int(uniform(8,12)*1000*1000) for _ in range(len(dates))]

filename = 'sample_DAU.csv'
f = open(filename, 'w')
f.write('date,DAU\n')
for i in range(len(dates)):
	f.write('{},{}\n'.format(dates[i],DAU[i]))
f.close()