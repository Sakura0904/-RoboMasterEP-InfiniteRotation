import socket
import threading
import select
import queue
import math
import time

REVOLVESPEED_DEBUG = 100

class RobotConnection(object):
    """
    Create a RobotConnection object with a given robot ip.
    """
    VIDEO_PORT = 40921      #视频流
    AUDIO_PORT = 40922     #音频流
    CTRL_PORT = 40923      #控制命令
    PUSH_PORT = 40924      #消息推送
    EVENT_PORT = 40925     #事件上报
    IP_PORT = 40926         #IP广播

    def __init__(self, robot_ip=''):
        self.robot_ip = robot_ip

        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#视频流
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#音频流
        self.ctrl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#控制命令
        self.push_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#消息推送
        self.event_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#事件上报
        self.ip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#IP广播

        self.push_socket.bind(('', RobotConnection.PUSH_PORT))#消息推送
        self.ip_socket.bind(('', RobotConnection.IP_PORT))#IP广播

        self.cmd_socket_list = [self.ctrl_socket, self.push_socket, self.event_socket]
        self.cmd_socket_msg_queue = {
            self.video_socket: queue.Queue(32),#视频流
            self.audio_socket: queue.Queue(32),#音频流
            self.ctrl_socket: queue.Queue(16),#控制命令
            self.push_socket: queue.Queue(16),#消息推送
            self.event_socket: queue.Queue(16)#事件上报
        }
        self.cmd_socket_recv_thread = threading.Thread(target=self.__socket_recv_task)#IP广播

        self.is_shutdown = True

    def update_robot_ip(self, robot_ip):
        """
        Update the robot ip
        """
        self.robot_ip = robot_ip

    def get_robot_ip(self, timeout=None):
        """
        Get the robot ip from ip broadcat port
        If optional arg 'timeout' is None (the default), block if necessary until
        get robot ip from broadcast port. If 'timeout' is a non-negative number,
        it blocks at most 'timeout' seconds and return None if no data back from
        robot broadcast port within the time. Otherwise, return the robot ip 
        immediately.
        """
        self.ip_socket.settimeout(timeout)
        msg = None
        try:
            msg, addr = self.ip_socket.recvfrom(1024)
        except Exception as e:
            print('Get robot ip failed, please check the robot networking-mode and connection !')
        else:
            msg = msg.decode('utf-8')
            msg = msg[msg.find('robot ip ') + len('robot ip ') : ]

        return msg

    def open(self): 
        """
        Open the connection
        It will connect the control port and event port with TCP and start a data
        receive thread.
        """
        self.ctrl_socket.settimeout(5)

        try:
            self.ctrl_socket.connect((self.robot_ip, RobotConnection.CTRL_PORT))
            self.event_socket.connect((self.robot_ip, RobotConnection.EVENT_PORT))
        except Exception as e:
            print('Connection failed, the reason is %s'%e)
            return False
        else:
            self.is_shutdown = False
            self.cmd_socket_recv_thread.start() 
            print('Connection successful')
            return True

    def close(self): 
        """
        Close the connection
        """
        self.is_shutdown = True
        self.cmd_socket_recv_thread.join()

    def start_video_recv(self):
        assert not self.is_shutdown, 'CONNECTION INVALID'
        if self.video_socket not in self.cmd_socket_list:
            self.video_socket.settimeout(5)
            try:
                self.video_socket.connect((self.robot_ip, RobotConnection.VIDEO_PORT))
            except Exception as e:
                print('Connection failed, the reason is %s'%e)
                return False 
            self.cmd_socket_list.append(self.video_socket)
        return True

    def stop_video_recv(self):
        if self.video_socket in self.cmd_socket_list:
            self.cmd_socket_list.remove(self.video_socket)
        return True

    def start_audio_recv(self):
        assert not self.is_shutdown, 'CONNECTION INVALID'
        if self.audio_socket not in self.cmd_socket_list:
            self.audio_socket.settimeout(5)
            try:
                self.audio_socket.connect((self.robot_ip, RobotConnection.AUDIO_PORT))
            except Exception as e:
                print('Connection failed, the reason is %s'%e)
                return False
            self.cmd_socket_list.append(self.audio_socket)
        return True

    def stop_audio_recv(self):
        if self.audio_socket in self.cmd_socket_list:
            self.cmd_socket_list.remove(self.audio_socket)
        return True

    def send_data(self, msg):
        """
        Send data to control port
        """
        msg += ';'
        self.__send_data(self.ctrl_socket, msg)

    def recv_video_data(self, timeout=None, latest_data=False):
        """
        Receive control data
        If optional arg 'timeout' is None (the default), block if necessary until
        get data from control port. If 'timeout' is a non-negative number,
        it blocks at most 'timeout' seconds and reuturn None if no data back from
        robot video port within the time. Otherwise, return the data immediately.
 
        If optional arg 'latest_data' is set to True, it will return the latest
        data, instead of the data in queue tail.
        """
        return self.__recv_data(self.video_socket, timeout, latest_data)

    def recv_audio_data(self, timeout=None, latest_data=False):
        """
        Receive control data
        If optional arg 'timeout' is None (the default), block if necessary until
        get data from control port. If 'timeout' is a non-negative number,
        it blocks at most 'timeout' seconds and reuturn None if no data back from
        robot video port within the time. Otherwise, return the data immediately.
 
        If optional arg 'latest_data' is set to True, it will return the latest
        data, instead of the data in queue tail.
        """
        return self.__recv_data(self.audio_socket, timeout, latest_data)

    def recv_ctrl_data(self, timeout=None, latest_data=False):
        """
        Receive control data
        If optional arg 'timeout' is None (the default), block if necessary until
        get data from control port. If 'timeout' is a non-negative number,
        it blocks at most 'timeout' seconds and reuturn None if no data back from
        robot control port within the time. Otherwise, return the data immediately.
 
        If optional arg 'latest_data' is set to True, it will return the latest
        data, instead of the data in queue tail.
        """
        return self.__recv_data(self.ctrl_socket, timeout, latest_data)

    def recv_push_data(self, timeout=None, latest_data=False):
        """
        Receive push data
        If optional arg 'timeout' is None (the default), block if necessary until
        get data from push port. If 'timeout' is a non-negative number,
        it blocks at most 'timeout' seconds and reuturn None if no data back from
        robot push port within the time. Otherwise, return the data immediately.
 
        If optional arg 'latest_data' is set to True, it will return the latest
        data, instead of the data in queue tail.

        接收推送数据  
        如果可选参数'timeout'为None(默认值)，必要时阻塞直到  
        从推端口获取数据。 如果'timeout'是非负数，  
        它最多阻塞'timeout'秒，如果没有数据返回None  
        在机器人推端口的时间内。 否则，立即返回数据。  
 
        如果可选参数'latest_data'被设置为True，它将返回最新的数据  
        数据，而不是队列尾部的数据。  
        """
        return self.__recv_data(self.push_socket, timeout, latest_data)

    def recv_event_data(self, timeout=None, latest_data=False):
        """
        Receive event data
        If optional arg 'timeout' is None (the default), block if necessary until
        get data from event port. If 'timeout' is a non-negative number,
        it blocks at most 'timeout' seconds and reuturn None if no data back from
        robot event port within the time. Otherwise, return the data immediately.
 
        If optional arg 'latest_data' is set to True, it will return the latest
        data, instead of the data in queue tail.
        """
        return self.__recv_data(self.event_socket, timeout, latest_data)

    def __send_data(self, socket_obj, data):
        assert not self.is_shutdown, 'CONECTION INVALID'
        return socket_obj.send(data.encode('utf-8'))
        
    def __recv_data(self, socket_obj, timeout, latest_data):
        assert not self.is_shutdown, 'CONECTION INVALID'
        msg = None
        if latest_data:
            while self.cmd_socket_msg_queue[socket_obj].qsize() > 1:
                self.cmd_socket_msg_queue[socket_obj].get()
        try:
            msg = self.cmd_socket_msg_queue[socket_obj].get(timeout=timeout)
        except Exception as e:
            return None
        else:
            return msg
        
    def __socket_recv_task(self):
        while not self.is_shutdown:
            rlist, _, _  = select.select(self.cmd_socket_list, [], [], 2)

            for s in rlist:
                msg, addr = s.recvfrom(4096)
                if self.cmd_socket_msg_queue[s].full():
                    self.cmd_socket_msg_queue[s].get()
                self.cmd_socket_msg_queue[s].put(msg)

        for s in self.cmd_socket_list:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                pass
