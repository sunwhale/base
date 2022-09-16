# ABAQUS安装

## 1. CentOS
[CentOS镜像地址](https://mirrors.tuna.tsinghua.edu.cn/centos/7.9.2009/isos/x86_64/)
配置图形界面
```
sudo vi /etc/sysconfig/network-scripts/ifcfg-ens33 # 连接网络
```
修改ONBOOT=yes，保存文件，重启，此时虚拟机可以连接网络。
```
sudo yum grouplist
sudo yum groupinstall "GNOME Desktop" "Graphical Administration Tools"
reboot
startx # 从命令行启动图形界面
```
输入命令 `systemctl get-default` 可查看当前默认的模式为 `multi-user.target`，即命令行模式，我们可以将它修改为图形界面模式`systemctl set-default graphical.target`，此时默认用图形界面启动。

## 2. 依赖包安装
```
sudo yum install lsb
lsb_release -a # 查看lsb是否安装好
```

## 3. 许可证服务器安装
```
su
mount -t iso9660 DS.SIMULIA.Suite.2020.Linux64.iso /media # 挂载Abaqus光盘
cd /media/3/SIMULIA_FLEXnet_LicenseServer/Linux64/1
./StartGUI.sh # 执行过程中勾选 > 仅文件-不启动许可证服务器程序
cp ABAQUSLM__lmgrd__SSQ.lic /usr/SIMULIA/License/2020/linux_a64/code/bin/ # 将许可证文件复制到许可证服务器安装路径
cd /usr/SIMULIA/License/2020/linux_a64/code/bin/ # 进入许可证服务器的安装路径
./lmgrd -c ABAQUSLM__lmgrd__SSQ.lic # 启动许可证服务器
./lmstat -a # 查看许可证服务器状态
```

## 4. ABAQUS GUI安装
```
cd /media/4/SIMULIA_EstablishedProducts/Linux64/1/
./StartGUI.sh
安装过程中给出许可证服务器的信息：27800@localhost
/var/DassaultSystemes/SIMULIA/Commands/ # abaqus可执行文件的安装路径
abaqus cae -mesa # 打开abaqus cae
sudo vim ~/.bashrc # 打开bash环境变量配置文件
export PATH="/var/DassaultSystemes/SIMULIA/Commands:$PATH" # 写入文件底部
重启shell
```
