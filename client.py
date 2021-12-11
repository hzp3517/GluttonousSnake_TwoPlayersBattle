"""用户端：负责从服务器端接收每次更新后的游戏界面信息并显示到屏幕上，同时监听键盘输入的控制方向的信息并上传给服务器"""

import socket
import sys
import os
import time
import pygame
from pygame.locals import *
from collections import deque
from transmitInfo import *

# ip_port=('10.46.84.165', 9500) # 访问的服务器的ip和端口
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
YELLOW = (200, 200, 30)     # 黄色
GREEN = (30, 200, 30)       # 绿色
BGCOLOR = (40, 40, 60)      # 背景色

SCORE_PER_LEVEL = 50 #多少分升一级（速度加快一次）
#-------------------------------------------------

#--------------与传输有关的常量--------------------
BUFSIZ = 1024
#-------------------------------------------------

player_id = None # 1或2，最先与服务器连接的就是玩家1，之后连接上的就是玩家2


def print_text(screen, font, x, y, text, fcolor=(255, 255, 255)):
    imgText = font.render(text, True, fcolor)
    screen.blit(imgText, (x, y))

def initScreen(screen):
    # 填充背景色
    screen.fill(BGCOLOR)
    # 画网格线 竖线
    for x in range(SIZE, SCREEN_WIDTH, SIZE):
        pygame.draw.line(screen, BLACK, (x, SCOPE_Y[0] * SIZE), (x, SCREEN_HEIGHT), LINE_WIDTH)
    # 画网格线 横线
    for y in range(SCOPE_Y[0] * SIZE, SCREEN_HEIGHT, SIZE):
        pygame.draw.line(screen, BLACK, (0, y), (SCREEN_WIDTH, y), LINE_WIDTH)

def drawSnake(screen, snake_1, snake_2):
    '''
    画蛇
    '''
    for s in snake_1:
        pygame.draw.rect(screen, 0, (s[0] * SIZE + LINE_WIDTH, s[1] * SIZE + LINE_WIDTH,
                                        SIZE - LINE_WIDTH * 2, SIZE - LINE_WIDTH * 2), 0)
    for s in snake_2:
        pygame.draw.rect(screen, 255, (s[0] * SIZE + LINE_WIDTH, s[1] * SIZE + LINE_WIDTH,
                                        SIZE - LINE_WIDTH * 2, SIZE - LINE_WIDTH * 2), 0)

def drawFood(screen, food_pos, food_style):
    '''
    画食物
    '''
    pygame.draw.rect(screen, FOOD_STYLE_LIST[food_style][1], (food_pos[0] * SIZE, food_pos[1] * SIZE, SIZE, SIZE), 0)

def printScore(screen, player_id, s1, l1, s2, l2):
    '''
    打印当前成绩。本玩家的成绩在前，对手的成绩在后。
    '''
    font1 = pygame.font.SysFont('SimHei', 24)  # 得分的字体
    if player_id == 1:
        print_text(screen, font1, 0, 7, f'蛇1等级：{l1}')
        print_text(screen, font1, 150, 7, f'蛇1得分：{s1}')
        print_text(screen, font1, 300, 7, f'蛇2等级：{l2}')
        print_text(screen, font1, 450, 7, f'蛇2得分：{s2}')
    else:
        print_text(screen, font1, 0, 7, f'蛇2等级：{l2}')
        print_text(screen, font1, 150, 7, f'蛇2得分：{s2}')
        print_text(screen, font1, 300, 7, f'蛇1等级：{l1}')
        print_text(screen, font1, 450, 7, f'蛇1得分：{s1}')
        
