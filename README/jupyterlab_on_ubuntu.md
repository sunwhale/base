# jupyter lab安装
参考：[Ubuntu20.04云服务器安装配置jupyter lab](https://blog.csdn.net/qq_15143201/article/details/126670116)

## 1. 安装Miniconda3
```shell
sudo wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3
sudo sed -i '$aexport PATH=/opt/miniconda3/bin:$PATH' /etc/profile # 写入环境变量
source /etc/profile
conda init
exit
```

## 2. 安装jupyter lab
```shell
conda create -n jupyter -y python==3.9
conda activate jupyter
pip install jupyterlab
```

## 3. jupyter lab配置文件:

生成配置文件和密码：
```shell
jupyter lab --generate-config # 生成jupyterlab配置文件
jupyter lab password # 设置密码，输入两次
```

修改默认配置文件：
```shell
nano /home/ubuntu/.jupyter/jupyter_lab_config.py
```
添加以下内容：
```
c.ServerApp.allow_origin = '*'
c.ServerApp.allow_remote_access = True
c.ServerApp.ip = '*'
c.ServerApp.open_browser = False
c.ServerApp.notebook_dir = '/home/ubuntu'
```
注意：  由于要使用域名访问服务，因此须在jupyter lab的配置中将c.ServerApp.allow_origin的值改为*以允许由域名访问（若要求严谨，可填写具体域名）。否则会报Blocking Cross Origin API request for /api/sessions.错误。

## 4. nginx配置文件:
```shell
sudo nano /etc/nginx/conf.d/jupyter.conf
```
```nginx
server {
    # SSL configuration
    listen 8080 ssl;
    server_name jupyter.sunjingyu.com;  # 如果你映射了域名，那么可以写在这里
    access_log  /var/log/nginx/access_jupyter.log;
    error_log  /var/log/nginx/error_jupyter.log;

    ssl_certificate /www/ssl/jupyter.sunjingyu.com_bundle.crt;
    ssl_certificate_key /www/ssl/jupyter.sunjingyu.com.key;

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
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    location / {
        proxy_pass http://127.0.0.1:8888;  # 转发的地址，即jupyter运行的地址
        proxy_redirect     off;

        proxy_set_header   Host                 $host;
        proxy_set_header   X-Real-IP            $remote_addr;
        proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    $scheme;

        proxy_http_version 1.1;
        proxy_set_header   Upgrade              $http_upgrade;
        proxy_set_header   Connection           "upgrade";

        proxy_read_timeout 120s;
        proxy_next_upstream error;
    }
}
```

另外，jupyter notebook需要nginx的websocket支持（否
则会报错误Replacing stale connection），因此修改nginx配置文件如下。

## 5. 运行jupyter notebook:
```shell
jupyter lab --allow-root
```

## 6. 命令流:
```shell
conda create -n jupyter -y python==3.9
conda activate jupyter
pip install jupyterlab
jupyter lab --generate-config # 生成jupyterlab配置文件
jupyter lab password # 设置密码，输入两次
sudo cp /home/ubuntu/base/conf/jupyter/jupyter_lab_config.py /home/ubuntu/.jupyter/jupyter_lab_config.py
```
