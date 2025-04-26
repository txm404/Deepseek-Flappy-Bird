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

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('像素小鸟')
clock = pygame.time.Clock()
font = pygame.font.SysFont('Noto Sans CJK TC', 30)
highscore_font = pygame.font.SysFont('Noto Sans CJK TC', 25) # Smaller font for highscore

# 文件路径
HIGHSCORE_FILE = "highscore.txt"
LEADERBOARD_FILE = "leaderboard.json"  # 新增排行榜文件
MAX_LEADERBOARD_ENTRIES = 5  # 排行榜显示的最大记录数

# Helper function to load high score
def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return int(f.read())
        except ValueError:
            print(f"Warning: Could not read high score from {HIGHSCORE_FILE}. Resetting to 0.")
            return 0
    else:
        return 0

# Helper function to save high score
def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(score))
    except IOError:
        print(f"Warning: Could not save high score to {HIGHSCORE_FILE}.")

# 添加排行榜相关函数
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Could not read leaderboard from {LEADERBOARD_FILE}. Creating new leaderboard.")
            return []
    else:
        return []

def save_leaderboard(leaderboard):
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f)
    except IOError:
        print(f"Warning: Could not save leaderboard to {LEADERBOARD_FILE}.")

def add_to_leaderboard(leaderboard, name, score):
    # 添加新分数到排行榜
    leaderboard.append({"name": name, "score": score})
    # 根据分数排序（降序）
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    # 只保留前N名
    return leaderboard[:MAX_LEADERBOARD_ENTRIES]

