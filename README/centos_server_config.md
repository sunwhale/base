# 服务器配置

## 1. 挂载数据盘
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh
sudo bash auto_disk.sh
sudo chmod 777 /www
sudo yum install wget git libX11 libGL libXrender
```

## 2. 安装miniconda
```shell
sudo wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3
sudo sed -i '$aexport PATH=/opt/miniconda3/bin:$PATH' /etc/profile # 写入环境变量
sudo source /etc/profile
sudo conda init
```

## 3. 建立虚拟环境flask
```shell
conda create -n flask python==3.9
```

## 4. 从git获取网站源代码
```shell
sudo git clone https://github.com/sunwhale/base.git
cd base
conda activate flask
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple some-package # 清华源
-i https://pypi.org/simple # 官方源	
```

## 5. 安装Nginx
```shell
sudo yum install -y epel-release
sudo yum -y install nginx
sudo systemctl enable nginx
sudo setsebool -P httpd_can_network_connect 1 # 如果Nginx无法监听本地端口，运行此命令
sudo fuser -k 80/tcp # 如果Nginx由于端口被占用无法启动，运行此命令
sudo fuser -k 443/tcp
sudo vim /etc/nginx/conf.d/base.conf
```

```Nginx配置文件内容
server {
    listen 80 default_server; 
    server_name sunjingyu.com;  # 如果你映射了域名，那么可以写在这里
    access_log  /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;
    
    # SSL configuration
    listen 443 ssl default_server;
    ssl_certificate /www/ssl/sunjingyu.com_bundle.crt;
    ssl_certificate_key /www/ssl/sunjingyu.com.key;
    ​ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
    ssl_ecdh_curve secp384r1;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    location / {
        proxy_pass http://127.0.0.1:8000;  # 转发的地址，即Gunicorn运行的地址
        proxy_redirect     off;

        proxy_set_header   Host                 $host;
        proxy_set_header   X-Real-IP            $remote_addr;
        proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    $scheme;
    }
}
```
```shell
sudo nginx -t # 查看配置文件状态
sudo systemctl restart nginx
```

## 6. 安装gunicorn
```shell
pip install gunicorn
gunicorn -w 1 wsgi:app
```

## 7. 使用Supervisor管理进程
```shell
sudo apt install supervisor
sudo vim /etc/supervisor.d/base.ini
```
```
[program:base]
command=/opt/miniconda3/bin/conda run -n flask gunicorn -w 1 wsgi:app
directory=/home/root/base
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
```
```shell
sudo systemctl restart supervisord
sudo supervisorctl
sudo supervisorctl reread  # 重新读取配置
sudo supervisorctl update  # 更新以便让配置生效
```

## 8. 使用bypy上传文件
```shell
pip install bypy
bypy list
bypy downdir /
```
[https://github.com/houtianze/bypy](https://github.com/houtianze/bypy)
