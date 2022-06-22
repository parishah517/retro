import socket, cv2, pickle,struct,imutils
import time
import jetson.inference
import jetson.utils
import cv2.aruco as aruco
from random import seed
from random import randint
from jetbot.jetbot import Robot

# initialize detectNet object and dictionary
net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.videoSource("csi://0", argv = ["--input-flip=rotate-180"])

# initialize aruco marker objects
aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_100)  # Use 5x5 dictionary to find markers
parameters = aruco.DetectorParameters_create()  # Marker detection parameters

# dictionary based on current forawrd direction, lists directions clockwise starting from current forward direction
current_forward = 'north'
direction_dict = {
    'north': ['north', 'east', 'south', 'west'],
    'east': ['east', 'south', 'west', 'north'],
    'south': ['south', 'west', 'north', 'east'],
    'west': ['west', 'north', 'east', 'south'],
    }

# for frame counting
k = 0
# initialize robot object
robot = Robot()

# dance routine function
def dance_routine():
    robot.right(0.3)
    time.sleep(0.256)
    robot.left(0.3)
    time.sleep(0.5)
    robot.right(0.3)
    time.sleep(0.5)
    robot.left(0.3)
    time.sleep(0.5)
    robot.right(0.3)
    time.sleep(0.5)
    robot.left(0.3)
    time.sleep(0.256)
    robot.left(0.3)
    time.sleep(1)
    robot.right(0.3)
    time.sleep(1)
    robot.right(0.3)
    time.sleep(0.256)
    robot.left(0.3)
    time.sleep(0.5)
    robot.right(0.3)
    time.sleep(0.5)
    robot.left(0.3)
    time.sleep(0.5)
    robot.right(0.3)
    time.sleep(0.5)
    robot.left(0.3)
    time.sleep(0.256)
    robot.right(0.3)
    time.sleep(1)
    robot.left(0.3)
    time.sleep(1)
    robot.stop()
def move_right():
    global current_forward, robot
    robot.right(.2)
    time.sleep(.325)
    robot.stop()
    current_forward = direction_dict[current_forward][1]
def move_left():
    global current_forward, robot
    robot.left(.2)
    time.sleep(.325)
    robot.stop()
    current_forward = direction_dict[current_forward][3]
def move_forward():
    global current_forward, robot
    robot.forward(.2)
    time.sleep(.65)
    robot.stop()
    current_forward = direction_dict[current_forward][0]
def move_backward():
    global current_forward, robot
    robot.right(.2)
    time.sleep(.65)
    robot.stop()
    current_forward = direction_dict[current_forward][2]

cloud_ip = "71.56.5.98"
cloud_port = 6000
cloud_addr = (cloud_ip, cloud_port)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.connect(cloud_addr)

with sock:
    packet = None
    data = sock.recv(10 * 1024)
    packet = pickle.loads(data)

    if packet['msg'] == 'start':
        while True:
            mission_data = {}
            frame = camera.Capture()
            # convert to cv2 to resize frame and use aruco marker detection
            frame = jetson.utils.cudaToNumpy(frame)
            frame = imutils.resize(frame, width=640)

            # drawing aruco markers
            corners, ids, rejected_img_points = aruco.detectMarkers(frame, aruco_dict,
                                                                    parameters=parameters)
            frame = aruco.drawDetectedMarkers(frame, corners, ids)

            # convert from cv2 back to cuda image format to use DetectNet
            frame = jetson.utils.cudaFromNumpy(frame)

            # extract detections in a list
            detections = net.Detect(frame)
            frame = jetson.utils.cudaToNumpy(frame)
            description_list = []

            for detection in detections:
                # extracts description associated with the class ID of the detected object and adds each description in frame to list
                description = net.GetClassDesc(detection.ClassID)
                description_list.append(description)

            mission_data['frame'] = frame
            mission_data['hostname'] = "bot1"
            mission_data['object'] = description_list
            mission_data['direction'] = current_forward

            packet = pickle.dumps(mission_data)
            out_data = struct.pack("Q", len(packet)) + packet
            sock.sendall(out_data)

            ack = sock.recv(10 * 1024)
            if not ack: break
            packet = pickle.loads(ack)
            print(packet)
            if packet['msg'] == 'mission complete':
                robot.stop()
                print(f"Found object in {current_forward}")
                break
            else:
                if not packet['hint']:
                    if k % 10 == 0:
                        if corners and 5 in ids:
                            move_right()
                            print("Marker found on the right")
                        else:
                            value = randint(0, 2)
                            if value is 0:
                                move_right()
                                print("Jetbot is moving right")
                            elif value is 1:
                                move_right()
                                # move_left()
                                print("Jetbot is moving left")
                            else:
                                move_forward()
                                print("Jetbot is moving forward")
                else:
                    hint = packet['hint']
                    if k % 10 == 0:
                        lst = direction_dict[current_forward]
                        hint_index = lst.index(hint)
                        if hint_index == 0:
                            move_forward()
                            print('forward')
                        elif hint_index == 1:
                            move_right()
                            print('right')
                        elif hint_index == 2:
                            move_backward()
                            print('back')
                        elif hint_index == 3:
                            move_left()
                            print('left')
                        else:
                            robot.stop()
                        if corners:
                            if 5 in ids:
                                value = randint(0, 1)
                                print("value ", value)
                                if value is 0:
                                    move_right()
                                    print('right')
                                else:
                                    move_left()
                                    print('left')
            k += 1

        while True:
            data = sock.recv(10 * 1024)
            if not data:
                continue
            else:
                break
        packet = pickle.loads(data)
        print(packet)
        if packet['msg'] == "start routine":
            dance_routine()
            print("Starting Dance Routine")
        sock.close()
