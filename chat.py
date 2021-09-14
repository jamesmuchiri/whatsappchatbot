import nltk
from nltk.stem. lancaster import LancasterStemmer
stemmer = LancasterStemmer()
import re
import numpy
import tflearn
import tensorflow
import random
import json
import os
import pandas as pd
import pickle

with open("intents.json",encoding="utf8") as file:
    data = json.load(file)

words = []
labels = []
docs_x = []
docs_y = []
  
for intents in data["intents"]:
    for pattern in intents["patterns"]:
        wrds = nltk.word_tokenize(pattern)
        words.extend(wrds)
        docs_x.append(wrds)
        docs_y.append(intents["tag"])

    if intents["tag"] not in labels:
        labels.append(intents["tag"])

words = [stemmer.stem(w.lower()) for w in words if w !="?"]
words = sorted(list(set(words)))

labels = sorted(labels)

train = []
output = []

out_empty = [0 for _ in range(len(labels))]

for x, doc in enumerate(docs_x):
    bag = []

    wrds = [stemmer.stem(w) for w in doc]
    for w in words:
        if w in wrds:
            bag.append(1)
        else:
            bag.append(0)
    output_row =  out_empty[:]
    output_row[labels.index(docs_y[x])]=1
        
    train.append(bag)
    output.append(output_row)

train = numpy.array(train)
output = numpy.array(output)


net = tflearn.input_data(shape=[None,len(train[0])])
net = tflearn.fully_connected(net,8)
net = tflearn.fully_connected(net,8)
net = tflearn.fully_connected(net, len(output[0]),activation ="softmax")
net = tflearn.regression(net)

model = tflearn.DNN(net)



model.fit(train,output, n_epoch=500, batch_size = 8, show_metric = True)
model.save("model.tflearn")

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(words.lower()) for words in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return numpy.array(bag) 




from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
from googleapiclient import discovery
from datetime import datetime
from dateutil.parser import parse
#from googleapiclient import error
import maya
from maya import MayaInterval
import mysql.connector


db = mysql.connector.connect(
    
    host = "localhost",
    user = "root",
    passwd = "matenzawa",
    database = "Healthcare_bot",
    autocommit = True
)


#mycursor.execute("CREATE DATABASE Healthcare_bot")
#mycursor.execute("CRAETE TABLE Appointments(first_name VARCHAR(50),last_name VARCHAR(50), personID int PRIMARY KEY AUTO_INCREMENT)")


app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome to the whatsapp chatbot for businesses"

@app.route("/bot", methods=["GET","POST"])


