import openai
import time
import random
import numpy as np
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


import os

general_rule = ("掼蛋是一种4人玩的纸牌游戏，游戏用两副108张牌（连鬼牌），由4位玩家进行，相对的两人为一方。基本的规则是，以更大的牌型压制对方，以第一位出完牌的玩家为上游。具体规则如下：\n\n"
                "```牌张与牌手```\n"
                "掼蛋使用两副共54*2=108张牌，称为全手牌。一桌四位玩家按序抓完，每人27张，称一手牌。与升级类似，四人中相对的两人为一方，而上家和下家为对方。玩家按顺序出牌。与争上游、斗地主等玩法类似，以更大的牌型压制前手牌，直至其余玩家放弃不出，称为一圈牌。从开始抓牌至完全出完各自手牌的过程称为一副牌，按照出完顺序的先后，称为上游、二游、三游和下游。如果一方两人分别为三游和下游，则称双下游，一般会对下一副牌的局势不利，见“贡牌”一节。\n\n"
                # "```贡牌```\n"
                # "从第二副牌开始，下游方需要给上游方牌点“进贡”最大的牌（例如王），而上游方需要还给下游方一张点数在2至10之间的牌。如果上副牌打出双下游，那么此方两人各需上贡自己手中最大的牌，这两张牌中较大的给上游，较小的给二游，并对应还牌。如果上贡牌点数相同，则按顺时针方向进贡。还牌结束后的第一圈由接受了上游牌的一方（通常是下游）先出牌。若抓到两个大王均被进贡的一人或两人抓到，则跳过进贡步骤，称为抗贡，首圈由上游先出牌。红心级牌（见牌点与牌型一节）不能在上贡之列。\n\n"
                "```出牌顺序```\n"
                "一圈牌中，出牌顺序为 “玩家索引0 -> 玩家索引1 -> 玩家索引2 -> 玩家索引3 -> 玩家索引0” ... 。\n\n"
                "```牌点与牌型```\n"
                "牌点由小到大排列为，2至10，J，Q，K，A，级牌，小王，大王。红心花色的级牌是掼蛋最为特殊的一张牌，可以充当任意牌点的花色牌（即除大小王）搭配使用，称为逢人配（每回合的逢人配只有一种红心牌，请留意回合信息）。在一圈中打出的牌型有：\n\n"
                "第一类：\n"
                "单张：任意一张单牌；\n"
                "对子：任意两张牌点相同的牌，包括对大王或对小王；\n"
                "木板：三对牌点相邻的对子，如223344；\n"
                "三同张：三张牌点相同的牌；\n"
                "钢板：两套牌点相同的三同张，如333444；\n"
                "三带二：三同张加一个对子，如55522；\n"
                "顺子：五张牌点相邻的牌，如23456；\n"
                "以上不同牌型不能压牌。\n\n"
                "第二类：\n"
                "炸弹：四张或四张以上牌点相同的牌；\n"
                "同花顺：五张花色相同的顺子；\n"
                "天王炸：大小王各两张。\n"
                "第一类牌型中，以牌点大者为大。三带二只比较三同张的大小。A在三连对、二连三、顺子、同花顺中作为1，为最小者。\n"
                "第二类可以压任意第一类牌型。而第二类牌型内部大小顺序为：\n"
                "炸弹张数多者为大，若张数相同，牌点最大的为大；\n"
                "同花顺以点数大者为大，同花顺可以压五张及以下的炸弹，但六张及以上的炸弹比同花顺更大；\n"
                "天王炸大过所有牌型。\n\n"
                # "```报牌```\n"
                # "升级是取得整局胜利的必要条件。升级规则如下：\n"
                # "牌局开始的第一副两方级数为均为2，即2为主牌，大于其他花色牌，红心2为逢人配。副牌中一方中一家获得上游，若该方对家均为下游，升三级，即若本局级数为2，下局则为5。同伴三游升2级，同伴末游升1级。下一副牌赢家的级数作为级牌。A级必打，即如果升级超过A级的仍然为A级。\n\n"
                "```计分```\n"
                "一局比赛中计分规则可以分为以下三种情况：\n"
                " 1. 队伍中的成员两人分别为头游和二游获得4分（称为双上，头两家打完所有手牌）。这时，敌方队伍为三游和末游戏（最后两个打完手牌）获得-4分。\n"
                " 2. 队伍中的成员两人分别为头游和三游（一名成员第一个打完所有手牌，另一名第三个打完所有手牌）获得2分。这时敌方队伍为二游和末游（成员分别为第二个打完手牌和最后一个打完手牌）获得-2分。\n"
                " 3. 队伍中的成员两人分别为头游和末游（一名成员第一个打完所有手牌，另一名最后一个打完所有手牌）获得1分。这时敌方队伍为二游和三游（成员分别为第二个打完手牌和第三个打完手牌）获得-1分。\n"
                " 注意：同队中的两人为相同分数，意味着这是一个讲究团队合作的游戏。\n"
                "```胜负```"
                "在进行的多局游戏中，队伍平均分数更高的一队的为胜利方，两人均为获胜者。"
                )

