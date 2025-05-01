# -*- coding: utf-8 -*-
import pygame
import random
import sys
import math
import os
import json  # 添加json模块用于处理排行榜数据

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.25
BIRD_JUMP = -7
PIPE_SPEED = 3
PIPE_GAP = 150
PIPE_FREQUENCY = 1500  # 毫秒

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
SKY_BLUE = (100, 150, 255) # 定义背景色
PIPE_GREEN = (0, 180, 0)
PIPE_BORDER_GREEN = (0, 220, 0)
BIRD_YELLOW = (255, 200, 0)
BEAK_ORANGE = (255, 100, 0)
TEXT_BG_COLOR = (0, 0, 0, 128) # 分数背景半透明黑

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('像素小鸟')
clock = pygame.time.Clock()

# 尝试加载支持中文的字体，如果失败则使用默认字体
try:
    font = pygame.font.SysFont('Noto Sans CJK TC', 30) # 尝试使用 SimHei
    highscore_font = pygame.font.SysFont('Noto Sans CJK TC', 25) # 尝试使用 SimHei
except pygame.error:
    print("警告: 找不到 SimHei 字体, 使用默认字体。中文可能无法正确显示。")
    font = pygame.font.Font(None, 30) # Pygame 默认字体
    highscore_font = pygame.font.Font(None, 25) # Pygame 默认字体


# 文件路径
HIGHSCORE_FILE = "highscore.txt"
LEADERBOARD_FILE = "leaderboard.json"  # 新增排行榜文件
MAX_LEADERBOARD_ENTRIES = 5  # 排行榜显示的最大记录数

# --- 辅助函数 ---

def load_highscore():
    """加载最高分"""
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return int(f.read())
        except ValueError:
            print(f"警告: 无法从 {HIGHSCORE_FILE} 读取最高分。重置为 0。")
            return 0
        except IOError as e:
            print(f"警告: 读取最高分文件时出错: {e}。重置为 0。")
            return 0
    else:
        return 0

def save_highscore(score):
    """保存最高分"""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(score))
    except IOError as e:
        print(f"警告: 无法将最高分保存到 {HIGHSCORE_FILE}: {e}。")

