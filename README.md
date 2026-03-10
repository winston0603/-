**### 国科大深澜认证自动登录**

适用于命令行，没有图形界面、网络驱动齐全的嵌入式设备
或其他想要自动登录的Linux设备

需事先安装python环境、加密和请求包

以openwrt(24.10及之前)为例：
`opkg install python3-light python3-urllib python3-codecs python3-openssl`

之后将本脚本下载到本地，赋予执行权限：
`chmod +x ./auto_login.py`

默认在/etc/srun_login.conf中存储账号密码，格式为：
```
username=xxxxx
password=xxxxx
```

在当前目录执行脚本：
`./auto_login.py`

原理是模拟js脚本对账号密码进行加密，发送请求和后端交互。也可以使用js实现。
