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
mark = 1    #防守方
tickBeginPenalty = 0
tickBeginGoalKick = 0
lastBallx = -110 + 37.5
lastBally = 0
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
        if race_state == JudgeResultEvent.ResultType.PlaceKick:
            print("Place Kick")
        elif race_state == JudgeResultEvent.ResultType.PenaltyKick:
            print("Penalty Kick")
        elif race_state == JudgeResultEvent.ResultType.GoalKick:
            print("Goal Kick")
        elif (race_state == JudgeResultEvent.ResultType.FreeKickLeftBot
              or race_state == JudgeResultEvent.ResultType.FreeKickRightBot
              or race_state == JudgeResultEvent.ResultType.FreeKickLeftTop
              or race_state == JudgeResultEvent.ResultType.FreeKickRightTop):
            print("Free Kick")

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

min_x=85
# 策略行为主函数，可将以下函数用策略模式封装
def strategy_common(field):
    # 最基本最常规情况下的执行策略
    # 假设黄方，给三个机器人限制活动范围
    global min_x
    football_now_x = field.ball.position.x
    football_now_y = field.ball.position.y
    futureBallx = 8 * football_now_x - 7 * BallPos[GlobalVariable.tick - 1].x
    futureBally = 8 * football_now_y - 7 * BallPos[GlobalVariable.tick - 1].y

    if football_now_x or futureBallx<-95:
        print("mmmmmmmmmmmmmmmmmmmmmm")
    if football_now_x>-75 and abs(futureBally)>20 and futureBallx>-110:
        for i in range (1,5):
            if (min(np.fabs(baseRobots[i].get_pos().y-oppRobots[1].get_pos().y),np.fabs(baseRobots[i].get_pos().y-oppRobots[2].get_pos().y),
                    np.fabs(baseRobots[i].get_pos().y-oppRobots[3].get_pos().y),np.fabs(baseRobots[i].get_pos().y-oppRobots[4].get_pos().y)
                    )<=10):
                # if i==1:
                if i == 1 and futureBallx > football_now_x and futureBallx > -95:
                     baseRobots[1].shoot(futureBallx, futureBally)# 1号机器人x不超过80的情况下追球（前锋）
                if i == 2 and futureBallx>football_now_x and futureBallx>-95:
                     baseRobots[2].moveto_within_x_limits(-min_x, -12, futureBallx, futureBally)# 2号机器人x不超过-12的情况下追球（后卫）
                if i == 3 and futureBallx>football_now_x and futureBallx>-95:
                     baseRobots[3].moveto_within_x_limits(-min_x, 5, futureBallx, futureBally)# 3号机器人x不超过5的情况下追球（中场）
                if i == 4 and futureBallx>football_now_x and futureBallx>-95:
                     baseRobots[4].moveto(futureBallx, futureBally)# 4号自由人追球
                     if football_now_x>0:
                        baseRobots[4].shoot(futureBallx, futureBally)
                     if football_now_x <=-95 or futureBallx <=-95:
                         baseRobots[4].moveto(futureBallx+20, futureBally)
                     elif football_now_x <= -95 and baseRobots[4].get_pos().x <= -95:
                         baseRobots[4].moveto(futureBallx + 20, futureBally)
            elif min(np.fabs(baseRobots[i].get_pos().y-oppRobots[1].get_pos().y),np.fabs(baseRobots[i].get_pos().y-oppRobots[2].get_pos().y),
                    np.fabs(baseRobots[i].get_pos().y-oppRobots[3].get_pos().y),np.fabs(baseRobots[i].get_pos().y-oppRobots[4].get_pos().y)
                    )>10 and futureBallx>football_now_x:
                if i==1 and abs(football_now_x-baseRobots[1].get_pos().x)<60:
                    baseRobots[1].shoot(futureBallx, futureBally)
                if i==2 and abs(football_now_x-baseRobots[1].get_pos().x)<50:
                     baseRobots[2].shoot(futureBallx, futureBally)# 2号机器人x不超过-12的情况下追球（后卫）
                if i == 3 and abs(football_now_x-baseRobots[1].get_pos().x)<40:
                     baseRobots[3].shoot(futureBallx, futureBally)# 3号机器人x不超过5的情况下追球（中场）
                if i == 4:
                    baseRobots[4].shoot(futureBallx, futureBally)  # 4号自由人追球
                    if football_now_x <= -95 or futureBallx <=-95:
                        baseRobots[4].moveto(futureBallx + 20, futureBally)
                    elif football_now_x <= -95 and baseRobots[4].get_pos().x <= -95:
                        baseRobots[4].moveto(futureBallx + 20, futureBally)
            else:
                baseRobots[2].moveto_within_x_limits(-min_x, -12, futureBallx, futureBally)
                baseRobots[3].moveto_within_x_limits(-min_x, 5, futureBallx, futureBally)


        avoidroads(field,futureBallx, futureBally,futureBallx, futureBally)
        if baseRobots[1].get_pos().x>=80:
            baseRobots[1].shoot(futureBallx, futureBally)
    # elif abs(football_now_y)<20 and futureBallx<-100:
    else:
        # for i in range(1,5):
        baseRobots[1].moveto_within_x_limits(-min_x, -12, -50, futureBally+10)
        baseRobots[4].moveto_within_x_limits(-min_x, -12, -50, futureBally-10)
        baseRobots[2].moveto_within_x_limits(-min_x, -12, futureBallx, futureBally)
        baseRobots[3].moveto_within_x_limits(-min_x, 5, futureBallx, futureBally)

    for i in range(1,5):
        if baseRobots[i].get_pos().x<=-90 and abs(baseRobots[i].get_pos().y)<=20:
            if i==1:
                baseRobots[1].moveto(futureBallx + 20, futureBally)
            if i == 4:
                baseRobots[4].moveto(futureBallx + 20, futureBally)
            if i == 2:
                baseRobots[2].moveto(futureBallx + 20, futureBally)
            if i == 3:
                baseRobots[3].moveto(futureBallx + 20, futureBally)
    for i in range(1,5):
        if football_now_x <= -95 and baseRobots[4].get_pos().x <= -95:
            if i == 1:
                baseRobots[1].moveto_within_x_limits(-min_x, -12, -50, futureBally + 10)
            if i == 4:
                baseRobots[4].moveto_within_x_limits(-min_x, -12, -50, futureBally - 10)
            if i == 2:
                baseRobots[2].moveto_within_x_limits(-min_x, -12, futureBallx, futureBally)
            if i == 3:
                baseRobots[3].moveto_within_x_limits(-min_x, 5, futureBallx, futureBally)


    # 防止四人大禁区
    # 一旦大禁区里面有两个非门将球员，则其余就近出去，即使本来就在外面也无所谓，当防守了
    num_in_big_area = 0
    dis = [-1, -1, -1, -1, -1]	# -1 表示不在禁区里面
    for i in range(1, 5):
        if baseRobots[i].get_pos().x < -77 and np.fabs(baseRobots[i].get_pos().y) < 50:	#禁区内机器人计数且计算距离，禁区外距离为负
            num_in_big_area += 1
            dis[i] = min(np.fabs(-72.5 - baseRobots[i].get_pos().x), np.fabs(np.fabs(baseRobots[i].get_pos().y) - 40))
    if num_in_big_area >= 2:
        out_robot1 = 1
        out_robot2 = 2
        for i in range(1, 5):
            if dis[i] < dis[out_robot1]:
                out_robot2 = out_robot1
                out_robot1 = i
            elif dis[i] < dis[out_robot2]:
                out_robot2 = i
        if dis[out_robot1] == np.fabs(baseRobots[out_robot1].get_pos().x + 72.5):
            baseRobots[out_robot1].moveto(-65, baseRobots[out_robot1].get_pos().y)
        elif np.fabs(baseRobots[out_robot1].get_pos().y > 0):
            baseRobots[out_robot1].moveto(baseRobots[out_robot1].get_pos().x, 50)
        else:
            baseRobots[out_robot1].moveto(baseRobots[out_robot1].get_pos().x, -50)

        if dis[out_robot2] == np.fabs(baseRobots[out_robot2].get_pos().x + 72.5):
            baseRobots[out_robot2].moveto(-65, baseRobots[out_robot2].get_pos().y)
        elif np.fabs(baseRobots[out_robot2].get_pos().y > 0):
            baseRobots[out_robot2].moveto(baseRobots[out_robot2].get_pos().x, 50)
        else:
            baseRobots[out_robot2].moveto(baseRobots[out_robot2].get_pos().x, -50)

    if baseRobots[0].get_pos().x <= -110 + 2.4:
        baseRobots[0].moveto(-110 + 1.5, 0)
    else:
        if np.fabs(football_now_y) < 50 - 0.7:
            if football_now_x > -110 + 17:
                baseRobots[0].moveto(-110 + 1.6, futureBally)
            else:
                baseRobots[0].moveto(futureBallx, futureBally)
            if math.sqrt(abs(baseRobots[0].get_pos().x-football_now_x)**2+abs(baseRobots[0].get_pos().y-football_now_y)**2)<5 and baseRobots[0].get_pos().x-football_now_x<0:
                baseRobots[0].shoot(futureBallx, futureBally)
        else:
            if football_now_y > 0:
                baseRobots[0].moveto(-110 + 1.6, 20 - 5.2)
            else:
                baseRobots[0].moveto(-110 + 1.6, -(20 - 5.2))

