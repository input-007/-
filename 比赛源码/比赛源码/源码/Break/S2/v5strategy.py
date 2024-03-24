import random
from typing import Tuple, Union

from V5RPC import *
import math
from baseRobot import *
from GlobalVariable import *
baseRobots = []# 定义我方机器人数组
oppRobots = []# 定义对方机器人数组
data_loader = DataLoader()
race_state = -1  # 定位球状态
race_state_trigger = -1    # 触发方

add_len=6
dec_len=-6

tickBeginBreakThrough = 0
tickBeginPenalty = 0
tickBeginGoalKick = 0
lastBallx = -110 + 37.5
lastBally = 0
BallPos = [Vector2(0, 0)] * 100000
resetHistoryRecord = False
newMatch = False
# 接收比赛状态变化的信息
@unbox_event
def on_event(event_type: int, args: EventArguments):
    # 打印当前状态，event表示比赛进入哪一阶段，比如暂停，上半场，下半场等等
    event = {
        0: lambda: print(args.judge_result.reason),
        1: lambda: print("Match Start"),
        2: lambda: print("Match Stop"),
        3: lambda: print("First Half Start"),
        4: lambda: print("Second Half Start"),
        5: lambda: print("Overtime Start"),
        6: lambda: print("Penalty Shootout Start"),
        7: lambda: print("MatchShootOutStart"),
        8: lambda: print("MatchBlockStart")
    }
    global race_state_trigger
    global race_state
    # 比赛进行过程中，打印当前状态，由于是点球大战策略，所以只打印点球状态，并打印出发球方
    if event_type == 0:
        race_state = args.judge_result.type
        race_state_trigger = args.judge_result.offensive_team
        if race_state == JudgeResultEvent.ResultType.PlaceKick:
            print("PlaceKick")
        actor = {
            Team.Self: lambda: print("By Self"),
            Team.Opponent: lambda: print("By Opp"),
            Team.Nobody: lambda: print("By Nobody"),
        }
        actor[race_state_trigger]()

    event[event_type]()


@unbox_int
# 控制队名。可以在合法合理的范围内把返回值改成任意你喜欢的队名，其他几行不用管
def get_team_info(server_version: int) -> str:
    version = {
        0: "V1.0",
        1: "V1.1"
    }
    print(f'server rpc version: {version.get(server_version, "V1.0")}')
    return '天山distance'


def strategy(field: Field, football_now_x, football_now_y):
    delay=3
    arrvie=0    #是否有球员进入
    global tickBeginBreakThrough
    if race_state == JudgeResultEvent.ResultType.PlaceKick:
        if race_state_trigger == Team.Self:
            # baseRobots[0].moveto(110, -15)
            # baseRobots[1].moveto(110, 15)
            baseRobots[1].moveto(110, -15)
            baseRobots[0].moveto(110, 15)
            avoidroads(field, 110, 15, 110, -15)
            for i in range(0, 2):
                if baseRobots[i].get_pos().x > 111 and (baseRobots[i].get_pos().y < 20 ):
                    # or baseRobots[i].get_pos().y>(-20)):
                    # # baseRobots[i].set_wheel_velocity(0, 0)
                    # if i==0:
                    #     arrvie = 0
                    # if i == 1:
                    #     arrvie = 1
                    # if arrvie!=-1:
                    #     baseRobots[i].moveto(115, 15 * (-1) ^ (-i))
                    #     delay-=1
                    #     if delay==0:
                            baseRobots[i].set_wheel_velocity(0, 0)
                        # baseRobots[i].pid_moveto = PID(1, 4, 2.2)
                        # baseRobots[i].pid_angle = PID(2, 0, 4.2)
                    # baseRobots[i].moveto(115, 15*(-1)^(i))
                if baseRobots[arrvie].get_pos().x<105:
                    baseRobots[arrvie].pid_moveto = PID(1.9, 0, 2.2)
                    baseRobots[arrvie].pid_angle = PID(2, 0, 4.2)

                if (field.tick - tickBeginBreakThrough >= 100 and
                    math.fabs(baseRobots[i].HistoryInformation[5].position.x - baseRobots[i].get_pos().x) < 10 and
                    ((baseRobots[i].get_pos().x - oppRobots[0].get_pos().x <8.2 and baseRobots[i].get_pos().x - oppRobots[0].get_pos().x >3)
                     or(baseRobots[i].get_pos().x - oppRobots[1].get_pos().x <8.2 and baseRobots[i].get_pos().x - oppRobots[0].get_pos().x >3))):
                    if baseRobots[i].robot.rotation > 0:
                        baseRobots[i].set_wheel_velocity(120, -125)
                    else:
                        baseRobots[i].set_wheel_velocity(-125, 120)
                if baseRobots[i].get_pos().x - oppRobots[0].get_pos().x <0 and baseRobots[i].get_pos().x - oppRobots[1].get_pos().x <0 :
                    if i==0:
                        baseRobots[0].moveto(110, -15)
                    elif i==1:
                        baseRobots[1].moveto(110, 15)


    if race_state_trigger == Team.Opponent:

        # baseRobots[0].moveto(oppRobots[0].get_pos().x, oppRobots[0].get_pos().y)

        baseRobots[0].moveto(baseRobots[0].get_pos().x+1, oppRobots[0].get_pos().y+2)
        baseRobots[1].moveto(baseRobots[1].get_pos().x, oppRobots[0].get_pos().y-2)



