import json
import time
import tkinter as tk
import customtkinter as ctk
import os
from tkinter import PhotoImage
from PIL import Image, ImageTk
from customtkinter import CTkCanvas, CTkButton
from tkinter import scrolledtext

with open('TOM3.json', 'r', encoding='utf-8') as file:
    json_data = json.load(file)

def get_card_image(card):
    card_images = {
        '梅花 A': '1.png', '梅花 2': '2.png', '梅花 3': '3.png', '梅花 4': '4.png', '梅花 5': '5.png',
        '梅花 6': '6.png', '梅花 7': '7.png', '梅花 8': '8.png', '梅花 9': '9.png', '梅花 10': '10.png',
        '梅花 J': '11.png', '梅花 Q': '12.png', '梅花 K': '13.png',
        '红心 A': '14.png', '红心 2': '15.png', '红心 3': '16.png', '红心 4': '17.png', '红心 5': '18.png',
        '红心 6': '19.png', '红心 7': '20.png', '红心 8': '21.png', '红心 9': '22.png', '红心 10': '23.png',
        '红心 J': '24.png', '红心 Q': '25.png', '红心 K': '26.png',
        '黑桃 A': '27.png', '黑桃 2': '28.png', '黑桃 3': '29.png', '黑桃 4': '30.png', '黑桃 5': '31.png',
        '黑桃 6': '32.png', '黑桃 7': '33.png', '黑桃 8': '34.png', '黑桃 9': '35.png', '黑桃 10': '36.png',
        '黑桃 J': '37.png', '黑桃 Q': '38.png', '黑桃 K': '39.png',
        '方片 A': '40.png', '方片 2': '41.png', '方片 2': '41.png', '方片 3': '42.png', '方片 4': '43.png', '方片 5': '44.png',
        '方片 6': '45.png', '方片 7': '46.png', '方片 8': '47.png', '方片 9': '48.png', '方片 10': '49.png',
        '方片 J': '50.png', '方片 Q': '51.png', '方片 K': '52.png',
        '小王': '53.png', '大王': '54.png'
    }
    return card_images.get(card)

def display_round_data(round_number):
    center_canvas.delete('all')  # Clear the center canvas

    # Now we can get the correct width and height for center_canvas
    center_canvas_width = center_canvas.winfo_width()
    center_canvas_height = center_canvas.winfo_height()

    for player in json_data:
        if player['轮次'] == round_number:

            player_index = player['玩家索引']
            hand = player['手牌']
            summary = player['解说']
            played_cards = player.get('玩家出牌', [])  # 使用get方法,默认为空列表

            player_boxes[player_index].delete('all')
            player_summaries[player_index].delete('1.0', tk.END)

            # 从手牌中移除已出的牌
            for card in played_cards:
                if card in hand:
                    hand.remove(card)

            x, y = 0, 0
            photo_references = []  # A new list to store photo references
            for i, card in enumerate(hand):
                card_image = get_card_image(card)
                if card_image:
                    image_path = f"D:/myproject/static/images/{card_image}"  # Ensure this path is correct
                    image = Image.open(image_path)
                    image = image.resize((50, 60))  # Adjust the image size
                    photo = ImageTk.PhotoImage(image)
                    player_boxes[player_index].create_image(x, y, image=photo, anchor='nw')
                    photo_references.append(photo)  # Store the reference
                    x += 55  # Adjust the next card's horizontal position
                    if (i + 1) % 15 == 0:  # New row for every 12 cards
                        x = 0
                        y += 65  # Adjust the next row's vertical position
            player_boxes[player_index].photos = photo_references  # Attach the list of photo references to the canvas

            player_summaries[player_index].insert(tk.INSERT, summary)

    cx, cy = 50, 50  # 初始位置
    center_photo_references = []  # A list to store photo references for center canvas
    for player in json_data:
        if player['轮次'] == round_number:
            played_cards = player.get('玩家出牌', [])
            player_id = player.get('玩家索引', "")
            center_canvas.create_text(170, cy + 60, text=f"玩家: {player_id}", font=("Arial", 24), fill="black",
                                      anchor='w')
            if played_cards:
                # center_canvas.create_text(210, cy + 60, text=f"ID: {player_id}", font=("Arial", 24), fill="black",
                #                           anchor='w')

                for card in played_cards:
                    card_image = get_card_image(card)
                    if card_image:
                        image_path = f"D:/myproject/static/images/{card_image}"
                        image = Image.open(image_path)
                        image = image.resize((50, 60))
                        photo = ImageTk.PhotoImage(image)
                        center_canvas.create_image(cx, cy, image=photo, anchor='w')
                        center_photo_references.append(photo)
                        cx += 55
                cy += 80 
                cx = 50 
            else:
                # 如果玩家没有出牌,显示"PASS"
                # center_canvas.create_text(cx+50, cy, text=f"ID: {player_id} PASS", font=("Arial", 24), fill="black",
                #                           anchor='w')
                center_canvas.create_text(220, cy+10, text="PASS", font=("Arial", 24), fill="red")
                cy += 30 

    center_canvas.photos = center_photo_references