obs_rule = ("观察是一本字典。主要观察空间：\n"
            " “玩家索引”，当前玩家（自己）的索引。"
            " “手牌”，玩家拥有的所有手牌。\n"
            " “自己剩余手牌数量”，当前玩家（自己）所剩下手牌的数量。\n"
            " “队友剩余手牌数量”，队友剩下的手牌数量。\n"
            " “下家对手剩余手牌数量”， 准备接你牌的敌人所剩余的手牌数量。\n"
            " “上家对手剩余手牌数量”， 你的上家敌人所剩余的手牌数量。\n"
            " “逢人配”，当前游戏的逢人配，可以充当任意牌点的花色牌（即除大小王）搭配使用。\n"
            " “是否拥有出牌权”，代表上回合你打出的牌没有玩家接，你拥有打出当前任意组合的机会。\n"
            " “最后一轮牌型、牌值和玩家索引”，当前场上打出的最后一轮手牌以及打出的玩家索引。\n\n"
            "请您根据以上信息，合理、准确地一步步分析场上的局面，分析步骤请根据以下模板：\n"
            " 1. 说出你目前拥有的手牌、剩余手牌数量以及当前的逢人配（并分析当前你手牌中所拥有的逢人配数量，并简短解释一下逢人配的作用）。\n"
            " 2. 你的队友（索引号为__）所有的手牌数量为__。\n"
            " 3. 你打出牌之后，准备要接你牌的对手（索引号为__），他所拥有的手牌数量为__。\n"
            " 4. 你的上家对手所拥有（索引号为__）的手牌数量为__。\n"
            " 5. 你是否具备出牌权（如果你有出牌权，意味着你可以打出任意组合的手牌）。\n"
            " 6. 如果你有出牌权，跳过这一步骤。如果没有，则分析上次出牌的玩家为: 队友/对手（玩家索引__），他打出的牌型和具体牌为: __， 以为他所剩余的手牌数量为__。"
            )

game_name = "掼蛋"
# history = [{'seatid': h.seatid, 'patterntype': h.pattern, 'cards': h.cards , 'patternvalue':h.value} for h in gameinfo.actions]
history_rule = ("游戏历史记录是一本字典。主要的记录空间：\n"
                " ```seatid```，做出操作的玩家索引。\n"
                " ```patterntype```，打出的牌型。\n"
                " ```cards```，组成牌型的具体牌值和花色。\n"
                "请您根据这些信息，合理、准确地一步步按照以下模板将字典中每一个元素转为可读的文本形式：\n"
                " 1（字典中的第一个元素，也就是最早的历史）. （```seatid```） + 队友/自己/对手 + 打出了牌值为 (```cards```) 的 (```patterntype```)。\n"
                " 2（字典中的第二个元素）. （```seatid```） + 队友/自己/对手 + 打出了牌值为 (```cards```) 的 (```patterntype```)。\n"
                " ... \n"
                " 注意：字典中的每个元素请用一句话来描述，请通过玩家索引准确推断出，做出这项操作的是队友、自己还是对手。")

# os.environ["OPENAI_API_BASE"] = "https://openai.api2d.net/v1"
# os.environ["OPENAI_API_KEY"] = "fk193574-JC4P6uf3KOUAd3Xipa0wI8XU5HdpyDIg"
os.environ["OPENAI_API_BASE"] = "https://api.zhiyungpt.com/v1"
os.environ["OPENAI_API_KEY"] = "sk-z82V95UKW9g7cdDpE6293bAd46F74aFeB99099DdFc3c374b"


