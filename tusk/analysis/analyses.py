from tusk import atus, variables
import matplotlib.pyplot as plt

ages = []
ft = []
for r in atus.db.query('''SELECT
	age, weighted_avg(family_time, respondents.weight)
	FROM respondent_link(respondents, summary, cps) where PRNMCHLD=0 GROUP BY age;'''):
	ages.append(r['age'])
	ft.append(r['TUFNWGTP)'])
plt.plot(ages, ft)

plt.show()