def avoidroads(field: Field, tarx0, tary0, tarx1, tary1):
    future_time = 14
    futureRobotX = future_time * baseRobots[0].get_pos().x - (future_time - 1) * baseRobots[0].get_last_pos().x
    futureRobotY = future_time * baseRobots[0].get_pos().y - (future_time - 1) * baseRobots[0].get_last_pos().y
    futureOpp0X = future_time * oppRobots[0].get_pos().x - (future_time - 1) * oppRobots[0].get_last_pos().x
    futureOpp0Y = future_time * oppRobots[0].get_pos().y - (future_time - 1) * oppRobots[0].get_last_pos().y
    futureOpp1X = future_time * oppRobots[1].get_pos().x - (future_time - 1) * oppRobots[1].get_last_pos().x
    futureOpp1Y  = future_time * oppRobots[1].get_pos().y - (future_time - 1) * oppRobots[1].get_last_pos().y
    len = 5
    if oppRobots[0].get_pos().x > baseRobots[0].get_pos().x and oppRobots[0].get_pos().x < tarx0 :
        if baseRobots[0].get_pos().y > 0:
            if futureOpp0Y + len > baseRobots[0].get_pos().y:
                baseRobots[0].moveto(tarx0, tary0 + add_len)
                print("0-1")
        if baseRobots[0].get_pos().y < 0:
            if futureOpp0Y - len < baseRobots[0].get_pos().y:
                baseRobots[0].moveto(tarx0, tary0 + dec_len)
                print("0-2")

    if oppRobots[1].get_pos().x > baseRobots[0].get_pos().x and oppRobots[1].get_pos().x < tarx0 :
        if baseRobots[0].get_pos().y > 0:
            if futureOpp1Y + len > baseRobots[0].get_pos().y:
                baseRobots[0].moveto(tarx0, tary0 + add_len)
                print("0-3")
        if baseRobots[0].get_pos().y < 0:
            if futureOpp1Y - len < baseRobots[0].get_pos().y:
                baseRobots[0].moveto(tarx0, tary0 + dec_len)
                print("0-4")

    if oppRobots[0].get_pos().x > baseRobots[1].get_pos().x and oppRobots[0].get_pos().x < tarx1 :
        if baseRobots[1].get_pos().y > 0:
            if futureOpp0Y + len > baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + add_len)
                print("1-1")
        if baseRobots[1].get_pos().y < 0:
            if futureOpp0Y - len < baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + dec_len)
                print("1-2")

    if oppRobots[1].get_pos().x > baseRobots[1].get_pos().x and oppRobots[1].get_pos().x < tarx1 :
        if baseRobots[1].get_pos().y > 0:
            if futureOpp1Y + len > baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + add_len)
                print("1-3")
        if baseRobots[1].get_pos().y < 0:
            if futureOpp1Y - len < baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + dec_len)
                print("1-4")




