@echo off
echo Waiting for device...
adb wait-for-device

echo Backup original cacerts...
adb shell "su -c 'cp -R /system/etc/security/cacerts /data/local/tmp/cacerts_backup 2>/dev/null || true'"

echo Mount tmpfs over cacerts...
adb shell "su -c 'mount -t tmpfs tmpfs /system/etc/security/cacerts'"

echo Restore original certificates...
adb shell "su -c 'cp -R /data/local/tmp/cacerts_backup/* /system/etc/security/cacerts/'"

echo Inject mitmproxy cert...
adb shell "su -c 'cp /sdcard/c8750f0d.0 /system/etc/security/cacerts/'"

echo Fix permissions...
adb shell "su -c 'chmod 644 /system/etc/security/cacerts/c8750f0d.0'"
adb shell "su -c 'chown root:root /system/etc/security/cacerts/c8750f0d.0'"

echo Verify certificate...
adb shell "su -c 'ls /system/etc/security/cacerts | grep c8750f0d'"

echo Done.
pause