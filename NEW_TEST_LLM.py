# import os
# import sys
# import numpy as np
# import random
# from rule import gdgame
# from utils import *
# from agent import GuaDannAgent
# from NEW_AGNET import *
# import json
# import argparse
# from huggingface_agent import *
# from rich.console import Console

import os
import sys
import numpy as np
import random
from rule import gdgame
from utils import *
from agent import GuaDannAgent
from NEW_AGNET import *
import json
import argparse
from rich.console import Console
from langchain.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import streamlit as st
from transformers import AutoTokenizer, AutoModel
import argparse

env = gdgame.GDGameEnv(1)
console = Console()


def load_model(model_name, base_url, callback_manager):
    if model_name == "qwen:7b-chat-v1.5-q6_K":
        model = TomAgent(args)
    elif model_name == "codellama":
        model = TomAgent(args)
    elif model_name == "yi:6b-chat":  
        model = TomAgent(args)
    elif model_name == "qwen:32b-chat-v1.5-q6_K":
        model = TomAgent(args)
    else:
        raise NotImplementedError

    return model

history_llm_rewards = []  # record every game llms' rewards
def run(i, args, callback_manager, base_url="http://localhost:30048", battle_RL=True):

    env.ResetGameDeck()
    game_records = []  # 用于保存历史信息的列表
    round_number = 1  # 用于记录当前轮数

    llm_agent = load_model(args.model, base_url, callback_manager)
    battle_agent = args.battle_agent
    k = args.top_k

    while not env.CheckGameOver():

        #all board infomation
        boardinfo = env.GetBoardInfo("v3")
        currseatid, valid_action_list, current_hands_number_record, hands = get_all_board_info(boardinfo) #玩家id, 合法动作, 玩家手牌数量情况, 自己的手牌

        #all game information
        gameinfo = env.GetGameInfo()
        mainface, maincardid, history = get_all_game_info(gameinfo) # 当前打的牌级, 当前的逢人配，数字形式的history

        # 转为中文
        maincard, cards, raw_legal_action, player_actions_history = convert_to_chinese(maincardid, hands, valid_action_list, history, round_number)

        # 获取最后一轮牌的信息
        last_cards = get_last_round_cards(player_actions_history, round_number)  # 最后一轮的牌型和牌值

        # 用于记录每轮信息的参数
        readable_text_amy_obs = ''
        short_memory_summary = ''
        belief = ''
        plan = ''
        explain = ''
        topk_readable = []
        obs_info = {}

        while True:
            try:
                if currseatid == 0 or currseatid == 2:

                    if k == 1:
                        type_ = 'RLapi'
                        decision_action = rl_based_combination(currseatid, hands, history, mainface,maincardid, env.GetFirstPlay(), env.GetRanking())

                        c_json = decision_action.decode('utf-8')  # Decode bytes to a UTF-8 string
                        decision_action = json.loads(c_json)  # Convert the JSON string to a dictionary

                        env.HandPlay(currseatid, decision_action['pattern'], decision_action['action'])
                        decision_action = match_rl_choice_with_candidates(decision_action, valid_action_list)
                        time.sleep(2)


                        # 用于 prompt observation的信息
                        obs_info = {
                            '玩家索引': currseatid,
                            '手牌': cards,
                            '自己剩余手牌数量': current_hands_number_record[currseatid],
                            '队友剩余手牌数量': current_hands_number_record[get_teammate_id(player_id=currseatid)],
                            '下家对手剩余手牌数量': current_hands_number_record[get_enemy_id(player_id=currseatid)[0]],
                            '上家对手剩余手牌数量': current_hands_number_record[get_enemy_id(player_id=currseatid)[1]],
                            '逢人配': maincard,
                            '是否拥有出牌权': env.GetFirstPlay(),
                            '最后一轮牌型、牌值和玩家索引': last_cards,
                            '当前出完手牌的玩家顺序': env.GetRanking()
                        }


                        # short_memory_summary = llm_agent.get_short_memory_summary(obs_info, currseatid,short_memory_summary)                        
                        # jieshuo=llm_agent.jieshuo(currseatid,hands,decision_action,history,short_memory_summary)
                        jieshuo=llm_agent.jieshuo(currseatid,hands,decision_action,history)
                    else:

                        type_ = 'llm'
                        print(f"LLM_{args.model} agent's turn!")
                        print('Current player ID: ', currseatid)
                        top_k, topk_readable = top_k_action(currseatid, hands, history, mainface, maincardid,
                                                               env.GetFirstPlay(), env.GetRanking(), k)


                        # 用于 prompt observation的信息
                        obs_info = {

                            '玩家索引': currseatid,
                            '手牌': cards,
                            '自己剩余手牌数量': current_hands_number_record[currseatid],
                            '队友剩余手牌数量': current_hands_number_record[get_teammate_id(player_id=currseatid)],
                            '下家对手剩余手牌数量': current_hands_number_record[get_enemy_id(player_id=currseatid)[0]],
                            '上家对手剩余手牌数量': current_hands_number_record[get_enemy_id(player_id=currseatid)[1]],
                            '逢人配': maincard,
                            '是否拥有出牌权': env.GetFirstPlay(),
                            '最后一轮牌型、牌值和玩家索引': last_cards,
                            '当前出完手牌的玩家顺序': env.GetRanking()
                        }


                        readable_text_amy_obs, short_memory_summary, belief, plan, act, explain = llm_agent.make_act(topk_readable, raw_legal_action,
                                                                                                         obs_info, currseatid,
                                                                                                         round_number,
                                                                                                         player_actions_history,
                                                                                                         console, mode=args.mode)

                        decision_action = top_k[int(act)]
                        env.HandPlay(currseatid, decision_action['pattern'], decision_action['action'])  ## 我们应该用大模型的决策作为输入才行！

                else:

                    print("Battel agent's turn!")
                    if battle_agent == 'RLapi_k_1':

                        type_ = 'RLapi'
                        decision_action = rl_based_combination(currseatid, hands, history, mainface,maincardid, env.GetFirstPlay(), env.GetRanking())

                        c_json = decision_action.decode('utf-8')  # Decode bytes to a UTF-8 string
                        decision_action = json.loads(c_json)  # Convert the JSON string to a dictionary

                        env.HandPlay(currseatid, decision_action['pattern'], decision_action['action'])
                        decision_action = match_rl_choice_with_candidates(decision_action, valid_action_list)
                        time.sleep(2)
                        # 用于 prompt observation的信息
                        obs_info = {
                            '玩家索引': currseatid,
                            '手牌': cards,
                            '自己剩余手牌数量': current_hands_number_record[currseatid],
                            '队友剩余手牌数量': current_hands_number_record[get_teammate_id(player_id=currseatid)],
                            '下家对手剩余手牌数量': current_hands_number_record[get_enemy_id(player_id=currseatid)[0]],
                            '上家对手剩余手牌数量': current_hands_number_record[get_enemy_id(player_id=currseatid)[1]],
                            '逢人配': maincard,
                            '是否拥有出牌权': env.GetFirstPlay(),
                            '最后一轮牌型、牌值和玩家索引': last_cards,
                            '当前出完手牌的玩家顺序': env.GetRanking()
                        }


                        # short_memory_summary = llm_agent.get_short_memory_summary(obs_info, currseatid,short_memory_summary)                        
                        # jieshuo=llm_agent.jieshuo(currseatid,hands,decision_action,history,short_memory_summary)
                        jieshuo=llm_agent.jieshuo(currseatid,hands,decision_action,history)
                        print(jieshuo)
                        
                    elif battle_agent == 'random':

                        type_ = 'random'
                        decision_action = rule_based_combination(valid_action_list, rule='random')
                        env.HandPlay(currseatid, decision_action['pattern'], decision_action['cards'])

                    elif battle_agent == 'rule-based':

                        type_ = 'rule_based'
                        decision_action = rule_based_combination(valid_action_list, rule='bestP_lowV')
                        env.HandPlay(currseatid, decision_action['pattern'], decision_action['cards'])
                    

                break

            except Exception as e:

                print("Error: {}".format(e))
                time.sleep(2)

                continue


        # print('round', round_number)
        # print('玩家类型', type_)
        # print('玩家出牌', parse_candidates([decision_action]))

        # Record each round infomation
        round_info = {
            'game': i,
            'round': round_number,
            '玩家类型': type_,
            '手牌': cards,
            '玩家出牌': parse_candidates([decision_action]),
            'currseatid': currseatid,
            'obs_info': obs_info,
            'candidates': raw_legal_action,  ## 玩家可选的出牌组合
            'top_k': topk_readable,
            'readable_text_amy_obs': readable_text_amy_obs,  ## 包含历史所有场上玩家出牌记录
            'short_memory_summary': short_memory_summary,
            'belief': belief,
            'plan': plan,
            'self_action': parse_candidates([decision_action]),
            'llm_analysis': explain,
            '解说':jieshuo
        }

        game_records.append(round_info)
        round_number += 1



    # 将历史信息保存为JSON文件
    output_dir = 'new_memory_test'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'{args.model}_vs_{args.battle_agent}_k{args.top_k}.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        if (i + 1) != 1:
            f.write("\n")

        json.dump(game_records, f, ensure_ascii=False, indent=1)

