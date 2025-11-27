# 🚀 GitHub Setup for Automated Windows Builds

This guide helps you set up GitHub to automatically build the Windows installer.

## 📋 Prerequisites

1. GitHub account (merrymelgeorge@gmail.com)
2. Git installed on your computer

## 🔧 Step-by-Step Setup

### Step 1: Create a New GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Sign in with `merrymelgeorge@gmail.com`
3. Fill in:
   - **Repository name:** `LitigationTracker`
   - **Description:** `A web-based platform for tracking litigations`
   - **Visibility:** Private (or Public)
4. **DO NOT** check "Add a README file"
5. Click **Create repository**

### Step 2: Push Code to GitHub

Open Terminal and run these commands:

```bash
# Navigate to the project
cd /Users/merrgeor/Downloads/LitigationTracker

# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - Litigation Tracker v1.0.0"

# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/LitigationTracker.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Wait for Automatic Build

1. Go to your repository on GitHub
2. Click on **Actions** tab
3. You'll see "Build Windows Installer" workflow running
4. Wait ~5-10 minutes for it to complete

### Step 4: Download the Installer

1. In the **Actions** tab, click on the completed workflow run
2. Scroll down to **Artifacts**
3. Download `LitigationTracker-Installer-xxxxxxx`
4. Extract the ZIP file
5. Share `LitigationTracker_Setup_1.0.0.exe` with your users!

---

## 🏷️ Creating a Release (Optional but Recommended)

To create a proper versioned release:

```bash
# Create a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push the tag
git push origin v1.0.0
```

This will:
1. Trigger a new build
2. Automatically create a GitHub Release
3. Attach the installer to the release
4. Users can download from the Releases page

---

## 🔄 Updating the Application

When you make changes:

```bash
# Add changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push

# For a new version release
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

---

## 📁 What Gets Built

The GitHub Action creates:

| Artifact | Description |
|----------|-------------|
| `LitigationTracker-Portable-xxx` | Standalone folder (no installer needed) |
| `LitigationTracker-Installer-xxx` | Windows installer (.exe) |

---

## ❓ Troubleshooting

### Build Failed
- Check the **Actions** tab for error logs
- Common issues: syntax errors in Python files

### Can't Push to GitHub
```bash
# If you get authentication errors, use GitHub CLI
brew install gh
gh auth login
```

### Workflow Not Triggering
- Ensure the `.github/workflows/build-windows.yml` file was pushed
- Check if Actions are enabled in repository Settings

---

## 🔒 Security Note

- Keep the repository **Private** if the code is proprietary
- Never commit sensitive data (passwords, API keys)
- The database file is automatically excluded via `.gitignore`

