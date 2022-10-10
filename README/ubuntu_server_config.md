# 服务器配置

## 1. 挂载数据盘
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh
sudo bash auto_disk.sh << XXG
y
XXG
sudo chmod 777 /www
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
conda create -n flask -y python==3.9
```

## 4. 从git获取网站源代码
```shell
git clone https://gitee.com/sunwhale/base.git
cd base
conda activate flask
pip install -r requirements.txt # -i https://pypi.org/simple #官方源
pip install psic gunicorn
```


## 5. 安装Nginx
```shell
sudo apt-get install -y nginx
sudo /etc/init.d/nginx start
sudo rm /etc/nginx/sites-enabled/default
sudo vim /etc/nginx/sites-enabled/base
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

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
    ssl_ecdh_curve secp384r1;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
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
sudo service nginx restart
```

## 6. 启动gunicorn
```shell
gunicorn -w 1 wsgi:app
gunicorn -w 1 -b 0.0.0.0 wsgi:app
```

## 7. 使用Supervisor管理进程
```shell
sudo apt install -y supervisor
sudo vim /etc/supervisor/conf.d/base.conf
```

```
[program:base]
command=/opt/miniconda3/bin/conda run -n flask gunicorn -w 1 wsgi:app
directory=/home/ubuntu/base
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
```

```shell
sudo service supervisor restart
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

## 9. 虚拟图形界面
```shell
sudo apt install xvfb
Xvfb :1 -screen 0 800x600x24 &
export DISPLAY=:1
```

## 10.  命令流
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh
sudo bash auto_disk.sh << XXG
y
XXG
sudo chmod 777 /www
sudo wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3
sudo sed -i '$aexport PATH=/opt/miniconda3/bin:$PATH' /etc/profile # 写入环境变量
source /etc/profile
conda init
exit

conda create -n flask -y python==3.9
conda activate flask
git clone https://gitee.com/sunwhale/base.git
cd base
pip install -r requirements.txt # -i https://pypi.org/simple #官方源
pip install psic gunicorn

sudo apt install -y supervisor nginx xvfb
sudo rm /etc/nginx/sites-enabled/default
sudo cp /www/config/base /etc/nginx/sites-enabled/base
sudo service nginx restart
sudo cp /www/config/base.conf /etc/supervisor/conf.d/base.conf
sudo service supervisor restart
```

ps aux | grep nginx