def strategy_goalkick(field):
    football_now_x = field.ball.position.x
    football_now_y = field.ball.position.y
    futureBallx = 4 * football_now_x - 3 * BallPos[GlobalVariable.tick - 1].x
    futureBally = 4 * football_now_y - 3 * BallPos[GlobalVariable.tick - 1].y
    global tickBeginGoalKick
    global race_state_trigger
    if race_state_trigger == Team.Self:
        if GlobalVariable.tick - tickBeginGoalKick <= 45:
            if baseRobots[0].get_pos().x < -5:
                baseRobots[0].set_wheel_velocity(125, 125)
            else:
                baseRobots[0].set_wheel_velocity(125, -125)

        if GlobalVariable.tick - tickBeginGoalKick <= 55:
            for i in range(1, 5):
                baseRobots[i].set_wheel_velocity(125, 125)
        else:
            strategy_common(field)
    if race_state_trigger == Team.Opponent:
        if GlobalVariable.tick - tickBeginGoalKick <= 45:
            if GlobalVariable.tick - tickBeginGoalKick <= 40:
                baseRobots[1].moveto(futureBallx, futureBally)
            else:
                strategy_common(field)
            baseRobots[2].moveto(-40, futureBally-6)
            baseRobots[3].moveto(-40, futureBally )
            baseRobots[4].moveto(-40, futureBally+6)
        else:
            strategy_common(field)
        # python start.py 20001