robot = RobotConnection('192.168.2.1')

def F_Init_RobotSetting():
    robot.open()
    #EP进入SDK模式控制
    robot.send_data('command')
    print('send data to robot   : SDK链接')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)
    #EP进入云台分离模式
    robot.send_data('robot mode free')
    print('send data to robot   : 云台分离')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)
def F_Open_GimbalDataCallback():
    #EP云台信息推送控制
    robot.send_data('gimbal push attitude on')
    print('send data to robot   : 云台信息推送控制')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)
def F_Open_GameDataCallback():
    #EP赛事系统回复数据开启
    robot.send_data('game_msg on')
    print('send data to robot   : 键鼠信息推送控制')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)
def F_Get_GimbalData():
    #EP数据流回传
    result = str(robot.recv_push_data(5))
    if  result.startswith("b'gimbal push attitude"):
        #print('EP云台和底盘的Pitch夹角:' + result.split(' ')[3])
        v_gimbal_yaw = result.split(' ')[4]
        return v_gimbal_yaw
    else:
        return None
def F_Get_GameData():
     #EP数据流回传
    result = str(robot.recv_push_data(5))
    print(result)
    if  result.startswith("b'game msg push"):
        #print('EP云台和底盘的Pitch夹角:' + result.split(' ')[3])
        v_keyboard = result.split(' ')[4]
        return v_gimbal_yaw
    else:
        return None
