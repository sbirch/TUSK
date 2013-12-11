import dataset
import matplotlib.pyplot as plt

db = dataset.connect('sqlite:///../db/atus.db')

res = db.query('select atussum_0312.TEAGE AS age, avg(atusresp_0312.TRTFAMILY) AS time from atusresp_0312, atussum_0312 where  atusresp_0312.TUCASEID = atussum_0312.TUCASEID GROUP BY age;')
age = []
time = []
for row in res:
    age.append(row['age'])
    time.append(row['time'])

plt.plot(age, time)

res = db.query('select atussum_0312.TEAGE AS age, avg(atusresp_0312.TRTFAMILY) from atusresp_0312, atussum_0312 where  atusresp_0312.TUCASEID = atussum_0312.TUCASEID and atussum_0312.TRCHILDNUM <= 0 GROUP BY age;')
