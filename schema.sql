CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;

DROP TABLE IF EXISTS Friendship CASCADE;
DROP TABLE IF EXISTS Tagged CASCADE;

DROP TABLE IF EXISTS Likes CASCADE;

DROP TABLE IF EXISTS Comments CASCADE;

DROP TABLE IF EXISTS Pictures CASCADE;

DROP TABLE IF EXISTS Albums CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Tags CASCADE;


CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    gender VARCHAR(6),
    email varchar(255) UNIQUE,
    password varchar(255),
    dob DATE NOT NULL,
    hometown VARCHAR(40),
    fname VARCHAR(40) NOT NULL,
    lname VARCHAR(40) NOT NULL,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);
CREATE TABLE Albums(
album_id INT auto_increment,
Name VARCHAR(40) NOT NULL,
date_of_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
user_id INT NOT NULL,
PRIMARY KEY (album_id), 
FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE 
);

CREATE TABLE Pictures(
picture_id INT AUTO_INCREMENT,
user_id INT, 
caption VARCHAR(200),
imgdata LONGBLOB,
album_id INT NOT NULL,
PRIMARY KEY (picture_id),
FOREIGN KEY (user_id) REFERENCES USERS (user_id),
FOREIGN KEY (album_id) REFERENCES ALBUMS(album_id) ON DELETE CASCADE
);
 
CREATE TABLE Comments(
comment_id INT NOT NULL AUTO_INCREMENT, 
text TEXT NOT NULL,
date DATETIME DEFAULT CURRENT_TIMESTAMP,
user_id INT NOT NULL,
picture_id INT NOT NULL, 
PRIMARY KEY (comment_id),
FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);

CREATE TABLE Likes(
user_id INT NOT NULL,
picture_id INT NOT NULL, 
PRIMARY KEY (picture_id, user_id),
FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);

CREATE TABLE Tags(
	tag_id INTEGER AUTO_INCREMENT,
    name VARCHAR(100), 
    PRIMARY KEY (tag_id)
);

CREATE TABLE Tagged(
	photo_id 	INTEGER,
    tag_id		INTEGER,
	PRIMARY KEY (photo_id, tag_id),
    FOREIGN KEY (photo_id)
		REFERENCES Pictures (picture_id),
	FOREIGN KEY (tag_id)
		REFERENCES Tags (tag_id)
);

CREATE TABLE Friendship(
UID1 INT NOT NULL, 
UID2 INT NOT NULL, 
CHECK (UID1 <> UID2),
PRIMARY KEY (UID1, UID2),
FOREIGN KEY (UID1) REFERENCES Users (user_id) ON DELETE CASCADE,
FOREIGN KEY (UID2) REFERENCES USERS (user_id) ON DELETE CASCADE
);

-- CREATE ASSERTION Comment-Constraint CHECK
-- 	(NOT EXISTS (SELECT * FROM Comments C, Pictures P
-- 			WHERE C.picture_id = P.picture_id AND P.user_id = C.user_id));

-- INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
-- INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
-- INSERT INTO Users (email, password, dob, fname, lname) VALUES ('test1@bu.edu', 'test', '2003-03-28', 'ftester', 'ltester');