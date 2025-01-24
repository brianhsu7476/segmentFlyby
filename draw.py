from math import *
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import polyline
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
import sys

def d(lat1, lon1, lat2, lon2):
	if lat1==lat2 and lon1==lon2:
		return 0
	C=acos(-1)/180
	lat1, lon1, lat2, lon2=lat1*C, lon1*C, lat2*C, lon2*C
	return 6371000*acos(sin(lat1)*sin(lat2)+cos(lat1)*cos(lat2)*cos(lon1-lon2))

def parse_xml(file_path):
	tree = ET.parse(file_path)
	root = tree.getroot()
	for elem in root.iter():
		elem.tag = elem.tag.split('}')[1] if '}' in elem.tag else elem.tag
		if 'xmlns' in elem.attrib:
			del elem.attrib['xmlns']
	return tree

def parse_gpx(file_path):
	tree=parse_xml(file_path)
	root=tree.getroot()
	a0=tree.find('trk').find('trkseg').findall('trkpt')
	timestamp_format="%Y-%m-%dT%H:%M:%SZ"
	a=[]
	for i in a0:
		dt1=datetime.strptime(a0[0].find('time').text, timestamp_format)
		dt2=datetime.strptime(i.find('time').text, timestamp_format)
		dt=(dt2 - dt1).total_seconds()
		a.append((float(i.get('lat')), float(i.get('lon')), dt, float(i.find('ele').text)))
	return a

def parse_segment(file_path):
	with open(file_path, 'r') as fp:
		b=json.load(fp)
	b=pd.json_normalize(b)
	return b['map.polyline'].apply(polyline.decode)[0], b['name'][0]

def local_min(a): # return the array of indices that are local minimum
	b=[]
	for i in range(len(a)):
		if (i==0 or a[i]<a[i-1]) and (i==len(a)-1 or a[i]<a[i+1]):
			b.append(i)
	return b

def match(a, b, d2):
	i, j=0, 0
	while j<len(b):
		if i==len(a):
			return 0
		if d(a[i][0], a[i][1], b[j][0], b[j][1])<d2:
			j+=1
		i+=1
	return 1

def find_match(a, b): # a activity, b segment
	d0, d1, d2=20, 20, 200 # start, end, path
	dis=[d(i[0], i[1], b[0][0], b[0][1]) for i in a]
	ok0=[]
	for i in local_min(dis):
		if dis[i]<d0:
			ok0.append(i)
	ok1=[]
	dis=[d(i[0], i[1], b[-1][0], b[-1][1]) for i in a]
	for i in local_min(dis):
		if dis[i]<d1:
			ok1.append(i)
	ok=[]
	for i in ok0:
		for j in ok1:
			if match(a[i:j+1], b, d2):
				ok.append((i, j))
	ret=min(ok, key=lambda x:a[x[1]][2]-a[x[0]][2])
	print(a[ret[1]][2]-a[ret[0]][2])
	return ret

def normal(a):
	sm=sum(a)
	return [i/sm for i in a]

def draw(x, y1, y2, name):
	# remember to remove the cache using rm ~/.cache/matplotlib -rf
	plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC']
	plt.rcParams['axes.unicode_minus'] = False
	fig, ax1 = plt.subplots()
	ax1.plot(x, y1, 'g-', label='y1: Elevation')
	ax1.set_xlabel('Distance (km)')
	ax1.set_ylabel('Elevation (m)')
	ax1.tick_params(axis='y')
	ax2 = ax1.twinx()
	ax2.plot(x, y2, 'r-', label='y2: Time Ahead')
	ax2.set_ylabel('Time Ahead (s)')
	ax2.tick_params(axis='y')
	fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
	plt.title(name)
	plt.savefig(sys.argv[1]+'/'+name+'.png')
	plt.show()

a0=parse_gpx(sys.argv[1]+'/activity0.gpx')
a1=parse_gpx(sys.argv[1]+'/activity1.gpx')
b, name=parse_segment(sys.argv[1]+'/segment')
t0=find_match(a0, b)
t1=find_match(a1, b)
t2=[t1[0]]
t3=[a1[t1[0]][2]]
for i in range(t0[0]+1, t0[1]):
	t2.append(min(list(range(t1[0], t1[1]+1)), key=lambda j:d(a0[i][0], a0[i][1], a1[j][0], a1[j][1])))
	t3.append(a1[t2[-1]][2])
t2.append(t1[1])
t3.append(a1[t1[1]][2])
dt=[a0[i][2]-a0[t0[0]][2]-t3[i-t0[0]]+t3[0] for i in range(t0[0], t0[1]+1)]
tmp=[d(a0[i][0], a0[i][1], a0[i+1][0], a0[i+1][1]) for i in range(t0[0], t0[1])]
dd=[0]
for i in tmp:
	dd.append(dd[-1]+i/1000)
ele=[a0[i][3] for i in range(t0[0], t0[1]+1)]
draw(dd, ele, dt, name)
