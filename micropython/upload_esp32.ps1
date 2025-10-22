$ports = @("COM3", "COM5")
$sourceDir = "micropython"
$files = @("main.py")

foreach ($port in $ports) {
    Write-Host "`nUploading files to ESP32 on $port..."
    foreach ($file in $files) {
        Write-Host "Transferring $file to $port..."
        mpremote connect $port cp "$sourceDir/$file" ":$file"
    }
    Write-Host "Upload complete on $port!"
}

mpremote connect COM3 run micropython/main.py