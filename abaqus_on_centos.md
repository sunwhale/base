# ABAQUS安装

## 1. CentOS
[CentOS镜像地址](https://mirrors.tuna.tsinghua.edu.cn/centos/7.9.2009/isos/x86_64/)
配置图形界面
```shell
sudo vi /etc/sysconfig/network-scripts/ifcfg-ens33 # 连接网络
```
修改ONBOOT=yes，保存文件，重启，此时虚拟机可以连接网络。
```shell
sudo yum install net-tools.x86_64
ifconfig # 查看虚拟机IP地址，用于ssh连接
```
```shell
sudo yum grouplist
sudo yum groupinstall "GNOME Desktop" "Graphical Administration Tools"
reboot
startx # 从命令行启动图形界面
```
输入命令 `systemctl get-default` 可查看当前默认的模式为 `multi-user.target`，即命令行模式，我们可以将它修改为图形界面模式`systemctl set-default graphical.target`，此时默认用图形界面启动。

## 2. 依赖包安装
```shell
sudo yum install lsb
lsb_release -a # 查看lsb是否安装好
```

## 3. 许可证服务器安装
```shell
sudo mount -t iso9660 DS.SIMULIA.Suite.2020.Linux64.iso /media # 挂载Abaqus光盘
sudo /media/3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/StartTUI.sh # 执行过程中勾选 > 仅文件-不启动许可证服务器程序
cp ABAQUSLM__lmgrd__SSQ.lic /usr/SIMULIA/License/2020/linux_a64/code/bin/ # 将许可证文件复制到许可证服务器安装路径
sudo /usr/SIMULIA/License/2020/linux_a64/code/bin/lmgrd -c /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 启动许可证服务器
sudo /usr/SIMULIA/License/2020/linux_a64/code/bin/lmstat -a # 查看许可证服务器状态
```

## 4. ABAQUS TUI安装
```shell
sudo /media/4/SIMULIA_EstablishedProducts/Linux64/1/StartTUI.sh # 安装过程中给出许可证服务器的信息：27800@localhost
/var/DassaultSystemes/SIMULIA/Commands/abaqus cae -mesa # 打开abaqus cae
sudo vim ~/.bashrc # 打开bash环境变量配置文件
export PATH="/var/DassaultSystemes/SIMULIA/Commands:$PATH" # 将abaqus commands路径写入环境变量
```

## 5. Fortran 关联
[Intel® oneAPI standalone component installation files](https://www.intel.com/content/www/us/en/developer/articles/tool/oneapi-standalone-components.html#fortran)
```shell
sudo yum install gcc-c++
wget https://registrationcenter-download.intel.com/akdlm/irc_nas/18703/l_fortran-compiler_p_2022.1.0.134_offline.sh
ifort安装位置：/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64
sudo vim /etc/profile
export PATH=$PATH:/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64/ifort # 写入环境变量
source /etc/profile
/media/4/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/StartTUI.sh # 接口安装
/var/DassaultSystemes/SIMULIA/Commands/abaqus verify -std -user_std -user_exp # 验证
```
 
