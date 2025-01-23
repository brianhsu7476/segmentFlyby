from math import *
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import polyline
import json
import pandas as pd

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
		a.append((float(i.get('lat')), float(i.get('lon')), dt))
	return a

def parse_segment(file_path):
	with open(file_path, 'r') as fp:
		b=json.load(fp)
	b=pd.json_normalize(b)
	b=b['map.polyline'].apply(polyline.decode)[0]
	return b

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
	print(ok0, ok1)
	ok=[]
	for i in ok0:
		for j in ok1:
			if match(a[i:j+1], b, d2):
				ok.append((i, j))
	return min(ok, key=lambda x:a[x[1]][2]-a[x[0]][2])

def normal(a):
	sm=sum(a)
	return [i/sm for i in a]

a0=parse_gpx('activity0.gpx')
a1=parse_gpx('activity1.gpx')
b=parse_segment('segment')
t0=find_match(a0, b)
t1=find_match(a1, b)
t2=[t1[0]]
for i in range(t0[0]+1, t0[1]+1):
	j=t2[-1]
	while j<t1[1] and d(a0[i][0], a0[i][1], a1[j][0], a1[j][1])>d(a0[i][0], a0[i][1], a1[j+1][0], a1[j+1][1]):
		j+=1
	if j<d(a0[i][0], a0[i][1], a1[j][0], a1[j][1])
	

# d0=[0]
# for i in range(t0[0], t0[1]):
# 	d0.append(d0[-1]+d(a0[i][0], a0[i][1], a0[i+1][0], a0[i+1][1]))
# d1=[0]
# for i in range(t1[0], t1[1]):
# 	d1.append(d1[-1]+d(a1[i][0], a1[i][1], a1[i+1][0], a1[i+1][1]))
# print(d0[-1], d1[-1])
# d0=[i/d0[-1] for i in d0]
# d1=[i/d1[-1] for i in d1]
# 