def reply_whatsapp():

    global responded_E
    global responded_F
    global responded_D
    global responded_T
    global responded_C
    global responded_A 
    global responded_I

    others = ("others","other")
    greetings = ("hi","hey","hello","start")
    confirm_app = ("y","of cours","for sure","sure")
    appointmnet = ("dental","asthma","allergies","cancer","surgery","diabetes","arthritis")
    
    msg = request.form.get('Body','').lower() 
    response = MessagingResponse()
    resp = response.message()

    
    results = model.predict([bag_of_words(msg,words)])[0]
    results_index =numpy.argmax(results)
    tag = labels[results_index]
    if results[results_index] > 0.7:
        for tg in data["intents"]:
            if tg["tag"] == tag:
                responses = tg["responses"]
                resp.body(random.choice(responses))


    elif msg.lower() in greetings:
        now = maya.MayaDT.from_datetime(datetime.utcnow())
        Time_zone = now.hour +3

        if 5<= Time_zone <12 :
            Good_Morning="Good Morning"
            reply_greetings =("{}🌅 \nWelcome to *Nav Healthcare Services*"
                            "\nWe can help you in getting right home healthcare service provided as per your needs"
                            "\n\nWhat can I do for you today? Feel free to ask me anything related to *Healthcare*"
            ).format(Good_Morning)
            resp.body(reply_greetings)
            resp.media('https://i.ibb.co/vw33c6C/Navv.png')
            
        elif  12 <= Time_zone < 17 :
            Good_Afternoon="Good Afternoon"
            reply_greetings =("{}🌄 \nWelcome to *Nav Healthcare Services*"
                            "\nWe can help you in getting right home healthcare service provided as per your needs"
                            "\n\nWhat can I do for you today? Feel free to ask me anything related to *Healthcare*"
            ).format(Good_Afternoon)
            resp.body(reply_greetings)
            resp.media('https://i.ibb.co/vw33c6C/Navv.png')
            
        else:
            Good_Evening="Good Evening"
            reply_greetings =("{}🌆 \nWelcome to *Nav Healthcare Services*"
                            "\nWe can help you in getting right home healthcare service provided as per your needs"
                            "\n\nWhat can I do for you today? Feel free to ask me anything related to *Healthcare*"
            ).format(Good_Evening)
            resp.body(reply_greetings)
            resp.media('https://i.ibb.co/vw33c6C/Navv.png')
        
        responded_E = False
        responded_F = False
        responded_D = False
        responded_T = False
        responded_C = False
        responded_A = False
        responded_I = False

        

    elif msg.lower() in confirm_app or  msg.lower() in others:
        r1=("Okay let's get you started. I just need you to answer a few questions."
        )
        resp.body(r1)
        response.message("First, What is the appointment about?")  
        responded_I = True
    
    elif responded_I == True or msg.lower() in appointmnet:
        illness = request.form['Body']

        global get_illness
        get_illness = illness
        
        r1 = ("Whats your *Email address*, just to check for any corresponding appointments")
        resp.body(r1)
        
        responded_E = True
        responded_I = False
       
    elif responded_E == True:
        email = request.form['Body']
        if email.endswith('@gmail.com') or email.endswith('@outlook.com'):

            global get_email
            get_email = email

            mycursor = db.cursor()
            mycursor.execute('''SELECT Email FROM Appointments WHERE Email = (%s)''', (get_email,))
            checkEmail = mycursor.fetchall()

            if (get_email,) in checkEmail:
                email_exist = ("\nSorry,😕 The *email* you are trying to use has an *appointment*")
                resp.body (email_exist)
                response.message("\nKindly use another one. Thanks")

            else:
                
                user_phone_number = request.values['From']
                if user_phone_number.startswith('whatsapp'):
                    global number
                    number = user_phone_number.split(':')[1]

                first_name = ("\nWhats your *full name*")
                resp.body (first_name)
                
                responded_E = False
                responded_F = True

        else:
            reply_VE=("Please give a valid Email address "
                "\n_*Example: matenzawa@gmail.com*_")
            resp.body(reply_VE)
            
    elif responded_F == True:

        global f_name
        f_name = request.form['Body']

        if not re.match("^[A-z][A-z|\.|\s]+$",f_name):
            reply_v = ("Please give a vallid name _*Example james muchiri*_")
            resp.body (reply_v)
        elif len(f_name) <10:
            reply_v = ("Kindly give your full name!!")
            resp.body (reply_v)
        else:
            age_get =("What is the *age* of the patient?")
            resp.body(age_get)

            responded_F = False
            responded_A = True


    elif responded_A == True:
        global age
        age = request.form['Body']

        try:
            val = int(age)
            if val > 150 :
                reply_v = ("The number is too large to be a vallid age.")
                resp.body (reply_v)
            else:
                date_get =("Thanks")
                resp.body(date_get)
                response.message("Please tell me the *date* you want to come in."
                        "\n_*Example: 24 jan, 2021*_")
                responded_A = False
                responded_D = True
        except ValueError:
            reply_v = ("Please give a vallid age. I only accept numbers.")
            resp.body (reply_v)

    
            
    elif responded_D == True:
        date = request.form['Body']
        tomorrow = maya.when(date)
        now = maya.now()
        print(tomorrow)

        if tomorrow < now:
            reply = ("Kindly give a valid date.It should be a greater than today.")
            resp.body(reply)

        else:
            global date_V
            date_V = tomorrow.date

            reply = ("At what *time?*")
            resp.body(reply)

            responded_D = False
            responded_T = True

    elif responded_T == True:
        time = request.form['Body']
        t = maya.when(time)
        if t.hour > 18 or t.hour < 8:
            reply=("Appointmrnts are only between 8AM ad 6PM")
            resp.body(reply)
        else:
            global time_h
            global time_m

            time_h = t.hour
            time_m = t.minute

            reply =("All right, we are set!"
                    "\n\nHey *{}*,"
                    "\nShould i schedule for you the following appointment?\n"
                    "\n *Name:*  {}"
                    "\n *Date:*   {}"
                    "\n *Time:*   {}:{}0 hrs"
                    "\n *For:*     {}"
                    "\n *Age:*     {}").format(f_name,f_name,date_V,time_h,time_m,get_illness,age)
            
            resp.body(reply)

            responded_T= False
            responded_C =True

          
           
    elif responded_C == True:
        confirm = request.form.get('Body','')

        c = ("yes","confirm","y")
        disagree = ("no","n","false")
        
        if confirm.lower() in c:

            mycursor = db.cursor()
            mycursor.execute('''INSERT INTO Appointments (Email) VALUES (%s)''', (get_email,))
            db.rollback()

            mycursor = db.cursor()
            mycursor.execute('''UPDATE Appointments SET Number= (%s),Illness = (%s),Name= (%s) WHERE Email = (%s)''', (number,get_illness,f_name,get_email))
            mycursor.execute('''UPDATE Appointments SET Age=(%s), Date= (%s),Time = (%s) WHERE Email = (%s)''', (age,date_V,time_h,get_email))
            db.commit()

            reply=("Your appointment on {} at {}:{}0 hrs has been scheduled successfully").format(date_V,time_h,time_m)
            resp.body(reply)

            responded_C = False

        elif confirm.lower() in disagree:
            reply = ("No appointment was booked"
                    "\nThanks for the time 🤗🤗")
            resp.body(reply)
            responded_C = False

        else:
            reply = ("You can reply with *yes* to confirm or *no* to disagree")
            resp.body(reply)
    

            


    elif 'see' in msg.lower():   

        mycursor = db.cursor()
        mycursor.execute('''SELECT Name FROM Appointments WHERE Email = (%s)''', (get_email,))
        records = mycursor.fetchall()
        for record in records:
            print(record)



    else:
        reply = ("Take it easy on me, i am still learning."
                    "\nMosty ask questions related to *Healthcare* and i will give you an appropriate answer. Thanks")
        resp.body(reply)
        resp.media('https://i.ibb.co/hs5YLXc/nn.png')

    return str(response)  

    


    #mycursor.execute('''UPDATE Appointments_booking SET first_name = %s, last_name=%s WHERE email = %s''', (get_fname,get_lname,get_email))

if __name__ == "__main__":

    model.load("model.tflearn")



app.run()