#    print(f'average scores over {i + 1} games, is {avg_reward}')
#    print('history_llm_rewards: ', history_llm_rewards)


import argparse
import streamlit as st


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guandan Game')
    parser.add_argument('--model', type=str, default='yi:6b-chat', help='Enter the model name')
    parser.add_argument('--battle_agent', type=str, default='RLapi_k_1', help='Select the battle agent')
    parser.add_argument('--top_k', type=int, default=1, help='Enter the top-k value')
    parser.add_argument('--mode', type=str, default='battle', help='Select the mode')
    parser.add_argument('--game_n', type=int, default=1, help='Enter the number of games')
    args = parser.parse_args()

    st.title("Guandan Game")
    models = ["qwen:7b-chat-v1.5-q6_K", "yi:6b-chat", "codellama","qwen:32b-chat-v1.5-q6_K"]
    model_name = st.selectbox("Select the model:", models, index=models.index(args.model))
    battle_agent = st.selectbox("Select the battle agent:", ["RL-agent", "random", "rule-based","RLapi_k_1"], index=["RL-agent", "random", "rule-based","RLapi_k_1"].index(args.battle_agent))
    top_k = st.number_input("Enter the top-k value:", value=args.top_k, step=1)
    mode = st.selectbox("Select the mode:", ["battle", "single_test"], index=["battle", "single_test"].index(args.mode))
    game_n = st.number_input("Enter the number of games:", value=args.game_n, step=1)

    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

   
    
    if st.button("Start Game"):
        args.model = model_name
        for i in range(int(game_n)):
            run(i, args, callback_manager)

    