class Bird:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.width = 30
        self.height = 30
        
    def update(self):
        # 应用重力
        self.velocity += GRAVITY
        self.y += self.velocity
        
        # 防止小鸟飞出屏幕顶部
        if self.y < 0:
            self.y = 0
            self.velocity = 0
            
    def jump(self):
        self.velocity = BIRD_JUMP
        
    def draw(self):
        # 绘制小鸟身体(圆形)
        pygame.draw.circle(screen, (255, 200, 0), (self.x + 15, self.y + 15), 15)
        # 绘制小鸟眼睛
        pygame.draw.circle(screen, WHITE, (self.x + 20, self.y + 10), 4)
        pygame.draw.circle(screen, BLACK, (self.x + 20, self.y + 10), 2)
        # 绘制小鸟嘴巴(三角形)
        pygame.draw.polygon(screen, (255, 100, 0), 
                           [(self.x + 40, self.y + 15), 
                            (self.x + 30, self.y + 10),
                            (self.x + 30, self.y + 20)])
        
    def get_mask(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Pipe:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.height = random.randint(150, 400)
        self.gap = PIPE_GAP
        self.top = self.height - self.gap // 2
        self.bottom = self.height + self.gap // 2
        self.width = 60
        self.passed = False
        
    def update(self):
        self.x -= PIPE_SPEED
        
    def draw(self):
        # 上管道
        pygame.draw.rect(screen, (0, 180, 0), (self.x, 0, self.width, self.top))
        # 上管道装饰(边缘)
        pygame.draw.rect(screen, (0, 220, 0), (self.x, self.top - 10, self.width, 10))
        # 下管道
        pygame.draw.rect(screen, (0, 180, 0), (self.x, self.bottom, self.width, SCREEN_HEIGHT - self.bottom))
        # 下管道装饰(边缘)
        pygame.draw.rect(screen, (0, 220, 0), (self.x, self.bottom, self.width, 10))
        
    def collide(self, bird):
        bird_rect = bird.get_mask()
        top_pipe = pygame.Rect(self.x, 0, self.width, self.top)
        bottom_pipe = pygame.Rect(self.x, self.bottom, self.width, SCREEN_HEIGHT - self.bottom)
        
        return bird_rect.colliderect(top_pipe) or bird_rect.colliderect(bottom_pipe)

def main():
    bird = Bird()
    pipes = []
    score = 0
    last_pipe = pygame.time.get_ticks()
    game_active = False
    game_over = False
    highscore = load_highscore()
    leaderboard = load_leaderboard()  # 加载排行榜
    
    # 玩家名称输入相关变量
    player_name = ""
    input_active = False
    name_entered = False
    
    while True:
        clock.tick(60)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if input_active:
                    # 处理玩家名称输入
                    if event.key == pygame.K_RETURN:
                        # 输入完成，添加到排行榜
                        if player_name:
                            leaderboard = add_to_leaderboard(leaderboard, player_name, score)
                            save_leaderboard(leaderboard)
                            input_active = False
                            name_entered = True
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        # 限制名称长度为10个字符
                        if len(player_name) < 10 and event.unicode.isprintable():
                            player_name += event.unicode
                elif event.key == pygame.K_SPACE:
                    if game_active:
                        bird.jump()
                    else:
                        if game_over and not name_entered and not input_active:
                            # 检查是否需要输入名字（进入排行榜）
                            if score > 0 and (len(leaderboard) < MAX_LEADERBOARD_ENTRIES or score > min([entry["score"] for entry in leaderboard] if leaderboard else [0])):
                                input_active = True
                                player_name = ""
                            else:
                                game_active = True
                                game_over = False
                                bird = Bird()
                                pipes = []
                                score = 0
                                last_pipe = pygame.time.get_ticks()
                                name_entered = False
                        elif game_over and name_entered:
                            # 重新开始游戏
                            game_active = True
                            game_over = False
                            bird = Bird()
                            pipes = []
                            score = 0
                            last_pipe = pygame.time.get_ticks()
                            name_entered = False
                        else:
                            # 首次开始游戏
                            game_active = True
                            game_over = False
                            bird = Bird()
                            pipes = []
                            score = 0
                            last_pipe = pygame.time.get_ticks()
        
        # 清屏并绘制纯色背景
        screen.fill((100, 150, 255))
        
        if game_active:
            # 更新小鸟
            bird.update()
            
            # 生成新管道
            time_now = pygame.time.get_ticks()
            if time_now - last_pipe > PIPE_FREQUENCY:
                pipes.append(Pipe())
                last_pipe = time_now
                
            # 更新管道
            for pipe in pipes:
                pipe.update()
                
                # 计分
                if pipe.x + pipe.width < bird.x and not pipe.passed:
                    pipe.passed = True
                    score += 1
                    
                # 碰撞检测
                if pipe.collide(bird):
                    game_active = False
                    game_over = True
                    if score > highscore:
                        highscore = score
                        save_highscore(highscore)
                    
                # 移除屏幕外的管道
                if pipe.x < -pipe.width:
                    pipes.remove(pipe)
            
            # 检测小鸟是否落地
            if bird.y + bird.height >= SCREEN_HEIGHT:
                game_active = False
                game_over = True
                if score > highscore:
                    highscore = score
                    save_highscore(highscore)
        
        # 绘制
        for pipe in pipes:
            pipe.draw()
            
        bird.draw()
        
        # 显示分数(带背景框)
        score_text = font.render(f'{score}', True, WHITE)
        text_rect = score_text.get_rect()
        pygame.draw.rect(screen, (0, 0, 0, 128), (10, 10, text_rect.width + 20, text_rect.height + 10), border_radius=5)
        screen.blit(score_text, (20, 15))
        
        # 游戏开始/结束提示
        if not game_active:
            if game_over:
                if input_active:
                    # 显示输入名字界面
                    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 30)
                    pygame.draw.rect(screen, WHITE, input_box, 2)
                    
                    # 渲染提示文本
                    prompt_text = font.render('输入你的名字:', True, WHITE)
                    prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
                    screen.blit(prompt_text, prompt_rect)
                    
                    # 渲染输入的文本
                    name_text = font.render(player_name, True, WHITE)
                    name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 15))
                    screen.blit(name_text, name_rect)
                    
                    # 渲染提示按Enter确认
                    enter_text = highscore_font.render('按Enter确认', True, WHITE)
                    enter_rect = enter_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                    screen.blit(enter_text, enter_rect)
                else:
                    # 游戏结束文本
                    text = font.render('游戏结束!', True, WHITE)
                    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
                    screen.blit(text, text_rect)

                    # 分数文本
                    score_text_end = highscore_font.render(f'得分: {score}', True, WHITE)
                    score_rect_end = score_text_end.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
                    screen.blit(score_text_end, score_rect_end)

                    # 最高分文本
                    highscore_text = highscore_font.render(f'最高分: {highscore}', True, WHITE)
                    highscore_rect = highscore_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                    screen.blit(highscore_text, highscore_rect)
                    
                    # 显示排行榜
                    title_text = font.render('排行榜', True, WHITE)
                    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
                    screen.blit(title_text, title_rect)
                    
                    # 显示排行榜条目
                    y_offset = 20
                    for i, entry in enumerate(leaderboard):
                        rank_text = highscore_font.render(f"{i+1}. {entry['name']}: {entry['score']}", True, WHITE)
                        rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
                        screen.blit(rank_text, rank_rect)
                        y_offset += 25
                    
                    # 重新开始提示
                    text2 = highscore_font.render('按空格键重新开始', True, WHITE)
                    text2_rect = text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140))
                    screen.blit(text2, text2_rect)
            else:
                # 开始游戏动画
                bird.y = SCREEN_HEIGHT // 2 + 50 * math.sin(pygame.time.get_ticks() * 0.005)
                bird.draw()
                text = font.render('按空格键开始游戏', True, WHITE)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
        
        pygame.display.update()

if __name__ == "__main__":
    main()