# global futureBallx
# global futureBally
def strategy_penalty(field):
    football_now_x = field.ball.position.x
    football_now_y = field.ball.position.y
    futureBallx = 4 * football_now_x - 3 * BallPos[GlobalVariable.tick - 1].x
    futureBally = 4 * football_now_y - 3 * BallPos[GlobalVariable.tick - 1].y
    global tickBeginPenalty
    global race_state_trigger
    # mark=1
    # if GlobalVariable.last_score[0] == GlobalVariable.score \
    #         and GlobalVariable.score != 0:  # 没进球，进攻策略更换
    #     GlobalVariable.type[0] += 1
    #
    # if GlobalVariable.score[1] / 2 * mark == 0 \
    #         and GlobalVariable.last_score[1] != GlobalVariable.score[1] \
    #         and GlobalVariable.score[1] != 0:  # 被进球，防守策略更换
    #     GlobalVariable.type[1] += 1
    #     mark += 1
    # print('type0==', GlobalVariable.type[0],'type1==',GlobalVariable.type[1])
    print('kick=',GlobalVariable.tick - tickBeginPenalty)
    if race_state_trigger == Team.Self:     #只有进行一次点球才显示
        # if GlobalVariable.type==1:
        if GlobalVariable.type[0]==1:
            for i in range(0, 5):
                #baseRobots[i].set_wheel_velocity(0, 0)
                baseRobots[i].set_wheel_velocity(0, 0)
            if GlobalVariable.tick - tickBeginPenalty <= 12:
                baseRobots[1].set_wheel_velocity(45, 45)
                baseRobots[3].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginPenalty <= 35:
                baseRobots[1].set_wheel_velocity(0, 0)
                baseRobots[3].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginPenalty <= 60:
                baseRobots[1].set_wheel_velocity(0, 0)
                baseRobots[3].throw_ball(football_now_x, football_now_y)
            else:
                strategy_common(field)

        if GlobalVariable.type[0]==2:
            for i in range(0, 5):
                # baseRobots[i].set_wheel_velocity(0, 0)
                baseRobots[i].set_wheel_velocity(0, 0)
            if GlobalVariable.tick - tickBeginPenalty <= 35:
                baseRobots[1].set_wheel_velocity(35, 35)
            elif GlobalVariable.tick - tickBeginPenalty <= 45:
                baseRobots[1].set_wheel_velocity(0, 0)
            # elif GlobalVariable.tick - tickBeginPenalty <= 60:
            #     baseRobots[1].moveto(oppRobots[0].get_pos().x, oppRobots[0].get_pos().y)
            if GlobalVariable.tick - tickBeginPenalty <= 15:
                # baseRobots[1].set_wheel_velocity(90, 80)
                baseRobots[3].set_wheel_velocity(125, 125)
                baseRobots[4].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginPenalty <= 35:
                # baseRobots[1].set_wheel_velocity(0, 0)
                # baseRobots[1].shoot(futureBallx, futureBally)
                # baseRobots[1].moveto(oppRobots[0].get_pos().x + 3, oppRobots[0].get_pos().y + 3)
                baseRobots[3].set_wheel_velocity(125, 125)
                baseRobots[4].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginPenalty <= 55:
                # baseRobots[1].moveto(oppRobots[0].get_pos().x, oppRobots[0].get_pos().y)
                baseRobots[3].throw_ball(football_now_x, football_now_y)
            else:
                strategy_common(field)
        if GlobalVariable.type[0] == 3:
            for i in range(0, 5):
                # baseRobots[i].set_wheel_velocity(0, 0)
                baseRobots[i].set_wheel_velocity(0, 0)
            if GlobalVariable.tick - tickBeginPenalty <= 35:
                baseRobots[1].set_wheel_velocity(35, 35)
            elif GlobalVariable.tick - tickBeginPenalty <= 45:
                baseRobots[1].set_wheel_velocity(0, 0)
            # elif GlobalVariable.tick - tickBeginPenalty <= 60:
            #     baseRobots[1].moveto(oppRobots[0].get_pos().x, oppRobots[0].get_pos().y)
            if GlobalVariable.tick - tickBeginPenalty <= 15:
                # baseRobots[1].set_wheel_velocity(90, 80)
                baseRobots[3].set_wheel_velocity(125, 125)
                baseRobots[4].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginPenalty <= 35:
                # baseRobots[1].set_wheel_velocity(0, 0)
                # baseRobots[1].shoot(futureBallx, futureBally)
                # baseRobots[1].moveto(oppRobots[0].get_pos().x + 3, oppRobots[0].get_pos().y + 3)
                baseRobots[3].set_wheel_velocity(125, 125)
                baseRobots[4].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginPenalty <= 55:
                # baseRobots[1].moveto(oppRobots[0].get_pos().x, oppRobots[0].get_pos().y)
                baseRobots[3].invthrow_ball(football_now_x, football_now_y)
            else:
                strategy_common(field)

    if race_state_trigger == Team.Opponent:
        if GlobalVariable.type[1]==1:
            if GlobalVariable.tick - tickBeginPenalty <= 60:
                # for i in range(0, 5):
                # baseRobots[0].set_wheel_velocity(0, 0)
                # if GlobalVariable.type[1] == 1:

                if GlobalVariable.tick - tickBeginPenalty <= 60 and football_now_x <= -70 and football_now_y <= 40:
                    baseRobots[0].moveto(futureBallx, futureBally)

                if GlobalVariable.tick - tickBeginPenalty <= 35:
                    baseRobots[1].set_wheel_velocity(120, 125)
                    baseRobots[2].set_wheel_velocity(119, 125)
                    baseRobots[3].set_wheel_velocity(115, 115)
                    baseRobots[4].set_wheel_velocity(115, 115)
                else:
                    for i in range(1,4):
                        baseRobots[i].moveto(0, futureBally+(i-1)*10)
                # if GlobalVariable.tick - tickBeginPenalty <= 17:
                #     baseRobots[0].set_wheel_velocity(95, 100)
                # else:
                #     baseRobots[0].throw_ball(football_now_x, football_now_y)
            else:
                strategy_common(field)

        if GlobalVariable.type[1]==2:
            if GlobalVariable.tick - tickBeginPenalty <= 60 and football_now_x <= -70 and football_now_y <= 40:
                for i in range(0, 5):
                    baseRobots[i].set_wheel_velocity(0, 0)
                baseRobots[0].set_wheel_velocity(125, 125)
            else:
                strategy_common(field)

        # if GlobalVariable.type[1]==GlobalVariable.ALL_Type:
        #     GlobalVariable.type[1]=1

