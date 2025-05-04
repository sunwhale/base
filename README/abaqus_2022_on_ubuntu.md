# ABAQUS安装
参考：[GitHub - franaudo/abaqus-ubuntu: Guide for the installation of Abaqus on Ubuntu](https://github.com/franaudo/abaqus-ubuntu)

## 1. 命令流
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh && sudo bash auto_disk.sh
sudo chmod -R 777 /www
sudo apt install -y ksh gcc g++ gfortran libstdc++5 build-essential make libjpeg62 libmotif-dev libmotif-common rpm

sudo apt-get update
sudo apt-get install -y libc6-i386 lsb-core

sudo mount -t iso9660 DS.SIMULIA.2022.Ubuntu.iso /media # 挂载Abaqus光盘

sudo bash /media/3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/StartTUI.sh # 执行过程中勾选 > Files only - do not start the license server program.
sudo bash /media/4/SIMULIA_EstablishedProducts/Linux64/1/StartTUI.sh # 安装过程中跳过许可证服务器的信息
sudo bash /media/5/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/StartTUI.sh # 接口安装

sudo cp /media/ABAQUSLM__lmgrd__SSQ.lic /usr/SIMULIA/License/2022/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 将许可证文件复制到许可证服务器安装路径
sudo mkdir /usr/tmp
sudo /usr/SIMULIA/License/2022/linux_a64/code/bin/lmgrd -c /usr/SIMULIA/License/2022/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 启动许可证服务器
sudo /usr/SIMULIA/License/2022/linux_a64/code/bin/lmstat -c /usr/SIMULIA/License/2022/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic -a # 查看许可证服务器状态
sudo sed -i '$alicense_server_type=FLEXNET' /usr/SIMULIA/EstProducts/2022/linux_a64/SMA/site/licensing.env # 修改配置文件
sudo sed -i '$aabaquslm_license_file=\"27800@localhost\"' /usr/SIMULIA/EstProducts/2022/linux_a64/SMA/site/licensing.env # 修改配置文件
sudo sed -i '$aPATH=/var/DassaultSystemes/SIMULIA/Commands:$PATH' /etc/profile # 写入环境变量

sudo bash l_fortran-compiler_p_2023.0.0.25394_offline.sh # 安装fortran编译器
sudo sed -i '$aPATH=/opt/intel/oneapi/compiler/2023.0.0/linux/bin/intel64:$PATH' /etc/profile # 写入环境变量
source /etc/profile
cd /var/DassaultSystemes/SIMULIA/Commands
sudo mv abq abaqus # 修改可执行程序名称
abaqus cae -mesa # 打开cae
abaqus verify -std -user_std -user_exp # 验证
```

## 2. Fortran 下载
[Intel® oneAPI standalone component installation files](https://www.intel.com/content/www/us/en/developer/articles/tool/oneapi-standalone-components.html#fortran)
### 2022.1.0.134
```shell
wget https://registrationcenter-download.intel.com/akdlm/irc_nas/18703/l_fortran-compiler_p_2022.1.0.134_offline.sh
sudo bash l_fortran-compiler_p_2022.1.0.134_offline.sh
ifort安装位置：/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64
sudo sed -i '$aPATH=/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64:$PATH' /etc/profile # 写入环境变量
source /etc/profile
 ```
### 2023.0.0.25394
```shell
wget https://registrationcenter-download.intel.com/akdlm/irc_nas/19105/l_fortran-compiler_p_2023.0.0.25394_offline.sh
sudo bash l_fortran-compiler_p_2023.0.0.25394_offline.sh
ifort安装位置：/opt/intel/oneapi/compiler/2023.0.0/linux/bin/intel64
sudo sed -i '$aPATH=/opt/intel/oneapi/compiler/2023.0.0/linux/bin/intel64:$PATH' /etc/profile # 写入环境变量
source /etc/profile
 ```

## 3. 单机并行计算设置
修改/usr/SIMULIA/EstProducts/2022/linux_a64/SMA/site/basic_v6.env中的"mp_mode = MPI" -> "mp_mode = THREADS"
