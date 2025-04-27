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
import threading

# API配置
API_URL = "https://api.nsmao.net/api/wy/query"
API_KEY = ""  # 在  https://api.nsmao.net/  获取你的APIKey
LEVEL = "jymaster"

# 初始化音频播放器
mixer.init()

class NetEaseMusicParser:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云VIP歌曲解析v1.0 By.Mete0r")
        self.root.geometry("800x650")
        
        # 从注册表读取下载路径
        self.download_path = self.get_download_path_from_registry()
        if not self.download_path:
            self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # 当前歌曲信息
        self.current_song = None
        self.current_volume = 0.7  # 默认音量70%
        mixer.music.set_volume(self.current_volume)
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        # 顶部框架
        top_frame = Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=X)
        
        # 输入框和按钮
        Label(top_frame, text="网易云歌曲链接:").pack(side=LEFT)
        self.url_entry = Entry(top_frame, width=50)
        self.url_entry.pack(side=LEFT, padx=5)
        
        self.parse_btn = Button(top_frame, text="解析", command=self.parse_song)
        self.parse_btn.pack(side=LEFT, padx=5)
        
        # 结果显示区域
        result_frame = Frame(self.root, padx=10, pady=10)
        result_frame.pack(fill=BOTH, expand=True)
        
        # 使用Treeview显示结果
        self.result_tree = ttk.Treeview(result_frame, columns=("value"), show="tree")
        self.result_tree.heading("#0", text="属性")
        self.result_tree.heading("value", text="值")
        self.result_tree.column("#0", width=200)
        self.result_tree.column("value", width=550)
        
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
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
        
        self.download_btn = Button(control_frame, text="下载歌曲", state=DISABLED, command=self.download_song)
        self.download_btn.pack(side=LEFT, padx=5)
        
        self.play_btn = Button(control_frame, text="播放", state=DISABLED, command=self.play_song)
        self.play_btn.pack(side=LEFT, padx=5)
        
        self.stop_btn = Button(control_frame, text="停止", state=DISABLED, command=self.stop_song)
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
        
        self.mv_btn = Button(func_frame, text="播放MV", state=DISABLED, command=self.play_mv)
        self.mv_btn.pack(side=LEFT, padx=5)
        
        self.select_folder_btn = Button(func_frame, text="选择下载文件夹", command=self.select_download_folder)
        self.select_folder_btn.pack(side=LEFT, padx=5)
        
        self.open_folder_btn = Button(func_frame, text="打开下载文件夹", command=self.open_download_folder)
        self.open_folder_btn.pack(side=LEFT, padx=5)
        
        # 状态栏
        self.status_var = StringVar()
        self.status_var.set("就绪")
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)
    
    def parse_song(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入网易云歌曲链接")
            return
        
        # 从URL中提取歌曲ID
        song_id = self.extract_song_id(url)
        if not song_id:
            messagebox.showerror("错误", "无法从链接中提取歌曲ID")
            return
        
        self.status_var.set("正在解析歌曲...")
        self.parse_btn.config(state=DISABLED)
        
        # 在后台线程中执行API请求
        threading.Thread(target=self._fetch_song_data, args=(song_id,), daemon=True).start()
    
    def _fetch_song_data(self, song_id):
        try:
            params = {
                "key": API_KEY,
                "id": song_id,
                "type": "json",
                "level": LEVEL
            }
            
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # 在主线程中更新UI
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
        
        # 清空结果树
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 显示解析结果
        self._display_song_info(self.current_song)
        
        # 启用下载和播放按钮
        self.download_btn.config(state=NORMAL)
        self.play_btn.config(state=NORMAL)
        self.stop_btn.config(state=NORMAL)
        
        # 如果有MV，启用MV按钮
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
                node = self.result_tree.insert(parent, "end", text=key, values=(""))
                self._display_song_info(value, node)
            elif isinstance(value, list):
                node = self.result_tree.insert(parent, "end", text=key, values=(""))
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        sub_node = self.result_tree.insert(node, "end", text=f"项目 {i+1}", values=(""))
                        self._display_song_info(item, sub_node)
                    else:
                        self.result_tree.insert(node, "end", text=f"项目 {i+1}", values=(str(item)))
            else:
                # 处理长URL显示
                display_value = str(value)
                if key.lower() == "url" and len(display_value) > 50:
                    display_value = display_value[:50] + "..."
                
                self.result_tree.insert(parent, "end", text=key, values=(display_value))
    
    def extract_song_id(self, url):
        # 尝试从URL中提取歌曲ID
        parsed = urlparse(url)
        if parsed.netloc != "music.163.com":
            return None
        
        # 从查询参数中获取id
        query = parse_qs(parsed.query)
        if "id" in query:
            return query["id"][0]
        
        # 从路径中获取id (如 /song?id=123)
        if parsed.path == "/song":
            return query.get("id", [None])[0]
        
        # 从分享链接中匹配 (如 /#/song?id=123)
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
        
        # 检查文件是否已存在
        if os.path.exists(save_path):
            if not messagebox.askyesno("确认", "文件已存在，是否覆盖？"):
                return
        
        self.status_var.set(f"正在下载: {song_name}...")
        self.download_btn.config(state=DISABLED)
        
        # 在后台线程中执行下载
        threading.Thread(target=self._download_file, args=(url, save_path), daemon=True).start()
    
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
                        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                        self.root.after(0, self._update_download_progress, progress)
            
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
        
        # 检查文件是否存在
        if not os.path.exists(save_path):
            messagebox.showerror("错误", "歌曲尚未下载，请先下载")
            return
        
        try:
            mixer.music.load(save_path)
            mixer.music.play()
            self.status_var.set(f"正在播放: {song_name}")
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {e}")
    
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
        folder = filedialog.askdirectory(title="选择下载文件夹", initialdir=self.download_path)
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
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\NetEaseMusicParser")
            winreg.SetValueEx(key, "DownloadPath", 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"无法保存到注册表: {e}")
    
    def get_download_path_from_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\NetEaseMusicParser")
            value, _ = winreg.QueryValueEx(key, "DownloadPath")
            winreg.CloseKey(key)
            return value
        except WindowsError:
            return None

if __name__ == "__main__":
    root = Tk()
    app = NetEaseMusicParser(root)
    root.mainloop()