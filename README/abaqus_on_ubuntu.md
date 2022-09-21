# ABAQUS安装
参考：[GitHub - franaudo/abaqus-ubuntu: Guide for the installation of Abaqus on Ubuntu](https://github.com/franaudo/abaqus-ubuntu)
## 1. 挂载数据盘
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh && sudo bash auto_disk.sh
sudo chmod -R 777 /www
```

## 2. 依赖包安装
```shell
sudo apt install -y ksh gcc g++ gfortran libstdc++5 build-essential make libjpeg62 libmotif-dev libmotif-common rpm
sudo apt-get update
sudo apt-get install -y libc6-i386 lsb-core
```

## 3. 许可证服务器安装
```shell
sudo mount -t iso9660 /www/abaqus2020/DS.SIMULIA.Suite.2020.Linux64.iso /media # 挂载Abaqus光盘
sudo cp -r /media /www/abaqus2020/ubuntu
sudo chmod 777 -R /www/abaqus2020/ubuntu
cd /www/abaqus2020/ubuntu
cp /www/abaqus2020/Linux.sh ./5/SIMULIA_Documentation/AllOS/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./5/SIMULIA_Isight/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./3/EXALEAD_Search_Doc/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./3/EXALEAD_CloudView/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./4/SIMULIA_EstablishedProducts/Linux64/1/inst/common/init/Linux.sh
cp /www/abaqus2020/Linux.sh ./4/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/inst/common/init/Linux.sh
sudo bash /www/abaqus2020/ubuntu/3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/StartTUI.sh # 执行过程中勾选 > Files only - do not start the license server program.
sudo cp /www/abaqus2020/ABAQUSLM__lmgrd__SSQ.lic /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 将许可证文件复制到许可证服务器安装路径
sudo mkdir /usr/tmp
sudo /usr/SIMULIA/License/2020/linux_a64/code/bin/lmgrd -c /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 启动许可证服务器
cd /usr/SIMULIA/License/2020/linux_a64/code/bin/
sudo ./lmstat -a # 查看许可证服务器状态
```

## 4. ABAQUS TUI安装
```shell
sudo bash /www/abaqus2020/ubuntu/4/SIMULIA_EstablishedProducts/Linux64/1/StartTUI.sh # 安装过程中跳过许可证服务器的信息
sudo vim /usr/SIMULIA/EstProducts/2020/linux_a64/SMA/site/custom_v6.env # 修改下面两行

license_server_type=FLEXNET
abaquslm_license_file="27800@localhost"

sudo sed -i '/license_server/clicense_server_type=FLEXNET' /usr/SIMULIA/EstProducts/2020/linux_a64/SMA/site/custom_v6.env # 直接修改
sudo sed -i "/dsls_license_config/cabaquslm_license_file=\"27800@localhost\"" /usr/SIMULIA/EstProducts/2020/linux_a64/SMA/site/custom_v6.env # 直接修改

sudo sed -i '$aPATH=/var/DassaultSystemes/SIMULIA/Commands:$PATH' /etc/profile # 写入环境变量
source /etc/profile
abaqus cae -mesa # 打开abaqus cae
```

## 5. Fortran 关联
[Intel® oneAPI standalone component installation files](https://www.intel.com/content/www/us/en/developer/articles/tool/oneapi-standalone-components.html#fortran)
```shell
wget https://registrationcenter-download.intel.com/akdlm/irc_nas/18703/l_fortran-compiler_p_2022.1.0.134_offline.sh
sudo bash l_fortran-compiler_p_2022.1.0.134_offline.sh
ifort安装位置：/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64
sudo sed -i '$aPATH=/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64:$PATH' /etc/profile # 写入环境变量
source /etc/profile
sudo bash /www/abaqus2020/ubuntu/4/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/StartTUI.sh # 接口安装
abaqus verify -std -user_std -user_exp # 验证
```

## 6. 命令流
```shell
sudo wget -O auto_disk.sh http://download.bt.cn/tools/auto_disk.sh && sudo bash auto_disk.sh
sudo chmod -R 777 /www
sudo apt install -y ksh gcc g++ gfortran libstdc++5 build-essential make libjpeg62 libmotif-dev libmotif-common rpm

sudo apt-get update
sudo apt-get install -y libc6-i386 lsb-core

sudo bash /www/abaqus2020/ubuntu/3/SIMULIA_FLEXnet_LicenseServer/Linux64/1/StartTUI.sh # 执行过程中勾选 > Files only - do not start the license server program.
sudo bash /www/abaqus2020/ubuntu/4/SIMULIA_EstablishedProducts/Linux64/1/StartTUI.sh # 安装过程中跳过许可证服务器的信息
sudo bash /www/abaqus2020/ubuntu/4/SIMULIA_EstablishedProducts_CAA_API/Linux64/1/StartTUI.sh # 接口安装

sudo cp /www/abaqus2020/ABAQUSLM__lmgrd__SSQ.lic /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 将许可证文件复制到许可证服务器安装路径
sudo mkdir /usr/tmp
sudo /usr/SIMULIA/License/2020/linux_a64/code/bin/lmgrd -c /usr/SIMULIA/License/2020/linux_a64/code/bin/ABAQUSLM__lmgrd__SSQ.lic # 启动许可证服务器
sudo sed -i '/license_server/clicense_server_type=FLEXNET' /usr/SIMULIA/EstProducts/2020/linux_a64/SMA/site/custom_v6.env # 修改配置文件
sudo sed -i "/dsls_license_config/cabaquslm_license_file=\"27800@localhost\"" /usr/SIMULIA/EstProducts/2020/linux_a64/SMA/site/custom_v6.env # 修改配置文件
sudo sed -i '$aPATH=/var/DassaultSystemes/SIMULIA/Commands:$PATH' /etc/profile # 写入环境变量

sudo bash /www/l_fortran-compiler_p_2022.1.0.134_offline.sh # 安装fortran编译器
sudo sed -i '$aPATH=/opt/intel/oneapi/compiler/2022.1.0/linux/bin/intel64:$PATH' /etc/profile # 写入环境变量
source /etc/profile
abaqus cae -mesa
```
 
