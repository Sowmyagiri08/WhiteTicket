import re
import urllib
from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template, request,flash,url_for,session
import reverse_geocoder as rg 
from werkzeug import secure_filename
import cv2
import sys
import pytesseract
import psycopg2
import googlemaps
import datetime
from datetime import date
import os
URL = 'http://www.way2sms.com/api/v1/sendCampaign'

def reverseGeocode(coordinates):
        result = rg.search(coordinates)
        #dict=json.loads(result)
    # result is a list containing ordered dictionary. 
    #pprint.pprint(dict)
        dict=result[0]
        return dict
		
def sendPostRequest(reqUrl, apiKey, secretKey, useType, phoneNo, senderId, textMessage):
  req_params = {
  'apikey':apiKey,
  'secret':secretKey,
  'usetype':useType,
  'phone': phoneNo,
  'message':textMessage,
  'senderid':senderId
  }
  return requests.post(reqUrl, req_params)

app = Flask(__name__)
app.secret_key='Sowmya08$'
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
   
@app.route('/')
def login():
	return render_template('index.html')

@app.route('/signup')
def signup():
	return render_template('signup.html')
	
	
@app.route('/loginp')
def loginp():
	return render_template('index.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      result = request.form
      return render_template("result.html",result = result)
	  
@app.route('/upload')
def upload():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_fil():
   if request.method == 'POST':
		cl="'"
		conn = psycopg2.connect(database = "postgres", user = "postgres", password = "sowmya", host = "127.0.0.1", port = "5432")
		cur = conn.cursor()
		f2 = request.files['file']
		f2.save(secure_filename(f2.filename))
		pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'
		config = ('-l eng --oem 1 --psm 3')
		im = cv2.imread(f2.filename, cv2.IMREAD_COLOR)
		text = pytesseract.image_to_string(im, config=config).encode('utf-8')
		F = open("testfile.txt","w") 
		F.write(text)
		F.close()
		f=open("testfile.txt","r")
		t=f.read().lower()
		f1=open("theatre_list.txt","r")
		theatres=f1.read().lower()
		tlist=theatres.replace(","," ").split()
		slist=t.replace(","," ").split()
		s=set(tlist)&set(slist)
		st=" ".join(s)
		f=open("testfile.txt","r")
		t=f.read()
		seat=re.findall(" [A-Z][0-9]+",t)
		seats=" ".join(seat)
		x = re.findall("ID.+",t)
		bid=" ".join(x)
		bid=bid[3:]
		time=re.findall("[0-9]{2}:[0-9]{2} [A|P]M",t)
		times=" ".join(time)
		print(times)
		movie=re.findall("Movie.+",t)
		movie=" ".join(movie)
		movie=movie[5:]
		movie=movie.replace(" ","")
		print(movie)
		cur.execute('DROP VIEW test')
		cur.execute("create view test as select * from palazzo")
		cur.execute("select * from test where booking_id='"+bid+cl)
		rows = cur.fetchall()
		for row in rows:
			str_for_qr=str(row[0])+"|"+str(row[1])+"|"+str(row[2])+"|"+str(row[3])+"|"+str(row[4])+"|"+str(row[5])
		today_date=date.today()
		today_time=datetime.datetime.now().time()
		sd=str(row[2])
		if str_for_qr==" ":
			print("Invalid")
		else:
			if today_date>row[2]:
				print("Invalid")
			if today_date==row[2]:
				if today_time>row[3]:
					print("Invalid")
			else:
				postgres_insert_query = """ INSERT INTO valids VALUES (%s,%s,%s,%s,%s,%s)"""
				record_to_insert = (bid, seats, st,times,movie,sd)
				cur.execute(postgres_insert_query, record_to_insert)
				conn.commit()
				cur.execute('select * from useerr')
				rows=cur.fetchall()
				for row in rows:
					pref=str(row[3])
					gmaps = googlemaps.Client(key='AIzaSyCn2LdtM5N7wyYtt9uBE7c0lUiMwl5SQdA')
					my_dist = gmaps.distance_matrix(st,pref)['rows'][0]['elements'][0]
					if(my_dist['status']=='ZERO_RESULTS'):
						msg_text="Ticket notification\n"+"Hey there! There are tickets available at your prefered theatre for the movie "+movie+"Seats: "+seats+" at "+st+times+" on "+sd
					
						print(msg_text)
						print(str(row[1]))
						response = sendPostRequest(URL, '9YC0M0G1T7MY7UZB2JJDQ7GB49JF2GDL', 'CKAHL8MRLZ7T2AAA', 'stage', str(row[1]), '32', msg_text )
						print (response.text)
		return 'file uploaded successfully '+f2.filename
		
@app.route('/gl')
def gl():
	return render_template("geolocation.html")


@app.route('/view', methods = ['GET', 'POST'])
def view():
	result=[]
	lat=request.form['lat']
	lon=request.form['lon']
	coordinates=(lat,lon)
	location=reverseGeocode(coordinates)
	conn = psycopg2.connect(database = "postgres", user = "postgres", password = "sowmya", host = "127.0.0.1", port = "5432")
	cl="'"
	
	cur = conn.cursor()
	today_date=str(date.today())
	today_time=str(datetime.datetime.now().time())
	cur.execute('select * from valids where'+cl+today_date+cl+'<showdate;')
	rows=cur.fetchall()
	for row in rows:
		m=[]
		pref=str(row[2])
		gmaps = googlemaps.Client(key='AIzaSyCn2LdtM5N7wyYtt9uBE7c0lUiMwl5SQdA')
		my_dist = gmaps.distance_matrix(pref,location['name']+','+location['admin2']+','+location['admin1'])['rows'][0]['elements'][0]
		if(my_dist['status']!='ZERO_RESULTS'):
			st=my_dist['distance']['text']
			st=st[0:3]
			if(float(st)<20.00):
				m.extend([row[1],row[2],row[3],row[4]])
				print
				result.append(m)
	if(len(result)>0):
		return render_template("view.html",r1=result[0])
	else:
		return render_template("view.html")
	
	
@app.route('/valid',methods=['GET', 'POST'])
def valid():
	conn = psycopg2.connect(database = "postgres", user = "postgres", password = "sowmya", host = "127.0.0.1", port = "5432")
	cl="'"
	cur = conn.cursor()
	username=request.form['username']
	session['username']=username
	password=request.form['password']
	cur.execute('select pwd from useerr where username='+cl+username+cl+"and pwd='"+password+cl+";")
	rows=cur.fetchall()
	if(cur.rowcount):
		return render_template("geolocation.html")
	else:
		return render_template("invalid.html")
		
		
@app.route('/sign',methods=['POST'])
def sign():
	conn = psycopg2.connect(database = "postgres", user = "postgres", password = "sowmya", host = "127.0.0.1", port = "5432")
	cl="'"
	cur = conn.cursor()
	username=request.form['usernamesignup']
	phone=request.form['emailsignup']
	pwd=request.form['passwordsignup']
	cpwd=request.form['passwordsignup_confirm']
	cur.execute('select pwd from useerr where username='+cl+username+cl+";")
	if(cur.rowcount==0):
		if(pwd==cpwd):
			postgres_insert_query = """ INSERT INTO useerr VALUES (%s,%s,%s)"""
			record_to_insert = (username,phone,pwd)
			cur.execute(postgres_insert_query, record_to_insert)
			conn.commit()
			return render_template("index.html")

@app.route('/changep',methods=['GET','POST'])
def changep():
	conn = psycopg2.connect(database = "postgres", user = "postgres", password = "sowmya", host = "127.0.0.1", port = "5432")
	cl="'"
	cur = conn.cursor()
	username=session.get('username',None)
	password=request.form['new1']
	sql = """ UPDATE useerr SET pwd = %s WHERE username = %s"""
	cur.execute(sql,(password,username))
	conn.commit()
	return 'Password updated successfully'
	


@app.route('/profile')
def profile():
	username=session.get('username',None)
	return render_template("profile.html",u=username)
@app.route('/changepwd')
def changepwd():
	return render_template('changepwd.html')
	
@app.route('/ut',methods=['POST'])
def ut():
	conn = psycopg2.connect(database = "postgres", user = "postgres", password = "sowmya", host = "127.0.0.1", port = "5432")
	cl="'"
	cur = conn.cursor()
	username=session.get('username',None)
	theatre=request.form['pref']
	sql = """ UPDATE useerr SET pref = %s WHERE username = %s"""
	cur.execute(sql,(theatre,username))
	conn.commit()
	return 'Preference updated successfully'
	
		
if __name__ == '__main__':
   app.run(debug = True)