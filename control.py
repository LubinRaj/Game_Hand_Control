import numpy as np
import cv2
import time
import imutils
from Keyboardinputs import  W, A, S, D, Q, E
from Keyboardinputs import PressKey, ReleaseKey
from imutils.video import FileVideoStream, VideoStream

key_up = W
key_down = S
key_left = A
key_right = D
press_boost = Q
press_brake = E
size_height = 360
size_width = 480
tracker_type = 'CSRT'
KEYS = {17:'W', 30:'A', 31:'S', 32:'D'}

def draw(ret, bbox, frame): # Draw bounding box
    if ret:# Tracking success
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        cv2.rectangle(frame, p1, p2, (0,255,0), 2, 1)
    else :# Tracking failure
        cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

def get_centroid(bbox): #center point of rectangle
    x, y, w, h = bbox
    centx = int(x + w // 2)
    centy = int(y + h // 2)
    return (centx, centy)

def drawbox(ret, bbox, frame): #draws rectangle from bbox
    global q
    if ret:
        #Tracking Success
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        cv2.rectangle(frame, p1, p2, (255,0,255), 2, 1)

    if p1[0] < 5: #quits program if taken hand to left top corner
        q = True # quit

key_steer, key_acc, key_boost = None, None, None #key to accelerate
pressed_acc,pressed_steer, pressed_boost = None, None , None

# delay = 0.3
last = 0 #last extreme of steer
chng = 3 #change in last, to remove small changes fulucations
chngt = 3 #to restart change to 0, if moved towards centre by some value

COLOR_RED = (0, 255, 0)
COLOR_BLACK = (0, 0, 0)

THRESH_ACTION = 20 # threshold for a action to be registered, inside this no movement

def steer(bbox): #to steer left and right
    global last, pressed_steer, key_steer
    x, _ = get_centroid(bbox)
    diff = x - cent[0]

    if abs(diff) < last: #2ns so, new diff is more,
        if abs(diff) < last-chng*chngt:
            last = 0
        return
    last = abs(diff) + chng

    if abs(diff) < THRESH_ACTION:
            return


    if diff > 0:
        key_steer = key_right
    else:
        key_steer = key_left

    pressed_steer = True
    PressKey(key_steer)
    return diff

def accelerate(bbox):
    global pressed_acc, key_acc

    _, y = get_centroid(bbox)
    diff = - (y - cent[1])  # '-' as y decr upward

    if abs(diff) < THRESH_ACTION:
        return

    if diff > 0:
        key_acc = key_up
    else:
        key_acc = key_down

    pressed_acc = True
    PressKey(key_acc)
    return diff

def boost(bbox):
    global pressed_acc, key_acc

    _, y = get_centroid(bbox)
    diff = - (y - cent2[1])  # '-' as y decr upward

    if abs(diff) < THRESH_ACTION:
        return

    if diff > 0:
        key_boost = press_boost
    else:
        key_boost = press_brake

    pressed_boost = True
    PressKey(key_boost)
    return diff


def draw_circle(frame, center, radius=THRESH_ACTION, color=COLOR_BLACK, thickness=3):
    cv2.circle(frame, center, radius, color, thickness)

def release_key(pressed, key):
    if not pressed:
        ReleaseKey(key)


def action(bbox , bbox2):
    global pressed_acc, pressed_steer, key_steer, key_acc , key_boost

    pressed_acc = False
    pressed_steer = False

    diff_acc = accelerate(bbox) #a
    diff_steer = steer(bbox)
    diff_boost = boost(bbox2) #s

    if not pressed_acc and key_acc is not None:
        ReleaseKey(key_acc)
        key_acc = None

    if not pressed_steer and key_steer is not None:
        ReleaseKey(key_steer)
        key_steer = None

    if not pressed_boost and key_boost is not None:
        release_key(key_boost)
        key_boost = None

    return diff_acc, diff_steer, diff_boost

# cv2.destroyAllWindows()
def get_frame():
    frame = fvs.read()
    if frame is None:
        return
    frame = imutils.resize(frame, width=size_width, height=size_height)
    return frame

fvs = FileVideoStream(0).start() #vs Video Stream
time.sleep(2.0) #to allow web cam to open

TIMER_SETUP = 3.0 # timer for capturing base image, get reading in posture
# mult = 10
t = time.time()

while True:
    frame = get_frame()
    curr = (time.time() - t)
    if curr > TIMER_SETUP:
        break
    cv2.putText(frame, str(int(TIMER_SETUP - curr)+1), (225,255), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_RED, 4)
    cv2.imshow("Setup", frame)
    cv2.waitKey(1)

FRAME = frame.copy()
cv2.destroyAllWindows()

#Make box around hand
frame = FRAME.copy()
cv2.putText(frame, 'Select First Hand', (30,30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_RED, 2)
bbox = cv2.selectROI(frame, False) # bounding box for left hand
frame = FRAME.copy()
cv2.putText(frame, 'Select Second Hand', (30,30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_RED, 2)
bbox2 = cv2.selectROI(frame, False)

cent = get_centroid(bbox)
cent2 = get_centroid(bbox2)

draw_circle(frame, cent)
draw_circle(frame, cent2) # circle, outside this movements will happend

BB = bbox
BB2 = bbox2 # saving it for later

cv2.destroyAllWindows()

# fvs = FileVideoStream(path_vid).start() #vs Video Stream
bbox = BB
bbox2 = BB2

# Creating the CSRT Tracker
tracker = cv2.TrackerCSRT_create()
tracker2 = cv2.TrackerCSRT_create() # left hand for steering

# Initialize tracker with first frame and bounding box
tracker.init(FRAME, bbox)
tracker2.init(FRAME, bbox2)

cv2.putText(frame.copy(), 'Put both your hands in Postion', (100,70), \
    cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_BLACK, 2)

TIMER_SETUP = 8
t = time.time()

while True:
    frame = get_frame()
    curr = (time.time() - t)
    if curr > TIMER_SETUP or frame is None:
        break
    cv2.putText(frame, str(int(TIMER_SETUP - curr)+1), (225,255), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_RED, 4)
    drawbox(True, bbox, frame)
    drawbox(True, bbox2, frame)
    cv2.imshow("Tracking", frame)
    cv2.waitKey(1)

cv2.destroyAllWindows()


q = False #to quit, take your hand on top corner

while True:
    frame = get_frame()

    if frame is None:
        break

#     frame = cv2.flip(frame, 1)
#     frame = imutils.resize(frame, width=size_width, height=)

    ret, bbox = tracker.update(frame)
    ret2, bbox2 = tracker2.update(frame) # retleft - True, if found hand

    if not ret == ret2 == True:
        print("Tracking stopped")
        break

    diff_acc, diff_steer, diff_boost  = action(bbox, bbox2)

    drawbox(ret, bbox, frame)
    drawbox(ret2, bbox2, frame)

    draw_circle(frame, cent)
    draw_circle(frame, cent2)

    cv2.putText(frame, tracker_type + " Tracker", (100,20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_BLACK,2);
    cv2.imshow("Tracking", frame)

    k = cv2.waitKey(1)

    if k == 13 or q: #13 is the Enter Key
        break

ReleaseKey(key_steer)
ReleaseKey(key_acc)
ReleaseKey(key_boost)

cv2.destroyAllWindows()
#fvs.stop()
