## 网易云VIP歌曲解析v1.0 By.Mete0r

> [!Warning]  
> 请注重版权意识，此软件仅作为学习使用  
> 此软件是为了方便各位下载音乐较为方便所设计  
> 请自觉购买音乐版权！  


## 更新日志

- **V2.0** : 2025/04/30 - ✨更新了音乐在线播放，右下角时间显示，下方歌词显示
- **V3.0** : 2025/05/21 - ✨更新了API辅助添加功能，现在可以不用自己封包了，直接去下载我封好的就可以用了  
- **V4.0** : 2025/06/10 - ✨更新了UI界面，添加了下载歌词的功能  
- **V4.1** : 2025/06/10 - ✨更新了UI界面，使之更加现代化，更新了利用ffmpeg转换音乐格式的功能，现在可以直接下载出wav格式了  

## 软件特点

1. 首次打开会选择系统默认的下载文件夹  
2. 可以手动选择下载路径，选择后软件会自动写入注册表下，后续再打开软件会自动从注册表中读取路径  
3. 使用公共免费API接口，高度自定义性！  
4. 100%开源，欢迎star和fork  
5. 界面简单，功能单一，无多余功能  

### 更新日志
**网易云VIP歌曲解析v1.2 By.Mete0r** - 未上传GitHub，此版本更新了双击显示信息复制信息  
**网易云VIP歌曲解析v2.0 By.Mete0r** - 已推送GitHub，此版本更新了音乐在线播放，右下角时间显示，下方歌词显示  

## 使用方法  
**直接去release页面下载最新版本即可，打开软件会自动提示填写API_Key，填写过后自动写入系统注册表**  
**如果需要更改API_Key，请在软件右上角Settings中修改**  
~~1. clone此仓库~~    
~~2. 打开**网易云VIP歌曲解析v1.0 By.Mete0r.py**文件，并去  [https://api.nsmao.net/](https://api.nsmao.net/)  获取你的APIKey~~  
~~3. 将你的APIKey填入第15行的API_KEY = ""中~~  
示例代码:  

``` python  
# API配置  
API_URL = "https://api.nsmao.net/api/wy/query"  
API_KEY = "123123123123"  # 在  https://api.nsmao.net/  获取你的APIKey  
LEVEL = "jymaster"~  
```  

~~4. 安装运行库文件,使用命令**pip install -r requirements.txt**~~  
~~5. 运行app.py文件，**python 网易云VIP歌曲解析v1.0 By.Mete0r.py**~~  
~~6. 输入一首歌曲的分享链接，点击解析看是否可以正常解析~~  
~~7. 如果可以正常解析，则说明成功，准备封装为exe~~  
~~8. 使用pyinstaller将app.py文件打包为exe文件，使用命令**pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." 网易云VIP歌曲解析v1.0 By.Mete0r.py**~~  

等待打包完成，在dist文件夹下找到网易云VIP歌曲解析v1.0 By.Mete0r.exe文件，双击运行即可  

有任何问题，欢迎提issue，或者在我的个人博客中联系我：[https://www.xscnas.top/](https://www.xscnas.top/)  