from tusk import atus, variables


result = atus.db.query('''SELECT age, weighted_avg(family_time, respondents.weight) FROM respondent_link(respondents, summary, cps) GROUP BY age;''')	

ages = []
ft = []
for r in result:
	ages.append(r['age'])
	ft.append(r['TUFNWGTP)'])
	#print r
	print '%s,%s' % (r['age'], r['TUFNWGTP)'])

'''
import matplotlib.pyplot as plt
plt.plot(ages, ft)
plt.show()
'''