def strategy_PlaceKick(field):
    # baseRobots[i].set_wheel_velocity(0, 0)
    global tickBeginPlaceKick
    global race_state_trigger
    # tickk=GlobalVariable.tick
    football_now_x = field.ball.position.x
    football_now_y = field.ball.position.y
    futureBallx = 8 * football_now_x - 7 * BallPos[GlobalVariable.tick - 1].x
    futureBally = 8 * football_now_y - 7 * BallPos[GlobalVariable.tick - 1].y
    # if GlobalVariable.tick - tickBeginGoalKick < 60:
    # if GlobalVariable.PlaceKick ==0:
    print('placetick=={}'.format(GlobalVariable.tick - tickBeginPlaceKick))
    if race_state_trigger == Team.Self:
        if GlobalVariable.tick - tickBeginPlaceKick<80:
            strategy_common(field)
            if GlobalVariable.tick - tickBeginPlaceKick < 20:
                baseRobots[1].set_wheel_velocity(125, 125)
            elif GlobalVariable.tick - tickBeginGoalKick >= 20:
                baseRobots[1].moveto(futureBallx, futureBally)

            baseRobots[2].moveto(100, 25)
            baseRobots[3].moveto(100, -25)

            if baseRobots[4].get_pos().x < 75:
                baseRobots[4].moveto(100, 0)
            else:
                if oppRobots[0].get_pos().y > 0:
                    baseRobots[4].set_wheel_velocity(125, -125)
                elif oppRobots[0].get_pos().y <= 0:
                    baseRobots[4].set_wheel_velocity(-125, 125)
        else:
            strategy_common(field)

    if race_state_trigger == Team.Opponent:

        strategy_common(field)
        # if GlobalVariable.tick - tickBeginGoalKick<15:
        #     baseRobots[1].moveto(100, 0)
        # elif GlobalVariable.tick - tickBeginGoalKick>=15:
        #     baseRobots[1].moveto(100, 20)
        # if GlobalVariable.tick - tickBeginGoalKick < 60:
        #     baseRobots[1].moveto(-70, futureBally)
        #     if abs(futureBallx-baseRobots[1].get_pos().x)<=9:
        #         baseRobots[1].set_wheel_velocity(-125,125)
        # else:
        #     strategy_common(field)

        baseRobots[2].moveto(football_now_x, football_now_y)
        baseRobots[3].moveto(football_now_x, football_now_y -3)
        baseRobots[4].moveto(futureBallx, futureBally - 3)
        baseRobots[1].moveto(futureBallx, futureBally)
        for i in range(1, 4):
            if math.sqrt(abs(futureBallx - baseRobots[i].get_pos().x) ** 2 + abs(
                    futureBally - baseRobots[i].get_pos().y) ** 2) <= 11:
                baseRobots[i].set_wheel_velocity(125, -125)

        if GlobalVariable.tick - tickBeginGoalKick < 80:
            baseRobots[0].moveto(-70, futureBally)
            if abs(futureBallx - baseRobots[4].get_pos().x) <= 9:
                if futureBally>0:
                    baseRobots[0].set_wheel_velocity(125, -125)
                else:
                    baseRobots[0].set_wheel_velocity(-125, 125)
        if GlobalVariable.tick - tickBeginGoalKick >= 80:
            strategy_common(field)

    # print('placetick=={}'.format(GlobalVariable.tick - tickBeginPlaceKick))
    # else:
    #     strategy_common(field)
        # if baseRobots[4].get_pos().x<70:
        #     baseRobots[4].set_wheel_velocity(100, 100)
        # else:
        #     if oppRobots[0].get_pos().y>0:
        #         baseRobots[4].set_wheel_velocity(125, -125)
        #     elif oppRobots[0].get_pos().y < 0:
        #         baseRobots[4].set_wheel_velocity(-125, 125)

