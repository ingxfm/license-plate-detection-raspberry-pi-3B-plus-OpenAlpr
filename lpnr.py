#Python Standard libraries
from datetime import datetime as dt
from urllib.request import urlopen
import json
import logging
import subprocess
import time as t

#3rd-party libraries
#from gpiozero import MotionSensor
import cv2
import mysql.connector
import numpy as np

#Local libraries/application
#None


def detect_license_plate():
    '''
    This function includes the detection of the license plate. Credits to `OpenAlpr <https://github.com/openalpr/openalpr>`_.
    The return values are 3 strings: plate, confidence and date. These 3 strings are saved in the MySQL database 'plates',
    in host='localhost', port='3306'.       
    '''    
    t.sleep(0.1)
    
    #subprocess module calls a linux terminal command and gets and output (see references 6, 7)
    process = subprocess.run(['alpr', '-c eu', '-p cz', '-n 3','-j',\
                              '/path/to/repository/to_detect_from.jpg'],\
                             stdout=subprocess.PIPE, text=True)
    #print(process.stdout,file=output_to_database)
    current_date = dt.now()   
    #takes output of subprocess and saves it
    diccionario = process.stdout
    #transforms subprocess output into json format (see reference 8)
    diccionario = json.loads(diccionario)
    #get result of the 'results' key
    #if empty, no plates detected        
    if diccionario['results']==[]:
        print('No plates detected')
    #if populated, print plate number and detection confidence
    elif diccionario['results']!=[]:
        #-----------------------------------------------------------------
        #for debugging purposes            
        print(diccionario['results'][0]['plate'])
        print(diccionario['results'][0]['confidence'])
        print(current_date)
        #-----------------------------------------------------------------
        plate = diccionario['results'][0]['plate']
        confidence = diccionario['results'][0]['confidence']
        #insert info into database
        connect_to_database = mysql.connector.connect(user='root', password='pi',
                                                      database='plates', host='localhost', port='3306')
        #-----------------------------------------------------------------
        #for debugging purposes
        #print(connect_to_database)
        #-----------------------------------------------------------------
        cursor = connect_to_database.cursor()
        #-----------------------------------------------------------------
        #for debugging purposes 
        #print(cursor)            
        #print(number)
        #-----------------------------------------------------------------
        #the format of the data for inserting it to database
        add_plate_info = ("INSERT INTO license_plates_detected "
          "(Plates, Confidence, Date) "
          "VALUES (%(Plates)s, %(Confidence)s, %(Date)s)")
        #-----------------------------------------------------------------
        #for debugging purposes
        #print(add_plate_info)
        #-----------------------------------------------------------------
        #the data to be inserted to database
        data_plate_info = {
            'Plates': plate,
            'Confidence': confidence,
            'Date': current_date,
            }
        #-----------------------------------------------------------------
        #for debugging purposes
        #print(data_plate_info)
        #-----------------------------------------------------------------
        #Insert the data
        cursor.execute(add_plate_info, data_plate_info)
        #Commit the insertion
        connect_to_database.commit()
        #Close cursor
        cursor.close()
        #close database
        connect_to_database.close() 

        
def get_stream_from_localhost():
    '''
    This function connects to the video stream and fetch the bytes from that stream. The return
    value is a list with the Start Of Image (SOI) byte, the End Of Image (EOI) byte and the range of
    bytes between the SOI and EOI. The stream is generated by the software
    `Motion-project <https://motion-project.github.io/>`_.    
    '''
    stream = urlopen('http://localhost:8081/', data=None)
    bytess = b''
    LOOPING = 1
    while LOOPING:
        bytess += stream.read(1024)
        a = bytess.find(b'\xff\xd8')
        b = bytess.find(b'\xff\xd9')
        #print('This is a:', a, ' and this is b:', b)
        if a != -1 and b != -1:            
            break
    list_values = [a, b, bytess]
    return list_values


