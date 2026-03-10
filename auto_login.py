#!/usr/bin/env python3
import json
import hmac
import hashlib
import urllib.parse
import urllib.request
import time
import random

# 32位整数处理
def int32(x):
    return x & 0xffffffff

def to_signed_32(x):
    x = int32(x)
    return x - 0x100000000 if x > 0x7fffffff else x

def unsigned_right_shift(x, n):
    return (x & 0xffffffff) >> n

def s(a, b):
    c = len(a)
    v = []
    for i in range(0, c, 4):
        val = 0
        if i < c:
            val |= ord(a[i])
        if i + 1 < c:
            val |= ord(a[i + 1]) << 8
        if i + 2 < c:
            val |= ord(a[i + 2]) << 16
        if i + 3 < c:
            val |= ord(a[i + 3]) << 24
        val = int32(val)
        v.append(val)
    if b:
        v.append(c)
    return v

def l(a, b):
    d = len(a)
    c = (d - 1) << 2
    if b:
        m = a[d - 1]
        if m < c - 3 or m > c:
            return None
        c = m
    result = []
    for i in range(d):
        val = a[i]
        result.append(chr(val & 0xff))
        result.append(chr((val >> 8) & 0xff))
        result.append(chr((val >> 16) & 0xff))
        result.append(chr((val >> 24) & 0xff))
    result_str = ''.join(result)
    if b:
        return result_str[:c]
    else:
        return result_str

