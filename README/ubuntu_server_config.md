# 服务器配置

## 1. 挂载数据盘
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh && sudo bash auto_disk.sh
sudo chmod 777 /www

## 2. 安装miniconda
sudo wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh
修改安装目录：/opt/miniconda3
打开环境变量文件：sudo vim ~/.bashrc
在文件末尾添加：export PATH="/opt/miniconda3/bin:$PATH"
sudo conda init

## 3. 建立虚拟环境flask
conda create -n flask python==3.9

## 4. 从git获取网站源代码
git clone https://github.com/sunwhale/base.git
cd base
conda activate flask
pip install -r requirements.txt
-i https://pypi.org/simple #官方源

## 5. 安装Nginx
sudo apt-get install nginx
sudo /etc/init.d/nginx start
sudo rm /etc/nginx/sites-enabled/default
sudo vim /etc/nginx/sites-enabled/base
Nginx配置文件内容
```
server {
    listen 80 default_server; 
    server_name sunjingyu.com;  # 如果你映射了域名，那么可以写在这里
    access_log  /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;
    
    # SSL configuration
    listen 443 ssl default_server;
    include snippets/ssl-sunjingyu.com.conf;
    include snippets/ssl-params.conf;
    
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
sudo vim /etc/nginx/snippets/ssl-sunjingyu.com.conf
```
ssl_certificate /www/ssl/sunjingyu.com_bundle.crt;
ssl_certificate_key /www/ssl/sunjingyu.com.key;
```
sudo vim /etc/nginx/snippets/ssl-params.conf
```
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
```
查看配置文件状态
sudo nginx -t
sudo service nginx restart

## 6. 安装gunicorn
pip install gunicorn
gunicorn -w 1 wsgi:app
gunicorn -w 1 -b 0.0.0.0 wsgi:app

## 7. 使用Supervisor管理进程
sudo apt install supervisor
sudo vim /etc/supervisor/conf.d/base.conf
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
sudo service supervisor restart
sudo supervisorctl
sudo supervisorctl reread  # 重新读取配置
sudo supervisorctl update  # 更新以便让配置生效

## 8. 使用bypy上传文件
pip install bypy
bypy list
bypy downdir /
[https://github.com/houtianze/bypy](https://github.com/houtianze/bypy)

## 9. 虚拟图形界面
```shell
sudo apt install xvfb
Xvfb :5 -screen 0 800x600x24 &
export DISPLAY=:5
```
