# jupyter notebook安装
参考：[腾讯云服务器Ubuntu20.0安装miniconda、jupyter，notebook设置中文和远程访问](https://blog.csdn.net/qq_17517409/article/details/117476542)

## 1. 安装Miniconda3
```shell
sudo wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3
sudo sed -i '$aexport PATH=/opt/miniconda3/bin:$PATH' /etc/profile # 写入环境变量
source /etc/profile
conda init
exit
```

## 2. 安装jupyter
```shell
conda create -n jupyter -y python==3.9
conda activate jupyter
pip install jupyter
```

## 3. 使用openssl生成验证文件:
openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout jupyter.pem -out jupyter.pem

## 4. jupyter配置文件:

生成notebook配置文件：
```shell
jupyter notebook --generate-config
```

打开python，创建一个密文的密码：
```
>>> from notebook.auth import passwd
>>> passwd()
Enter password: 输入密码
Verify password: 再次输入
```

修改默认配置文件：
```shell
nano /home/ubuntu/.jupyter/jupyter_notebook_config.py
```
添加以下内容：
```
c.NotebookApp.ip = '*'
c.NotebookApp.password = 'argon2:$argon2id$v=19$m=10240,t=10,p=8$gqj1+mlQG6p3QfLdHyNfrg$scTfP4xOYAj2Z/tQA7gtIhvtbUwagB9nVhLc0hiYbVY'
c.NotebookApp.open_browser = False
c.NotebookApp.port = 8888
c.NotebookApp.notebook_dir = '/home/ubuntu'
c.NotebookApp.allow_origin = '*'
```
注意：  由于要使用域名访问服务，因此须在jupyter notebook的配置中将c.NotebookApp.allow_origin的值改为*以允许由域名访问（若要求严谨，可填写具体域名）。否则会报Blocking Cross Origin API request for /api/sessions.错误。

## 5. nginx配置文件:
```shell
sudo nano /etc/nginx/conf.d/jupyter.conf
```
```nginx
server {
    # SSL configuration
    listen 8888 ssl;
    server_name jupyter.sunjingyu.com;  # 如果你映射了域名，那么可以写在这里
    access_log  /var/log/nginx/access_jupyter.log;
    error_log  /var/log/nginx/error_jupyter.log;

    ssl_certificate /home/ubuntu/jupyter.sunjingyu.com_bundle.crt;
    ssl_certificate_key /home/ubuntu/jupyter.sunjingyu.com.key;

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
        proxy_pass http://127.0.0.1:8889;  # 转发的地址，即jupyter运行的地址
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

## 6. 运行jupyter notebook:
```shell
jupyter notebook --allow-root
```