def print_stream_variables(passed_list):
    '''
    This function functions takes the passed list from the function get_stream_from_localhost().
    It uses this list to create and image. The image then is used by the detect_license_plate()
    function to search for a license plate number.    
    '''   
    #print('Segunda impresion','This is a:', passed_list[0], 'and this is b:', passed_list[1])
    a1 = passed_list[0] #local variable to this function
    b1 = passed_list[1] #local variable to this function
    byte_list = passed_list[2] #local variable to this function
    jpg = byte_list[a1:b1+2] #local variable to this function    
    i = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    cv2.imwrite('to_detect_from.jpg', i)
    return i
#    cv2.imshow('i', i)
#    if cv2.waitKey(1)==27:
#        exit(0)


def main():
    '''
    This is the main function. It measures the script execution time, as well
    as calling the other functions for the end goal which is detecting whether
    or not there is a license plate and saving the license plate number as  a string,
    in a database in case there is one.
    '''
    start_time = t.time()
    start_time_total = t.time()
    returned_list = get_stream_from_localhost()    
    print_stream_variables(returned_list)
    stop_time = t.time()
    dtt = stop_time - start_time
    print('The time to get the image from the stream is', dtt)
    #returned_imaged = print_stream_variables()
    start_time = t.time()
    detect_license_plate()
    stop_time = t.time()
    dtt = stop_time - start_time
    print('The detection time is', dtt)
    stop_time_total = t.time()
    dtt_total = stop_time_total - start_time_total
    print('The total script time is', dtt_total)
    

#live streaming from Motion, framerate 2 FPS
#------------------------------------------------------------------------
try:
    t.sleep(0.1)
    if __name__ == '__main__':
        main()
        
except ConnectionError:
    logging.basicConfig(filename='error_log.log', level = logging.DEBUG)
    exception_date = dt.now()
    logging.debug(
        '\nConnectionError\n'
        '1.Unable to get live feed. Verify the Motion project feed and connection.\n'
        '2.Try entering "sudo service motion start" in the terminal.\n'
        '3.In the terminal enter "sudo nano /etc/motion/motion.conf", for the configuration file.\n'
        '4.For local host video feed aim to: "http://localhost:8081/".\n'
        + str(exception_date) + '\n')
    t.sleep(0.5)
    
except OSError:    
    logging.basicConfig(filename='error_log.log', level = logging.DEBUG)
    exception_date = dt.now()
    logging.debug(
        '\nOSError:\n'
        '1.Unable to get live feed. Verify the Motion project feed and connection.\n'
        '2.Try entering "sudo service motion start" in the terminal.\n'
        '3.In the terminal enter "sudo nano /etc/motion/motion.conf", for the configuration file.\n'
        '4.For local host video feed aim to: "http://localhost:8081/".\n'
        '5.Verify OpenAlpr detection function and/or service in terminal.\n'
        + str(exception_date) + '\n')
    t.sleep(0.5)
                
#------------------------------------------------------------------------
    
            
           
#References:
#1.https://dev.mysql.com/doc/connector-python/en/connector-python-example-cursor-transaction.html
#2.https://picamera.readthedocs.io/en/release-1.13/recipes2.html
#3.http://doc.openalpr.com/accuracy_improvements.html
#4.https://www.pyimagesearch.com/2018/09/17/opencv-ocr-and-text-recognition-with-tesseract/
#5.https://gpiozero.readthedocs.io/_/downloads/en/stable/pdf/
#6.https://docs.python.org/3/library/subprocess.html
#7.https://www.youtube.com/watch?v=2Fp1N6dof0Y
#8.https://docs.python.org/3/library/json.html
#9.https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html
#10.https://github.com/openalpr/openalpr/wiki/OpenALPR-Design
#11.https://www.reddit.com/r/raspberry_pi/comments/baxwz5/how_to_install_openalpr_on_raspberry_pi/