add_len=6
dec_len=-6
base1=1
base2=2
def avoidroads(field: Field, tarx0, tary0, tarx1, tary1):
    future_time = 14
    futureRobotX = future_time * baseRobots[base2].get_pos().x - (future_time - 1) * baseRobots[base2].get_last_pos().x
    futureRobotY = future_time * baseRobots[base2].get_pos().y - (future_time - 1) * baseRobots[base2].get_last_pos().y
    futureOpp0X = future_time * oppRobots[base2].get_pos().x - (future_time - 1) * oppRobots[base2].get_last_pos().x
    futureOpp0Y = future_time * oppRobots[base2].get_pos().y - (future_time - 1) * oppRobots[base2].get_last_pos().y
    futureOpp1X = future_time * oppRobots[1].get_pos().x - (future_time - 1) * oppRobots[1].get_last_pos().x
    futureOpp1Y  = future_time * oppRobots[1].get_pos().y - (future_time - 1) * oppRobots[1].get_last_pos().y
    len = 5
    if oppRobots[base2].get_pos().x > baseRobots[base2].get_pos().x and oppRobots[base2].get_pos().x < tarx0 :
        if baseRobots[base2].get_pos().y > 0:
            if futureOpp0Y + len > baseRobots[base2].get_pos().y:
                baseRobots[base2].moveto(tarx0, tary0 + add_len)
                # print("0-1")
        if baseRobots[base2].get_pos().y < 0:
            if futureOpp0Y - len < baseRobots[base2].get_pos().y:
                baseRobots[base2].moveto(tarx0, tary0 + dec_len)
                # print("0-2")

    if oppRobots[1].get_pos().x > baseRobots[0].get_pos().x and oppRobots[1].get_pos().x < tarx0 :
        if baseRobots[base2].get_pos().y > 0:
            if futureOpp1Y + len > baseRobots[base2].get_pos().y:
                baseRobots[base2].moveto(tarx0, tary0 + add_len)
                # print("0-3")
        if baseRobots[base2].get_pos().y < 0:
            if futureOpp1Y - len < baseRobots[base2].get_pos().y:
                baseRobots[base2].moveto(tarx0, tary0 + dec_len)
                # print("0-4")

    if oppRobots[base2].get_pos().x > baseRobots[1].get_pos().x and oppRobots[base2].get_pos().x < tarx1 :
        if baseRobots[1].get_pos().y > 0:
            if futureOpp0Y + len > baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + add_len)
                # print("1-1")
        if baseRobots[1].get_pos().y < 0:
            if futureOpp0Y - len < baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + dec_len)
                # print("1-2")

    if oppRobots[1].get_pos().x > baseRobots[1].get_pos().x and oppRobots[1].get_pos().x < tarx1 :
        if baseRobots[1].get_pos().y > 0:
            if futureOpp1Y + len > baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + add_len)
                # print("1-3")
        if baseRobots[1].get_pos().y < 0:
            if futureOpp1Y - len < baseRobots[1].get_pos().y:
                baseRobots[1].moveto(tarx1, tary1 + dec_len)
                # print("1-4")