def F_Test_Revolve(w1 = 100,w2 = -100,w3 = -100,w4 = 100,):
    #EP进入小陀螺模式 速度设置100
    v_revolve_command = 'chassis wheel' + ' w1 ' + str(w1) + ' w2 ' + str(w2) + ' w3 ' + str(w3) + ' w4 ' + str(w4)
    robot.send_data(v_revolve_command)
    #print('send data to robot   : 底盘旋转命令' + v_revolve_command)
    recv = robot.recv_ctrl_data(5)
    #print('recv data from robot : %s'%recv)

'''
    #版本号
    robot.send_data('version ?')
    print('send data to robot   : version ?')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)

    #视频流
    robot.send_data('stream on')
    print('send data to robot   : stream on')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)

    result = robot.start_video_recv()
    if result:
        stream_data = robot.recv_video_data(5)
        print('recv video data from robot %s'%stream_data)
        robot.stop_video_recv()

    robot.send_data('stream off')
    print('send data to robot   : stream off')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)

    #音频流
    robot.send_data('audio on')
    print('send data to robot   : audio on')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)

    result = robot.start_audio_recv()
    if result:
        stream_data = robot.recv_audio_data(5)
        print('recv audio data from robot %s'%stream_data)
        robot.stop_audio_recv()

    robot.send_data('audio off')
    print('send data to robot   : audio off')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)

    #退出控制
    robot.send_data('quit')
    print('send data to robot   : quit')
    recv = robot.recv_ctrl_data(5)
    print('recv data from robot : %s'%recv)

    robot.close()
'''

if __name__ == '__main__':
    F_Init_RobotSetting()
    F_Open_GimbalDataCallback()
    F_Open_GameDataCallback()
    F_Test_Revolve(0,0,0,0)
    

    lspeed_gimbal_xy = [0,0,0,0]#云台x轴y轴yaw轴pitch轴输入量
    lspeed_chassis_xy = [0,0,0]#底盘x轴y轴yaw轴解算量
    lspeed_moto = [0,0,0,0]#底盘四电机解算

    while True:
        F_Get_GameData()
        lspeed_gimbal_xy[0] = 0#v_gimbal_value[0] #云台x轴移动命令
        lspeed_gimbal_xy[1] = 0#v_gimbal_value[1] #云台y轴移动命令
        #print(v_gimbal_value)

        v_gimbal_angle = F_Get_GimbalData()
        v_gimbal_angle = float(v_gimbal_angle)+50#云台角度补偿

        lspeed_chassis_xy[0] = lspeed_gimbal_xy[0]*math.cos(math.radians(float(v_gimbal_angle))) - lspeed_gimbal_xy[1]*math.sin(math.radians(float(v_gimbal_angle)))#底盘x轴解算
        lspeed_chassis_xy[1] = lspeed_gimbal_xy[0]*math.sin(math.radians(float(v_gimbal_angle))) + lspeed_gimbal_xy[1]*math.cos(math.radians(float(v_gimbal_angle)))#底盘y轴解算
        lspeed_chassis_xy[2] = REVOLVESPEED_DEBUG 

        lspeed_moto[0] = lspeed_chassis_xy[0] - lspeed_chassis_xy[1] + lspeed_chassis_xy[2]
        lspeed_moto[1] = lspeed_chassis_xy[0] + lspeed_chassis_xy[1] - lspeed_chassis_xy[2]
        lspeed_moto[2] = lspeed_chassis_xy[0] - lspeed_chassis_xy[1] - lspeed_chassis_xy[2]
        lspeed_moto[3] = lspeed_chassis_xy[0] + lspeed_chassis_xy[1] + lspeed_chassis_xy[2]
        F_Test_Revolve(lspeed_moto[0],lspeed_moto[1],lspeed_moto[2],lspeed_moto[3]) 
        
        #print(str(v_gimbal_angle) + '\t\t' + str(lspeed_moto[0]) + '\t\t' + str(lspeed_moto[1]) + '\t\t' + str(lspeed_moto[2]) + '\t\t' + str(lspeed_moto[3]))
        v_gimbal_value = [0,0]