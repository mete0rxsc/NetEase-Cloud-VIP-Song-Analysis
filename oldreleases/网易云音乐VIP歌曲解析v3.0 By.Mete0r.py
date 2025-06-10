import requests
import json
import re
import os
import webbrowser
import winreg
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlparse, parse_qs
from pygame import mixer
from io import BytesIO
import threading
from PIL import Image, ImageTk  # 需要安装Pillow库


# API配置（初始值仅用于示例，实际运行从注册表读取）
API_URL = "https://api.nsmao.net/api/wy/query"
LEVEL = "jymaster"


# 初始化音频播放器
mixer.init()


class NetEaseMusicParser:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云VIP歌曲解析器v2.0 By.Metr0r")
        self.root.geometry("800x700")

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

        # 当前播放时长和歌曲长度
        self.song_length = 0

        # 创建UI
        self.create_ui()

    def create_ui(self):
        # 顶部框架
        top_frame = Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=X)

        Label(top_frame, text="网易云歌曲链接:").pack(side=LEFT)
        self.url_entry = Entry(top_frame, width=50)
        self.url_entry.pack(side=LEFT, padx=5)

        self.parse_btn = Button(top_frame, text="解析", command=self.parse_song)
        self.parse_btn.pack(side=LEFT, padx=5)

        # 设置按钮
        self.settings_btn = Button(top_frame, text="Settings", font=(
            "微软雅黑", 8), fg="blue", bd=0, command=self.open_settings)
        self.settings_btn.pack(side=RIGHT, padx=5)
        self.settings_btn.pack(side=RIGHT, padx=5)

        # 结果显示区域
        result_frame = Frame(self.root, padx=10, pady=10)
        result_frame.pack(fill=BOTH, expand=True)

        # 使用Treeview显示结果
        self.result_tree = ttk.Treeview(
            result_frame, columns=("display", "full"), show="tree")
        self.result_tree.heading("#0", text="属性")
        self.result_tree.heading("display", text="值")
        self.result_tree.column("display", width=550)
        self.result_tree.column("full", width=0, stretch=False)  # 隐藏完整值列

        vsb = ttk.Scrollbar(result_frame, orient="vertical",
                            command=self.result_tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal",
                            command=self.result_tree.xview)
        self.result_tree.configure(
            yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.result_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 底部控制按钮
        bottom_frame = Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill=X, side=BOTTOM)

        # 播放控制区域
        control_frame = Frame(bottom_frame)
        control_frame.pack(side=LEFT, fill=X, expand=True)

        self.download_btn = Button(
            control_frame, text="下载歌曲", state=DISABLED, command=self.download_song)
        self.download_btn.pack(side=LEFT, padx=5)

        self.play_btn = Button(control_frame, text="播放",
                               state=DISABLED, command=self.play_song)
        self.play_btn.pack(side=LEFT, padx=5)

        self.stop_btn = Button(control_frame, text="停止",
                               state=DISABLED, command=self.stop_song)
        self.stop_btn.pack(side=LEFT, padx=5)

        # 音量控制
        Label(control_frame, text="音量:").pack(side=LEFT, padx=(10, 0))
        self.volume_scale = Scale(control_frame, from_=0, to=100, orient=HORIZONTAL,
                                  command=self.set_volume)
        self.volume_scale.set(int(self.current_volume * 100))
        self.volume_scale.pack(side=LEFT, padx=5)

        # 其他功能按钮
        func_frame = Frame(bottom_frame)
        func_frame.pack(side=RIGHT)

        self.mv_btn = Button(func_frame, text="播放MV",
                             state=DISABLED, command=self.play_mv)
        self.mv_btn.pack(side=LEFT, padx=5)

        self.select_folder_btn = Button(
            func_frame, text="选择下载文件夹", command=self.select_download_folder)
        self.select_folder_btn.pack(side=LEFT, padx=5)

        self.open_folder_btn = Button(
            func_frame, text="打开下载文件夹", command=self.open_download_folder)
        self.open_folder_btn.pack(side=LEFT, padx=5)

        # 歌词显示区域
        self.lyric_label = Label(self.root, text="", font=(
            "微软雅黑", 14), anchor='center', fg="blue")
        self.lyric_label.pack(side=BOTTOM, fill=X, pady=10)

        # 时间显示标签
        self.time_label = Label(
            self.root, text="00:00 / 00:00", bd=1, relief=SUNKEN, anchor=E)
        self.time_label.pack(side=BOTTOM, fill=X)

        # 状态栏
        self.status_var = StringVar()
        self.status_var.set("就绪")
        status_bar = Label(
            self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)

        # 绑定双击事件以复制值
        self.result_tree.bind("<Double-1>", self.on_tree_double_click)

    def on_tree_double_click(self, event):
        item = self.result_tree.identify('item', event.x, event.y)
        column = self.result_tree.identify_column(event.x)

        if not item or not column:
            return

        # 获取完整值
        full_value = self.result_tree.item(item, "values")[1]

        if full_value and column == "#1":  # 点击“值”列
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

        for i, (time_sec, text) in enumerate(self._parsed_lyrics):
            if i + 1 < len(self._parsed_lyrics) and self._parsed_lyrics[i+1][0] > current_time:
                self.lyric_label.config(text=text)
                return
        if self._parsed_lyrics:
            self.lyric_label.config(text=self._parsed_lyrics[-1][1])

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

        # 解析歌词
        self._parsed_lyrics = []
        if "lyric" in self.current_song:
            self._parsed_lyrics = self.parse_lyrics(self.current_song["lyric"])
        else:
            self.lyric_label.config(text="")

        # 清除旧数据
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        self._display_song_info(self.current_song)

        self.download_btn.config(state=NORMAL)
        self.play_btn.config(state=NORMAL)
        self.stop_btn.config(state=NORMAL)

        if "mv_info" in self.current_song and self.current_song["mv_info"].get("mv"):
            self.mv_btn.config(state=NORMAL)
        else:
            self.mv_btn.config(state=DISABLED)

    def _handle_error(self, error_msg):
        self.parse_btn.config(state=NORMAL)
        messagebox.showerror("错误", f"解析失败: {error_msg}")
        self.status_var.set(f"错误: {error_msg}")

    def _display_song_info(self, song_data, parent=""):
        for key, value in song_data.items():
            if isinstance(value, dict):
                node = self.result_tree.insert(
                    parent, "end", text=key, values=("", ""))
                self._display_song_info(value, node)
            elif isinstance(value, list):
                node = self.result_tree.insert(
                    parent, "end", text=key, values=("", ""))
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        sub_node = self.result_tree.insert(
                            node, "end", text=f"项目 {i+1}", values=("", ""))
                        self._display_song_info(item, sub_node)
                    else:
                        display_value = str(item)
                        full_value = str(item)

                        if key.lower() == "url" and len(display_value) > 50:
                            display_value = display_value[:50] + "..."

                        self.result_tree.insert(
                            node, "end", text=f"项目 {i+1}", values=(display_value, full_value))
            else:
                display_value = str(value)
                full_value = str(value)

                # 特殊处理：歌词只显示第一行
                if key.lower() == "lyric":
                    lines = display_value.strip().split('\n')
                    if len(lines) > 0:
                        display_value = lines[0] + \
                            ("..." if len(lines) > 1 else "")

                # URL 缩略处理
                elif key.lower() == "url" and len(display_value) > 50:
                    display_value = display_value[:50] + "..."

                self.result_tree.insert(
                    parent, "end", text=key, values=(display_value, full_value))

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
        self.download_btn.config(state=NORMAL)
        self.status_var.set(f"下载完成: {os.path.basename(save_path)}")
        messagebox.showinfo("完成", f"歌曲已下载到:\n{save_path}")

    def _download_error(self, error_msg):
        self.download_btn.config(state=NORMAL)
        self.status_var.set(f"下载失败: {error_msg}")
        messagebox.showerror("错误", f"下载失败: {error_msg}")

    def play_song(self):
        if not self.current_song:
            return

        song_name = f"{self.current_song['name']} - {self.current_song['artist']}.flac"
        save_path = os.path.join(self.download_path, song_name)

        if not os.path.exists(save_path):
            choice = messagebox.askyesnocancel(
                "选择播放方式", "歌曲尚未下载。\n请选择：\n\n是：在线播放（需要网络）\n否：下载后再播放\n取消：取消播放")
            if choice is None:
                return
            elif choice:
                self.stream_and_play(self.current_song.get("url"))
            else:
                self.download_and_play()
        else:
            try:
                mixer.music.load(save_path)
                mixer.music.play()
                self.song_length = mixer.Sound(file=save_path).get_length()
                self.root.after(500, self.update_time_display)
                self.status_var.set(f"正在播放: {song_name}")
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
        volume = int(val) / 100.0
        self.current_volume = volume
        mixer.music.set_volume(volume)

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

        Label(dialog, text="请访问API网站获取并输入您的API Key：").pack(pady=5)

        entry_frame = Frame(dialog)
        entry_frame.pack(pady=5, fill=X, padx=20)

        api_entry = Entry(entry_frame, width=40, show="*")
        api_entry.pack(side=LEFT, expand=True, fill=X)

        def open_website():
            webbrowser.open("https://api.nsmao.net/user/login")

        Button(entry_frame, text="打开网站", command=open_website).pack(
            side=RIGHT, padx=(5, 0))

        def confirm():
            entered_key = api_entry.get().strip()
            if self.validate_api_key(entered_key):
                self.save_api_key_to_registry(entered_key)
                self.api_key = entered_key
                dialog.destroy()
            else:
                messagebox.showerror("错误", "请输入正确的API Key")
                api_entry.delete(0, END)

        Button(dialog, text="确认", command=confirm).pack(pady=10)
        self.root.wait_window(dialog)

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
        settings_win.geometry("400x250")
        settings_win.transient(self.root)
        settings_win.grab_set()

        Label(settings_win, text="当前API Key:").pack(anchor=W, padx=10, pady=5)
        current_key = self.api_key if self.api_key else "<未设置>"
        Label(settings_win, text=current_key,
              fg="gray").pack(anchor=W, padx=10)

        Label(settings_win, text="更改API Key:").pack(anchor=W, padx=10, pady=5)
        new_key_entry = Entry(settings_win, width=40, show="*")
        new_key_entry.pack(padx=10, fill=X)

        Label(settings_win, text="默认音量 (0-100):").pack(anchor=W, padx=10, pady=5)
        volume_scale = Scale(settings_win, from_=0, to=100, orient=HORIZONTAL)
        volume_scale.set(int(self.current_volume * 100))
        volume_scale.pack(padx=10, fill=X)

        def save_settings():
            new_key = new_key_entry.get().strip()
            if new_key and not self.validate_api_key(new_key):
                messagebox.showerror("错误", "请输入正确的API Key")
                return

            if new_key:
                self.save_api_key_to_registry(new_key)
                self.api_key = new_key

            self.current_volume = volume_scale.get() / 100.0
            mixer.music.set_volume(self.current_volume)
            self.save_volume_to_registry(self.current_volume)
            messagebox.showinfo("成功", "设置已保存")
            settings_win.destroy()

        Button(settings_win, text="保存", command=save_settings).pack(pady=10)

        settings_win.bind("<Return>", lambda event: save_settings())


if __name__ == "__main__":
    root = Tk()
    icon_path = os.path.join(os.path.dirname(__file__), "aicon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    app = NetEaseMusicParser(root)
    root.mainloop()
