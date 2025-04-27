## 网易云VIP歌曲解析v1.0 By.Mete0r

> [!Warning]  
> 请注重版权意识，此软件仅作为学习使用  
> 此软件是为了方便各位下载音乐较为方便所设计  
> 请自觉购买音乐版权！  


## 使用方法  
1. clone此仓库  
2. 打开**网易云VIP歌曲解析v1.0 By.Mete0r.py**文件，并去  [https://api.nsmao.net/](https://api.nsmao.net/)  获取你的APIKey  
3. 将你的APIKey填入第15行的API_KEY = ""中
示例代码:  

``` python  
# API配置  
API_URL = "https://api.nsmao.net/api/wy/query"  
API_KEY = "123123123123"  # 在  https://api.nsmao.net/  获取你的APIKey  
LEVEL = "jymaster"  
```  

4. 安装运行库文件,使用命令**pip install -r requirements.txt**  
5. 运行app.py文件，**python 网易云VIP歌曲解析v1.0 By.Mete0r.py**  
6. 输入一首歌曲的分享链接，点击解析看是否可以正常解析  
7. 如果可以正常解析，则说明成功，准备封装为exe  
8. 使用pyinstaller将app.py文件打包为exe文件，使用命令**pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." 网易云VIP歌曲解析v1.0 By.Mete0r.py**  

等待打包完成，在dist文件夹下找到网易云VIP歌曲解析v1.0 By.Mete0r.exe文件，双击运行即可  

有任何问题，欢迎提issue，或者在我的个人博客中联系我：[https://www.xscnas.top/](https://www.xscnas.top/)  