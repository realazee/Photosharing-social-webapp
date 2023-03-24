######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu> 
# Edited by: Aaron Zheng <aaronz@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'tn4LifeBFM.'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		gender=request.form.get('gender')
		email=request.form.get('email')
		password=request.form.get('password')
		dob=request.form.get('dob')
		fName=request.form.get('fName')
		lName=request.form.get('lName')
		hometown=request.form.get('hometown')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		#print("INSERT INTO Users (email, password,dob, fName, lName) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(email, password, dob, fName, lName))
		print("------")
		print(cursor.execute("INSERT INTO Users (gender, email, password,dob, fName, lName, hometown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(gender, email, password, dob, fName, lName, hometown)))
		print("------")
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		return flask.redirect(flask.url_for('register'))
		#return render_template('register.html', supress='False')

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures")
	return cursor.fetchall() 

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		albumName = request.form.get('albumName')
		hashTags = request.form.get('hashtags')
		cursor = conn.cursor()
		#execute making an album if it doesn't exist, or selecting an album if it does.
		if(not cursor.execute("SELECT album_id FROM Albums WHERE user_id = '{0}' AND Name = '{1}'".format(uid, albumName))):
			cursor.execute('''INSERT INTO Albums (user_id, Name) VALUES (%s, %s)''', (uid, albumName))

		album_id = getAlbumIdFromName(uid, albumName)
		#insert into pictures with the album id, NOT the album name.
		#a get album id from album name function would be necessary. 
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, album_id))
		pid = getLastInsertedPhotoId()
		#if hashtags are not empty, split them by spaces as a delimiter.
		if hashTags != "":
			hashTags = hashTags.split()
			for tag in hashTags:
				#for every hashtag, check if it exists in the database, if not, add it
				if(not cursor.execute("SELECT tag_id FROM Tags WHERE name = '{0}'".format(tag))):
					cursor.execute('''INSERT INTO Tags (name) VALUES (%s)''', (tag))
				#insert the photo and its tag into the tagged relationship
				cursor.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''', (pid, getTagIdFromName(tag)))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
	

def getAlbumIdFromName(uid, albumName):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Albums WHERE user_id = '{0}' AND Name = '{1}'".format(uid, albumName))
	return cursor.fetchone()[0]

def getLastInsertedPhotoId():
	cursor = conn.cursor()
	cursor.execute("SELECT LAST_INSERT_ID()")
	return cursor.fetchone()[0]
def getTagIdFromName(name):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE name = '{0}'".format(name))
	return cursor.fetchone()[0]
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')




#addon feature pages

#friends
@app.route("/friends", methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	
	try:
		friendEmail=request.form.get('friendEmail')
	except:
		#fix all except statements to redirect to appropriate error pages later.
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	if request.method == 'POST':

		uid1 = getUserIdFromEmail(flask_login.current_user.id)
		uid2 = getUserIdFromEmail(friendEmail)
		if isAbleToFriend(uid1, uid2):
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Friendship (UID1, UID2) VALUES ('{0}', '{1}')".format(uid1, uid2))
			conn.commit()
	friends = getUserFriends(getUserIdFromEmail(flask_login.current_user.id))
	return render_template('friends.html', friends=friends)



def isAbleToFriend(uid1, uid2):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT uid1 FROM Friendship WHERE uid1 = '{0}' AND uid2 = '{1}'".format(uid1, uid2)):
		#this means you are already friends with this user. 
		return False
	elif (uid1 == uid2):
		#you cannot friend yourself!
		return False
	else:
		return True
	
def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT uid2, email FROM Friendship, Users WHERE uid1 = '{0}' AND uid2 = user_id".format(uid))
	return cursor.fetchall() 

def getEmailFromUserId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]
#pictures
@app.route("/pictures", methods=['GET', 'POST'])
def pictures():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('pictures.html', photos=getUsersPhotos(uid), base64=base64)


@app.route("/allpictures", methods=['GET', 'POST'])
def allpictures():
	return render_template('allpictures.html', photos=getAllPhotos(), base64=base64)

#albums
@app.route("/albums", methods=['GET', 'POST'])
def albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('albums.html', albums=getUsersAlbums(uid))

@app.route("/allalbums", methods=['GET', 'POST'])
def allalbums():
	return render_template('allalbums.html', albums=getAllAlbums())

@app.route("/viewalbums/<album_id>", methods=['GET', 'POST'])
def viewalbums(album_id):
	return render_template('viewalbums.html', photos=getPhotosFromAlbum(album_id), base64=base64)

def getPhotosFromAlbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall()

def getAllAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, Name FROM Albums")
	return cursor.fetchall() 

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, Name FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() 


#hashtags
@app.route("/hashtags", methods=['GET', 'POST'])
def hashtags():
	if request.method == 'POST':
		#convert list of tag names to a list of tag ids
		tagname = request.form.get('tagsearch')
		tagname = tagname.split()
		tagid = []
		for tag in tagname:
			tagid.append(getTagIdFromName(tag))
		allphotos = {}
		for id in tagid:
			allphotos[id] = getPhotosFromHashtag(id)
		candidates = set(picture_id for imgdata, picture_id, caption in allphotos[tagid[0]])
		for tag in tagid[1:]:
			pics = set(picture_id for imgdata, picture_id, caption in allphotos[tag])
			candidates = candidates.intersection(pics)

		photos = []
		for imgdata, picture_id, caption in allphotos[tagid[0]]:
			if picture_id in candidates:
				photos.append((imgdata, picture_id, caption))


		return render_template('viewtag.html', photos=photos, base64=base64, hashtags=getHashtags(), top3 = getTop3Hashtags())
	return render_template('hashtags.html', hashtags=getHashtags(), top3 = getTop3Hashtags())


def getTop3Hashtags():
	cursor = conn.cursor()
	cursor.execute("SELECT Tags.tag_id, Tags.name FROM Tagged, Tags WHERE Tags.tag_id = Tagged.tag_id GROUP BY tag_id ORDER BY COUNT(Tagged.tag_id) DESC LIMIT 3")
	return cursor.fetchall() 


@app.route("/myhashtags", methods=['GET', 'POST'])
def myhashtags():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		tagname = request.form.get('tagsearch')
		tagname = tagname.split()
		tagid = []
		for tag in tagname:
			tagid.append(getTagIdFromName(tag))
		allphotos = {}
		for id in tagid:
			allphotos[id] = getUserPhotosFromHashtag(id)
		candidates = set(picture_id for imgdata, picture_id, caption in allphotos[tagid[0]])
		for tag in tagid[1:]:
			pics = set(picture_id for imgdata, picture_id, caption in allphotos[tag])
			candidates = candidates.intersection(pics)

		photos = []
		for imgdata, picture_id, caption in allphotos[tagid[0]]:
			if picture_id in candidates:
				photos.append((imgdata, picture_id, caption))
		return render_template('viewtag.html', photos=photos, base64=base64, hashtags=getHashtags())
	return render_template('myhashtags.html', hashtags=getUsersHashtags(uid))

def getUsersHashtags(uid):
	cursor = conn.cursor()
	#get hashtags used in user's photos 
	cursor.execute("SELECT Tags.tag_id, Tags.name FROM Tagged, Tags WHERE Tags.tag_id = Tagged.tag_id AND Tagged.photo_id IN (SELECT picture_id FROM Pictures WHERE user_id = '{0}')".format(uid))
	return cursor.fetchall()
def getUserPhotosFromHashtag(uid, tagid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Tagged, Pictures WHERE tag_id = '{0}' AND photo_id = picture_id AND user_id = '{1}'".format(tagid, uid))
	return cursor.fetchall()

#view all images under searched hashtag

	

def getPhotosFromHashtag(tagid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Tagged, Pictures WHERE tag_id = '{0}' AND photo_id = picture_id".format(tagid))
	return cursor.fetchall() 


#delete picture
@app.route("/deletepicture/<picture_id>", methods=['GET', 'POST'])
def deletepicture(picture_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pid = picture_id
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Tagged WHERE photo_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}' AND user_id = '{1}'".format(pid, uid))
	conn.commit()
	return render_template('pictures.html', photos=getUsersPhotos(uid), base64=base64)

#delete album
@app.route("/deletealbum/<album_id>", methods=['GET', 'POST'])
def deletealbum(album_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	aid = album_id
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Tagged WHERE photo_id IN (SELECT picture_id FROM Pictures WHERE album_id = '{0}')".format(aid))
	cursor.execute("DELETE FROM Pictures WHERE album_id = '{0}'".format(aid))
	cursor.execute("DELETE FROM Albums WHERE album_id = '{0}' AND user_id = '{1}'".format(aid, uid))
	conn.commit()
	return render_template('albums.html', albums=getUsersAlbums(uid))

def getHashtags():
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id, name FROM Tags")
	return cursor.fetchall() 

#like and comments

@app.route("/likepicture/<picture_id>", methods=['GET', 'POST'])
def likepicture(picture_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pid = picture_id
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}', '{1}')".format(uid, pid))
	conn.commit()
	return render_template('allpictures.html', photos=getAllPhotos(), base64=base64)

#return the number of likes on a picture
def countLikes(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchone()[0]

#picture details page

@app.route("/singlepicture/<picture_id>", methods=['GET', 'POST'])
def singlepicture(picture_id):
	if(not flask_login.current_user.is_authenticated):
		uid = -1
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	pid = picture_id
	likecount = countLikes(pid)
	if request.method == 'POST':
		text = request.form.get('comment')
		cursor = conn.cursor()
		#if the owner of the picture is yourself
		if not uid == getUserIdFromPhoto(pid):
			cursor.execute("INSERT INTO Comments (user_id, picture_id, text) VALUES ('{0}', '{1}', '{2}')".format(uid, pid, text))
		conn.commit()
		return render_template('singlepicture.html', photos=getSinglePhoto(pid), base64=base64, comments=getComments(pid), likecount = likecount)
	return render_template('singlepicture.html', photos=getSinglePhoto(pid), base64=base64, comments=getComments(pid), likecount = likecount)

def getUserIdFromPhoto(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchall()[0][0]

def getComments(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT Users.email, Comments.text FROM Comments, Users WHERE Comments.user_id = Users.user_id AND Comments.picture_id = '{0}'".format(pid))
	return cursor.fetchall()

def getSinglePhoto(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchall()

#recommendation functions

@app.route("/myrecommendations", methods=['GET', 'POST'])
def myrecommendations():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends = getTop3Friends(uid)
	#convert user ids from getTop3Friends to emails
	rec = []
	for friend in friends:
		rec.append(getEmailFromUserId(friend[0]))
	#convert photo ids from getRecommendedPhotos to image data needed to display the photos
	pids = getRecommendedPhotos(uid)
	photos = []
	for photo in photos:
		photos.append(getSinglePhoto(pids[0]))

	
	return render_template('myrecommendations.html', friends=rec, photos=photos, base64=base64)


#find the top 3 friends that are most often the friends of friends
def getTop3Friends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT f2.UID2 FROM Friendship AS f1, Friendship AS f2 WHERE f1.UID1 = '{0}' AND f2.UID1 = f1.UID2 AND f2.UID2 NOT IN (SELECT uid2 FROM Friendship WHERE uid1 = '{0}') AND f2.UID2 <> '{0}' GROUP BY f2.UID2 ORDER BY COUNT(*) DESC LIMIT 10".format(uid))
	
	# dict = {} #dictionary with user id as the key, and number of times friended by friends of the currently logged in user as the value
	# #for every friend in the current user's friends
	# for friend in getAllFriends(uid):	
	# 	#for every friend of the friend of the current user we are iterating on
	# 	for friendoffriend in getAllFriends(friend):
	# 		if friendoffriend in dict:
	# 			dict[friendoffriend] += 1
	# 		else:
	# 			#this friend of a friend hasnt been added to dict yet
	# 			dict[friendoffriend] = 1
	# print(dict)
	# rank = []
	# for k,v in dict.items():
	# 	#if a higher ranked friend than the current top rank and isnt already a friend
	# 	if v > dict[rank[0]] and not isAlreadyFriend(k):
	# 		rank.push(k)
	# rankedemails = []
	# for i in range (len(rank)):
	# 	rankedemails[i] = getEmailFromUserId(rank[i])
		
	# #print(rankedemails)
	# return rankedemails
	
	return cursor.fetchall()



def getRecommendedPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT Tags.tag_id FROM Tagged, Tags WHERE Tags.tag_id = Tagged.tag_id AND Tagged.photo_id IN (SELECT picture_id FROM Pictures WHERE user_id = '{0}') GROUP BY tag_id ORDER BY COUNT(*) DESC LIMIT 3".format(uid))
	tags = cursor.fetchall()
	
	pids = []
	for tag in tags:
		cursor.execute("SELECT photo_id FROM Tagged WHERE tag_id = '{0}' GROUP BY photo_id".format(tag))
		pids.append(cursor.fetchall())

	return pids

	

def getAllFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT UID2 FROM Friendship WHERE UID1 = '{0}'".format(uid))
	return cursor.fetchall()

def isAlreadyFriend(uid):
	if uid in getAllFriends(uid):
		return True
	else:
		return False
	

#activity rankings
@app.route("/activityrank", methods=['GET', 'POST'])
#rank the users and display the top 10 emails by their activity
def activityrank():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, COUNT(*) AS activity FROM Pictures GROUP BY user_id UNION SELECT user_id, COUNT(*) AS activity FROM Comments GROUP BY user_id ORDER BY activity DESC LIMIT 10")
	ids = cursor.fetchall()
	emails = []
	for id in ids:
		emails.append(getEmailFromUserId(id[0]))
	return render_template('activityrank.html', users=emails)


		
#comment search
@app.route("/commentsearch", methods=['GET', 'POST'])
#returns the user emails of all comments that exactly match the search query
def commentsearch():
	if request.method == 'POST':
		comment = request.form.get('comment')
		cursor = conn.cursor()
		cursor.execute("SELECT user_id,COUNT(*) AS ccount FROM Comments WHERE text='{0}' GROUP BY user_id ORDER BY ccount DESC LIMIT 10".format(comment))
		ids = cursor.fetchall()
		emails = []
		for id in ids:
			emails.append(getEmailFromUserId(id[0]))
		return render_template('commentsearch.html', users=emails)
	return render_template('commentsearch.html')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

#comments

