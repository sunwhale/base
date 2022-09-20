DSY_LIBPATH_VARNAME=LD_LIBRARY_PATH

which lsb_release
if [[ $? -ne 0 ]] ; then
  echo "lsb_release is not found: check in the PDIR the list of installed packages for servers validation."
  exit 12
fi

DSY_OS_Release="CentOS"
echo "DSY_OS_Release=\""${DSY_OS_Release}"\""
export DSY_OS_Release=${DSY_OS_Release}

if [[ -n ${DSY_Force_OS} ]]; then
  DSY_OS=${DSY_Force_OS}
  echo "DSY_Force_OS=\""${DSY_Force_OS}"\", use it for DSY_OS"
  return
fi

case ${DSY_OS_Release} in
    "RedHatEnterpriseServer"|"RedHatEnterpriseClient"|"RedHatEnterpriseWorkstation"|"CentOS")
        DSY_OS=linux_a64;;
    "SUSELINUX"|"SUSE")
        DSY_OS=linux_a64;;
    *)
        echo "Unknown linux release \""${DSY_OS_Release}"\""
        echo "exit 8"
        exit 8;;
esac
