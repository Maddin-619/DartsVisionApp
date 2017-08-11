# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import time, threading
import cv2
import multiprocessing
import pika
from multiprocessing import Process, Queue, current_process, freeze_support
import RPi.GPIO as GPIO


class CustomTimer(threading.Timer):
    def __init__(self, interval, function, args=[], kwargs={}):
        self._original_function = function
        super(CustomTimer, self).__init__(
            interval, self._do_execute, args, kwargs)

    def _do_execute(self, *a, **kw):
        self.result = self._original_function(*a, **kw)

    def join(self):
        super(CustomTimer, self).join()
        return self.result

class Field:

    def __init__(self, contour, x, y):
        self.contour = contour
        self.x = x
        self.y = y

class Dart:

    def __init__(self, contour = None, x = 0, y = 0, detectTime = 0):
        self.contour = contour
        self.x = ((x*2592)//640)
        self.y = ((y*1952)//480)
        self.detectTime = detectTime

class DartVision:
    
    def __init__(self):
        self.camera = PiCamera()
        self.imageDartBoard = None
        self.fieldContours = None
        self.imageDebug = None
        self.amqpConnection = None
        self.amqpChannel = None
        self.commandQueue = Queue()

    def init(self):
        self.light(True)
        self.takePicture(1)
        self.getField()
        self.connect('martin-desktop')

    def run(self):
        # Fork Process which listens to the commands form the Node.js UI
        Process(target=self.commandListener, args=(self.commandQueue, self.amqpChannel)).start()

        # Execute commands
        for command in iter(self.commandQueue.get, 'STOP'):
            if command == 'light_on':
                self.light(True)
            elif command == 'light_off':
                self.light(False)
            elif command == 'game_on':
                self.detectDarts()
        

    def light(switch):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(8, GPIO.OUT)
        GPIO.output(8, not switch)

    def takePicture(sleeptime):
        
        self.camera.resolution = (2592,1952)
        rawCapture = PiRGBArray(camera)

        # allow the camera to warmup
        time.sleep(sleeptime)

        # grab an image from the camera
        camera.capture(rawCapture, format="bgr")
        self.imageDartBoard = rawCapture.array

    def getField():
        if(self.imageDartBoard == None): return
        # Convert BGR to HSV
        hsv = cv2.cvtColor(self.imageDartBoard, cv2.COLOR_BGR2HSV)

        # define range of blue color in HSV
        lower_green = np.array([35,50,50])
        upper_green = np.array([100,255,255])
        
        lower_red1 = np.array([0,70,50])
        upper_red1 = np.array([45,255,255])
    
        lower_red2 = np.array([95,50,50])
        upper_red2 = np.array([180,255,255])

        lower_black = np.array([0,0,0])
        upper_black = np.array([180,255,50])

        # Kernal
        kernel = np.ones((3,3),np.uint8)
        kernel1 = np.ones((5,5),np.uint8)
        kernel2 = np.ones((7,7),np.uint8)
        kernel3 = np.ones((13,13),np.uint8)
        kernel4 = np.ones((15,15),np.uint8)

        # Threshold the HSV image to get only black colors
        black_mask = cv2.inRange(hsv, lower_black, upper_black)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel2, iterations = 1)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel2)
        cv2.imwrite('TestBlackMask.png', black_mask)

        # Find and draw black areas
        roi_mask = np.zeros((1952,2592),np.uint8)
        black_contours = []
        img, contours, hierarchy = cv2.findContours(black_mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
        i = 0;
        for cnt in contours:
            if (hierarchy.item(0,i,2) != -1) and (hierarchy.item(0,i,3) != -1) and (cv2.contourArea(cnt) > 700000):
                hull = cv2.convexHull(cnt)
                cv2.drawContours(roi_mask, [hull], 0, (255,255,255),cv2.FILLED)
            if (hierarchy.item(0, hierarchy.item(0,i,3),3) != -1) and (cv2.contourArea(contours[hierarchy.item(0,i,3)]) > 700000 and (cv2.contourArea(cnt) > 5000)):
                hull = cv2.convexHull(cnt)
                #cv2.drawContours(image, [hull], 0, (255,0,0),1)
                M = cv2.moments(hull)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                black_contours.append(Field(hull, cx, cy))
            i = i + 1
        cv2.imwrite('TestROIMask.png',roi_mask)

        # Threshold the HSV image to get only green colors
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_mask = cv2.bitwise_and(green_mask,roi_mask)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel2)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel2)
        cv2.imwrite('TestGreenMask.png',green_mask)

        # Threshold the HSV image to get only red colors
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        red_mask = cv2.bitwise_and(red_mask, roi_mask)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel3)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel2)
        cv2.imwrite('TestRedMask.png', red_mask)

        # Build the white space with die Contours from the other
        white_mask = cv2.bitwise_or(black_mask,green_mask)
        white_mask = cv2.bitwise_or(white_mask,red_mask)
        white_mask = cv2.bitwise_not(white_mask)
        white_mask = cv2.bitwise_and(white_mask,roi_mask)
        white_mask = cv2.erode(white_mask,kernel1,iterations = 3)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel2)
        cv2.imwrite('TestWhiteMask.png',white_mask)


        # Find and draw green areas
        green_contours = []
        img, contours, hierarchy = cv2.findContours(green_mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        i = 0;
        for cnt in contours:
            if (cv2.contourArea(cnt) > 200):
                hull = cv2.convexHull(cnt)
                #cv2.drawContours(image, [hull], 0, (0,255,0),1)
                if(hierarchy.item(0,i,3) != -1):
                    tempContour = hull
                elif(hierarchy.item(0,i,2) != -1):
                    tempindex = i
                    M = cv2.moments(hull)
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    green_contours.append(Field(hull, cx, cy))
                else:
                    M = cv2.moments(hull)
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    green_contours.append(Field(hull, cx, cy))
            i = i + 1
        green_contours[tempindex].innerContour = tempContour

        # Find and draw red areas
        red_contours = []
        img, contours, hierarchy = cv2.findContours(red_mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if (cv2.contourArea(cnt) > 200):
                hull = cv2.convexHull(cnt)
                #cv2.drawContours(image, [hull], 0, (0,0,255),1)
                M = cv2.moments(hull)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                red_contours.append(Field(hull, cx, cy))

        # Find and draw white areas
        white_contours = []
        img, contours, hierarchy = cv2.findContours(white_mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if (cv2.contourArea(cnt) > 6000):
                hull = cv2.convexHull(cnt)
                #cv2.drawContours(image, [hull], 0, (255,255,255),1)
                M = cv2.moments(hull)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                white_contours.append(Field(hull, cx, cy))

        if((len(white_contours)<20) or (len(black_contours)<20) or (len(red_contours)<21) or (len(green_contours)<21)): return

        # Calculate the Points of Field
        black_contours.sort(key = lambda Field: Field.x, reverse=False)
        black_contours[0].points = 20
        if(black_contours[1].y > black_contours[2].y):
            black_contours[1].points = 12
            black_contours[2].points = 18
        else:
            black_contours[1].points = 18
            black_contours[2].points = 12
        black_contours[3].points = 20

        black_contours_middle = black_contours[4:8]
        black_contours_middle.sort(key = lambda Field: Field.y, reverse=False)
        black_contours_middle[0].points = 13
        black_contours_middle[1].points = 18
        black_contours_middle[2].points = 12
        black_contours_middle[3].points = 14
        black_contours[4:8] = black_contours_middle
        black_contours_middle = []

        if(black_contours[8].y > black_contours[9].y):
            black_contours[8].points = 14
            black_contours[9].points = 13
        else:
            black_contours[8].points = 13
            black_contours[9].points = 14
        if(black_contours[10].y > black_contours[11].y):
            black_contours[10].points = 8
            black_contours[11].points = 10
        else:
            black_contours[10].points = 10
            black_contours[11].points = 8

        black_contours_middle = black_contours[12:16]
        black_contours_middle.sort(key = lambda Field: Field.y, reverse=False)
        black_contours_middle[0].points = 10
        black_contours_middle[1].points = 2
        black_contours_middle[2].points = 7
        black_contours_middle[3].points = 8
        black_contours[12:16] = black_contours_middle
        black_contours_middle = []

        black_contours[16].points = 3
        if(black_contours[17].y > black_contours[18].y):
            black_contours[17].points = 7
            black_contours[18].points = 2
        else:
            black_contours[17].points = 2
            black_contours[18].points = 7
        black_contours[19].points = 3

        for feld in black_contours:
            feld.multi = 1

        white_contours.sort(key = lambda Field: Field.x, reverse=False)
        white_contours_middle = white_contours[8:12]
        white_contours_middle.sort(key = lambda Field: Field.y, reverse=False)

        if(white_contours[0].y > white_contours[1].y):
            white_contours[0].points = 5
            white_contours[1].points = 1
        else:
            white_contours[0].points = 1
            white_contours[1].points = 5
        if(white_contours[2].y > white_contours[3].y):
            white_contours[2].points = 9
            white_contours[3].points = 4
        else:
            white_contours[2].points = 4
            white_contours[3].points = 9
        if(white_contours[4].y > white_contours[5].y):
            white_contours[4].points = 5
            white_contours[5].points = 1
        else:
            white_contours[4].points = 1
            white_contours[5].points = 5
        if(white_contours[6].y > white_contours[7].y):
            white_contours[6].points = 9
            white_contours[7].points = 4
        else:
            white_contours[6].points = 4
            white_contours[7].points = 9

        white_contours_middle[0].points = 6
        white_contours_middle[1].points = 6
        white_contours_middle[2].points = 11
        white_contours_middle[3].points = 11
        white_contours[8:12] = white_contours_middle
        white_contours_middle = []
        if(white_contours[12].y > white_contours[13].y):
            white_contours[12].points = 16
            white_contours[13].points = 15
        else:
            white_contours[12].points = 15
            white_contours[13].points = 16
        if(white_contours[14].y > white_contours[15].y):
            white_contours[14].points = 19
            white_contours[15].points = 17
        else:
            white_contours[14].points = 17
            white_contours[15].points = 19
        if(white_contours[16].y > white_contours[17].y):
            white_contours[16].points = 16
            white_contours[17].points = 15
        else:
            white_contours[16].points = 15
            white_contours[17].points = 16
        if(white_contours[18].y > white_contours[19].y):
            white_contours[18].points = 19
            white_contours[19].points = 17
        else:
            white_contours[18].points = 17
            white_contours[19].points = 19

        for feld in white_contours:
            feld.multi = 1

        red_contours.sort(key = lambda Field: Field.x, reverse=False)
        red_contours[0].points = 40
        red_contours[0].multi = 2
        if(red_contours[1].y > red_contours[2].y):
            red_contours[1].points = 24
            red_contours[1].multi = 2
            red_contours[2].points = 36
            red_contours[2].multi = 2
        else:
            red_contours[1].points = 36
            red_contours[1].multi = 2
            red_contours[2].points = 24
            red_contours[2].multi = 2
        red_contours[3].points = 60
        red_contours[3].multi = 3
        if(red_contours[4].y > red_contours[5].y):
            red_contours[4].points = 36
            red_contours[4].multi = 3
            red_contours[5].points = 54
            red_contours[5].multi = 3
        else:
            red_contours[4].points = 54
            red_contours[4].multi = 3
            red_contours[5].points = 36
            red_contours[5].multi = 3

        red_contours_middle = red_contours[6:10]
        red_contours_middle.sort(key = lambda Field: Field.y, reverse=False)
        red_contours_middle[0].points = 26
        red_contours_middle[0].multi = 2
        red_contours_middle[1].points = 39
        red_contours_middle[1].multi = 3
        red_contours_middle[2].points = 42
        red_contours_middle[2].multi = 3
        red_contours_middle[3].points = 28
        red_contours_middle[3].multi = 2
        red_contours[6:10] = red_contours_middle
        red_contours_middle = []

        red_contours[10].points = 50
        red_contours[10].multi = 2
        if(red_contours[11].y > red_contours[12].y):
            red_contours[11].points = 24
            red_contours[11].multi = 3
            red_contours[12].points = 30
            red_contours[12].multi = 3
        else:
            red_contours[11].points = 30
            red_contours[11].multi = 3
            red_contours[12].points = 24
            red_contours[12].multi = 3
        if(red_contours[13].y > red_contours[14].y):
            red_contours[13].points = 16
            red_contours[13].multi = 2
            red_contours[14].points = 20
            red_contours[14].multi = 2
        else:
            red_contours[13].points = 20
            red_contours[13].multi = 2
            red_contours[14].points = 16
            red_contours[14].multi = 2
        if(red_contours[15].y > red_contours[16].y):
            red_contours[15].points = 21
            red_contours[15].multi = 3
            red_contours[16].points = 6
            red_contours[16].multi = 3
        else:
            red_contours[15].points = 6
            red_contours[15].multi = 3
            red_contours[16].points = 21
            red_contours[16].multi = 3
        red_contours[17].points = 9
        red_contours[17].multi = 3
        if(red_contours[18].y > red_contours[19].y):
            red_contours[18].points = 14
            red_contours[18].multi = 2
            red_contours[19].points = 4
            red_contours[19].multi = 2
        else:
            red_contours[18].points = 4
            red_contours[18].multi = 2
            red_contours[19].points = 14
            red_contours[19].multi = 2
        red_contours[20].points = 6
        red_contours[20].multi = 3

        green_contours.sort(key = lambda Field: Field.x, reverse=False)

        if(green_contours[0].y > green_contours[1].y):
            green_contours[0].points = 10
            green_contours[0].multi = 2
            green_contours[1].points = 2
            green_contours[1].multi = 2
        else:
            green_contours[0].points = 2
            green_contours[0].multi = 2
            green_contours[1].points = 10
            green_contours[1].multi = 2

        green_contours_middle = green_contours[2:6]
        green_contours_middle.sort(key = lambda Field: Field.y, reverse=False)
        green_contours_middle[0].points = 8
        green_contours_middle[0].multi = 2
        green_contours_middle[1].points = 3
        green_contours_middle[1].multi = 3
        green_contours_middle[2].points = 15
        green_contours_middle[2].multi = 3
        green_contours_middle[3].points = 18
        green_contours_middle[3].multi = 2
        green_contours[2:6] = green_contours_middle
        green_contours_middle = []

        if(green_contours[6].y > green_contours[7].y):
            green_contours[6].points = 27
            green_contours[6].multi = 3
            green_contours[7].points = 12
            green_contours[7].multi = 3
        else:
            green_contours[6].points = 12
            green_contours[6].multi = 3
            green_contours[7].points = 27
            green_contours[7].multi = 3

        green_contours_middle = green_contours[8:13]
        green_contours_middle.sort(key = lambda Field: Field.y, reverse=False)
        green_contours_middle[0].points = 12
        green_contours_middle[0].multi = 2
        green_contours_middle[1].points = 18
        green_contours_middle[1].multi = 3
        green_contours_middle[2].points = 25
        green_contours_middle[2].multi = 1
        green_contours_middle[3].points = 33
        green_contours_middle[3].multi = 3
        green_contours_middle[4].points = 22
        green_contours_middle[4].multi = 2
        green_contours[8:13] = green_contours_middle
        green_contours_middle = []
        if(green_contours[12].y > green_contours[13].y):
            green_contours[13].points = 48
            green_contours[13].multi = 3
            green_contours[14].points = 45
            green_contours[14].multi = 3
        else:
            green_contours[13].points = 45
            green_contours[13].multi = 3
            green_contours[14].points = 48
            green_contours[14].multi = 3

        green_contours_middle = green_contours[15:19]
        green_contours_middle.sort(key = lambda Field: Field.y, reverse=False)
        green_contours_middle[0].points = 30
        green_contours_middle[0].multi = 2
        green_contours_middle[1].points = 51
        green_contours_middle[1].multi = 3
        green_contours_middle[2].points = 57
        green_contours_middle[2].multi = 3
        green_contours_middle[3].points = 32
        green_contours_middle[3].multi= 2
        green_contours[15:19] = green_contours_middle
        green_contours_middle = []
        if(green_contours[18].y > green_contours[19].y):
            green_contours[19].points = 38
            green_contours[19].multi = 2
            green_contours[20].points = 34
            green_contours[20].multi = 2
        else:
            green_contours[19].points = 34
            green_contours[19].multi = 2
            green_contours[20].points = 38
            green_contours[20].multi = 2

        field_contours = []
        field_contours.extend(black_contours)
        field_contours.extend(white_contours)
        field_contours.extend(red_contours)
        field_contours.extend(green_contours)

        for item in field_contours:
            cv2.drawContours(image, [item.contour], 0, (0,255,255),1)

        cv2.imwrite('TestImage.png',image)
        self.fieldContours = field_contours
        self.imageDebug = image

    def connect(self, hostname):
        # Connect to the RabbitMQ Server 
        self.amqpConnection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname))
        self.amqpChannel = connection.channel()
        self.amqpChannel.queue_declare(queue='points', durable=False)
        self.amqpChannel.queue_declare(queue='task', durable=False)

    def disconnect(self):
        # Close the channel and the connection
        self.amqpChannel.close()
        self.amqpConnection.close()
        self.camera.close()

    def commandListener(commandQueue, channel):
        for method_frame, properties, body in channel.consume('task'):
        msg = bytes.decode(body)
        print(msg)
        commandQueue.put(msg)
        channel.basic_ack(method_frame.delivery_tag)

    def detectDarts(self):
        queue = Queue()
        Process(target=self.worker, args=(queue)).start()
        #video analyse
        with PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.framerate = 4
            rawCapture = PiRGBArray(camera, size=(640, 480))
            # allow the camera to warmup
            time.sleep(0.1)
            fgbg = cv2.createBackgroundSubtractorMOG2(history=20, varThreshold=40, detectShadows=0)
            kernel = np.ones((3,3),np.uint8)
            # capture frames from the camera
            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                # grab the raw NumPy array representing the image, then initialize the timestamp
                # and occupied/unoccupied text
                image = frame.array
                gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
                fgmask = fgbg.apply(image)
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel, iterations = 1)
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel, iterations = 1)
                #ret,thresh = cv2.threshold(fgmask,250,255,cv2.THRESH_BINARY)
                dart_contours = []
                img, contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
                for cnt in contours:
                    if(cv2.contourArea(cnt)>20):
                        leftmost = tuple(cnt[cnt[:,:,0].argmin()][0])
                        dart_contours.append(Dart(cnt,leftmost[0],leftmost[1],time.time()))
                        #print(cv2.contourArea(cnt))
                if len(dart_contours) > 0:
                    dart_contours.sort(key = lambda Dart: Dart.x, reverse=False)
                    queue.put(dart_contours[0])
                # show the frame
                #dst = cv2.add(fgmask,gray)
                #cv2.imshow("Dart_Points", dst)
                key = cv2.waitKey(1) & 0xFF

                # clear the stream in preparation for the next frame
                rawCapture.truncate(0)

                # if the `q` key was pressed or another command gets in, break from the loop
                if key == ord("q") or not self.commandQueue.empty():
                    break
            cv2.destroyAllWindows()
            camera.close()
            queue.put('STOP')

    def worker(self, input, field_contours, img, channel):
        cv2.namedWindow('Hit_point', cv2.WINDOW_NORMAL)
        priviosDart = Dart()
        priviosDart.Time = 0
        priviosDart.x = 25000
        hand = False
        t = None
        for dart in iter(input.get, 'STOP'):
            if(cv2.contourArea(dart.contour)>10000):
                hand = True
            if (dart.detectTime - priviosDart.detectTime < 0.5):
                if t:
                    t.cancel()
            else:
                if t:
                    hand = t.join()
                priviosDart.Time = 0
                priviosDart.x = 25000
            if (dart.x > priviosDart.x):
                t = CustomTimer(0.4, validateDart, args=(priviosDart, hand))
                t.start()
            elif(dart.x <= priviosDart.x):
                t = CustomTimer(0.4, validateDart, args=(dart, hand))
                t.start()
            priviosDart = dart

    def validateDart(self, dart, hand):
        if hand:
            print("Naechste Aufnahme")
            self.amqpChannel.basic_publish(exchange='',
                                           routing_key='points',
                                           body='next')
            return False
        # DEBUG: Draw dart hit point into the image
        test = cv2.circle(self.imageDebug.copy(), (dart.x, dart.y), 6, (0,0,255), -1)
        cv2.imshow("Hit_point", test)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        # DEBUG: Draw dart hit point into the image
        for item in self.fieldContours:
                if cv2.pointPolygonTest(item.contour,(dart.x,dart.y),False) >= 0:
                    print(item.points)
                    if(item.multi == 1):
                        print("Single " + str(item.points))
                        self.amqpChannel.basic_publish(exchange='',
                                                       routing_key='points',
                                                       body='1x' + str(item.points))
                    elif(item.multi == 2):
                        print("Double " + str(item.points/item.multi))
                        self.amqpChannel.basic_publish(exchange='',
                                            routing_key='points',
                                            body='2x' + str(item.points))
                    elif(item.multi == 3):
                        print("Trible " + str(item.points/item.multi))
                        self.amqpChannel.basic_publish(exchange='',
                                            routing_key='points',
                                            body='3x' + str(item.points))
                    break

if __name__ == '__main__':
    dartVision = DartVision()
    dartVision.init()
    dartVision.run()
    dartVision.disconnect()
