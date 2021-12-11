from collections import deque

"""
服务器给用户发的消息的总格式：
[Snake类encoding_str / none]#[Food类encoding_str / none]#[Score类encoding_str / none]#[Status类encoding_str / none]
（无中括号，某个类如果无信息就用none填充）

用户给服务器发的消息只有方向信息：
Direction类encoding_str
"""


class Snake():
    '''
    蛇所对应的deque:
    蛇1：deque[(x0,y0),(x1,y1),...]
    蛇1方向：(dx,dy)：可以是(0,1), (0,-1), (-1,0), (1,0)
    蛇2：deque[(x0,y0),(x1,y1),...]
    蛇2方向：(dx,dy)：可以是(0,1), (0,-1), (-1,0), (1,0)
    编码形式：
    snake:x0,y0|x1,y1...*dx,dy+x0,y0|x1,y1...*dx,dy
    '''
    def __init__(self, snake_1: deque, direct_1: tuple, snake_2: deque, direct_2: tuple):
        self.snake_1 = snake_1
        self.direct_1 = direct_1
        self.snake_2 = snake_2
        self.direct_2 = direct_2

    def encoding(self, encode=False):
        encoding_str = "snake:"
        q = self.snake_1.copy()
        while len(q):
            pos = q[0]
            encoding_str += str(pos[0]) + ',' + str(pos[1])
            q.popleft()
            if len(q):
                encoding_str += '|'
        encoding_str += '*'
        encoding_str += str(self.direct_1[0]) + ',' + str(self.direct_1[1])
        encoding_str += '+'
        q = self.snake_2.copy()
        while len(q):
            pos = q[0]
            encoding_str += str(pos[0]) + ',' + str(pos[1])
            q.popleft()
            if len(q):
                encoding_str += '|'
        encoding_str += '*'
        encoding_str += str(self.direct_2[0]) + ',' + str(self.direct_2[1])
        if encode:
            encoding_str = encoding_str.encode()
        return encoding_str

    @staticmethod
    def decoding(encoding_str): #注意参数不加self
        if type(encoding_str) == bytes:
            encoding_str = encoding_str.decode()
        snake_1 = deque()
        snake_2 = deque()
        tmp_list = encoding_str.split(':')
        assert tmp_list[0] == 'snake'
        snake_info_list = tmp_list[1].split('+')
        snake_list = [i.split('*')[0] for i in snake_info_list]
        direct_list = [i.split('*')[1] for i in snake_info_list]

        pos_list = snake_list[0].split('|')
        for pos in pos_list:
            x, y = [int(i) for i in pos.split(',')]
            snake_1.append((x, y))
        pos_list = snake_list[1].split('|')
        for pos in pos_list:
            x, y = [int(i) for i in pos.split(',')]
            snake_2.append((x, y))
        dx, dy = [int(i) for i in direct_list[0].split(',')]
        direct_1 = (dx, dy)
        dx, dy = [int(i) for i in direct_list[1].split(',')]
        direct_2 = (dx, dy)

        return snake_1, direct_1, snake_2, direct_2


class Food():
    '''
    食物信息：(x, y), t（t为类型(0/1/2)，在本地可以存储类型对应的颜色以及分数）
    编码形式：
    food:x,y|t
    '''
    def __init__(self, food: tuple, style: int):
        self.food = food
        self.style = style

    def encoding(self, encode=False):
        encoding_str = "food:" + str(self.food[0]) + ',' + str(self.food[1]) + '|' + str(self.style)
        if encode:
            encoding_str = encoding_str.encode()
        return encoding_str

    @staticmethod
    def decoding(encoding_str):
        if type(encoding_str) == bytes:
            encoding_str = encoding_str.decode()
        tmp_list = encoding_str.split(':')
        assert tmp_list[0] == 'food'
        term_list = tmp_list[1].split('|')
        x, y = [int(i) for i in term_list[0].split(',')]
        pos = (x, y)
        style = int(term_list[1])
        return pos, style


class Score():
    '''
    分数以及等级（可以按照当前玩家，对面玩家的顺序传“x,x,x,x”（分别是玩家1分数，玩家1等级，玩家2分数，玩家2等级））
    分数、等级信息：(self_score, self_level, oppo_score, oppo_level)
    编码形式：
    score:s_1,l_1,s_2,l_2
    '''
    def __init__(self, score: tuple):
        self.score = score

    def encoding(self, encode=False):
        encoding_str = "score:"
        for i in range(len(self.score) - 1):
            encoding_str += (str(self.score[i]) + ',')
        encoding_str += str(self.score[-1])
        if encode:
            encoding_str = encoding_str.encode()
        return encoding_str

    def decoding(encoding_str):
        if type(encoding_str) == bytes:
            encoding_str = encoding_str.decode()
        tmp_list = encoding_str.split(':')
        assert tmp_list[0] == 'score'
        s_1, l_1, s_2, l_2 = [int(i) for i in tmp_list[1].split(',')]
        return (s_1, l_1, s_2, l_2)



