# ABAQUS安装
参考：[GitHub - franaudo/abaqus-ubuntu: Guide for the installation of Abaqus on Ubuntu](https://github.com/franaudo/abaqus-ubuntu)
## 1. 挂载数据盘
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh && sudo bash auto_disk.sh
sudo chmod -R 777 /www
```

## 2. 依赖包安装
```shell
sudo apt install ksh gcc g++ gfortran libstdc++5 build-essential make libjpeg62 libmotif-dev libmotif-common rpm
sudo apt-get update
sudo apt-get install libc6-i386 lsb-core
```

## 3. 许可证服务器安装
```shell
sudo mount -t iso9660 /www/abaqus2020/DS.SIMULIA.Suite.2020.Linux64.iso /media # 挂载Abaqus光盘
sudo cp -r /media /opt/abaqus2020
sudo chmod 777 -R /opt/abaqus2020
cd /opt/abaqus2020/
cp /www/abaqus2020/Linux.sh ./5/SIMULIA_Documentation/AllOS/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./5/SIMULIA_Isight/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./3/EXALEAD_Search_Doc/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./3/EXALEAD_CloudView/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./4/SIMULIA_EstablishedProducts/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./4/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/inst/common/init/Linux.sh
sudo bash /opt/abaqus2020/3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/StartTUI.sh # 执行过程中勾选 > Files only - do not start the license server program.
sudo cp /www/abaqus2020/ABAQUSLM__lmgrd__SSQ.lic /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 将许可证文件复制到许可证服务器安装路径
sudo mkdir /usr/tmp
sudo /usr/SIMULIA/License/2020/linux_a64/code/bin/lmgrd -c /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 启动许可证服务器
cd /usr/SIMULIA/License/2020/linux_a64/code/bin/
sudo ./lmstat -a # 查看许可证服务器状态
```

## 4. ABAQUS TUI安装
```shell
sudo bash /opt/abaqus2020/4/SIMULIA_EstablishedProducts/Linux64/1/StartTUI.sh # 安装过程中跳过许可证服务器的信息
sudo vim /usr/SIMULIA/EstProducts/2020/linux_a64/SMA/site/custom_v6.env # 修改下面两行
license_server_type=FLEXNET
abaquslm_license_file="27800@localhost"
sudo vim /etc/profile
export PATH="/var/DassaultSystemes/SIMULIA/Commands:$PATH" # 将abaqus commands路径写入环境变量
source /etc/profile
/var/DassaultSystemes/SIMULIA/Commands/abaqus cae -mesa # 打开abaqus cae
```

## 5. Fortran 关联
[Intel® oneAPI standalone component installation files](https://www.intel.com/content/www/us/en/developer/articles/tool/oneapi-standalone-components.html#fortran)
```shell
wget https://registrationcenter-download.intel.com/akdlm/irc_nas/18703/l_fortran-compiler_p_2022.1.0.134_offline.sh
sudo bash l_fortran-compiler_p_2022.1.0.134_offline.sh
ifort安装位置：/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64
sudo vim /etc/profile
export PATH=$PATH:/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64 # 写入环境变量
source /etc/profile
sudo bash /opt/abaqus2020/4/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/StartTUI.sh # 接口安装
/var/DassaultSystemes/SIMULIA/Commands/abaqus verify -std -user_std -user_exp # 验证
```
 
