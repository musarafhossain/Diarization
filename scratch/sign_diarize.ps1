# Create self-signed Code Signing cert for Ilvi
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Ilvi, O=Ilvi, C=NL" -KeyUsage DigitalSignature -FriendlyName "Ilvi Code Signing Certificate" -CertStoreLocation "Cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(5)

Write-Host "Created certificate thumbprint:" $cert.Thumbprint

# Add to Trusted Root Certification Authorities & Trusted Publishers for CurrentUser
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store([System.Security.Cryptography.X509Certificates.StoreName]::Root, [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser)
$rootStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
$rootStore.Add($cert)
$rootStore.Close()

$pubStore = New-Object System.Security.Cryptography.X509Certificates.X509Store([System.Security.Cryptography.X509Certificates.StoreName]::TrustedPublisher, [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser)
$pubStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
$pubStore.Add($cert)
$pubStore.Close()

Write-Host "Added to Trusted Root and Trusted Publisher stores."

# Sign diarize.exe
$exePath = "F:\Local Transcrtiption\diarize_dist\diarize\diarize.exe"
$sig = Set-AuthenticodeSignature -FilePath $exePath -Certificate $cert -Description "Ilvi Offline Diarization Engine" -DescriptionUrl "https://ilvi.ai/"

# Verify signature
Get-AuthenticodeSignature $exePath | Format-List
