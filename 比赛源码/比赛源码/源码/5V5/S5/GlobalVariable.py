from typing import List


class GlobalVariable:
    # 用以存储一些全局变量
    tick = -1
    tick_delay = 4
    score=[0,0]        #score 0自己得分，1对方得分
    last_score=[0,0]   #
    type: list[int]=[1,1]         #type 0进攻策略，1防守策略
    ALL_Type=4