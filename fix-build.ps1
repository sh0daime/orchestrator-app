# Post-build script to fix home.html paths
# This copies dist/src/home.html to dist/home.html and fixes asset paths

$distSrcHtml = "dist/src/home.html"
$distHtml = "dist/home.html"

if (Test-Path $distSrcHtml) {
    # Copy the file
    Copy-Item -Path $distSrcHtml -Destination $distHtml -Force
    
    # Read the content
    $content = Get-Content $distHtml -Raw
    
    # Replace absolute paths with relative paths
    $content = $content -replace 'src="/assets/', 'src="./assets/'
    $content = $content -replace 'href="/assets/', 'href="./assets/'
    
    # Write back
    Set-Content -Path $distHtml -Value $content -NoNewline
    
    Write-Host "Fixed dist/home.html with relative asset paths"
} else {
    Write-Host "Warning: dist/src/home.html not found"
}