def printGameOver(screen, player_id, alive):
    '''
    在游戏结束时，打印“game over”字样。
    在游戏结束时，对某个用户，打印“你的锅”/“他的锅”/“你俩一块背锅”。
    '''
    font2 = pygame.font.Font(None, 72)  # GAME OVER 的字体
    fwidth, fheight = font2.size('GAME OVER')
    print_text(screen, font2, (SCREEN_WIDTH - fwidth) // 2, (SCREEN_HEIGHT - fheight) // 2, 'GAME OVER', RED)


    font3 = pygame.font.SysFont('SimHei', 56)  # 背锅信息的字体
    g1_text = "你的锅"
    g2_text = "他的锅"
    g3_text = "你俩一块背锅"
    g1_width, g1_height = font3.size(g1_text)
    g2_width, g2_height = font3.size(g2_text)
    g3_width, g3_height = font3.size(g3_text)

    if player_id == 1:
        if alive[0]==True and alive[1]==False:
            print_text(screen, font3, (SCREEN_WIDTH - g2_width) // 2, (SCREEN_HEIGHT - fheight) // 2 + g2_height*2, g2_text, GREEN)
        elif alive[0]==False and alive[1]==True:
            print_text(screen, font3, (SCREEN_WIDTH - g1_width) // 2, (SCREEN_HEIGHT - fheight) // 2 + g1_height*2, g1_text, YELLOW)
        elif alive[0]==False and alive[1]==False:
            print_text(screen, font3, (SCREEN_WIDTH - g3_width) // 2, (SCREEN_HEIGHT - fheight) // 2 + g3_height*2, g3_text, RED)
    else:
        if alive[0]==True and alive[1]==False:
            print_text(screen, font3, (SCREEN_WIDTH - g1_width) // 2, (SCREEN_HEIGHT - fheight) // 2 + g1_height*2, g1_text, YELLOW)
        elif alive[0]==False and alive[1]==True:
            print_text(screen, font3, (SCREEN_WIDTH - g2_width) // 2, (SCREEN_HEIGHT - fheight) // 2 + g2_height*2, g2_text, GREEN)
        elif alive[0]==False and alive[1]==False:
            print_text(screen, font3, (SCREEN_WIDTH - g3_width) // 2, (SCREEN_HEIGHT - fheight) // 2 + g3_height*2, g3_text, RED)


def playProcess(client: socket.socket, player_id: int):
    assert player_id in [1, 2]

    #-------初始化游戏信息--------
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('贪吃蛇') #窗口栏显示的标题
    font_info = pygame.font.SysFont('SimHei', 24)  # 得分（上方栏）的字体
    font_result = pygame.font.Font(None, 72)  # GAME OVER 的字体
    # 让以下变量作为本函数中的全局变量，这样在游戏输掉之后画面中的这些信息也不会丢失（比如蛇死的时候所处的位置）
    # win_1 = False # 玩家1是赢了还是输了
    s1, l1, s2, l2 = 0, 0, 0, 0
    snake_1, snake_2 = None, None
    food_pos = None
    food_style = None
    alive = (False, False) # 分别对应玩家1，玩家2
    #----------------------------

    #----------------大循环中用到的状态变量----------------
    waitForPlayer2 = True
    waitForStart = False
    gameStart = False
    gameOver = False
    #----------------------------------------------------


    while True: #大循环
        """
        每个子循环必须包含以下过程：
        while xxx:
            initScreen(screen) # 初始化窗口画面

            # 确保能正常关闭窗口
            for event in pygame.event.get():
                if event.type == QUIT:
                    return

            xxxxxxxxxxx # 具体子模块内容

            pygame.display.update() #更新画面
        """

        #**********************等待玩家2进入游戏的阶段***************************
        while waitForPlayer2:

            for event in pygame.event.get():
                if event.type == QUIT:
                    # sys.exit()
                    return

            initScreen(screen)

            if player_id == 1:
                print_text(screen, font_info, 0, 7, f'您是玩家1，等待玩家2进入游戏...')

            # 等待服务器初始化游戏界面的消息
            client.settimeout(0) #不阻塞模式
            try: 
                data = client.recv(BUFSIZ)
            except BlockingIOError as e: 
                data = None

            if data: # 服务器发来初始化游戏界面消息了的情况
                # assert data.decode() == "WaitStart" # 玩家2也进入了
                snake_info = data.decode().split('#')[0]
                snake_1, direct_1, snake_2, direct_2 = Snake.decoding(snake_info)
                waitForPlayer2 = False
                waitForStart = True
            # else:
            #     waitForPlayer2 = False
            #     waitForStart = True

            pygame.display.update()
        #***********************************************************************


        #**********************等待游戏开始的阶段***************************
        pressedEnter = False #玩家是否已经按下回车键
        while waitForStart:
            initScreen(screen)
            drawSnake(screen, snake_1, snake_2)

            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                # 等待接收键盘回车键
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        client.send("PressedEnter".encode()) # 给服务器发消息表明已经按下了回车键
                        pressedEnter = True

            if player_id == 1:
                if pressedEnter:
                    print_text(screen, font_info, 0, 7, f'玩家1，请等待对方开始游戏...')
                else:
                    print_text(screen, font_info, 0, 7, f'玩家1，请按回车键开始...')
            else:
                if pressedEnter:
                    print_text(screen, font_info, 0, 7, f'玩家2，请等待对方开始游戏...')
                else:
                    print_text(screen, font_info, 0, 7, f'您是玩家2。请按回车键开始...')

            # 等待服务器的消息
            client.settimeout(0) #不阻塞模式
            try: 
                data = client.recv(BUFSIZ)
            except BlockingIOError as e: 
                data = None
            if data: #来消息了的情况

                msg = "ACK"
                client.send(msg.encode()) # 返回服务器一个确认信息，避免服务器端因连续两次发送消息而出现粘包

                assert data.decode() == "GameStart" # 开始游戏
                pressedEnter = False
                waitForStart = False
                gameStart = True

            pygame.display.update()
        #***********************************************************************


        #**********************游戏进行的阶段***************************
        directChoosed = False # 在某一次服务器传回更新信息之后，用户是否已经通过键盘输入了合法的方向

        while gameStart:
            initScreen(screen)

            drawSnake(screen, snake_1, snake_2)
            printScore(screen, player_id, s1, l1, s2, l2)

            if food_pos and type(food_style)==int: # 即food_style不为None的情况，因为它是有可能为0的。
                drawFood(screen, food_pos, food_style)

            # 等待服务器的消息
            client.settimeout(0) #不阻塞模式
            try: 
                data = client.recv(BUFSIZ)
            except BlockingIOError as e: 
                data = None
            if data: # 服务器来消息了，说明需要更新画面了
                directChoosed = False
                snake_info, food_info, score_info, status_info = data.decode().split('#')
                snake_1, direct_1, snake_2, direct_2 = Snake.decoding(snake_info)
                food_pos, food_style = Food.decoding(food_info)
                s1, l1, s2, l2 = Score.decoding(score_info)
                finish, alive = Status.decoding(status_info)

                if finish: #gameover
                    gameStart = False
                    gameOver = True
                    pygame.display.update()
                    continue #此次循环不再监听键盘输入


            # 监听键盘输入
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE: # 暂停的情况，先不考虑
                        pass
                        # pause = not pause
                    else:
                        # 注意：目前这里为了两个用户在一台机器上调试方便，用户1用wasd控制，用户2用上下左右控制，后续可以统一起来

                        if not directChoosed: # 在此次更新后还未输入有效的方向信息

                            if player_id == 1: # 用户1的情况
                                if event.key == K_w:
                                    # 这个判断是为了防止蛇向上移时按了向下键，导致直接 GAME OVER
                                    if not direct_1[1]:
                                        direct_1 = (0, -1)
                                        directChoosed = True
                                elif event.key == K_s:
                                    if not direct_1[1]:
                                        direct_1 = (0, 1)
                                        directChoosed = True
                                elif event.key == K_a:
                                    if not direct_1[0]:
                                        direct_1 = (-1, 0)
                                        directChoosed = True
                                elif event.key == K_d:
                                    if not direct_1[0]:
                                        direct_1 = (1, 0)
                                        directChoosed = True

                                # 向服务器端发送更新的方向信息
                                direct_info = Direction(direct_1).encoding(encode=True)
                                client.send(direct_info)

                            else: # 用户2的情况
                                if event.key == K_UP:
                                    # 这个判断是为了防止蛇向上移时按了向下键，导致直接 GAME OVER
                                    if not direct_2[1]:
                                        direct_2 = (0, -1)
                                        directChoosed = True
                                elif event.key == K_DOWN:
                                    if not direct_2[1]:
                                        direct_2 = (0, 1)
                                        directChoosed = True
                                elif event.key == K_LEFT:
                                    if not direct_2[0]:
                                        direct_2 = (-1, 0)
                                        directChoosed = True
                                elif event.key == K_RIGHT:
                                    if not direct_2[0]:
                                        direct_2 = (1, 0)
                                        directChoosed = True

                                # 向服务器端发送更新的方向信息
                                direct_info = Direction(direct_2).encoding(encode=True)
                                client.send(direct_info)

            pygame.display.update()

        #***********************************************************************
                



        #**********************上一轮游戏结束后，等待新一轮游戏开始的阶段***************************
        pressedEnter = False # 玩家是否已经按下回车键
        while gameOver:
            initScreen(screen) # 初始化窗口画面

            drawSnake(screen, snake_1, snake_2)
            if not pressedEnter:
                printScore(screen, player_id, s1, l1, s2, l2)
                printGameOver(screen, player_id, alive)

            for event in pygame.event.get():
                if event.type == QUIT: # 确保能正常关闭窗口
                    return
                # 等待接收键盘回车键
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        client.send("PressedEnter".encode()) # 给服务器发消息表明已经按下了回车键
                        pressedEnter = True

            if player_id == 1:
                if pressedEnter:
                    print_text(screen, font_info, 0, 7, f'玩家1，请等待对方开始游戏...')
            else:
                if pressedEnter:
                    print_text(screen, font_info, 0, 7, f'玩家2，请等待对方开始游戏...')

            # 等待服务器的消息
            client.settimeout(0) #不阻塞模式
            try: 
                data = client.recv(BUFSIZ)
            except BlockingIOError as e: 
                data = None
            if data: #来消息了的情况

                msg = "ACK"
                client.send(msg.encode()) # 返回服务器一个确认信息，避免服务器端因连续两次发送消息而出现粘包

                assert data.decode() == "GameStart" # 开始游戏
                pressedEnter = False
                gameOver = False
                gameStart = True

            pygame.display.update() #更新画面
        #***********************************************************************
        

def main():

    # 连接服务器
    client = socket.socket() # 服务端为tcp方式，客户端也采用tcp方式  默认参数即为tcp
    client.connect(ip_port)
    # 接收服务器返回的消息，可能有两种情况：["WaitForAnotherPlayer", "WaitStart"]
    client.settimeout(None) #阻塞模式
    data = client.recv(BUFSIZ)

    if data.decode() == "WaitForAnotherPlayer": # 另一个玩家还没有上线的情况
        player_id = 1 # 由于先连接上，称为玩家1
    else:
        assert data.decode() == "WaitStart"
        player_id = 2
    playProcess(client, player_id)

    # 执行到这里，说明已从playProcess中退出，说明已经关闭了窗口，此时需要先把客户端连接关掉，再退出程序
    client.close() #关闭客户端
    sys.exit() # 退出程序

        

if __name__ == '__main__':
    main()