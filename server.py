"""服务器端：负责处理用户连接，获取用户上传的方向改变信息，进行分析后将更新信息返回给用户"""

import socket
import os
import threading
import time
import queue
import csv
import glob
import random
from collections import deque
from transmitInfo import *

# ip_port=('10.46.84.165', 9500) # 绑定IP与端口
ip_port=('192.168.124.6', 9500) # 绑定IP与端口

#--------------与游戏有关的常量--------------------
SCREEN_WIDTH = 600      # 屏幕宽度
SCREEN_HEIGHT = 480     # 屏幕高度
SIZE = 20               # 小方格大小
LINE_WIDTH = 1          # 网格线宽度

# 游戏区域的坐标范围
SCOPE_X = (0, SCREEN_WIDTH // SIZE - 1)
SCOPE_Y = (2, SCREEN_HEIGHT // SIZE - 1)

# 食物的分值及颜色
FOOD_STYLE_LIST = [(10, (255, 100, 100)), (20, (100, 255, 100)), (30, (100, 100, 255))]

LIGHT = (100, 100, 100)
DARK = (200, 200, 200)      # 蛇的颜色
BLACK = (0, 0, 0)           # 网格线颜色
RED = (200, 30, 30)         # 红色，GAME OVER 的字体颜色
BGCOLOR = (40, 40, 60)      # 背景色

SCORE_PER_LEVEL = 50 #多少分升一级（速度加快一次）
#-------------------------------------------------

#--------------与传输有关的常量--------------------
BUFSIZ = 1024
#-------------------------------------------------

# connect_queue = queue.Queue() # 用于记录所有正在连接的用户信息的队列
clients_info = [] # 用于记录两个玩家信息的列表

sk = socket.socket() # 默认tcp方式传输
sk.bind(ip_port) # 绑定监听
sk.listen(2) # 最大连接数

# 初始化蛇
def init_snake(order):
    snake = deque()
    if order == 1:
        snake.append((2, SCOPE_Y[0]))
        snake.append((1, SCOPE_Y[0]))
        snake.append((0, SCOPE_Y[0]))
    elif order == 2:
        snake.append((2, SCOPE_Y[1]))
        snake.append((1, SCOPE_Y[1]))
        snake.append((0, SCOPE_Y[1]))
    return snake

def create_food(snake_1, snake_2):
    food_x = random.randint(SCOPE_X[0], SCOPE_X[1])
    food_y = random.randint(SCOPE_Y[0], SCOPE_Y[1])
    while (food_x, food_y) in snake_1 or (food_x, food_y) in snake_2:
        # 如果食物出现在蛇身上，则重来
        food_x = random.randint(SCOPE_X[0], SCOPE_X[1])
        food_y = random.randint(SCOPE_Y[0], SCOPE_Y[1])
    food_style = random.randint(0, 2)
    return (food_x, food_y), food_style



def task():

    # ------------初始化一些与游戏有关的变量----------------
    # 蛇
    snake_1 = init_snake(1)
    snake_2 = init_snake(2)
    direct_1 = (1, 0)
    direct_2 = (1, 0)

    game_over = True
    last_move_time = None
    # pause = False       # 暂停

    alive_1 = False
    alive_2 = False
    # ---------------------------------------------------

    # while len(clients_info) < 2: # 等待客户的连接
    print("Waiting for Player-1 to connect...")
    conn_1, address_1 = sk.accept() # 接受数据  连接对象与客户端地址
    clients_info.append((conn_1, address_1))
    print('Player-1: ' + str(address_1[0]) + ' connect.')
    msg = "WaitForAnotherPlayer" # 等待另一个用户连接
    conn_1.send(msg.encode()) # 返回信息给用户

    print("Waiting for Player-2 to connect...")
    conn_2, address_2 = sk.accept() # 接受数据  连接对象与客户端地址
    clients_info.append((conn_2, address_2))
    print('Player-2: ' + str(address_2[0]) + ' connect.')
    msg = "WaitStart" # 等待玩家2开始
    # conn_1.send(msg.encode()) # 返回信息给用户
    conn_2.send(msg.encode()) # 返回信息给用户
    snake_info = Snake(snake_1, direct_1, snake_2, direct_2).encoding()
    transmit_info = "{}#{}#{}#{}".format(snake_info, 'none', 'none', 'none')
    print('Send info: ' + transmit_info)
    conn_1.send(transmit_info.encode()) # 返回信息给用户
    conn_2.send(transmit_info.encode())
    
    while True: #大循环

        #**********************等待游戏开始以及游戏初始化的阶段***************************
        print('-------------------------------')
        print("Waiting for players to start...")
        conn_1.settimeout(None) #阻塞模式
        data = conn_1.recv(BUFSIZ)
        assert data.decode() == "PressedEnter"
        conn_2.settimeout(None) #阻塞模式
        data = conn_2.recv(BUFSIZ)
        assert data.decode() == "PressedEnter"

        game_over = False
        alive_1 = True
        alive_2 = True
        # start = True
        snake_1 = init_snake(1) # snake是一个deque对象
        snake_2 = init_snake(2)
        food_pos, food_style = create_food(snake_1, snake_2)
        direct_1 = (1, 0)
        direct_2 = (1, 0)
        score_1 = 0
        score_2 = 0
        orispeed = 0.5      # 原始速度
        speed = orispeed
        last_move_time = None
        # pause = False       # 暂停
        
        print("Game Start.")
        msg = "GameStart"
        conn_1.send(msg.encode()) # 返回信息给用户
        conn_2.send(msg.encode())

        # 从两个用户端收取确认消息，防止这里连续两次发送消息而产生粘包
        conn_1.settimeout(None) #阻塞模式
        data = conn_1.recv(BUFSIZ)
        conn_2.settimeout(None) #阻塞模式
        data = conn_2.recv(BUFSIZ)


        snake_info = Snake(snake_1, direct_1, snake_2, direct_2).encoding()
        food_info = Food(food_pos, food_style).encoding()
        score_info = Score((score_1, score_1 // SCORE_PER_LEVEL + 1, score_2, score_2 // SCORE_PER_LEVEL + 1)).encoding()
        status_info = Status(game_over, (alive_1, alive_2)).encoding()
        transmit_info = "{}#{}#{}#{}".format(snake_info, food_info, score_info, status_info)
        print('Send info: ' + transmit_info)
        conn_1.send(transmit_info.encode())
        conn_2.send(transmit_info.encode())
        last_move_time = time.time() # 初始化上次移动的时间
        #***********************************************************************



        #**********************游戏进行中的阶段***************************
        directChanged_1 = False # 在本次更新后，玩家1的方向有没有被改变过
        directChanged_2 = False # 在本次更新后，玩家1的方向有没有被改变过

        while not game_over:
            curTime = time.time()

            if not directChanged_1:
                # 以非阻塞模式监听用户1发来的方向改变消息
                conn_1.settimeout(0) #不阻塞模式
                try: 
                    data = conn_1.recv(BUFSIZ)
                except BlockingIOError as e: 
                    data = None
                if data: # 请求改变方向的情况
                    direct_1 = Direction.decoding(data)
                    directChanged_1 = True

            if not directChanged_2:
                # 以非阻塞模式监听用户2发来的方向改变消息
                conn_2.settimeout(0) #不阻塞模式
                try: 
                    data = conn_2.recv(BUFSIZ)
                except BlockingIOError as e: 
                    data = None
                if data: # 请求改变方向的情况
                    direct_2 = Direction.decoding(data)
                    directChanged_2 = True


            # 到了更新两条蛇的时间
            if curTime - last_move_time > speed:
                directChanged_1 = False
                directChanged_2 = False

                # if not pause: # 先不考虑

                # 计算蛇1的情况
                next_s_1 = (snake_1[0][0] + direct_1[0], snake_1[0][1] + direct_1[1]) # snake_1[0]表示蛇头的那一格，第二个[0]或[1]表示横向还是纵向
                if next_s_1 == food_pos: # 吃到了食物
                    snake_1.appendleft(next_s_1)
                    score_1 += FOOD_STYLE_LIST[food_style][0]
                    food_pos, food_style = create_food(snake_1, snake_2)
                else:
                    if SCOPE_X[0] <= next_s_1[0] <= SCOPE_X[1] and SCOPE_Y[0] <= next_s_1[1] <= SCOPE_Y[1] \
                            and next_s_1 not in snake_1 and next_s_1 not in snake_2:
                        snake_1.appendleft(next_s_1)
                        snake_1.pop()
                    else:
                        game_over = True
                        alive_1 = False # 蛇1死了

                # 计算蛇2的情况
                next_s_2 = (snake_2[0][0] + direct_2[0], snake_2[0][1] + direct_2[1])
                if next_s_2 == food_pos: # 吃到了食物
                    snake_2.appendleft(next_s_2)
                    score_2 += FOOD_STYLE_LIST[food_style][0]
                    food_pos, food_style = create_food(snake_1, snake_2)
                else:
                    if SCOPE_X[0] <= next_s_2[0] <= SCOPE_X[1] and SCOPE_Y[0] <= next_s_2[1] <= SCOPE_Y[1] \
                            and next_s_2 not in snake_1 and next_s_2 not in snake_2:
                        snake_2.appendleft(next_s_2)
                        snake_2.pop()
                    else:
                        game_over = True
                        alive_2 = False # 蛇2死了

                # 更新速度
                if speed > 0.1:
                    speed = orispeed - 0.05 * (max(score_1, score_2) // 50)

                # 更新时间
                last_move_time = curTime

                # 将更新后的数据传给两个用户
                snake_info = Snake(snake_1, direct_1, snake_2, direct_2).encoding()
                food_info = Food(food_pos, food_style).encoding()
                score_info = Score((score_1, score_1 // SCORE_PER_LEVEL + 1, score_2, score_2 // SCORE_PER_LEVEL + 1)).encoding()
                status_info = Status(game_over, (alive_1, alive_2)).encoding()
                transmit_info = "{}#{}#{}#{}".format(snake_info, food_info, score_info, status_info)
                print('Send info: ' + transmit_info)
                conn_1.send(transmit_info.encode())
                conn_2.send(transmit_info.encode())
        #***********************************************************************




def main():
    t = threading.Thread(target=task) #, args=(host, port)
    t.daemon = True
    t.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("The server is paused. Input \'exit\' to close the server. Press any key to recover...")
            if(input() == 'exit'): #如果服务器这端也输入'exit'，则关掉服务器
                while(len(clients_info)):
                    conn, address = clients_info[0]
                    clients_info.pop(0)
                    conn.close()  # 关闭与用户的连接
                    # print('client: ' + str(address[0]) + ' has closed connection.')

                print('Close the server.')
                break
            else:
                print('Recover. Waiting for client to connect...')
                continue

if __name__ == "__main__":
    main()