class TomAgent:

    # TODO: 原来的有涉及到valid_action_list, 感觉可以添加其他人还剩下多少张牌的信息。 他们还有conversation这个，感觉我们是不是也可以加上? 可以加上所有已经出过的牌
    def __init__(self, args):
        # self.llm = OpenAI(model_name="gpt-3.5-turbo", base_url= "https://api.zhiyungpt.com/v1", api_key = "sk-z82V95UKW9g7cdDpE6293bAd46F74aFeB99099DdFc3c374b")
        self.args = args
        callback_manager = [StreamingStdOutCallbackHandler()]
        print("----------------")
        print(args.model)
        self.llm = Ollama(model=args.model, callbacks=callback_manager)

    # 得到除了自己以外的其他玩家id
    def get_other_id(self, player_id):

        id_list = [0, 1, 2, 3]
        id_list.remove(player_id)

        return id_list

    def get_teammate_id(self, player_id):

        number = 0 if player_id == 2 else 2

        return number

    def check_action(self, action, valid_action_list):

        if int(action) < 0:
            return False

        if int(action) >= len(valid_action_list):
            return False

        return True

    def planning_module(self, observation, player_id, belief, mode, top_k_action, short_memory_summary, pattern='',
                        last_plan='') -> str:

        """Make Plans and Evaluate Plans."""
        """Combining these two modules together to save costs"""

        teammate_id = self.get_teammate_id(player_id)
        other_id = self.get_other_id(player_id)

        enemy_id = other_id
        enemy_id.remove(teammate_id)

        if mode == 'second_tom':
            prompt = PromptTemplate.from_template(
                "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {other_id} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。 \n"
                + " 游戏规则是： {rule} \n"
                # + "  {pattern} \n"
                + " 您现在对游戏状态的观察是：{observation}\n"
                + " 您当前的游戏进度总结（包括自己、队友、对手的历史操作）为：{recent_observations}\n"
                + " 您的信念：\n{belief}\n"
                + " 您当前可以进行的合法操作列表：{top_k_action}\n"
                + "了解所有给定的信息，您可以做以下事情（请简短回复）：\n"
                + " 1. 将合法操作列表字典转为可读文本，采用以下格式转换（每个动作对应一个语句）：\n"
                + " 合法动作索引0：牌型为___，组成牌型的手牌为___。\n"
                + " 合法动作索引1：... \n。"
                + " ...\n"
                + " 2. 基于您的信念，为每一个动作索引制定一套后续方案，方案的核心可以是：优先自己走牌、辅助队友走牌或者压制敌方不让敌方走牌等，然后逐步和你队友赢得最终的整个{game_name}游戏（方案数量应该跟合法动作索引数量一致）。格式如下：\n"
                + " 方案0： 我打出动作索引0的话 ... 我的方案核心是 ... (请拓展)\n"
                + " 方案1： 我打出动作索引1的话 ... 我的方案核心是 ... (请拓展)\n"
                + " ... \n"
                + " 注意：本回合你只能打出合法操作列表中的操作。\n"
                + " 3. 分析每套方案对比赛后续走势影响以及信念（需要考虑到对方两名玩家的手牌情况）。\n"
                + " 如果我采用方案0，对后续比赛可能造成的影响___，这套方案的潜在信念为___。\n"
                + " ... \n"
                + " 4. 估算每套方案的预期增益：了解游戏规则、方案以及您对{game_name}的了解，结合您分析每套方案对比赛后续走势影响以及信念，估算出选择这套方案后你们队伍可能获得的最终分数。格式如下：\n"
                + " 采用方案0后，我走完所有手牌的名次为___（原因）。我队友预期走完牌的名次为___（原因）。队伍可以获得的总分为___分。\n"
                + " ... \n"
                + " 5. 方案选择：请客观地逐步输出每个方案的预期获益排名，选择预计预期收益最高的方案/策略 （给出具体的方案数字/选项）。\n\n"
            )

        elif mode == 'first_tom':
            prompt = PromptTemplate.from_template(
                "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {other_id} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。 \n"
                + " 游戏规则是： {rule} \n"
                # + "  {pattern} \n"
                + " 您现在对游戏状态的观察是：{observation}\n"
                + " 您当前的游戏进度总结（包括自己、队友、对手的历史操作）为：{recent_observations}\n"
                + " 您的信念：\n{belief}\n"
                + " 您当前可以进行的合法操作列表：{top_k_action}\n"
                + "了解所有给定的信息，您可以做以下事情（请简短回复）：\n"
                + " 1. 将合法操作列表字典转为可读文本，采用以下格式转换（每个动作对应一个语句）：\n"
                + " 合法动作索引0：牌型为___，组成牌型的手牌为___。\n"
                + " 合法动作索引1：... \n。"
                + " ...\n"
                + " 2. 基于您的信念，为每一个动作索引制定一套后续方案，方案的核心可以是：优先自己走牌、辅助队友走牌或者压制敌方不让敌方走牌等，然后逐步和你队友赢得最终的整个{game_name}游戏（方案数量应该跟合法动作索引数量一致）。格式如下：\n"
                + " 方案0： 我打出动作索引0的话 ... 我的方案核心是 ... (请拓展)\n"
                + " 方案1： 我打出动作索引1的话 ... 我的方案核心是 ... (请拓展)\n"
                + " ... \n"
                + " 注意：本回合你只能打出合法操作列表中的操作。\n"
                + " 3. 分析每套方案对比赛后续走势影响以及信念（需要考虑到对方两名玩家的手牌情况）。\n"
                + " 如果我采用方案0，对后续比赛可能造成的影响___，这套方案的潜在信念为___。\n"
                + " ... \n"
                + " 4. 估算每套方案的预期增益：了解游戏规则、方案以及您对{game_name}的了解，结合您分析每套方案对比赛后续走势影响以及信念，估算出选择这套方案后你们队伍可能获得的最终分数。格式如下：\n"
                + " 采用方案0后，我走完所有手牌的名次为___（原因）。我队友预期走完牌的名次为___（原因）。队伍可以获得的总分为___分。\n"
                + " ... \n"
                + " 5. 方案选择：请客观地逐步输出每个方案的预期获益排名，选择预计预期收益最高的方案/策略 （给出具体的方案数字/选项）。\n\n"
            )
        else:
            prompt = PromptTemplate.from_template(
                "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {other_id} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。 \n"
                + " 游戏规则是： {rule} \n"
                # + "  {pattern} \n"
                + " 您现在对游戏状态的观察是：{observation}\n"
                + " 您当前的游戏进度总结（包括自己、队友、对手的历史操作）为：{recent_observations}\n"
                + " 您当前可以进行的合法操作列表：{top_k_action}\n"
                + "了解所有给定的信息，您可以做以下事情（请简短回复）：\n"
                + " 1. 将合法操作列表字典转为可读文本，采用以下格式转换（每个动作对应一个语句）：\n"
                + " 合法动作索引0：牌型为___，组成牌型的手牌为___。\n"
                + " 合法动作索引1：... \n。"
                + " ...\n"
                + " 2. 为每一个动作索引制定一套后续方案，方案的核心可以是：优先自己走牌、辅助队友走牌或者压制敌方不让敌方走牌等，然后逐步和你队友赢得最终的整个{game_name}游戏（方案数量应该跟合法动作索引数量一致）。格式如下：\n"
                + " 方案0： 我打出动作索引0的话 ... 我的方案核心是 ... (请拓展)\n"
                + " 方案1： 我打出动作索引1的话 ... 我的方案核心是 ... (请拓展)\n"
                + " ... \n"
                + " 注意：本回合你只能打出合法操作列表中的操作。\n"
                + " 3. 分析每套方案对比赛后续走势影响以及信念（需要考虑到对方两名玩家的手牌情况）。\n"
                + " 如果我采用方案0，对后续比赛可能造成的影响___，这套方案的潜在信念为___。\n"
                + " ... \n"
                + " 4. 估算每套方案的预期增益：了解游戏规则、方案以及您对{game_name}的了解，结合您分析每套方案对比赛后续走势影响以及信念，估算出选择这套方案后你们队伍可能获得的最终分数。格式如下：\n"
                + " 采用方案0后，我走完所有手牌的名次为___（原因）。我队友预期走完牌的名次为___（原因）。队伍可以获得的总分为___分。\n"
                + " ... \n"
                + " 5. 方案选择：请客观地逐步输出每个方案的预期获益排名，选择预计预期收益最高的方案/策略 （给出具体的方案数字/选项）。\n\n"
                # + " 制定合理的与队友配合的方案：请根据您慢慢仔细地理解现在可以进行的动作{top_k_action}，然后根据可以执行的动作来制定几种策略。策略中必须包含与你队友的配合，逐步和你队友赢得最终的整个{game_name}游戏（最多制定不多于5套方案且不可以有重复的方案）。\n"
                # + " 对每个方案的输赢潜在信念：了解游戏规则、您当前的观察、之前游戏进度的总结、每个新方案，然后逐步推断出您对每个方案中你和队友配合以及分析如何通过这种配合来对抗敌方配合的几个信念。\n"
                # + " 估算每个方案的预期增益：了解游戏规则、方案以及您对{game_name}的了解，请通过分析敌方可能的配合策略，以及场上局势，解释一下如果不选择该方案会是什么结果，并一步步解释为什么这个与队友相互配合的方案是合理的？ \n"
                # + " 方案选择：请客观地逐步输出每个方案的预期获益排名，并综合考虑策略改进情况，选择预计预期筹码收益最高的方案/策略 （给出具体的方案数字/选项）。 \n\n "
            )

        agent_summary_description = short_memory_summary

        kwargs = dict(
            user_index=player_id,
            other_id=other_id,
            game_name=game_name,
            teammate_index=teammate_id,
            enemy1_id=enemy_id[0],
            enemy2_id=enemy_id[1],
            rule=general_rule,
            observation=observation,
            recent_observations=agent_summary_description,
            top_k_action=top_k_action,
            belief = belief
        )

        plan_prediction_chain = LLMChain(llm=self.llm, prompt=prompt)
        self.plan = plan_prediction_chain.run(**kwargs)
        self.plan = self.plan.strip()

        return self.plan.strip()

    # TODO: BELIEF
    def get_belief(self, observation, player_id, mode, short_memory_summary, pattern='',
                        last_plan='') -> str:
        """React to get a belief."""

        teammate_id = self.get_teammate_id(player_id)
        other_id = self.get_other_id(player_id)

        enemy_id = other_id
        enemy_id.remove(teammate_id)

        if mode == 'second_tom':
            prompt = PromptTemplate.from_template(
                "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {other_id} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。 \n"
                + " 游戏规则是： {rule} \n"
                + " 您现在对游戏状态的观察是：{observation}\n"
                + " 您当前的游戏进度总结（包括自己、队友、对手的历史操作）为：{recent_observations}\n"
                + " 了解游戏规则、你拥有的牌、你的观察、当前游戏的进度总结以及你对 {game_name} 的了解，你能做以下事情吗？\n"
                + " 我的手牌分析：了解所有给定的信息后，请逐步分析您在本轮中手牌的优势和劣势是什么。\n"
                + " 对玩家索引 {teammate_index}（队友）的手牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{teammate_index}（队友）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，队友选择的出牌组合，以此逐步分析队友手牌的优势和劣势分别是什么。例如，他的手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。 \n"
                + " 玩家索引为 {teammate_index}（队友）当前对您手牌的潜在看法：了解所有给定的信息以及您对{game_name}的了解，如果您是玩家索引为 {teammate_index}的玩家（他只能观察我的行为，但看不到我的牌），请逐步推断出玩家索引为{teammate_index} 的队友对你手牌优势和劣势的信念（提示：可以分析在他信念中，我手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。"
                + " 对我们团队配合计划的信念：了解所有给定的信息、对我的手牌分析以及对队友手牌的信念，请逐步分析出当前我方团队之间的最优合作信念（提示：根据历史出牌记录，以及场上局势，思考应当持有怎样的合作信念才能让我方团队赢得比赛）。\n"
                + " 对玩家索引 {enemy1_id}（敌人）的牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{enemy1_id}（敌人1）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，玩家索引为{enemy1_id}敌人1选择的出牌组合，以此逐步分析这位敌人手牌的优势和劣势分别是什么。例如，他的手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。 \n"
                + " 对玩家索引 {enemy2_id}（敌人）的牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{enemy2_id}（敌人2）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，玩家索引为{enemy1_id}敌人2选择的出牌组合，以此逐步分析这位敌人手牌的优势和劣势分别是什么。例如，他的手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。 \n"
                + " 玩家索引为 {enemy1_id}，{enemy2_id}（敌人）当前对您手牌的潜在看法：了解所有给定的信息以及您对{game_name}的了解，如果您是玩家索引为 {enemy1_id}， {enemy2_id}的玩家（他只能观察我的行为，但看不到我的牌），请逐步推断出他们（敌人）对你手牌优势和劣势的信念（提示：可以分析在他信念中，我手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。\n\n"
            )
        elif mode == 'first_tom':
            prompt = PromptTemplate.from_template(
                "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {other_id} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。 \n"
                + " 游戏规则是： {rule} \n"
                # + " Your estimated judgement about the behaviour pattern of {recipient_name} and improved strategy is: {pattern} \n"
                + " 您现在对游戏状态的观察是：{observation}\n"
                + " 您当前的游戏进度总结（包括自己、队友、对手的历史操作）为：{recent_observations}\n"
                # + " Understanding the game rule, the cards you have, your observation,  progress summarization in the current game, the estimated behaviour pattern of {recipient_name}, and your knowledge about the {game_name}, can you do following things? "
                + " 了解游戏规则、你拥有的牌、你的观察、当前游戏的进度总结以及你对 {game_name} 的了解，你能做以下事情吗？\n"
                + " 我的手牌分析：了解所有给定的信息后，请逐步分析您在本轮中手牌的优势和劣势是什么。\n"
                + " 对玩家索引 {teammate_index}（队友）的手牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{teammate_index}（队友）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，队友选择的出牌组合，以此逐步分析队友手牌的优势和劣势分别是什么。例如，他的手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。 \n"
                + " 对我们团队配合计划的信念：了解所有给定的信息、对我的手牌分析以及对队友手牌的信念，请逐步分析出当前我方团队之间的最优合作信念（提示：根据历史出牌记录，以及场上局势，思考应当持有怎样的合作信念才能让我方团队赢得比赛）。\n"
                + " 对玩家索引 {enemy1_id}（敌人）的牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{enemy1_id}（敌人1）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，玩家索引为{enemy1_id}敌人1选择的出牌组合，以此逐步分析这位敌人手牌的优势和劣势分别是什么。例如，他的手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。 \n"
                + " 对玩家索引 {enemy2_id}（敌人）的牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{enemy2_id}（敌人2）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，玩家索引为{enemy1_id}敌人2选择的出牌组合，以此逐步分析这位敌人手牌的优势和劣势分别是什么。例如，他的手牌中拥有最大和最小的组合是什么、可能缺少第一类（不能压牌）牌型是什么等）。 \n\n"
                # + " 对{enemy2_id}（敌人）的牌的信念：了解所有给定的信息，请逐步推断出玩家索引为{enemy2_id}（敌人2）的手牌特点（提示：根据历史出牌记录，思考当其他玩家打出某种出牌组合时，玩家索引为{enemy1_id}敌人2选择的出牌组合，以此逐步分析这位敌人手牌的优势和劣势分别是什么）。
                # + " Analysis on {recipient_name}'s Cards: Understanding all given information, please analysis what is {recipient_name}'s best combination and advantages of {recipient_name}'s cards  in the current round  step by step."
            )
        agent_summary_description = short_memory_summary

        kwargs = dict(
            user_index=player_id,
            other_id=other_id,
            game_name=game_name,
            teammate_index=teammate_id,
            enemy1_id=enemy_id[0],
            enemy2_id=enemy_id[1],
            rule=general_rule,
            observation=observation,
            recent_observations=agent_summary_description,
        )

        belief_prediction_chain = LLMChain(llm=self.llm, prompt=prompt)
        self.belief = belief_prediction_chain.run(**kwargs)
        self.belief = self.belief.strip()

        return self.belief.strip()

    def get_short_memory_summary(self, observation: str, player_id: int, short_memory_summary) -> str:
    

        """React to get a belief."""

        teammate_id = self.get_teammate_id(player_id)
        other_id = self.get_other_id(player_id)

        enemy_id = other_id
        enemy_id.remove(teammate_id)

        prompt = PromptTemplate.from_template(
            "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {teammate_index} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。\n"
            + " 游戏规则是： {rule} \n"
            + " 你目前为止的所有观察为： {observation} \n"
            + " 当前游戏历史记录包括所有玩家最近几回合的操作： {agent_action_history}\n"
              " 历史记录值转换规则： {history_rule}\n"
            + " 请根据游戏规则、历史记录值转换规则、自己的索引以及您对{game_name}的了解，将当前的历史记录转为可读文本。"
        )

        agent_summary_description = short_memory_summary

        kwargs = dict(
            user_index=player_id,
            teammate_index=teammate_id,
            enemy1_id=enemy_id[0],
            enemy2_id=enemy_id[1],
            game_name=game_name,
            rule=general_rule,
            agent_action_history=agent_summary_description,
            observation=observation,
            history_rule=history_rule
        )

        belief_prediction_chain = LLMChain(llm=self.llm, prompt=prompt)
        self.belief = belief_prediction_chain.run(**kwargs)
        self.belief = self.belief.strip()
        return self.belief.strip()

    # 把历史数据转为可读的text
    def convert_obs(self, observation, player_id):

        teammate_id = self.get_teammate_id(player_id)
        other_id = self.get_other_id(player_id)
        enemy_id = other_id
        enemy_id.remove(teammate_id)

        prompt = PromptTemplate.from_template(
            "您是玩家索引为 {user_index} 的 NPC 角色背后的玩家，并且您正在与玩家索引为 {recipient_index} 玩棋盘游戏 {game_name}。 其中玩家索引为 {teammate_index} 是你的队友，其余两位玩家索引为 {enemy1_id} ，{enemy2_id} 是你要对抗的对手。\n"
            + " 游戏规则是： {rule} \n"
            + " 你目前为止的所有观察为： {observation} \n"
            + " 观测值转换规则为： {observation_rule} \n"
            + " 请根据观察转换规则和您对 {game_name} 的了解，将 ···{observation}··· 转换为可读文本 （请简洁准确地回复）。\n\n"
        )

        kwargs = dict(
            user_index=player_id,
            teammate_index=teammate_id,
            rule=general_rule,
            recipient_index=other_id,
            observation=observation,
            game_name=game_name,
            observation_rule=obs_rule,
            enemy1_id=enemy_id[0],
            enemy2_id=enemy_id[1]
        )
        obs_prediction_chain = LLMChain(llm=self.llm, prompt=prompt)
        self.read_observation = obs_prediction_chain.run(**kwargs)
        self.read_observation = self.read_observation.strip()

        return self.read_observation

    def action_decision(self, top_k_action, plan: str, observation: str = None, act: str = None,
                        short_memory_summary: str = ""):

        """React to a given observation."""
        prompt = PromptTemplate.from_template(
            "您的计划是：{plan}"
            + "\n 根据计划，请从可用的动作列表中选择下一个动作：{top_k_action}（只需一个数字，代表你要选择动作的索引。请确保所选择的数字在动作列表的长度范围内！）。"
            # + "\n注意：计划中的“最优方案编号”等价于“动作索引”，请慢慢充分地理解动作列表中的每一个动作含义（每一个元素为一个动作，代表可以打出的牌型和具体牌值）以及计划选择的最终方案，并选择与方案理念最匹配匹配的“动作索引”。"
            + "并根据对计划的理解，解释你选择这个动作的原因（仅回答句子）。请回复并按 | 分割 \n"
            + "'|' 前是一个数字（代表你要选择的动作索引） '|'后是回答句子（代表选择这个动作的解释）"
            + "\n\n"
        )

        kwargs = dict(
            # observation= observation,
            top_k_action=top_k_action,
            plan=plan,
        )
        action_prediction_chain = LLMChain(llm=self.llm, prompt=prompt)

        result = action_prediction_chain.run(**kwargs)
        if "|" in result:
            result, result_comm = result.split("|", 1)
        else:
            result_comm = ""
        return result.strip(), result_comm.strip()

    def make_act(self, top_k_action, valid_action_list, observation: str, player_id: int, round: int, player_action_his, console,
                 log_file_name='', mode='nontom', no_highsight_obs=False, verbose_print=True):

        readable_text_amy_obs = self.convert_obs(observation, player_id,)
        if verbose_print:
            console.print('readable_text_obs: ', style="red")
            print(readable_text_amy_obs + '\n')

        # only need last 8 round action histroy.
        if len(player_action_his) > 8:
            player_action_his = player_action_his[-8:]

        time.sleep(0)
        if round == 1:
            short_memory_summary = f'{1}th Game Start \n' + readable_text_amy_obs
        else:
            short_memory_summary = self.get_short_memory_summary(observation=readable_text_amy_obs, player_id=player_id,
                                                                 short_memory_summary=player_action_his)

        if verbose_print:
            console.print('short_memory_summary: ', style="yellow")
            print(short_memory_summary + '\n')

        time.sleep(2)
        # if  round <= 1:
        #     self.pattern = self.get_pattern(player_id,'',short_summarization=short_memory_summary,mode=mode)
        #     console.print('pattern: ', style="blue")
        #     print(self.pattern)

        # time.sleep(0)

        if mode == 'second_tom' or mode == 'first_tom' and round != 1:

            belief = self.get_belief(observation=readable_text_amy_obs, player_id=player_id,
                                    short_memory_summary=short_memory_summary,
                                    last_plan='', mode=mode)
            if verbose_print:
                console.print(" belief: " , style="deep_pink3")
                print(" belief: " + str(belief))

        else:
            belief = ''

        time.sleep(2)

        if verbose_print:
            console.print("所有合法的操作列表 ", style="green")
            print(valid_action_list)
            print('\n')

            console.print("top_k 操作列表 ", style="magenta")
            print(top_k_action)
            print('\n')


        plan = self.planning_module(observation=readable_text_amy_obs, player_id=player_id, belief=belief,
                                    top_k_action=top_k_action, short_memory_summary=short_memory_summary,
                                    last_plan='', mode=mode)

        if verbose_print:
            console.print("玩家 " + str(player_id) + " plan: ", style="orchid")
            print("玩家 " + str(player_id) + " plan: " + str(plan) + '\n')

        time.sleep(2)

        promp_head = ''
        act, explain = self.action_decision(top_k_action=top_k_action, plan=plan)

        if verbose_print:
            console.print(" act and explain: ", style="blue")
            print(act + '\n')
            print(explain + '\n' + '\n')

        while self.check_action(act, top_k_action) != True:
            print('Action + ', str(act), ' is not a valid action in valid_action_list, please try again.\n')
            promp_head += 'Action {act} is not a valid action in {valid_action_list}, please try again.\n'
            act, comm = self.action_decision(top_k_action=top_k_action, plan=plan)

        time.sleep(2)

        return readable_text_amy_obs, short_memory_summary, belief, plan, act, explain
        
      
    def jieshuo(self, cid, handcard, action,history):
        rule = "掼蛋游戏的技巧包括记牌、进贡回贡、炸弹使用、红桃配配、双贡打牌、控牌、送牌、抓牌、插牌、理牌、组火和冲刺等多个方面。要记住牌的分布，善用炸弹、配好红桃、灵活运用各种牌型，尤其在双贡和冲刺时要善于判断时机。"
        style = "掼蛋游戏细分为开局、中盘、高潮和终局四个阶段，不同阶段的解说风格和侧重点有所不同。开局阶段描述比赛开始时各位选手手牌的概况和初始策略，每位选手手中的牌型及其对比赛策略的影响。中盘阶段叙述比赛中期，选手如何运用策略和手中的牌来掌控或改变游戏局势，详细解说每位选手如何根据对局的发展调整策略和手法。高潮阶段描绘比赛中的关键转折点，如重大出牌或意外战术，强调那些改变比赛走向的戏剧性瞬间和决策。终局阶段讲述如何决出胜负，包括各个选手在最后阶段的表现和策略，突出展示决定性的手牌和策略选择。"
        prompt = PromptTemplate(template="你的seatid为 {cid}，结合历史出牌信息: {history},以及你的当前手牌{handcard}; 结合游戏规则{rule}, 结合场上局势，结合解说风格{style}，假想你作为专业的掼蛋游戏解说，从掼蛋教学角度，结合掼蛋技巧，历史出牌记录，自己手牌分析等信息。揣测上家，下家出牌心理，并且简要分析你打出这个组合{action}的原因：[]", input_variables=["cid", "history", "handcard", "rule","style","action"])
        kwargs = dict(
            cid=cid,
            history=history,
            handcard=handcard,
            rule=rule,
            style=style,
            action=action,
            # short_memory_summary=short_memory_summary,
        )
        jieshuo = LLMChain(llm=self.llm, prompt=prompt)    
        result = jieshuo.run(**kwargs)
        return result         