def load_leaderboard():
    """加载排行榜"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f: # 指定utf-8编码
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 无法从 {LEADERBOARD_FILE} 读取排行榜: {e}。创建新的排行榜。")
            return []
    else:
        return []

def save_leaderboard(leaderboard):
    """保存排行榜"""
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f: # 指定utf-8编码
            json.dump(leaderboard, f, ensure_ascii=False, indent=4) # ensure_ascii=False 保存中文
    except IOError as e:
        print(f"警告: 无法将排行榜保存到 {LEADERBOARD_FILE}: {e}。")

def add_to_leaderboard(leaderboard, name, score):
    """添加分数到排行榜并排序截取"""
    leaderboard.append({"name": name, "score": score})
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    return leaderboard[:MAX_LEADERBOARD_ENTRIES]

# --- 游戏元素函数 ---

def create_bird():
    """创建小鸟状态字典"""
    return {
        'x': 100,
        'y': SCREEN_HEIGHT // 2,
        'velocity': 0,
        'width': 30,
        'height': 30
    }

def update_bird(bird):
    """纯函数更新小鸟状态"""
    new_velocity = bird['velocity'] + GRAVITY
    new_y = bird['y'] + new_velocity

    # 防止飞出顶部
    if new_y < 0:
        new_y = 0
        new_velocity = 0

    # 不在这里处理落地，落地是碰撞/结束条件
    return {**bird, 'velocity': new_velocity, 'y': new_y}

def jump_bird(bird):
    """小鸟跳跃的新状态"""
    return {**bird, 'velocity': BIRD_JUMP}

def draw_bird(bird):
    """绘制小鸟（无副作用）"""
    center_x = bird['x'] + bird['width'] // 2
    center_y = bird['y'] + bird['height'] // 2
    radius = bird['width'] // 2

    # 绘制小鸟身体(圆形)
    pygame.draw.circle(screen, BIRD_YELLOW, (center_x, center_y), radius)
    # 绘制小鸟眼睛
    eye_x = center_x + radius * 0.3
    eye_y = center_y - radius * 0.3
    pygame.draw.circle(screen, WHITE, (int(eye_x), int(eye_y)), 4)
    pygame.draw.circle(screen, BLACK, (int(eye_x), int(eye_y)), 2)
    # 绘制小鸟嘴巴(三角形)
    beak_tip_x = center_x + radius + 10 # 嘴尖 x 坐标
    beak_tip_y = center_y          # 嘴尖 y 坐标
    beak_base_y1 = center_y - 5   # 嘴根部上 y
    beak_base_y2 = center_y + 5   # 嘴根部下 y
    beak_base_x = center_x + radius # 嘴根部 x
    pygame.draw.polygon(screen, BEAK_ORANGE,
                       [(beak_tip_x, beak_tip_y),
                        (beak_base_x, beak_base_y1),
                        (beak_base_x, beak_base_y2)])

def get_bird_rect(bird):
    """获取小鸟碰撞检测矩形"""
    return pygame.Rect(bird['x'], bird['y'], bird['width'], bird['height'])

def create_pipe():
    """创建管道状态字典"""
    # 随机化缺口中心的位置，确保管道至少有一定高度
    min_center_y = PIPE_GAP // 2 + 50
    max_center_y = SCREEN_HEIGHT - PIPE_GAP // 2 - 50
    gap_center_y = random.randint(min_center_y, max_center_y)

    top_pipe_height = gap_center_y - PIPE_GAP // 2
    bottom_pipe_y = gap_center_y + PIPE_GAP // 2

    return {
        'x': SCREEN_WIDTH,
        'width': 60,
        'top_height': top_pipe_height, # 上管道的高度
        'bottom_y': bottom_pipe_y,    # 下管道的顶部Y坐标
        'passed': False
    }

def update_pipe(pipe):
    """纯函数更新管道状态"""
    return {**pipe, 'x': pipe['x'] - PIPE_SPEED}

def draw_pipe(pipe):
    """绘制管道（无副作用）"""
    # 上管道主体
    pygame.draw.rect(screen, PIPE_GREEN, (pipe['x'], 0, pipe['width'], pipe['top_height']))
    # 上管道边缘装饰
    pygame.draw.rect(screen, PIPE_BORDER_GREEN, (pipe['x'] - 2, pipe['top_height'] - 10, pipe['width'] + 4, 10)) # 稍微宽一点
    pygame.draw.rect(screen, BLACK, (pipe['x'] - 2, pipe['top_height'] - 10, pipe['width'] + 4, 10), 1) # 黑色描边

    # 下管道主体
    bottom_pipe_height = SCREEN_HEIGHT - pipe['bottom_y']
    pygame.draw.rect(screen, PIPE_GREEN, (pipe['x'], pipe['bottom_y'], pipe['width'], bottom_pipe_height))
    # 下管道边缘装饰
    pygame.draw.rect(screen, PIPE_BORDER_GREEN, (pipe['x'] - 2, pipe['bottom_y'], pipe['width'] + 4, 10)) # 稍微宽一点
    pygame.draw.rect(screen, BLACK, (pipe['x'] - 2, pipe['bottom_y'], pipe['width'] + 4, 10), 1) # 黑色描边

def pipe_collide(pipe, bird):
    """检测管道与小鸟碰撞"""
    bird_rect = get_bird_rect(bird)
    top_pipe_rect = pygame.Rect(pipe['x'], 0, pipe['width'], pipe['top_height'])
    bottom_pipe_rect = pygame.Rect(pipe['x'], pipe['bottom_y'], pipe['width'], SCREEN_HEIGHT - pipe['bottom_y'])

    return bird_rect.colliderect(top_pipe_rect) or bird_rect.colliderect(bottom_pipe_rect)

# --- 游戏状态重置 ---
def reset_game(game_state):
    """重置游戏状态以开始新游戏"""
    # 保留最高分和排行榜，重置其他状态
    return {
        **game_state, # 保留 highscore, leaderboard
        'bird': create_bird(),
        'pipes': [],
        'score': 0,
        'last_pipe': pygame.time.get_ticks() - PIPE_FREQUENCY + 500, # 稍微延迟第一次出管
        'game_active': True,
        'game_over': False,
        'player_name': "", # 重置玩家名
        'input_active': False,
        'name_entered': False # 重置名字输入状态
    }

# --- 主游戏函数 ---
def main():
    # 初始化游戏状态
    game_state = {
        'bird': create_bird(),
        'pipes': [],
        'score': 0,
        'last_pipe': 0, # 会在reset_game或首次开始时设置
        'game_active': False, # 初始为非活动状态
        'game_over': False,
        'highscore': load_highscore(),
        'leaderboard': load_leaderboard(),
        'player_name': "",
        'input_active': False, # 是否处于名字输入状态
        'name_entered': False  # 名字是否已输入完成
    }

    running = True
    while running:
        # --- 事件处理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False # 结束主循环
            if event.type == pygame.KEYDOWN:
                if game_state['input_active']:
                    # 处理玩家名称输入
                    if event.key == pygame.K_RETURN:
                        # 确认输入 (名字不能为空)
                        if game_state['player_name'].strip(): # 去掉首尾空格后判断
                            game_state['leaderboard'] = add_to_leaderboard(
                                game_state['leaderboard'],
                                game_state['player_name'].strip(), # 保存处理过的名字
                                game_state['score']
                            )
                            save_leaderboard(game_state['leaderboard'])
                            game_state['input_active'] = False
                            game_state['name_entered'] = True # 标记名字已输入
                        else:
                            # 可以在这里加个提示，比如输入框闪烁或提示文字
                            print("名字不能为空！")
                    elif event.key == pygame.K_BACKSPACE:
                        game_state['player_name'] = game_state['player_name'][:-1]
                    else:
                        # 限制名称长度为10个字符, 且是可打印字符
                        if len(game_state['player_name']) < 10 and event.unicode.isprintable():
                            game_state['player_name'] += event.unicode
                # 非输入状态下的按键处理
                elif event.key == pygame.K_SPACE:
                    if game_state['game_active']:
                        game_state['bird'] = jump_bird(game_state['bird'])
                    elif game_state['game_over']: # 游戏结束状态
                        if not game_state['name_entered']: # 如果还没输入名字
                             # 检查是否需要输入名字（进入排行榜）
                            should_enter_name = game_state['score'] > 0 and (
                                len(game_state['leaderboard']) < MAX_LEADERBOARD_ENTRIES or
                                game_state['score'] > (min(entry["score"] for entry in game_state['leaderboard']) if game_state['leaderboard'] else 0)
                            )
                            if should_enter_name:
                                game_state['input_active'] = True # 激活输入状态
                                game_state['player_name'] = ""    # 清空名字
                            else:
                                # 不需要输入名字，直接重置游戏
                                game_state = reset_game(game_state)
                        else:
                            # 名字已经输入过了，按空格直接重置游戏
                             game_state = reset_game(game_state)
                    else: # 初始界面状态
                        game_state = reset_game(game_state) # 开始新游戏

        # --- 游戏逻辑更新 ---
        if game_state['game_active']:
            # 更新小鸟
            game_state['bird'] = update_bird(game_state['bird'])

            # 检测小鸟是否落地 (碰撞)
            if game_state['bird']['y'] + game_state['bird']['height'] >= SCREEN_HEIGHT:
                game_state['game_active'] = False
                game_state['game_over'] = True
                # 更新最高分(如果需要)
                if game_state['score'] > game_state['highscore']:
                    game_state['highscore'] = game_state['score']
                    save_highscore(game_state['highscore'])
                # 不在此处检查是否进入排行榜，交给按空格后的逻辑

            # 生成新管道
            time_now = pygame.time.get_ticks()
            if time_now - game_state['last_pipe'] > PIPE_FREQUENCY:
                game_state['pipes'].append(create_pipe())
                game_state['last_pipe'] = time_now

            # 更新管道并处理碰撞和计分
            updated_pipes = []
            for pipe in game_state['pipes']:
                # 管道碰撞检测
                if pipe_collide(pipe, game_state['bird']):
                    game_state['game_active'] = False
                    game_state['game_over'] = True
                    # 更新最高分(如果需要)
                    if game_state['score'] > game_state['highscore']:
                        game_state['highscore'] = game_state['score']
                        save_highscore(game_state['highscore'])
                    # 碰撞后不需要再更新这条管道的位置了，但还是要保留以绘制结束画面
                    updated_pipes.append(pipe) # 保留当前状态的管道
                    continue # 跳过该管道的后续处理

                # 更新管道位置
                updated_pipe = update_pipe(pipe)

                # 计分逻辑
                bird_center_x = game_state['bird']['x'] + game_state['bird']['width'] // 2
                pipe_end_x = updated_pipe['x'] + updated_pipe['width']
                if not updated_pipe['passed'] and bird_center_x > pipe_end_x:
                    updated_pipe = {**updated_pipe, 'passed': True}
                    game_state['score'] += 1

                # 保留仍在屏幕内或刚出屏幕的管道
                if updated_pipe['x'] > -updated_pipe['width']:
                    updated_pipes.append(updated_pipe)

            game_state['pipes'] = updated_pipes


        # --- 绘制 ---
        # 绘制背景
        screen.fill(SKY_BLUE)

        # 绘制管道 (无论游戏是否激活都要画，除非是初始界面)
        if game_state['game_active'] or game_state['game_over']:
            for pipe in game_state['pipes']:
                draw_pipe(pipe)

        # 绘制小鸟 (根据状态绘制)
        if game_state['game_active'] or game_state['game_over']:
             draw_bird(game_state['bird']) # 绘制游戏中的或结束时的小鸟
        elif not game_state['game_active'] and not game_state['game_over']: # 初始界面
             # 开始游戏动画小鸟
             animated_y = SCREEN_HEIGHT // 2 + 20 * math.sin(pygame.time.get_ticks() * 0.005) # 幅度小一点
             animated_bird_state = create_bird()
             animated_bird_state['y'] = animated_y
             draw_bird(animated_bird_state) # 只绘制这个动画鸟


        # 显示分数 (仅在游戏活动时显示在左上角)
        if game_state['game_active']:
            score_surf = font.render(f'{game_state["score"]}', True, WHITE)
            score_rect = score_surf.get_rect(topleft=(20, 15))
            # 绘制半透明背景
            bg_rect = pygame.Rect(10, 10, score_rect.width + 20, score_rect.height + 10)
            # 创建一个带alpha通道的surface来绘制半透明矩形
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill(TEXT_BG_COLOR)
            screen.blit(s, (bg_rect.left, bg_rect.top))
            # 绘制分数文本
            screen.blit(score_surf, score_rect)


        # 游戏开始/结束提示
        if not game_state['game_active']:
            if game_state['game_over']:
                if game_state['input_active']:
                    # --- 显示输入名字界面 ---
                    # 提示文本
                    prompt_surf = font.render('进入排行榜! 输入名字:', True, WHITE)
                    prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
                    screen.blit(prompt_surf, prompt_rect)

                    # 输入框背景
                    input_box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20, 200, 40)
                    pygame.draw.rect(screen, WHITE, input_box_rect, 2, border_radius=5) # 带圆角

                    # 显示输入的文本
                    name_surf = font.render(game_state['player_name'], True, WHITE)
                    # 文本应该在输入框内左对齐，加一点边距
                    name_rect = name_surf.get_rect(midleft=(input_box_rect.left + 10, input_box_rect.centery))
                    screen.blit(name_surf, name_rect)

                    # 光标效果 (可选，简单的闪烁下划线)
                    if pygame.time.get_ticks() % 1000 < 500: # 每秒闪烁一次
                        cursor_x = name_rect.right + (5 if game_state['player_name'] else 0) # 根据有无文字调整位置
                        cursor_y = input_box_rect.bottom - 5
                        pygame.draw.line(screen, WHITE, (cursor_x, input_box_rect.top + 5), (cursor_x, cursor_y), 2)


                    # 确认提示
                    enter_surf = highscore_font.render('按 Enter 确认', True, WHITE)
                    enter_rect = enter_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                    screen.blit(enter_surf, enter_rect)

                else: # 非输入状态的游戏结束界面
                    # --- 显示游戏结束信息和排行榜 ---
                    y_pos = SCREEN_HEIGHT // 2 - 150 # 初始Y坐标

                    # 游戏结束文本
                    over_surf = font.render('游戏结束!', True, RED) # 用红色更醒目
                    over_rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                    screen.blit(over_surf, over_rect)
                    y_pos += 40

                    # 分数文本
                    score_surf = highscore_font.render(f'得分: {game_state["score"]}', True, WHITE)
                    score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                    screen.blit(score_surf, score_rect)
                    y_pos += 30

                    # 最高分文本
                    hs_surf = highscore_font.render(f'最高分: {game_state["highscore"]}', True, WHITE)
                    hs_rect = hs_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                    screen.blit(hs_surf, hs_rect)
                    y_pos += 50 # 留出更多空间给排行榜

                    # 显示排行榜标题
                    lb_title_surf = font.render('排行榜', True, WHITE)
                    lb_title_rect = lb_title_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                    screen.blit(lb_title_surf, lb_title_rect)
                    y_pos += 35

                    # 显示排行榜条目
                    if game_state['leaderboard']:
                        for i, entry in enumerate(game_state['leaderboard']):
                            rank_surf = highscore_font.render(f"{i+1}. {entry['name']} : {entry['score']}", True, WHITE)
                            rank_rect = rank_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                            screen.blit(rank_surf, rank_rect)
                            y_pos += 25
                    else:
                         no_lb_surf = highscore_font.render("暂无记录", True, WHITE)
                         no_lb_rect = no_lb_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                         screen.blit(no_lb_surf, no_lb_rect)
                         y_pos += 25


                    # 重新开始提示 (根据是否需要输入名字调整位置)
                    y_pos = max(y_pos, SCREEN_HEIGHT // 2 + 120) # 确保提示在排行榜下方
                    restart_surf = highscore_font.render('按空格键继续', True, WHITE)
                    restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                    screen.blit(restart_surf, restart_rect)

            else: # 初始开始界面
                # 绘制游戏标题
                title_surf = font.render('像素小鸟', True, WHITE)
                title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
                screen.blit(title_surf, title_rect)

                # 绘制操作提示
                start_surf = font.render('按空格键开始游戏', True, WHITE)
                start_rect = start_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
                screen.blit(start_surf, start_rect)

        # 更新显示
        pygame.display.update()
        clock.tick(60) # 控制帧率

    # 退出 Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
