'''
这个文件是主要开发文件，涵盖了策略全部的四个接口
-on_event接收比赛状态变化的信息。
    参数event_type type表示事件类型；
    参数EventArgument表示该事件的参数，如果不含参数，则为NULL。
-get_team_info控制队名。
    修改返回值的字符串即可修改自己的队名
-get_instruction控制5个机器人的轮速(leftspeed,rightspeed)，以及最后的reset(1即表明需要reset)
    通过返回值来给机器人赋轮速
    比赛中的每拍被调用，需要策略指定轮速，相当于旧接口的Strategy。
    参数field为In/Out参数，存储当前赛场信息，并允许策略修改己方轮速。
    ！！！所有策略的开发应该在此模块
-get_placement控制5个机器人及球在需要摆位时的位置
    通过返回值来控制机器人和球的摆位。
    每次自动摆位时被调用，需要策略指定摆位信息。
    定位球类的摆位需要符合规则，否则会被重摆
'''
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

tickBeginPenalty = 0
tickBeginGoalKick = 0
lastBallx = -110 + 77.5
lastBally = -50 + 57.5
BallPos = [Vector2(0, 0)] * 100000
resetHistoryRecord = False
newMatch = False

# 打印比赛状态，详细请对比v5rpc.py
@unbox_event
def on_event(event_type: int, args: EventArguments):
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
    if event_type == 0:
        race_state = args.judge_result.type
        race_state_trigger = args.judge_result.offensive_team
        if race_state == JudgeResultEvent.ResultType.PenaltyKick:
            print("Penalty Kick")


        actor = {
            Team.Self: lambda: print("By Self"),
            Team.Opponent: lambda: print("By Opp"),
            Team.Nobody: lambda: print("By Nobody"),
        }
        actor[race_state_trigger]()

    event[event_type]()


@unbox_int
def get_team_info(server_version: int) -> str:
    version = {
        0: "V1.0",
        1: "V1.1"
    }
    print(f'server rpc version: {version.get(server_version, "V1.0")}')
    global newMatch
    newMatch = True
    return '天山distance'# 在此行修改双引号中的字符串为自己的队伍名



def strategy_penalty(field):
    football_now_x = field.ball.position.x
    football_now_y = field.ball.position.y
    futureBallx = 4 * football_now_x - 3 * BallPos[GlobalVariable.tick - 1].x
    futureBally = 4 * football_now_y - 3 * BallPos[GlobalVariable.tick - 1].y
    global tickBeginPenalty
    global race_state_trigger
    if race_state_trigger == Team.Self:
        for i in range(0, 5):
            baseRobots[i].set_wheel_velocity(125, 125)
        if GlobalVariable.tick - tickBeginPenalty <= 12:
            baseRobots[1].set_wheel_velocity(120, 120)
            #baseRobots[1].set_wheel_velocity(125, 105)
        elif GlobalVariable.tick - tickBeginPenalty <= 35:
            baseRobots[1].set_wheel_velocity(100, 100)
            #baseRobots[1].set_wheel_velocity(125, 125)
        else:
            #baseRobots[1].set_wheel_velocity(123, 122)
            baseRobots[1].throw_ball(football_now_x, football_now_y)

    if race_state_trigger == Team.Opponent:
        if GlobalVariable.tick - tickBeginPenalty <= 40:
            for i in range(0, 5):
                baseRobots[0].set_wheel_velocity(0, 0)
                baseRobots[1].set_wheel_velocity(120, 125)
                baseRobots[2].set_wheel_velocity(119, 125)
                baseRobots[3].set_wheel_velocity(115, 115)
                baseRobots[4].set_wheel_velocity(115, 115)
            if GlobalVariable.tick - tickBeginPenalty <= 1:
                baseRobots[0].throw_ball(football_now_x, football_now_y)
            else:
                baseRobots[0].throw_ball(football_now_x, football_now_y)
        else:
            baseRobots[1].set_wheel_velocity(0, 0)
            baseRobots[2].set_wheel_velocity(0, 0)
            baseRobots[3].set_wheel_velocity(0, 0)
            baseRobots[4].set_wheel_velocity(0, 0)


@unbox_field
def get_instruction(field: Field):
    # python start.py 20000    print(field.tick)  # tick从2起始
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

    football_now_x = -field.ball.position.x   # 黄方假设，球坐标取反
    football_now_y = -field.ball.position.y

    field.ball.position.x = -field.ball.position.x
    field.ball.position.y = -field.ball.position.y

    global BallPos
    BallPos[GlobalVariable.tick] = Vector2(football_now_x, football_now_y)
    if resetHistoryRecord is True:
        for i in range(GlobalVariable.tick, GlobalVariable.tick - 11, -1):
            BallPos[i] = Vector2(football_now_x, football_now_y)

    strategy_penalty(field)


    for i in range(0, 5):
        baseRobots[i].save_last_information(football_now_x, football_now_y)
    data_loader.set_tick_state(GlobalVariable.tick, race_state)
    resetHistoryRecord = False

    velocity_to_set = []
    for i in range(0, 5):
        velocity_to_set.append((baseRobots[i].robot.wheel.left_speed, baseRobots[i].robot.wheel.right_speed))

    return velocity_to_set, 0    # 以第二元素的(0,1)表明重置开关,1表示重置


@unbox_field
def get_placement(field: Field) -> List[Tuple[float, float, float]]:
    final_set_pos: List[Union[Tuple[int, int, int], Tuple[float, float, float]]]
    global resetHistoryRecord
    resetHistoryRecord = True
    if race_state == JudgeResultEvent.ResultType.PenaltyKick:
        global tickBeginPenalty
        tickBeginPenalty = field.tick
        if race_state_trigger == Team.Self:
            print("点球进攻摆位")
            set_pos = [[80, 0, 0],
                       [-5, 15, 0],
                       [-7, 20, 0],
                       [-50, 8, 0],
                       [0, -15, 0],
                       [5, 10, 0]]
        else:   # if race_state_trigger == Team.Opponent:
            print("点球防守摆位")
            set_pos = [[-75, 0, -35],
                       [9, -25, -137],
                       [9, -15, -136],
                       [9, 15, 135],
                       [9, 25, 134],
                       [5, 10, 0]]
    else:
            set_pos = [[-90, 0, 90],
                   [10, 20, -90],
                   [10, -20, -90],
                   [10, 40, -90],
                   [10, -40, -90],
                   [0.0, 0.0, 0.0]]
    print("race_state = " + str(race_state))

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
                     (set_pos[5][0], set_pos[5][1], set_pos[5][2])]

    print(final_set_pos)
    return final_set_pos  # 最后一个是球位置（x,y,角）,角其实没用