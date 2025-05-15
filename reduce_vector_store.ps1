# PowerShell script to reduce ChromaDB vector store size for Render deployment
# 1. Backup current vector store
# 2. Keep only a few files in uploads/
# 3. Delete and regenerate vector store
# 4. Commit and push changes

# Set variables
$projectRoot = "$PSScriptRoot"
$chromaDir = Join-Path $projectRoot 'data\faiss_index\chroma'
$uploadsDir = Join-Path $projectRoot 'data\uploads'
$backupDir = Join-Path $projectRoot ('chroma_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))

Write-Host "Backing up current ChromaDB vector store..."
if (Test-Path $chromaDir) {
    Copy-Item $chromaDir $backupDir -Recurse -Force
    Write-Host "Backup created at $backupDir"
} else {
    Write-Host "ChromaDB directory not found. Skipping backup."
}

# List files in uploads and keep only the smallest one
Write-Host "Reducing uploads to only the smallest file..."
$uploadFiles = Get-ChildItem $uploadsDir -File | Sort-Object Length
if ($uploadFiles.Count -gt 1) {
    $filesToRemove = $uploadFiles | Select-Object -Skip 1
    foreach ($file in $filesToRemove) {
        Remove-Item $file.FullName -Force
        Write-Host "Removed: $($file.Name)"
    }
    Write-Host "Kept: $($uploadFiles[0].Name)"
} elseif ($uploadFiles.Count -eq 1) {
    Write-Host "Only one file present: $($uploadFiles[0].Name)"
} else {
    Write-Host "No files found in uploads. Please add at least one file."
    exit 1
}

# Delete current ChromaDB vector store
Write-Host "Deleting current ChromaDB vector store..."
if (Test-Path $chromaDir) {
    Remove-Item $chromaDir -Recurse -Force
    Write-Host "Deleted: $chromaDir"
}

# Recreate ChromaDB vector store with process_uploads.py
Write-Host "Regenerating ChromaDB vector store with process_uploads.py..."
python process_uploads.py

# Git add, commit, and push
Write-Host "Staging and committing new vector store..."
git add data/faiss_index/chroma/
git commit -m "Reduce ChromaDB vector store size for Render free tier"
git push

Write-Host "Done! You can now redeploy on Render."