def update_rounds():
    current_round = 1
    while current_round <= max_round:
        display_round_data(current_round)
        time.sleep(1)  # 1秒延迟
        window.update()
        current_round += 1

def start_game():
    # Filter out players with missing or invalid '轮次' values
    global max_round
    rounds = [player['轮次'] for player in json_data if isinstance(player.get('轮次'), int)]
    if rounds:
        max_round = max(rounds)
        update_rounds()
    else:
        print("No valid round numbers found in the JSON data.")

window = ctk.CTk()
window.title("Guan Dan Game Visualizer")
window.geometry('1920x1080') 

player_boxes = {}
player_summaries = {}

player_area_weight = 6

for i in range(4):
    frame = ctk.CTkFrame(window, corner_radius=10)
    if i == 0:
        frame.grid(row=0, column=0, padx=50, pady=20, sticky='nsew')
    elif i == 1:
        frame.grid(row=0, column=2, padx=50, pady=20, sticky='nsew')
    elif i == 2:
        frame.grid(row=2, column=2, padx=50, pady=20, sticky='nsew')
    else:
        frame.grid(row=2, column=0, padx=50, pady=20, sticky='nsew')

    window.grid_columnconfigure(i % 2 * 2, weight=3)
    window.grid_rowconfigure(i // 2 * 2, weight=3)

    canvas = tk.Canvas(frame, bg='white', highlightthickness=0)
    canvas.grid(row=0, column=0, sticky='nsew')

    frame.grid_rowconfigure(0, weight=4) 
    frame.grid_columnconfigure(0, weight=4)
    player_boxes[i] = canvas

    frame.grid_rowconfigure(1, weight=1)

    summary_text = scrolledtext.ScrolledText(
        frame,
        wrap='word',
        font=("宋体", 10, "normal"),
        padx=10,
        pady=10,
        background='white',
        foreground='black',
        insertbackground='black',
    )
    summary_text.grid(row=1, column=0, sticky='nsew')
    player_summaries[i] = summary_text

center_frame = ctk.CTkFrame(window, corner_radius=10)
center_frame.grid(row=1, column=1, padx=50, pady=50, sticky='nsew')
window.grid_columnconfigure(1, weight=1)
window.grid_rowconfigure(1, weight=2) 

center_canvas = tk.Canvas(center_frame, bg='white', highlightthickness=0)
center_canvas.grid(row=0, column=0, sticky='nsew')
center_frame.grid_rowconfigure(0, weight=1)
center_frame.grid_columnconfigure(0, weight=1)


start_button = ctk.CTkButton(window, text="Start Game", command=start_game)
start_button.grid(row=3, column=0, columnspan=3, pady=50)

window.mainloop()
