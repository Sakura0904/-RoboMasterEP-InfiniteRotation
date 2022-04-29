import time
import robomaster
from robomaster import conn
from MyQR import myqr
from PIL import Image
##########################
import socket
import sys
from multi_robomaster import multi_robot
from robomaster import led, blaster

QRCODE_NAME = "qrcode.png"

host = "192.168.2.1"
port = 40923

def main():

        address = (host, int(port))

        # 与机器人控制命令端口建立 TCP 连接
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print("Connecting...")

        s.connect(address)

        print("Connected!")

        # EP进入SDK模式
        msg = "command;"
        s.send(msg.encode('utf-8'))
        buf = s.recv(1024)
        print(buf.decode('utf-8') + 'about command EP进入SDK模式')

        # EP进入云台分离模式
        msg = 'robot mode free;'
        s.send(msg.encode('utf-8'))
        buf = s.recv(1024)
        print(buf.decode('utf-8') + 'robot mode free EP进入云台分离模式')

        # EP进入小陀螺模式 速度设置300
        msg = 'chassis wheel w1 100 w2 -100 w3 -100 w4 100; '
        s.send(msg.encode('utf-8'))
        buf = s.recv(1024)
        print(buf.decode('utf-8') + 'EP进入小陀螺模式 速度设置100')

        while True:
            msg = 'gimbal push attitude on;'
            s.send(msg.encode('utf-8'))
            buf = s.recv(1024)
            print(buf.decode('utf-8'))

            '''
                # 等待用户输入控制指令
                msg = input(">>> please input SDK cmd: ")

                # 当用户输入 Q 或 q 时，退出当前程序
                if msg.upper() == 'Q':
                        break

                # 添加结束符
                msg += ';'

                # 发送控制命令给机器人
                s.send(msg.encode('utf-8'))

                try:
                        # 等待机器人返回执行结果
                        buf = s.recv(1024)

                        print(buf.decode('utf-8'))
                except socket.error as e:
                        print("Error receiving :", e)
                        sys.exit(1)
                if not len(buf):
                        break
            '''
        

        # 关闭端口连接
        s.shutdown(socket.SHUT_WR)
        s.close()


if __name__ == '__main__':
    helper = conn.ConnectionHelper()
    info = helper.build_qrcode_string(ssid="NBo_techx", password="yjy123456")
    myqr.run(words=info)
    time.sleep(1)
    img = Image.open(QRCODE_NAME)
    img.show()
    if helper.wait_for_connection():
        print("Connected!")
    else:
        print("Connect failed!")
    eplink = conn.scan_robot_ip_list()
    print(eplink)


    robots_sn_list = ['3JKCJ98001080V']
    multi_robots = multi_robot.MultiEP()
    #multi_robots.initialize()
    number = multi_robots.number_id_by_sn([0, robots_sn_list[0]])
    print("The number of robot is: {0}".format(number))

    main()

