import requests
import json
import re
import os
import sys
import webbrowser
import winreg
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlparse, parse_qs
from pygame import mixer
from io import BytesIO
import threading
from tkinter import PanedWindow


# API配置（初始值仅用于示例，实际运行从注册表读取）
API_URL = "https://api.nsmao.net/api/wy/query"
LEVEL = "jymaster"


# 初始化音频播放器
mixer.init()


class NetEaseMusicParser:

    def get_base_path(self):
        if getattr(sys, 'frozen', False):  # 是否是打包后的exe
            return os.path.dirname(sys.executable)
        else:
            return os.path.abspath(".")

    def __init__(self, root):
        self.root = root
        self.root.title("T3网易云歌曲解析器By.Metr0r")
        self.root.geometry("1500x1000")

        # 显示广告提示
        self._show_advertisement()

        # 检查API密钥
        self.api_key = self.check_api_key()
        if not self.api_key:
            self.prompt_for_api_key()
            self.api_key = self.check_api_key()

        # 从注册表读取下载路径
        self.download_path = self.get_download_path_from_registry()
        if not self.download_path:
            self.download_path = os.path.join(
                os.path.expanduser("~"), "Downloads")

        # 当前歌曲信息
        self.current_song = None
        self.current_volume = self.get_volume_from_registry()  # 默认音量70%
        mixer.music.set_volume(self.current_volume)

        # 初始化音量显示标签
        self.volume_value = None

        # 当前播放时长和歌曲长度
        self.song_length = 0

        # 新增歌词格式和编码变量
        self.lyric_format = StringVar(value="LRC")
        self.encoding = StringVar(value="utf-8")

        # 检查ffmpeg是否可用
        base_path = self.get_base_path()
        print(f"Base Path: {base_path}")
        ffmpeg_dir = os.path.join(
            base_path, "ffmpeg-2024-09-26-git-f43916e217-full_build", "bin")
        print(f"FFmpeg Dir: {ffmpeg_dir}")
        self.ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        print(f"FFmpeg Path: {self.ffmpeg_path}")
        print(f"是否存在: {os.path.exists(self.ffmpeg_path)}")
        self.has_ffmpeg = os.path.exists(self.ffmpeg_path)

        # 如果程序目录中没有，检查系统PATH
        if not self.has_ffmpeg:
            self.ffmpeg_path = self._find_ffmpeg_in_path()
            self.has_ffmpeg = self.ffmpeg_path is not None

        # 如果仍然没有找到，显示警告
        if not self.has_ffmpeg:
            self._show_ffmpeg_warning()

        # 创建现代化样式
        self.style = ttk.Style()

        # 圆角按钮样式
        self.style.configure("Rounded.TButton",
                             font=("微软雅黑", 10),
                             padding=6,
                             relief="flat",
                             borderwidth=1,
                             bordercolor="#bdbdbd",
                             background="#f5f5f5",
                             foreground="black",
                             focuscolor=self.style.lookup(
                                 "TButton", "focuscolor"),
                             focusthickness=self.style.lookup("TButton", "focusthickness"))
        self.style.map("Rounded.TButton",
                       background=[("active", "#e0e0e0"),
                                   ("!active", "#f5f5f5")],
                       bordercolor=[("active", "#9e9e9e"), ("!active", "#bdbdbd")])

        # 圆角组合框样式
        self.style.configure("Rounded.TCombobox",
                             arrowsize=12,
                             relief="flat",
                             borderwidth=1,
                             bordercolor="#bdbdbd",
                             padding=5,
                             fieldbackground="white")
        self.style.map("Rounded.TCombobox",
                       fieldbackground=[("readonly", "white")],
                       selectbackground=[("readonly", "#e0f7fa")],
                       selectforeground=[("readonly", "black")],
                       background=[("active", "#f5f5f5")],
                       bordercolor=[("active", "#9e9e9e"), ("!active", "#bdbdbd")])

        # 圆角框架样式
        self.style.configure("Rounded.TFrame",
                             background="white",
                             borderwidth=1,
                             relief="solid",
                             bordercolor="#bdbdbd")

        # 圆角树视图样式
        self.style.configure("Rounded.Treeview",
                             font=("微软雅黑", 10),
                             rowheight=25,
                             padding=2,
                             borderwidth=1,
                             relief="solid",
                             bordercolor="#bdbdbd")
        self.style.configure("Rounded.TTreeview.Heading",
                             font=("微软雅黑", 10, "bold"),
                             padding=2,
                             borderwidth=1,
                             relief="solid",
                             bordercolor="#bdbdbd")

        # 圆角滚动条样式
        self.style.configure("Rounded.Vertical.TScrollbar",
                             gripcount=0,
                             background="#e0e0e0",
                             bordercolor="#bdbdbd",
                             arrowcolor="#757575",
                             troughcolor="#f5f5f5")
        self.style.configure("Rounded.Horizontal.TScrollbar",
                             gripcount=0,
                             background="#e0e0e0",
                             bordercolor="#bdbdbd",
                             arrowcolor="#757575",
                             troughcolor="#f5f5f5")

        # 圆角标签样式
        self.style.configure("Rounded.TLabel",
                             font=("微软雅黑", 10),
                             padding=5,
                             borderwidth=1,
                             relief="solid",
                             bordercolor="#bdbdbd",
                             background="white")

        # 创建UI
        self.create_ui()

    def create_ui(self):
        # 主背景框架
        main_bg_frame = ttk.Frame(self.root, style="Rounded.TFrame")
        main_bg_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # 顶部框架
        top_frame = ttk.Frame(
            main_bg_frame, style="Rounded.TFrame", padding=10)
        top_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(top_frame, text="网易云歌曲链接:",
                  style="Rounded.TLabel").pack(side=LEFT)

        # 圆角输入框
        self.url_entry = ttk.Entry(
            top_frame, width=50, style="Rounded.TCombobox")
        self.url_entry.pack(side=LEFT, padx=5)

        # 解析按钮
        self.parse_btn = ttk.Button(
            top_frame,
            text="解析",
            command=self.parse_song,
            style="Rounded.TButton"
        )
        self.parse_btn.pack(side=LEFT, padx=5)

        # 下载歌词按钮
        self.download_lyric_btn = ttk.Button(
            top_frame,
            text="下载歌词",
            state=DISABLED,
            command=self.download_lyric,
            style="Rounded.TButton"
        )
        self.download_lyric_btn.pack(side=LEFT, padx=5)

        # 设置按钮
        self.settings_btn = ttk.Button(
            top_frame,
            text="更多设置",
            command=self.open_settings,
            style="Rounded.TButton"
        )
        self.settings_btn.pack(side=RIGHT, padx=5)

        # 主内容框架
        main_frame = ttk.Frame(main_bg_frame, style="Rounded.TFrame")
        main_frame.pack(fill=BOTH, expand=True)

        # 添加这行 - 创建PanedWindow
        main_paned = PanedWindow(main_frame, orient=HORIZONTAL)
        main_paned.pack(fill=BOTH, expand=True)

        # 左栏 - 歌曲信息
        left_frame = ttk.Frame(main_paned, style="Rounded.TFrame")
        main_paned.add(left_frame, minsize=300)  # 设置最小宽度

        # 右栏 - 歌词显示
        right_frame = ttk.Frame(main_paned, style="Rounded.TFrame")
        main_paned.add(right_frame, minsize=400)  # 设置最小宽度

        # 歌曲信息Treeview
        self.info_tree = ttk.Treeview(
            left_frame,
            columns=("value"),
            show="tree headings",
            style="Rounded.Treeview"
        )
        self.info_tree.heading("#0", text="属性", anchor=W)
        self.info_tree.heading("value", text="值", anchor=W)
        self.info_tree.column("#0", width=150, anchor=W, stretch=False)
        self.info_tree.column("value", width=250, anchor=W)

        # 滚动条
        vsb = ttk.Scrollbar(
            left_frame,
            orient="vertical",
            command=self.info_tree.yview,
            style="Rounded.Vertical.TScrollbar"
        )
        self.info_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        self.info_tree.pack(fill=BOTH, expand=True)

        # 歌词文本区域
        self.lyric_text = Text(
            right_frame,
            wrap=WORD,
            font=("微软雅黑", 12),
            bd=0,
            highlightthickness=1,
            highlightbackground="#bdbdbd"
        )
        scrollbar = ttk.Scrollbar(
            right_frame,
            command=self.lyric_text.yview,
            style="Rounded.Vertical.TScrollbar"
        )
        self.lyric_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.lyric_text.pack(fill=BOTH, expand=True)

        # 底部控制按钮框架
        bottom_frame = ttk.Frame(
            main_bg_frame, style="Rounded.TFrame", padding=10)
        bottom_frame.pack(fill=X, pady=(10, 0))

        # 底部按钮样式
        button_style = {
            "style": "Rounded.TButton",
            "padding": (10, 5)
        }

        # 实时歌词显示
        self.lyric_label = ttk.Label(
            main_bg_frame,
            text="",
            font=("微软雅黑", 14),
            anchor='center',
            foreground="blue",
            style="Rounded.TLabel"
        )
        self.lyric_label.pack(fill=X)

        # 播放控制区域
        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(side=LEFT, fill=X, expand=True)

        self.download_btn = ttk.Button(
            control_frame,
            text="下载歌曲",
            state=DISABLED,
            command=self.download_song,
            **button_style
        )
        self.download_btn.pack(side=LEFT, padx=5)

        self.play_btn = ttk.Button(
            control_frame,
            text="播放",
            state=DISABLED,
            command=self.play_song,
            **button_style
        )
        self.play_btn.pack(side=LEFT, padx=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="停止",
            state=DISABLED,
            command=self.stop_song,
            **button_style
        )
        self.stop_btn.pack(side=LEFT, padx=5)

        # 音量控制
        ttk.Label(control_frame, text="音量:", style="Rounded.TLabel").pack(
            side=LEFT, padx=(10, 0))
        self.volume_scale = ttk.Scale(
            control_frame,
            from_=0,
            to=100,
            orient=HORIZONTAL,
            command=self.set_volume,
            style="Rounded.Horizontal.TScale"
        )
        self.volume_scale.set(int(self.current_volume * 100))
        self.volume_scale.pack(side=LEFT, padx=5)

        # 添加音量数值显示标签
        self.volume_value = ttk.Label(
            control_frame,
            text=f"{int(self.current_volume * 100)}",
            style="Rounded.TLabel"
        )
        self.volume_value.pack(side=LEFT, padx=5)

        # 其他功能按钮
        func_frame = ttk.Frame(bottom_frame)
        func_frame.pack(side=RIGHT)

        self.mv_btn = ttk.Button(
            func_frame,
            text="播放MV",
            state=DISABLED,
            command=self.play_mv,
            **button_style
        )
        self.mv_btn.pack(side=LEFT, padx=5)

        self.select_folder_btn = ttk.Button(
            func_frame,
            text="选择下载文件夹",
            command=self.select_download_folder,
            **button_style
        )
        self.select_folder_btn.pack(side=LEFT, padx=5)

        self.open_folder_btn = ttk.Button(
            func_frame,
            text="打开下载文件夹",
            command=self.open_download_folder,
            **button_style
        )
        self.open_folder_btn.pack(side=LEFT, padx=5)

        # 歌词显示区域
        self.lyric_label = ttk.Label(
            main_bg_frame,
            text="",
            font=("微软雅黑", 14),
            anchor='center',
            foreground="blue",
            style="Rounded.TLabel"
        )
        self.lyric_label.pack(fill=X, pady=(0, 10))

        # 时间显示标签
        self.time_label = ttk.Label(
            main_bg_frame,
            text="00:00 / 00:00",
            anchor=E,
            style="Rounded.TLabel"
        )
        self.time_label.pack(fill=X)

        # 状态栏
        self.status_var = StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(
            main_bg_frame,
            textvariable=self.status_var,
            anchor=W,
            style="Rounded.TLabel"
        )
        status_bar.pack(fill=X)

        # 绑定双击事件以复制值
        self.info_tree.bind("<Double-1>", self.on_tree_double_click)

    def on_tree_double_click(self, event):
        item = self.info_tree.identify('item', event.x, event.y)
        column = self.info_tree.identify_column(event.x)

        if not item or not column:
            return

        # 获取完整值
        full_value = self.info_tree.item(item, "values")[0]

        if full_value and column == "#1":  # 点击"值"列
            self.root.clipboard_clear()
            self.root.clipboard_append(full_value)
            self.status_var.set(f"已复制: {full_value}")
            messagebox.showinfo(
                "提示", f"已复制:\n{full_value}", icon=messagebox.INFO)

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    def update_time_display(self):
        if mixer.music.get_busy():
            current_pos = mixer.music.get_pos() / 1000
            time_str = f"{self.format_time(current_pos)} / {self.format_time(self.song_length)}"
            self.time_label.config(text=time_str)

            # 更新歌词
            self.update_lyric_display(current_pos)

            self.root.after(500, self.update_time_display)
        else:
            self.time_label.config(text="00:00 / 00:00")
            self.lyric_label.config(text="")  # 播放结束清空歌词

    def parse_lyrics(self, lyric_text):
        lines = lyric_text.strip().split('\n')
        parsed = []

        for line in lines:
            if not line.startswith('[') or ']' not in line:
                continue
            time_str, text = line.split(']', 1)
            time_str = time_str[1:]  # 去掉[
            try:
                m, s = map(float, time_str.split(':'))
                sec = int(m * 60 + s)
                parsed.append((sec, text.strip()))
            except:
                continue

        return sorted(parsed, key=lambda x: x[0])

    def update_lyric_display(self, current_time):
        if not hasattr(self, '_parsed_lyrics') or not self._parsed_lyrics:
            return

        # 显示当前时间对应的歌词
        current_lyric = ""
        for i, (time_sec, text) in enumerate(self._parsed_lyrics):
            if current_time >= time_sec:
                if i + 1 >= len(self._parsed_lyrics) or current_time < self._parsed_lyrics[i+1][0]:
                    current_lyric = text
                    break

        if current_lyric:
            self.lyric_label.config(text=current_lyric)

    def parse_song(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入网易云歌曲链接")
            return

        song_id = self.extract_song_id(url)
        if not song_id:
            messagebox.showerror("错误", "无法从链接中提取歌曲ID")
            return

        self.status_var.set("正在解析歌曲...")
        self.parse_btn.config(state=DISABLED)
        threading.Thread(target=self._fetch_song_data,
                         args=(song_id,), daemon=True).start()

    def _fetch_song_data(self, song_id):
        try:
            params = {
                "key": self.api_key,
                "id": song_id,
                "type": "json",
                "level": LEVEL
            }

            response = requests.get(API_URL, params=params)
            response.raise_for_status()

            data = response.json()
            self.root.after(0, self._handle_response, data)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))

    def _handle_response(self, data):
        self.parse_btn.config(state=NORMAL)

        if data.get("code") != 200:
            messagebox.showerror("错误", data.get("msg", "未知错误"))
            self.status_var.set("解析失败")
            return

        self.current_song = data["data"]
        self.status_var.set("解析成功")

        # 启用相关按钮
        self.download_btn.config(state=NORMAL)
        self.play_btn.config(state=NORMAL)
        self.stop_btn.config(state=NORMAL)
        self.mv_btn.config(state=NORMAL if self.current_song.get(
            "mv_info", {}).get("mv") else DISABLED)

        # 清除旧数据
        for item in self.info_tree.get_children():
            self.info_tree.delete(item)

        # 显示歌曲信息 (左栏)
        song_info = [
            ("歌曲ID", self.current_song.get("id", "")),
            ("歌曲名", self.current_song.get("name", "")),
            ("歌手", self.current_song.get("artist", "")),
            ("专辑名", self.current_song.get("album", "")),
            ("歌曲总时长", self.current_song.get("duration", "")),
            ("歌曲文件大小", self.current_song.get("size", "")),
            ("音质", self.current_song.get("format", "")),
            ("封面", self.current_song.get("pic", "")),
            ("直链", self.current_song.get("url", "")),
            ("Tips:双击可以复制哦~", self.current_song.get("name", ""))
        ]

        for name, value in song_info:
            self.info_tree.insert("", "end", text=name,
                                  values=(value,), tags=("info",))

        self.info_tree.tag_configure("info", font=("微软雅黑", 10))

        # 显示歌词 (右栏)
        self.lyric_text.delete(1.0, END)
        if "lyric" in self.current_song:
            self.lyric_text.insert(END, self.current_song["lyric"])
            self.download_lyric_btn.config(state=NORMAL)
        else:
            self.lyric_text.insert(END, "无歌词信息")
            self.download_lyric_btn.config(state=DISABLED)

        # 解析歌词
        self._parsed_lyrics = []
        if "lyric" in self.current_song and self.current_song["lyric"]:
            self._parsed_lyrics = self.parse_lyrics(self.current_song["lyric"])
            self.lyric_label.config(text="准备显示歌词...")  # 初始提示
        else:
            self.lyric_label.config(text="无歌词信息")  # 无歌词时的提示

    def _handle_error(self, error_msg):
        self.parse_btn.config(state=NORMAL)
        messagebox.showerror("错误", f"解析失败: {error_msg}")
        self.status_var.set(f"错误: {error_msg}")

    def extract_song_id(self, url):
        parsed = urlparse(url)
        if parsed.netloc != "music.163.com":
            return None

        query = parse_qs(parsed.query)
        if "id" in query:
            return query["id"][0]

        if parsed.path == "/song":
            return query.get("id", [None])[0]

        match = re.search(r"(?:id=|/song\?id=)(\d+)", url)
        if match:
            return match.group(1)

        return None

    def download_song(self):
        if not self.current_song:
            return

        url = self.current_song.get("url")
        if not url:
            messagebox.showerror("错误", "没有可用的下载URL")
            return

        song_name = f"{self.current_song['name']} - {self.current_song['artist']}.flac"
        save_path = os.path.join(self.download_path, song_name)

        if os.path.exists(save_path):
            if not messagebox.askyesno("确认", "文件已存在，是否覆盖？"):
                return

        self.status_var.set(f"正在下载: {song_name}...")
        self.download_btn.config(state=DISABLED)
        threading.Thread(target=self._download_file, args=(
            url, save_path), daemon=True).start()

    def _download_file(self, url, save_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * \
                            100 if total_size > 0 else 0
                        self.root.after(
                            0, self._update_download_progress, progress)

            self.root.after(0, self._download_complete, save_path)
        except Exception as e:
            self.root.after(0, self._download_error, str(e))

    def _update_download_progress(self, progress):
        self.status_var.set(f"下载进度: {progress:.1f}%")

    def _download_complete(self, save_path):
        if not save_path.lower().endswith('.flac'):
            # 如果不是flac文件，直接完成
            self.download_btn.config(state=NORMAL)
            self.status_var.set(f"下载完成: {os.path.basename(save_path)}")
            messagebox.showinfo("完成", f"歌曲已保存到:\n{save_path}")
            return

        # 如果是flac文件且有ffmpeg，弹出格式选择对话框
        if self.has_ffmpeg:
            self._prompt_format_selection(save_path)
        else:
            self.download_btn.config(state=NORMAL)
            self.status_var.set(f"下载完成: {os.path.basename(save_path)}")
            messagebox.showinfo(
                "完成", f"歌曲已保存到:\n{save_path}\n(无ffmpeg，无法转换格式)")

            self.download_btn.config(state=NORMAL)
            self.status_var.set(f"下载完成: {os.path.basename(save_path)}")
            messagebox.showinfo("完成", f"歌曲已保存到:\n{save_path}")

    def _download_error(self, error_msg):
        self.download_btn.config(state=NORMAL)
        self.status_var.set(f"下载失败: {error_msg}")
        messagebox.showerror("错误", f"下载失败: {error_msg}")

    def download_and_play(self):
        """下载歌曲并播放"""
        if not self.current_song:
            return

        url = self.current_song.get("url")
        if not url:
            messagebox.showerror("错误", "没有可用的下载URL")
            return

        song_name = f"{self.current_song['name']} - {self.current_song['artist']}.flac"
        save_path = os.path.join(self.download_path, song_name)

        self.status_var.set(f"正在下载: {song_name}...")
        threading.Thread(target=self._download_and_play_file,
                         args=(url, save_path), daemon=True).start()

    def _download_and_play_file(self, url, save_path):
        """下载文件并播放的内部方法"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # 添加转换逻辑
            if save_path.lower().endswith('.flac') and self.has_ffmpeg:
                wav_path = save_path[:-5] + '.wav'
                if self._convert_flac_to_wav(save_path, wav_path):
                    os.remove(save_path)
                    save_path = wav_path

            self.root.after(0, lambda: self._play_downloaded_file(save_path))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "错误", f"下载失败: {str(e)}"))

    def _play_downloaded_file(self, save_path):
        """播放已下载文件的内部方法"""
        try:
            # 检查是否有转换后的wav文件
            if save_path.lower().endswith('.flac') and self.has_ffmpeg:
                wav_path = save_path[:-5] + '.wav'
                if os.path.exists(wav_path):
                    save_path = wav_path

            mixer.music.load(save_path)
            mixer.music.play()
            self.song_length = mixer.Sound(file=save_path).get_length()
            self.root.after(500, self.update_time_display)
            song_name = os.path.basename(save_path)
            self.status_var.set(f"正在播放: {song_name}")
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {e}")

    def play_song(self):
        if not self.current_song:
            return

        song_name = f"{self.current_song['name']} - {self.current_song['artist']}"
        flac_path = os.path.join(self.download_path, song_name + ".flac")
        wav_path = os.path.join(self.download_path, song_name + ".wav")

        # 检查文件是否存在（flac或wav）
        has_flac = os.path.exists(flac_path)
        has_wav = os.path.exists(wav_path)

        if not has_flac and not has_wav:
            choice = messagebox.askyesnocancel(
                "选择播放方式",
                "歌曲尚未下载。\n请选择：\n\n是：在线播放（需要网络）\n否：下载后再播放\n取消：取消播放"
            )
            if choice is None:
                return
            elif choice:
                self.stream_and_play(self.current_song.get("url"))
            else:
                self.download_and_play()
        else:
            try:
                # 优先播放WAV文件（如果存在）
                if has_wav:
                    mixer.music.load(wav_path)
                    save_path = wav_path
                else:
                    mixer.music.load(flac_path)
                    save_path = flac_path

                mixer.music.play()
                self.song_length = mixer.Sound(file=save_path).get_length()
                self.root.after(500, self.update_time_display)
                self.status_var.set(f"正在播放: {os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"播放失败: {e}")

    def stream_and_play(self, url):
        if not url:
            messagebox.showerror("错误", "没有可用的播放URL")
            return

        self.status_var.set("正在缓冲在线歌曲...")
        threading.Thread(target=self._stream_audio,
                         args=(url,), daemon=True).start()

    def _stream_audio(self, url):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            audio_data = BytesIO(response.content)
            temp_path = os.path.join(self.download_path, ".temp_stream.flac")
            with open(temp_path, "wb") as f:
                f.write(audio_data.getvalue())

            mixer.music.load(temp_path)
            mixer.music.play()
            self.song_length = mixer.Sound(temp_path).get_length()
            self.root.after(500, self.update_time_display)

            self.root.after(0, lambda: self.status_var.set("正在播放在线歌曲..."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "错误", f"在线播放失败: {str(e)}"))

    def stop_song(self):
        if mixer.music.get_busy():
            mixer.music.stop()
            self.status_var.set("播放已停止")

    def set_volume(self, val):
        try:
            volume = float(val) / 100.0  # 先用float转换，再除以100
            self.current_volume = volume
            mixer.music.set_volume(volume)
            if hasattr(self, 'volume_value') and self.volume_value:
                self.volume_value.config(text=f"{int(float(val))}")
        except ValueError:
            pass  # 忽略转换错误

    def play_mv(self):
        if not self.current_song or not self.current_song.get("mv_info", {}).get("mv"):
            return

        mv_url = self.current_song["mv_info"]["mv"]
        webbrowser.open(mv_url)

    def select_download_folder(self):
        folder = filedialog.askdirectory(
            title="选择下载文件夹", initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.save_download_path_to_registry(folder)
            messagebox.showinfo("成功", f"下载文件夹已设置为:\n{folder}")

    def open_download_folder(self):
        try:
            os.startfile(self.download_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")

    def save_download_path_to_registry(self, path):
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER, r"Software\NetEaseMusicParser")
            winreg.SetValueEx(key, "DownloadPath", 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"无法保存到注册表: {e}")

    def get_download_path_from_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\NetEaseMusicParser")
            value, _ = winreg.QueryValueEx(key, "DownloadPath")
            winreg.CloseKey(key)
            return value
        except WindowsError:
            return None

    def check_api_key(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\NetEaseMusicParser")
            api_key, _ = winreg.QueryValueEx(key, "APIKey")
            winreg.CloseKey(key)
            return api_key
        except WindowsError:
            return None

    def prompt_for_api_key(self):
        dialog = Toplevel(self.root)
        dialog.title("请输入API Key")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        # 主容器
        main_frame = ttk.Frame(dialog, style="Rounded.TFrame", padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(main_frame, text="请访问API网站获取并输入您的API Key：",
                  style="Rounded.TLabel").pack(pady=5)

        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=X, pady=5)

        api_entry = ttk.Entry(entry_frame, width=40,
                              show="*", style="Rounded.TCombobox")
        api_entry.pack(side=LEFT, expand=True, fill=X)

        website_btn = ttk.Button(
            entry_frame,
            text="打开网站",
            command=lambda: webbrowser.open(
                "https://api.nsmao.net/user/login"),
            style="Rounded.TButton"
        )
        website_btn.pack(side=RIGHT, padx=(5, 0))

        confirm_btn = ttk.Button(
            main_frame,
            text="确认",
            command=lambda: self._confirm_api_key(dialog, api_entry),
            style="Rounded.TButton"
        )
        confirm_btn.pack(pady=10)

        self.root.wait_window(dialog)

    def _confirm_api_key(self, dialog, api_entry):
        entered_key = api_entry.get().strip()
        if self.validate_api_key(entered_key):
            self.save_api_key_to_registry(entered_key)
            self.api_key = entered_key
            dialog.destroy()
        else:
            messagebox.showerror("错误", "请输入正确的API Key")
            api_entry.delete(0, END)

    def validate_api_key(self, key):
        return len(key) >= 16

    def save_api_key_to_registry(self, key):
        try:
            key_path = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER, r"Software\NetEaseMusicParser")
            winreg.SetValueEx(key_path, "APIKey", 0, winreg.REG_SZ, key)
            winreg.CloseKey(key_path)
        except Exception as e:
            print(f"写入注册表失败: {e}")

    def get_volume_from_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\NetEaseMusicParser")
            vol, _ = winreg.QueryValueEx(key, "Volume")
            winreg.CloseKey(key)
            return vol / 100.0
        except WindowsError:
            return 0.7  # 默认音量

    def save_volume_to_registry(self, volume):
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER, r"Software\NetEaseMusicParser")
            winreg.SetValueEx(key, "Volume", 0,
                              winreg.REG_DWORD, int(volume * 100))
            winreg.CloseKey(key)
        except Exception as e:
            print(f"写入音量失败: {e}")

    def open_settings(self):
        settings_win = Toplevel(self.root)
        settings_win.title("设置")
        settings_win.geometry("400x300")
        settings_win.resizable(False, False)
        settings_win.transient(self.root)
        settings_win.grab_set()

        # 主容器
        main_frame = ttk.Frame(
            settings_win, style="Rounded.TFrame", padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # 当前API Key
        current_key_frame = ttk.Frame(main_frame)
        current_key_frame.pack(fill=X, pady=5)

        ttk.Label(current_key_frame, text="当前API Key:",
                  style="Rounded.TLabel").pack(side=LEFT)
        current_key = self.api_key if self.api_key else "<未设置>"
        ttk.Label(current_key_frame, text=current_key, foreground="gray",
                  style="Rounded.TLabel").pack(side=LEFT, padx=10)

        # 更改API Key
        new_key_frame = ttk.Frame(main_frame)
        new_key_frame.pack(fill=X, pady=5)

        ttk.Label(new_key_frame, text="更改API Key:",
                  style="Rounded.TLabel").pack(side=LEFT)
        new_key_entry = ttk.Entry(
            new_key_frame, width=40, show="*", style="Rounded.TCombobox")
        new_key_entry.pack(side=LEFT, padx=10, fill=X, expand=True)

        # 音量设置
        volume_frame = ttk.Frame(main_frame)
        volume_frame.pack(fill=X, pady=5)

        ttk.Label(volume_frame, text="默认音量 (0-100):",
                  style="Rounded.TLabel").pack(side=LEFT)

        volume_scale = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient=HORIZONTAL,
            style="Rounded.Horizontal.TScale"
        )
        volume_scale.set(int(self.current_volume * 100))
        volume_scale.pack(side=LEFT, padx=10, fill=X, expand=True)

        # 添加音量数值显示
        self.settings_volume_value = ttk.Label(
            volume_frame,
            text=f"{int(self.current_volume * 100)}",
            style="Rounded.TLabel"
        )
        self.settings_volume_value.pack(side=LEFT)
        # 保存按钮
        save_btn = ttk.Button(
            main_frame,
            text="保存",
            command=lambda: self._save_settings(
                settings_win, new_key_entry, volume_scale),
            style="Rounded.TButton"
        )
        save_btn.pack(pady=10)

        # GitHub 链接
        github_frame = ttk.Frame(main_frame)
        github_frame.pack(fill=X, pady=5)

        self.github_link = ttk.Label(
            github_frame,
            text="GitHub开源地址: https://github.com/mete0rxsc/NetEase-Cloud-VIP-Song-Analysis",
            foreground="blue",
            cursor="hand2",  # 显示手型光标
            style="Rounded.TLabel"
        )
        self.github_link.pack(side=LEFT, padx=10)
        self.github_link.bind(
            "<Button-1>", lambda e: webbrowser.open_new("https://github.com/mete0rxsc/NetEase-Cloud-VIP-Song-Analysis"))

    def _save_settings(self, dialog, new_key_entry, volume_scale):
        new_key = new_key_entry.get().strip()
        if new_key and not self.validate_api_key(new_key):
            messagebox.showerror("错误", "请输入正确的API Key")
            return

        if new_key:
            self.save_api_key_to_registry(new_key)
            self.api_key = new_key

        volume_value = volume_scale.get()
        self.current_volume = volume_value / 100.0
        mixer.music.set_volume(self.current_volume)
        self.save_volume_to_registry(self.current_volume)

        # 更新主界面音量显示
        self.volume_scale.set(volume_value)
        self.volume_value.config(text=f"{int(volume_value)}")

        messagebox.showinfo("成功", "设置已保存")
        dialog.destroy()

    def download_lyric(self):
        if not self.current_song or not self.current_song.get("lyric"):
            return

        # 创建歌词下载对话框
        dialog = Toplevel(self.root)
        dialog.title("下载歌词")
        dialog.geometry("300x200")
        dialog.resizable(False, False)

        # 主容器
        main_frame = ttk.Frame(dialog, style="Rounded.TFrame", padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # 歌词格式选择
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=X, pady=5)

        ttk.Label(format_frame, text="选择歌词格式:", style="Rounded.TLabel").pack(
            side=LEFT, padx=(0, 10))

        self.lyric_format = StringVar(value="LRC")
        format_menu = ttk.Combobox(
            format_frame,
            textvariable=self.lyric_format,
            values=["LRC", "SRT"],
            state="readonly",
            style="Rounded.TCombobox"
        )
        format_menu.pack(side=LEFT, fill=X, expand=True)

        # 文件编码选择
        encoding_frame = ttk.Frame(main_frame)
        encoding_frame.pack(fill=X, pady=5)

        ttk.Label(encoding_frame, text="选择文件编码:",
                  style="Rounded.TLabel").pack(side=LEFT, padx=(0, 10))

        self.encoding = StringVar(value="utf-8")
        encoding_menu = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding,
            values=["utf-8", "gbk", "utf-16"],
            state="readonly",
            style="Rounded.TCombobox"
        )
        encoding_menu.pack(side=LEFT, fill=X, expand=True)

        # 保存按钮
        save_btn = ttk.Button(
            main_frame,
            text="保存",
            command=lambda: self._save_lyric(dialog),
            style="Rounded.TButton"
        )
        save_btn.pack(pady=10)

    def _save_lyric(self, dialog):
        file_ext = ".lrc" if self.lyric_format.get() == "LRC" else ".srt"

        # 确保lrc目录存在
        lrc_dir = os.path.join(self.download_path, "lrc")
        try:
            os.makedirs(lrc_dir, exist_ok=True)  # 创建目录(如果不存在)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建歌词目录: {str(e)}")
            return

        save_path = os.path.join(
            lrc_dir,  # 保存到lrc子目录
            f"{self.current_song['name']}-{self.current_song['artist']}{file_ext}"
        )

        try:
            with open(save_path, "w", encoding=self.encoding.get()) as f:
                f.write(self.current_song["lyric"])
            messagebox.showinfo("成功", f"歌词已保存到:\n{save_path}")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def _convert_flac_to_wav(self, input_path, output_path):
        """使用ffmpeg将FLAC转换为WAV"""
        import subprocess
        cmd = [
            self.ffmpeg_path,
            '-y',  # 自动覆盖已存在的文件
            '-i', input_path,
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '2',
            output_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"FLAC转WAV失败: {e}")
            return False

    def _find_ffmpeg_in_path(self):
        """检查系统PATH环境变量中是否有ffmpeg"""
        import shutil
        try:
            # 检查系统PATH中是否有ffmpeg
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                print(f"从系统PATH中找到ffmpeg: {ffmpeg_path}")
                return ffmpeg_path
        except Exception as e:
            print(f"检查系统PATH时出错: {e}")
        return None

    def _show_ffmpeg_warning(self):
        """显示ffmpeg未找到的警告"""
        warning_msg = (
            "未找到可用的ffmpeg:\n\n"
            "1. 程序目录中不存在ffmpeg\n"
            "2. 系统PATH环境变量中也未找到ffmpeg\n\n"
            "将无法将音频转换为WAV格式"
        )

        # 使用after延迟显示，避免干扰主窗口初始化
        self.root.after(100, lambda: messagebox.showwarning(
            "ffmpeg未找到", warning_msg))

    def _prompt_format_selection(self, flac_path):
        """显示格式选择对话框"""
        dialog = Toplevel(self.root)
        dialog.title("选择保存格式")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 主容器
        main_frame = ttk.Frame(dialog, style="Rounded.TFrame", padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(main_frame, text="""请选择要保存的音频格式:
                  flac在非专业播放器中无法播放，
                  如果您是小白用户，请选择wav格式
                  Tips:在选择了Wav格式的情况下，
                  程序可能会有卡顿，属格式转换中的正常现象""",
                  style="Rounded.TLabel").pack(pady=5)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        # 三个格式选择按钮
        flac_only_btn = ttk.Button(
            button_frame,
            text="仅保留FLAC",
            command=lambda: self._handle_format_selection(
                dialog, flac_path, "flac_only"),
            style="Rounded.TButton"
        )
        flac_only_btn.pack(side=LEFT, padx=5, expand=True)

        wav_only_btn = ttk.Button(
            button_frame,
            text="仅保留WAV",
            command=lambda: self._handle_format_selection(
                dialog, flac_path, "wav_only"),
            style="Rounded.TButton"
        )
        wav_only_btn.pack(side=LEFT, padx=5, expand=True)

        both_btn = ttk.Button(
            button_frame,
            text="保留两种格式",
            command=lambda: self._handle_format_selection(
                dialog, flac_path, "both"),
            style="Rounded.TButton"
        )
        both_btn.pack(side=LEFT, padx=5, expand=True)

    def _handle_format_selection(self, dialog, flac_path, choice):
        """处理用户选择的格式"""
        try:
            wav_path = flac_path[:-5] + '.wav'

            if choice == "flac_only":
                # 仅保留FLAC，不做任何转换
                pass
            elif choice == "wav_only":
                # 转换为WAV并删除FLAC
                if self._convert_flac_to_wav(flac_path, wav_path):
                    os.remove(flac_path)
                    save_path = wav_path
                else:
                    messagebox.showerror("错误", "FLAC转WAV失败，保留原始FLAC文件")
            elif choice == "both":
                # 保留两种格式，只做转换
                if not self._convert_flac_to_wav(flac_path, wav_path):
                    messagebox.showerror("错误", "FLAC转WAV失败，仅保留FLAC文件")

            self.download_btn.config(state=NORMAL)
            self.status_var.set("下载完成")
            dialog.destroy()

            # 显示最终保存路径
            if choice == "wav_only":
                messagebox.showinfo("完成", f"歌曲已保存为WAV格式:\n{wav_path}")
            elif choice == "both":
                messagebox.showinfo(
                    "完成", f"歌曲已保存为两种格式:\nFLAC: {flac_path}\nWAV: {wav_path}")
            else:
                messagebox.showinfo("完成", f"歌曲已保存为FLAC格式:\n{flac_path}")

        except Exception as e:
            messagebox.showerror("错误", f"处理格式时出错: {str(e)}")
            dialog.destroy()

    def _show_advertisement(self):
        """显示广告提示对话框"""
        # 先检查是否已经设置不显示广告
        if self._should_skip_advertisement():
            return

        dialog = Toplevel(self.root)
        dialog.title("软件信息")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 主容器
        main_frame = ttk.Frame(dialog, style="Rounded.TFrame", padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # 广告文本
        ad_label = ttk.Label(
            main_frame,
            text="""我的博客\nhttps://www.xscnet.cn/  
        欢迎您的光临，
        有事没事前来看看呐~""",
            font=("微软雅黑", 12),
            justify=CENTER,
            style="Rounded.TLabel"
        )
        ad_label.pack(pady=20)

        # 添加不再显示复选框
        self.skip_ad_var = BooleanVar(value=False)
        skip_ad_cb = ttk.Checkbutton(
            main_frame,
            text="不再显示此广告",
            variable=self.skip_ad_var,
            style="Rounded.TCheckbutton"
        )
        skip_ad_cb.pack(pady=5)

        # 确认按钮
        confirm_btn = ttk.Button(
            main_frame,
            text="确定",
            command=lambda: self._close_advertisement(dialog),
            style="Rounded.TButton"
        )
        confirm_btn.pack()

        # 让对话框获得焦点
        dialog.focus_set()

    def _should_skip_advertisement(self):
        """检查是否应该跳过广告显示"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\NetEaseMusicParser")
            value, _ = winreg.QueryValueEx(key, "SkipAdvertisement")
            winreg.CloseKey(key)
            return bool(value)
        except WindowsError:
            return False  # 如果注册表项不存在，默认显示广告

    def _close_advertisement(self, dialog):
        """关闭广告对话框并打开博客"""
        # 如果用户勾选了"不再显示"复选框，则保存到注册表
        if self.skip_ad_var.get():
            try:
                key = winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER, r"Software\NetEaseMusicParser")
                winreg.SetValueEx(key, "SkipAdvertisement",
                                  0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
            except Exception as e:
                print(f"无法保存到注册表: {e}")

        # 打开博客链接
        try:
            webbrowser.open_new("https://www.xscnet.cn/")
        except Exception as e:
            print(f"打开浏览器失败: {e}")
            # 如果自动打开失败，提供手动打开的提示
            self.root.clipboard_clear()
            self.root.clipboard_append("https://www.xscnet.cn/")
            messagebox.showinfo("提示", "网址已复制到剪贴板，请手动粘贴到浏览器中打开")

        dialog.destroy()


if __name__ == "__main__":
    root = Tk()
    icon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    app = NetEaseMusicParser(root)
    root.mainloop()