class Status():
    '''
    游戏是否结束"continue"/"over"，玩家1/2是否在游戏结束时还活着"alive"/"dead"
    finish: True/False
    alive: True/False, True/False
    编码形式：
    status:continue|alive,dead
    '''
    def __init__(self, finish: bool, alive=(False, False)):
        self.finish = finish
        self.alive = alive

    def encoding(self, encode=False):
        encoding_str = "status:"
        if self.finish == False:
            encoding_str += 'continue|'
        else:
            encoding_str += 'over|'
        result_1 = 'alive' if self.alive[0] else "dead"
        result_2 = 'alive' if self.alive[1] else "dead"
        encoding_str += result_1 + ',' + result_2
        if encode:
            encoding_str = encoding_str.encode()
        return encoding_str

    def decoding(encoding_str):
        if type(encoding_str) == bytes:
            encoding_str = encoding_str.decode()
        tmp_list = encoding_str.split(':')
        status_list = tmp_list[1].split('|')
        finish = False if status_list[0]=="continue" else True
        result_1, result_2 = status_list[1].split(',')
        result_1 = True if result_1=="alive" else False
        result_2 = True if result_2=="alive" else False
        return finish, (result_1, result_2)


class Direction():
    '''
    用户对应的蛇的新方向：
    (dx,dy)
    编码形式：
    direction:dx,dy
    '''
    def __init__(self, direct: tuple):
        self.direct = direct

    def encoding(self, encode=False):
        encoding_str = "direction:" + str(self.direct[0]) + ',' + str(self.direct[1])
        if encode:
            encoding_str = encoding_str.encode()
        return encoding_str

    def decoding(encoding_str):
        if type(encoding_str) == bytes:
            encoding_str = encoding_str.decode()
        tmp_list = encoding_str.split(':')
        assert tmp_list[0] == 'direction'
        dx, dy = [int(i) for i in tmp_list[1].split(',')]
        return (dx, dy)



if __name__ == '__main__':
    SCREEN_WIDTH = 600      # 屏幕宽度
    SCREEN_HEIGHT = 480     # 屏幕高度
    SIZE = 20               # 小方格大小
    LINE_WIDTH = 1          # 网格线宽度
    # 游戏区域的坐标范围
    SCOPE_X = (0, SCREEN_WIDTH // SIZE - 1)
    SCOPE_Y = (2, SCREEN_HEIGHT // SIZE - 1)

    # snake_1 = deque()
    # snake_2 = deque()

    # snake_1.append((2, SCOPE_Y[0]))
    # snake_1.append((1, SCOPE_Y[0]))
    # snake_1.append((0, SCOPE_Y[0]))
    # # snake.pop() #删掉的是(0,2) 即从后端删掉
    # # snake.popleft() #删去队首
    # snake_2.append((2, SCOPE_Y[1]))
    # snake_2.append((1, SCOPE_Y[1]))
    # snake_2.append((0, SCOPE_Y[1]))

    # direct_1 = ((0, 1))
    # direct_2 = ((0, -1))

    # print(snake_1, direct_1, snake_2, direct_2)
    # snake_class = Snake(snake_1, direct_1, snake_2, direct_2)
    # snake_encoding_str = snake_class.encoding()
    # print(snake_encoding_str)
    # print(Snake.decoding(snake_encoding_str))

    # print(snake_1, snake_2)


    # food = (2, 3)
    # style = 0
    # food_class = Food(food, style)
    # food_encoding_str = food_class.encoding()
    # print(food_encoding_str)
    # print(Food.decoding(food_encoding_str)[0], Food.decoding(food_encoding_str)[1])


    # score = (100, 2, 60, 1)
    # score_class = Score(score)
    # score_encoding_str = score_class.encoding()
    # print(score_encoding_str)
    # print(Score.decoding(score_encoding_str))

    finish = True
    alive_1, alive_2 = True, False
    status_class = Status(finish, (alive_1, alive_2))
    status_encoding_str = status_class.encoding()
    print(status_encoding_str)
    print(Status.decoding(status_encoding_str))

    # direct = (0, -1)
    # direction_class = Direction(direct)
    # direction_encoding_str = direction_class.encoding()
    # print(direction_encoding_str)
    # print(Direction.decoding(direction_encoding_str))