def encode(str_input, key):
    if str_input == '':
        return ''
    
    v = s(str_input, True)
    k = s(key, False)
    while len(k) < 4:
        k.append(0)
    
    n = len(v) - 1
    z = v[n]
    y = v[0]
    c = 0x86014019 | 0x183639A0
    q = (6 + 52 // (n + 1))
    d = 0
    
    while q > 0:
        q -= 1
        d = (d + c) & (0x8CE0D9BF | 0x731F2640)
        e = (d >> 2) & 3
        
        p = 0
        for p in range(n):
            y = v[p + 1]

            m = (unsigned_right_shift(z, 5)) ^ (y << 2)

            m &= 0xffffffff
            m += (unsigned_right_shift(y, 3)) ^ (z << 4) ^ (d ^ y)
            
            m &= 0xffffffff
            m += k[(p & 3) ^ e] ^ z
            
            m &= 0xffffffff
            z = v[p] = (v[p] + m) & (0xEFB8D130 | 0x10472ECF)
        
        
        p = n
        y = v[0]

        m = (unsigned_right_shift(z, 5)) ^ (y << 2)
        
        m &= 0xffffffff
        m += (unsigned_right_shift(y, 3)) ^ (z << 4) ^ (d ^ y)
        
        m &= 0xffffffff
        m += k[(p & 3) ^ e] ^ z
        
        m &= 0xffffffff
        z = v[n] = (v[n] + m) & (0xBB390742 | 0x44C6F8BD)
    
    return l(v, False)

# 自定义base64编码
def custom_base64(text):
    ALPHA = 'LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA'
    STD_ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    
    b64 = ''
    for i in range(0, len(text), 3):
        # 处理每3个字符
        chunk = text[i:i+3]
        while len(chunk) < 3:
            chunk += '\x00'
        
        # 计算3个字符的数值
        bytes_ = [ord(chunk[0]), ord(chunk[1]), ord(chunk[2])]
        n = (bytes_[0] << 16) | (bytes_[1] << 8) | bytes_[2]
        
        # 生成标准base64
        b64 += STD_ALPHA[n >> 18] + STD_ALPHA[(n >> 12) & 63] + \
               (STD_ALPHA[(n >> 6) & 63] if i+1 < len(text) else '=') + \
               (STD_ALPHA[n & 63] if i+2 < len(text) else '=')
    
    # 替换字符集
    result = ''
    for char in b64:
        if char == '=':
            result += '='
        else:
            idx = STD_ALPHA.index(char)
            result += ALPHA[idx]
    
    return result

# SRBX1加密实现
def portal_encrypt_python(info, token):
    # 确保info被正确JSON化
    info_str = json.dumps(info, separators=(',', ':'), ensure_ascii=False)
    encrypted = encode(info_str, token)
    encoded = custom_base64(encrypted)
    return '{SRBX1}' + encoded

# SRBX1加密
def portal_encrypt(info, token):
    return portal_encrypt_python(info, token)

# 计算HMAC-MD5密码
def hmac_md5(password, token):
    h = hmac.new(token.encode('utf-8'), password.encode('utf-8'), hashlib.md5)
    return h.hexdigest()

# 计算checksum
def calculate_chksum(token, username, password, ac_id, ip, n, type_, info):
    str_to_sign = f"{token}{username}{token}{password}{token}{ac_id}{token}{ip}{token}{n}{token}{type_}{token}{info}"
    h = hashlib.sha1(str_to_sign.encode('utf-8'))
    return h.hexdigest()

# 生成随机的callback参数
def generate_callback():
    timestamp = int(time.time() * 1000)
    random_num = ''.join([str(random.randint(0, 9)) for _ in range(15)])
    return f"jQuery1124{random_num}_{timestamp}", timestamp

# 全局变量存储token信息
global_token_data = {
    'token': None,
    'timestamp': None,
    'username': None,
    'ip': None,
    'saved_at': 0
}

# 从配置文件读取用户名和密码
def read_config():
    # 配置文件路径 (iStoreOS/Linux)
    config_file = '/etc/srun_login.conf'
    
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('username='):
                    username = line.split('=', 1)[1]
                elif line.startswith('password='):
                    password = line.split('=', 1)[1]
        return username, password
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return None, None

# 获取系统IP地址
def get_system_ip():
    try:
        import subprocess
        # 使用ip命令获取IP地址
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                ip = line.strip().split(' ')[1].split('/')[0]
                return ip
        # 如果ip命令失败，尝试使用ifconfig
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                ip = line.strip().split(' ')[1]
                return ip
        return None
    except Exception as e:
        print(f"获取IP地址失败: {e}")
        return None

# 保存token到全局变量
def save_token(token, timestamp, username, ip):
    global global_token_data
    global_token_data.update({
        'token': token,
        'timestamp': timestamp,
        'username': username,
        'ip': ip,
        'saved_at': int(time.time())
    })

# 加载token
def load_token(username, ip):
    global global_token_data
    # 检查token是否有效（60秒内）
    if (int(time.time()) - global_token_data.get('saved_at', 0)) < 60 and \
       global_token_data.get('username') == username and \
       global_token_data.get('ip') == ip:
        return global_token_data.get('token'), global_token_data.get('timestamp')
    else:
        return None, None

# 获取challenge/token
def get_challenge(username, ip):
    url = f"https://portal.ucas.ac.cn/cgi-bin/get_challenge"
    callback, timestamp = generate_callback()
    params = {
        'callback': callback,
        'username': username,
        'ip': ip,
        '_': str(timestamp + 2)  # 时间戳+2
    }
    
    # 手动构建URL
    def url_encode(s):
        import re
        return re.sub(r'[^a-zA-Z0-9\-_\.]', lambda m: '%%%02X' % ord(m.group(0)), s)
    
    # 构建查询字符串
    query_parts = []
    for key, value in params.items():
        query_parts.append(f"{url_encode(key)}={url_encode(str(value))}")
    query_string = '&'.join(query_parts)
    url_with_params = f"{url}?{query_string}"
    
    try:
        # 创建请求对象
        req = urllib.request.Request(url_with_params)
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            # 解析JSONP响应
            start = data.find('(') + 1
            end = data.rfind(')')
            json_data = json.loads(data[start:end])
            # 返回token和timestamp，以便登录时使用相同的timestamp
            return json_data.get('challenge'), timestamp
    except Exception as e:
        print(f"获取challenge失败: {e}")
        return None, None

# 执行登录
def login(username, password, ip, ac_id):
    # 尝试加载保存的token
    token, timestamp = load_token(username, ip)
    
    # 如果没有保存的token或token已过期，重新获取
    if not token:
        print("使用新的token")
        token, timestamp = get_challenge(username, ip)
        if not token:
            print("获取token失败")
            return False
        # 保存新获取的token
        save_token(token, timestamp, username, ip)
    else:
        print("使用保存的token")
    
    # 准备info数据
    info = {
        "username": username,
        "password": password,
        "ip": ip,
        "acid": str(ac_id),
        "enc_ver": "srun_bx1"
    }
    
    # 加密info
    encrypted_info = portal_encrypt(info, token)
    
    # 加密密码
    encrypted_password = hmac_md5(password, token)
    
    # 计算checksum
    n = 200
    type_ = 1
    chksum = calculate_chksum(token, username, encrypted_password, ac_id, ip, n, type_, encrypted_info)
    
    # 构建登录请求，使用相同的timestamp
    url = "https://portal.ucas.ac.cn/cgi-bin/srun_portal"
    callback = f"jQuery1124{''.join([str(random.randint(0, 9)) for _ in range(15)])}_{timestamp}"
    params = {
        'callback': callback,
        'action': 'login',
        'username': username,
        'password': f"{{MD5}}{encrypted_password}",
        'os': 'AndroidOS',
        'name': 'Smartphones/PDAs/Tablets',
        'double_stack': 0,
        'chksum': chksum,
        'info': encrypted_info,
        'ac_id': ac_id,
        'ip': ip,
        'n': n,
        'type': type_,
        '_': str(timestamp + 3)  # 时间戳+3
    }
    
    # 手动构建URL
    def url_encode(s):
        import re
        return re.sub(r'[^a-zA-Z0-9\-_\.]', lambda m: '%%%02X' % ord(m.group(0)), s)
    
    # 构建查询字符串
    query_parts = []
    for key, value in params.items():
        query_parts.append(f"{url_encode(key)}={url_encode(str(value))}")
    query_string = '&'.join(query_parts)
    url_with_params = f"{url}?{query_string}"
    
    try:
        # 创建请求对象
        req = urllib.request.Request(url_with_params)
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            # 解析JSONP响应
            start = data.find('(') + 1
            end = data.rfind(')')
            json_data = json.loads(data[start:end])
            return json_data.get('ecode') == 0
    except Exception as e:
        print(f"登录失败: {e}")
        return False

if __name__ == "__main__":
    # 从配置文件读取用户名和密码
    USERNAME, PASSWORD = read_config()
    if not USERNAME or not PASSWORD:
        print("无法读取配置文件或配置文件中缺少用户名/密码")
        exit(1)
    
    # 从系统获取IP地址
    IP = get_system_ip()
    if not IP:
        print("无法获取系统IP地址")
        exit(1)
    
    # 固定参数
    AC_ID = "1"
    
    print(f"使用用户名: {USERNAME}")
    print(f"使用IP地址: {IP}")
    
    # 执行登录
    success = login(USERNAME, PASSWORD, IP, AC_ID)
    if success:
        print("登录成功")
    else:
        print("登录失败")