@unbox_field
def get_instruction(field: Field):
    # python start.py 20000    print(field.tick)  # tick从2起始
    GlobalVariable.tick = field.tick
    global resetHistoryRecord
    # print("111111111111")
    # football_now_y = field.ball.position.y

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

    # if field.ball.position.x>110:
    #     GlobalVariable.score[0]+=1
    #     # GlobalVariable.type[1]+=1
    #     # print('score1=',GlobalVariable.score[1])
    # if field.ball.position.x < -110:
    #     GlobalVariable.score[1] += 1
    #     # GlobalVariable.type[0] += 1
    # print('score1=', GlobalVariable.score[1])
    # print('score0=', GlobalVariable.score[0])

    # mark=1
    # if GlobalVariable.last_score[0] == GlobalVariable.score \
    #         and GlobalVariable.score != 0:  # 没进球，进攻策略更换
    #     GlobalVariable.type[0] += 1
    #
    # if GlobalVariable.score[1] / 2 * mark == 0 \
    #         and GlobalVariable.last_score[1] != GlobalVariable.score[1] \
    #         and GlobalVariable.score[1] != 0:  # 被进球，防守策略更换
    #     GlobalVariable.type[1] += 1
    #     mark += 1
    # print('type0==', GlobalVariable.type[0],'type1==',GlobalVariable.type[1])

    global BallPos
    BallPos[GlobalVariable.tick] = Vector2(football_now_x, football_now_y)
    if resetHistoryRecord is True:
        for i in range(GlobalVariable.tick, GlobalVariable.tick - 11, -1):
            BallPos[i] = Vector2(football_now_x, football_now_y)

    if race_state == JudgeResultEvent.ResultType.PenaltyKick:
        strategy_penalty(field)

        if field.ball.position.x > 110:
            GlobalVariable.score[0] += 1
            # GlobalVariable.type[1]+=1
            # print('score1=',GlobalVariable.score[1])
        elif field.ball.position.x < -110:
            GlobalVariable.score[1] += 1
            # GlobalVariable.type[0] += 1
        print('score1=', GlobalVariable.score[1])
        print('score0=', GlobalVariable.score[0])


    elif race_state == JudgeResultEvent.ResultType.GoalKick:
        strategy_goalkick(field)
    elif race_state == JudgeResultEvent.ResultType.PlaceKick:
        strategy_PlaceKick(field)
    else:
        strategy_common(field)


    # if field.ball.position.x>110:
    #     GlobalVariable.score[0]+=1
    #     # GlobalVariable.type[1]+=1
    #     # print('score1=',GlobalVariable.score[1])
    # elif field.ball.position.x < -110:
    #     GlobalVariable.score[1] += 1
    #     # GlobalVariable.type[0] += 1
    # print('score1=', GlobalVariable.score[1])
    # print('score0=', GlobalVariable.score[0])


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
    global mark
    resetHistoryRecord = True
    print('last_score:{},{}'.format(GlobalVariable.last_score[0],GlobalVariable.last_score[1]))

    if race_state == JudgeResultEvent.ResultType.PlaceKick:
        global tickBeginPlaceKick
        tickBeginPlaceKick = field.tick
        if race_state_trigger == Team.Self:
            print("开球进攻摆位")
            # set_pos = [[-100, 20, 0],
            #            [0, -5, 90],
            #            [-30, -30, 0],
            #            [-50, 30, 0],
            #            [-80, 0, 0],
            #            [0.0, 0.0, 0.0]]

            set_pos = [[-100, 20, 0],
                       [0, -5, -90],
                       # [-30, -30, 0],
                       [-25, 5, 40],
                       [-25, -5, -40],
                       [-35, 0, 0],
                       [0.0, 0.0, 0.0]]
            # set_pos = [(-103, 0, 90), (30, 0, 0), (-3, -10, 0), (-3, 10, 0), (-3, 0, 0), (0.0, 0.0, 0.0)]
        else:   # if race_state_trigger == Team.Opponent:
            print("开球防守摆位")
            # set_pos = [[-6, -70, -89],
            #            [-30, -47, -120],
            #            # [-30, -30, 0],
            #            [-30, -35, 40],
            #            [-25, -30, 40],
            #            [-70, 0, -90],
            #            [0.0, 0.0, 0.0]]
            set_pos = [[-70, 0, 90],
                       [-30, -47, -60],
                       # [-30, -30, 0],
                       [-30, -35, -40],
                       [-25, -30, -40],
                       [-5, -70, 0],
                       [0.0, 0.0, 0.0]]
            # set_pos = [(-105, 0, 90), (10, 20, -90), (10, -20, -90), (10, 40, -90), (10, -40, -90), (0.0, 0.0, 0.0)]
    elif race_state == JudgeResultEvent.ResultType.PenaltyKick:
        global tickBeginPenalty
        tickBeginPenalty = field.tick

        if race_state_trigger == Team.Self:
            if GlobalVariable.last_score[0] == GlobalVariable.score[0] :
                    # and GlobalVariable.score[0] != 0:  # 没进球，进攻策略更换
                GlobalVariable.type[0] += 1
        if GlobalVariable.type[0]>=GlobalVariable.ALL_Type:
            GlobalVariable.type[0]=1
        else:
            if GlobalVariable.score[1] / 2 * mark == 0 \
                    and GlobalVariable.last_score[1] != GlobalVariable.score[1] \
                    and GlobalVariable.score[1] != 0:  # 被进球，防守策略更换
                GlobalVariable.type[1] += 1
                mark += 1
        if GlobalVariable.type[1]>=GlobalVariable.ALL_Type:
            GlobalVariable.type[1]=1

        if race_state_trigger == Team.Self:
            GlobalVariable.last_score[0] = GlobalVariable.score[0]
        else:
            GlobalVariable.last_score[1] = GlobalVariable.score[1]
        print('type0==', GlobalVariable.type[0], 'type1==', GlobalVariable.type[1])

        if race_state_trigger == Team.Self:
            if GlobalVariable.type[0] == 1:
                print("点球进攻摆位1")
                set_pos = [[-103, 0, 0],
                           [72.5, -10, 90],
                           # [-50, -50, -30],
                           [-9, 55, 30],
                           [-10, 50, -20],
                           [-30, 0, 0],
                           [5, 10, 0.0]]
            elif GlobalVariable.type[0] == 2:
                print("点球进攻摆位2")
                set_pos = [[-103, 0, 0],
                           [70.5, 5, -90],
                           # [-50, -50, -30],
                           [-9, 55, 30],
                           [-10, -80, 34],
                           [-10, -70, 32],
                           [5, 10, 0.0]]
            elif GlobalVariable.type[0] == 3:
                print("点球进攻摆位3")
                set_pos = [[-103, 0, 0],
                           [70.5, -5, 90],
                           # [-50, -50, -30],
                           [-9, 55, 30],
                           [-10, 80, -34],
                           [-10, 70, -32],
                           [5, 10, 0.0]]
            else:
                set_pos = [[-103, 0, 0],
                           [72.5, -10, 90],
                           # [-50, -50, -30],
                           [-9, -70, 30],
                           [-10, 50, -20],
                           [-30, 70, 0],
                           [-40, 10, 0.0]]

        else:   # if race_state_trigger == Team.Opponent:
            print("点球防守摆位")
            if GlobalVariable.type[1] == 1:
                # set_pos = [[-95, 0, 0],
                #            [10, 20, 0],
                #            [10, -20, 0],
                #            [10, 50, 0],
                #            [10, -50, 0],
                #            [0, 0.0, 0.0]]
                set_pos = [[-75, 0, 35],
                           [10, -55, -136],
                           [10, -40, -135],
                           [10, 40, 135],
                           [10, 55, 134],
                           [5, 10, 0]]
            elif GlobalVariable.type[1] == 2:
                set_pos = [[-95, 0, 60],
                           [-90, 8, 0],
                           [10, -30, -90],
                           [10, 20, -90],
                           [10, -50, -90],
                           [0, 0.0, 0.0]]

            else:
                set_pos = [[-95, 0, 60],
                           [10, 8, 0],
                           [10, -70, -90],
                           [10, 20, -90],
                           [10, 70, -90],
                           [0, 0.0, 0.0]]

    elif race_state == JudgeResultEvent.ResultType.GoalKick:
        global tickBeginGoalKick
        tickBeginGoalKick = field.tick
        if race_state_trigger == Team.Self:
            print("门球进攻摆位")
            set_pos = [[-101 - 1, 0, -61],
                       [-55, -40, -90],
                       [-55, -30, -90],
                       [-85, -75, -90],
                       [-80, -75, -90],
                       [-95.27, -9.05, 0.0]]
        else:  # if race_state_trigger == Team.Opponent:
            print("门球防守摆位")
            set_pos = [[-105, 0, 0],
                       [30, 0, 0],
                       [-40, -10, 0],
                       [-40, 0, 0],
                       [-40, 10, 0],
                       [0, 0.0, 0.0]]
    elif (race_state == JudgeResultEvent.ResultType.FreeKickLeftTop
          or race_state == JudgeResultEvent.ResultType.FreeKickRightTop
          or race_state == JudgeResultEvent.ResultType.FreeKickRightBot
          or race_state == JudgeResultEvent.ResultType.FreeKickLeftBot):
        if race_state_trigger == Team.Self:
            print("争球进攻摆位")
            set_pos = [[-103, 0, 90],
                       [30, 0, 0],
                       [-3, -10, 0],
                       [-3, 10, 0],
                       [-3, 0, 0],
                       [0.0, 0.0, 0.0]]
        else:   # if race_state_trigger == Team.Opponent:
            print("争球防守摆位")
            set_pos = [[-105, 0, 0],
                       [30, 0, 0],
                       [10, -10, 0],
                       [10, 10, 0],
                       [10, 0, 0],
                       [0.0, 0.0, 0.0]]
    else:
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