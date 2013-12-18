import numpy as np
import scipy.spatial
from sklearn import manifold
import matplotlib.pyplot as plt
import tusk.atus as atus
import math
import functools32
from collections import Counter

random_cases = [x['caseid'] for x in atus.db.query('select respondents.caseid from respondents inner join summary on respondents.caseid=summary.caseid where minutes_working>120 order by random() limit 500')]

'''
random_cases = [20031009031805, 20110505111101, 20120302121318, 20030504033191,
20110302111360, 20040201041709, 20060302060511, 20080302081207, 20040112032778,
20100112091142, 20030705032646, 20100605100732, 20051110050839, 20081110081173,
20031211031999, 20090111080659, 20110101111533, 20040605041647, 20101111102089,
20050403051716, 20030112022622, 20100301101675, 20110504111952, 20050404050948,
20101211101391, 20110403111160, 20080302081151, 20100908101628, 20080201080730,
20080605080167, 20030504032942, 20110403110501, 20041211041182, 20070302071571,
20091009091727, 20060605061393, 20050706051141, 20051110051311, 20091110091985,
20100301101588, 20080605080547, 20031110030649, 20040504041194, 20110808112195,
20040201040766, 20050706051175, 20110212100922, 20100402101639, 20121009121668,
20090909091448, 20080201080836, 20040110033112, 20030807032050, 20120403121652,
20090908091367, 20051211052239, 20041009041726, 20110112101558, 20110604111221,
20110101112303, 20060302060501, 20110402111572, 20110504111043, 20060504061709,
20070504071540, 20100302100879, 20050707051673, 20060807060533, 20070504071415,
20061211061382, 20030403031703, 20080807082185, 20090706091095, 20070404072432,
20100201101183, 20030403031975, 20090303090536, 20090111081932, 20040907041797,
20060909061509, 20090302092134, 20120605122173, 20040704042004, 20120403122380,
20030212020681, 20030604033336, 20050605051503, 20070404071681, 20030908033334,
20040112031370, 20030403032090, 20050807051406, 20090504092493, 20060101061528,
20030302031598, 20060402062179, 20030908031287, 20070101070597, 20040908041705,
20120504122342]
'''

@functools32.lru_cache(maxsize=None)
def get_case_data(c):
	r = atus.db.query('''select
		activity_code,
		activity_number,
		start_minute,
		stop_minute
		from activities where caseid=%d order by start_minute''' % c)
	return list(r)

@functools32.lru_cache(maxsize=None)
def get_case_data_1(c):
	entries = get_case_data(c)
	activity_vector = {}
	for entry in entries:
		for m in xrange(entry['start_minute'], entry['stop_minute']+1):
			activity_vector[m] = entry['activity_code']

	result = tuple([activity_vector.get(m,None) for m in xrange(0, 1440+1, 10)])
	return result

@functools32.lru_cache(maxsize=None)
def get_case_data_2(c):
	entries = get_case_data(c)
	tier1_vector = Counter()
	for entry in entries:
		tier1_vector[int(entry['activity_code'][:2])] += entry['stop_minute'] - entry['start_minute']

	# Note that this ignores class 18 (travel) and class 50 (data codes)
	result = np.array([tier1_vector.get(tier1, 0) for tier1 in xrange(0, 18)])
	return result

def actdiff(x,y):
	if x is None or y is None:
		return 1

	x1,x2,x3 = x[:2],x[2:4],x[4:]
	y1,y2,y3 = y[:2],y[2:4],y[4:]

	if x1 == '18':
		x1 = x2
	if y1 == '18':
		y1 = y2

	score = 1
	if x1 == y1:
		score -= 0.5
	if x1 == y1 and x2 == y2:
		score -= 0.3
	if x == y:
		score -= 0.2

	return score

def case_distance_1(c1, c2):
	c1, c2 = int(c1), int(c2)
	d1 = get_case_data_1(c1)
	d2 = get_case_data_1(c2)
	return sum([actdiff(x,y) for x,y in zip(d1,d2)])**3

def case_distance_2(c1, c2):
	c1, c2 = int(c1), int(c2)
	d1 = get_case_data_2(c1)
	d2 = get_case_data_2(c2)
	return np.sum( (d1-d2)**2 )

def color_day(case):
	weekday = atus.db.get('''select weekday from respondents where caseid=%d''' % case)
	if weekday.lower() in ['saturday', 'sunday']:
		return plt.cm.winter(0.0)
	return plt.cm.winter(1.0)

def color_work(case):
	mins = atus.db.get('''select minutes_working from summary where caseid=%d''' % case)
	if mins < 120:
		return plt.cm.winter(0.0)
	return plt.cm.winter(1.0)

def look(case):
	marker = 'o'
	weekday = atus.db.get('''select weekday from respondents where caseid=%d''' % case)
	if weekday.lower() in ['saturday', 'sunday']:
		marker = 'v'

	#mins = atus.db.get('''select minutes_working from summary where caseid=%d''' % case)
	income_code = atus.db.get('''select family_income_code from cps where caseid=%d and lineno=1''' % case)

	return 40, marker, plt.cm.Greys(1.0 - (income_code/16.0))

np.set_printoptions(precision=2)

case_vectors = []
for case in random_cases:
	case_vectors.append((case,))

dists = scipy.spatial.distance.pdist(
		case_vectors, case_distance_2
	)
dists = scipy.spatial.distance.squareform(dists)
#print scipy.spatial.distance.squareform(dists)


mds = manifold.MDS(2, dissimilarity="precomputed")
Y = mds.fit_transform(dists)

for i in xrange(len(Y)):
	size, marker, color = look(case_vectors[i])
	plt.scatter(Y[i, 0], Y[i, 1], c=color, s=size, marker=marker)
plt.title("MDS embedding")

plt.show()