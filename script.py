#!/usr/bin/env python3

# Import stuff
from bs4 import BeautifulSoup
import requests
import smtplib
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
import datetime

# Set the email accounts from which to send and receive the notification email
YOUR_GOOGLE_EMAIL = 'srb.donotreply@gmail.com'  
YOUR_GOOGLE_EMAIL_APP_PASSWORD = 'lbmwjaihlymvkuhq'  
YOUR_RECIPIENT_EMAIL = 'emailshivank@gmail.com'


# Pick which courses, professors, and sections you want to monitor by following the format
# "Course Name": {"Professor Name" : ("Section Number(s)")}
courses_and_profs_plus_sections = {
    "CMSC351": {"Justin Wyss-Gallifent" : ("0101"), "Herve Franceschi" : ("0401"), "Clyde Kruskal" : ("0301")},
}

# The main function which will run every time the schedule of classes is updated
def script_main():
       
    
    # Loop through all the courses
    for course_name in courses_and_profs_plus_sections.keys():
        
        # Go the the website and make a request
        temp_site_url = "https://app.testudo.umd.edu/soc/search?courseId="+course_name+"&sectionId=&termId=202408&_openSectionsOnly=on&creditCompare=&credits=&courseLevelFilter=ALL&instructor=&_facetoface=on&_blended=on&_online=on&courseStartCompare=&courseStartHour=&courseStartMin=&courseStartAM=&courseEndHour=&courseEndMin=&courseEndAM=&teachingCenter=ALL&_classDay1=on&_classDay2=on&_classDay3=on&_classDay4=on&_classDay5=on"
        r = requests.get(temp_site_url)

        # Parse the HTML and find all of the professors and sections
        temp_soup = BeautifulSoup(r.content, 'html.parser')
        all_profs_on_testudo = temp_soup.find_all('div', attrs = {'class': 'section-info-container'})

        for row in all_profs_on_testudo:
            
            # Get the professor and section from testudo
            prof = row.find('span', attrs = {'class': 'section-instructor'})
            section = row.find('span', attrs = {'class': 'section-id'}).text
            section = section.encode('ascii', errors='ignore')
            section = str(section)
            section = str( ''.join(filter(str.isdigit, section) ) )
            
            # If the one on testudo matches something we are looking for, and the number of seats is 
            # greater than 0, send an email
            if str(prof.text) in courses_and_profs_plus_sections[course_name].keys() and section in courses_and_profs_plus_sections[course_name][str(prof.text)]:
                print(prof.text)
                print(section)
                open_seats = row.find('span', attrs = {'class': 'open-seats-count'})
                if int(open_seats.text) > 0:
                    
                    smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    smtpserver.ehlo()
                    smtpserver.login(YOUR_GOOGLE_EMAIL, YOUR_GOOGLE_EMAIL_APP_PASSWORD)                
                    sent_from = YOUR_GOOGLE_EMAIL
                    sent_to = YOUR_RECIPIENT_EMAIL  
                    email_text = str(prof.text) + " has " + str(open_seats.text) + " open seats in " + course_name + " in section " + section
                    smtpserver.sendmail(sent_from, sent_to, email_text)
                    smtpserver.close()                


# Create and run the scheduler to run the function every time testudo updates


print("The script is running")


sched = BlockingScheduler()
trigger = OrTrigger([CronTrigger(minute = '30-31', hour='7-23', start_date='2024-05-23', end_date='2026-05-23', day_of_week='mon-sat'),
                    CronTrigger(minute ='30-31', hour = '17-23', start_date='2024-05-23', end_date='2026-05-23', day_of_week='sun')])
sched.add_job(script_main, trigger)

print("The scheduler has added the job")
sched.start()










# Code used to figure out what HTML elements needed to be extracted
# CMSC351_profs = ["Justin Wyss-Gallifent", "Herve Franceschi"]

# soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib 

# clean = soup.prettify()

# file1 = open('myfile.txt', 'w')

# file1.write(clean)

# file1.close()

# table = soup.find_all('div', attrs = {'class': 'section-info-container'})

# file1 = open('clean_table.txt', 'w')

# for row in table:
#     file1.write(row.prettify())

# file1.close()

# file1 = open('results.txt', 'w')

# for row in table:
#     prof = row.find('span', attrs = {'class': 'section-instructor'})
#     if str(prof.text) in CMSC351_profs:
#         open_seats = row.find('span', attrs = {'class': 'open-seats-count'})
#         file1.write(prof.text + " " + open_seats.text + "\n")

# file1.close()



