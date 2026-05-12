## 使用正常的

mitmproxy 必须监听所有地址

mitmweb --listen-host 0.0.0.0 --listen-port 8080

有些夜神用宿主机地址：

adb shell settings put global http_proxy 192.168.0.106:8080


直接使用 
adb shell settings put global http_proxy 10.0.2.2:8080


查看是否成功：

adb shell settings get global http_proxy

http://mitm.it



## 安装mitmproxy
python -m pip install mitmproxy

命令：mitmproxy 必须监听所有地址

mitmweb --listen-host 0.0.0.0 --listen-port 8080

## 打开mitm.it 证书下载页面
adb shell am start -a android.intent.action.VIEW -d http://mitm.it

- 没走通 可能雷电不支持file 目的 ：实现abd自动安装证书 手点的安装证书 
adb shell am start -a android.intent.action.VIEW  -d file:///sdcard/Download/mitmproxy-ca-cert.cer

- 测试abd打开https mitweb是否拿到数据
adb shell am start -a android.intent.action.VIEW -d https://httpbin.org/get

adb shell am start -a android.intent.action.VIEW -d https://baidu.com
 

## 其他命令（不一定能使用）

- 设置代理：

adb shell settings put global http_proxy 192.168.0.106:8080

- 查看是否成功：

adb shell settings get global http_proxy