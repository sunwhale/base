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
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ # -i https://pypi.org/simple #官方源
pip install gunicorn
```


## 5. 安装Nginx
```shell
sudo apt-get install -y nginx
sudo /etc/init.d/nginx start
sudo rm /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-enabled/base # 编辑配置文件
sudo nginx -t # 查看配置文件状态
sudo service nginx restart
```

```nginx
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
```

## 6. 启动gunicorn
```shell
gunicorn -w 1 wsgi:app
gunicorn -w 1 -b 0.0.0.0 wsgi:app
```

## 7. 使用supervisor管理进程
```shell
sudo apt install -y supervisor
sudo service supervisor restart
sudo supervisorctl
sudo supervisorctl reread  # 重新读取配置
sudo supervisorctl update  # 更新以便让配置生效
```
### gunicorn配置文件
注意：supervisor运行过程中不包含系统环境变量，需要手动配置。
```shell
sudo vim /etc/supervisor/conf.d/gunicorn.conf
[program:gunicorn]
command=/opt/miniconda3/bin/conda run -n flask gunicorn -c pygun.py wsgi:app --log-level=debug --preload
directory=/home/ubuntu/base
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stdout_logfile=./stdout.log
stderr_logfile=./error.log
environment=PATH="/home/ubuntu/.local/bin:/opt/miniconda3/bin:/opt/miniconda3/condabin:/opt/miniconda3/bin:/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64:/var/DassaultSystemes/SIMULIA/Commands:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
```
### abaqus许可证服务器配置文件
```shell
sudo vim /etc/supervisor/conf.d/lmgrd.conf
[program:lmgrd]
command=/usr/SIMULIA/License/2022/linux_a64/code/bin/lmgrd -c /usr/SIMULIA/License/2022/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic
directory=/home/ubuntu/abaqus
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
redirect_stderr=true
stdout_logfile=./stdout.log
stderr_logfile=./error.log
environment=PATH="/home/ubuntu/.local/bin:/opt/miniconda3/bin:/opt/miniconda3/condabin:/opt/miniconda3/bin:/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64:/var/DassaultSystemes/SIMULIA/Commands:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
```

## 8. 使用bypy上传/下载百度网盘中的文件
[https://github.com/houtianze/bypy](https://github.com/houtianze/bypy)
```shell
pip install bypy
bypy list
bypy downdir /
```

## 9. 虚拟图形界面
用于解决无图形界面linux系统三维绘图的问题。
```shell
sudo apt install xvfb
Xvfb :1 -screen 0 800x600x24 &
export DISPLAY=:1
```

## 10. 安装glances
用于监视系统进程。
```shell
sudo apt install glances
glances -w
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
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ # -i https://pypi.org/simple #官方源
pip install gunicorn

conda create -n jupyter -y python==3.9
conda activate jupyter
pip install jupyterlab jupyterlab-language-pack-zh-CN
jupyter lab --generate-config # 生成jupyterlab配置文件
jupyter lab password # 设置密码，输入两次
sudo cp /home/ubuntu/base/conf/jupyter/jupyter_lab_config.py /home/ubuntu/.jupyter/jupyter_lab_config.py

sudo apt install -y supervisor nginx xvfb glances

sudo rm /etc/nginx/sites-enabled/default
sudo cp /home/ubuntu/base/conf/nginx/*.conf /etc/nginx/conf.d
sudo service nginx restart
sudo cp /home/ubuntu/base/conf/supervisor/*.conf /etc/supervisor/conf.d
sudo service supervisor restart
sudo supervisorctl
```

ps aux | grep nginx