# python start.py 20001
@unbox_field
def get_instruction(field: Field):
    # python start.py 20000pytprint(field.tick)  # tick从2起始
    GlobalVariable.tick = field.tick
    global resetHistoryRecord
    for i in range(0, 5):
        baseRobots.append(BaseRobot())
        oppRobots.append(BaseRobot())
        baseRobots[i].update(field.self_robots[i], resetHistoryRecord)
        oppRobots[i].update(field.opponent_robots[i], resetHistoryRecord)
        global newMatch
        if field.tick == 2: #newMatch is True:
            for j in range(0, 8):
                baseRobots[i].HistoryInformation[j] = field.self_robots[i].copy()   # 第0拍主动维护历史数据
                baseRobots[i].PredictInformation[j] = field.self_robots[i].copy()	# 第0拍主动维护预测数据
            newMatch = False
        baseRobots[i].PredictRobotInformation(4)#(GlobalVariable.tick_delay)
    print("brngvvvvvv")
    football_now_x = -field.ball.position.x   # 黄方假设，球坐标取反
    football_now_y = -field.ball.position.y

    field.ball.position.x = -field.ball.position.x
    field.ball.position.y = -field.ball.position.y
    print("brng00000")
    strategy(field, football_now_x, football_now_y)

    print("brng5555")
    for i in range(0, 5):
        baseRobots[i].save_last_information(football_now_x, football_now_y)
        oppRobots[i].save_last_information(football_now_x, football_now_y)
    data_loader.set_tick_state(GlobalVariable.tick, race_state)
    resetHistoryRecord = False
    print("brngffffffff")
    velocity_to_set = []
    for i in range(0, 5):
        velocity_to_set.append((baseRobots[i].robot.wheel.left_speed, baseRobots[i].robot.wheel.right_speed))
    return velocity_to_set, 0    # 以第二元素的(0,1)表明重置开关,1表示重置


@unbox_field
def get_placement(field: Field) -> List[Tuple[float, float, float]]:
    final_set_pos: List[Union[Tuple[int, int, int], Tuple[float, float, float]]]
    global tickBeginBreakThrough
    tickBeginBreakThrough = field.tick
    if race_state == JudgeResultEvent.ResultType.PlaceKick:
        if race_state_trigger == Team.Self:
            print("开球进攻摆位")
            set_pos = [[-103, 20, 0],       #base0
                       [-103, -20, 0],      #base1
                       [-3, -10, 0],
                       [-3, 10, 0],
                       [-3, 0, 0],
                       [0.0, 0.0, 0.0]]
            # set_pos = [(-103, 0, 90), (30, 0, 0), (-3, -10, 0), (-3, 10, 0), (-3, 0, 0), (0.0, 0.0, 0.0)]
        else:   # if race_state_trigger == Team.Opponent:
            print("开球防守摆位")
            set_pos = [[-80, -10, 0],
                       [-80, 10, 0],
                       [-10, -80, -90],
                       [-10, 70, -90],
                       [-10, -80, -90],
                       [0.0, 0.0, 0.0]]
            # set_pos = [(-105, 0, 90), (10, 20, -90), (10, -20, -90), (10, 40, -90), (10, -40, -90), (0.0, 0.0, 0.0)]
    else:
        set_pos = [[-100, 20, 90],
                   [10, 20, -90],
                   [10, -20, -90],
                   [10, 40, -90],
                   [10, -40, -90],
                   [0.0, 0.0, 0.0]]

    for set_pos_s in set_pos:     # 摆位反转
        set_pos_s[0] = -set_pos_s[0]
        set_pos_s[1] = -set_pos_s[1]
        set_pos_s[2] -= 180
        if set_pos_s[2] < -180:
            set_pos_s[2] += 360

    final_set_pos = [(set_pos[0][0], set_pos[0][1], set_pos[0][2]),
                     (set_pos[1][0], set_pos[1][1], set_pos[1][2]),
                     (set_pos[2][0], set_pos[2][1], set_pos[2][2]),
                     (set_pos[3][0], set_pos[3][1], set_pos[3][2]),
                     (set_pos[4][0], set_pos[4][1], set_pos[4][2]),
                     (0.0, 0.0, 0.0)]

    print(final_set_pos)
    return final_set_pos  # 最后一个是球位置（x,y,角）,角其实没用
