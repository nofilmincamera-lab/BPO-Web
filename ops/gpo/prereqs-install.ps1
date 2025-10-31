<#
.SYNOPSIS
    BPO Intelligence Pipeline - Prerequisites Installation Script (GPO Deployment)

.DESCRIPTION
    This script is executed via GPO Computer Startup Script.
    It installs and configures all prerequisites for the BPO Intelligence Pipeline:
    - Windows features (WSL2, Hyper-V, Containers)
    - Docker Desktop
    - Git
    - Directory structure
    - Firewall rules
    - NPX (for Context7 MCP if needed)

.NOTES
    File Name      : prereqs-install.ps1
    Prerequisite   : Run as SYSTEM via GPO Computer Startup Script
    Execution      : GPO Computer Configuration > Policies > Windows Settings > Scripts > Startup
#>

[CmdletBinding()]
param()

# ============================================================================
# CONFIGURATION
# ============================================================================
$ErrorActionPreference = "Continue"  # Continue on non-critical errors
$ProjectRoot = "D:\BPO-Project"
$LogFile = "$ProjectRoot\ops\logs\prereqs-install.log"
$InstallerShare = "\\\\DOMAIN\\SYSVOL\\YourDomain\\Installers"  # UPDATE THIS

# Installer paths (update with your actual paths)
$DockerDesktopMSI = "$InstallerShare\DockerDesktop.msi"
$GitInstaller = "$InstallerShare\Git-2.43.0-64-bit.exe"
$NodeJSInstaller = "$InstallerShare\node-v20.11.0-x64.msi"

# ============================================================================
# LOGGING FUNCTION
# ============================================================================
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    
    # Ensure log directory exists
    $LogDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    
    # Write to log file
    Add-Content -Path $LogFile -Value $LogMessage
    
    # Also write to console for debugging
    Write-Host $LogMessage
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
function Test-WindowsFeature {
    param([string]$FeatureName)
    
    $Feature = Get-WindowsOptionalFeature -Online -FeatureName $FeatureName -ErrorAction SilentlyContinue
    return ($Feature -and $Feature.State -eq "Enabled")
}

function Install-WindowsFeatureIfNeeded {
    param(
        [string]$FeatureName,
        [string]$DisplayName
    )
    
    if (Test-WindowsFeature -FeatureName $FeatureName) {
        Write-Log "$DisplayName is already enabled" -Level "INFO"
        return $true
    }
    
    Write-Log "Enabling $DisplayName..." -Level "INFO"
    try {
        Enable-WindowsOptionalFeature -Online -FeatureName $FeatureName -All -NoRestart -ErrorAction Stop | Out-Null
        Write-Log "$DisplayName enabled successfully" -Level "INFO"
        return $true
    } catch {
        Write-Log "Failed to enable $DisplayName : $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Install-MSI {
    param(
        [string]$InstallerPath,
        [string]$ProductName,
        [string]$Arguments = "/qn /norestart"
    )
    
    if (-not (Test-Path $InstallerPath)) {
        Write-Log "$ProductName installer not found: $InstallerPath" -Level "WARN"
        return $false
    }
    
    Write-Log "Installing $ProductName..." -Level "INFO"
    try {
        $Process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$InstallerPath`" $Arguments" -Wait -PassThru
        if ($Process.ExitCode -eq 0 -or $Process.ExitCode -eq 3010) {
            Write-Log "$ProductName installed successfully" -Level "INFO"
            return $true
        } else {
            Write-Log "$ProductName installation failed with exit code: $($Process.ExitCode)" -Level "ERROR"
            return $false
        }
    } catch {
        Write-Log "Failed to install $ProductName : $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
try {
    Write-Log "========================================" -Level "INFO"
    Write-Log "BPO Intelligence Pipeline - Prerequisites Installation" -Level "INFO"
    Write-Log "========================================" -Level "INFO"
    
    $NeedReboot = $false
    
    # ========================================================================
    # STEP 1: Create Directory Structure
    # ========================================================================
    Write-Log "Creating directory structure..." -Level "INFO"
    
    $Directories = @(
        "$ProjectRoot\data\raw",
        "$ProjectRoot\data\processed",
        "$ProjectRoot\data\ollama",
        "$ProjectRoot\data\label-studio",
        "$ProjectRoot\Heuristics",
        "$ProjectRoot\ops\secrets",
        "$ProjectRoot\ops\logs",
        "$ProjectRoot\ops\init-scripts",
        "$ProjectRoot\ops\grafana-dashboards",
        "$ProjectRoot\docker"
    )
    
    foreach ($Dir in $Directories) {
        if (-not (Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
            Write-Log "Created directory: $Dir" -Level "INFO"
        } else {
            Write-Log "Directory already exists: $Dir" -Level "INFO"
        }
    }
    
    # ========================================================================
    # STEP 2: Enable Windows Features
    # ========================================================================
    Write-Log "Enabling Windows features..." -Level "INFO"
    
    $Features = @(
        @{Name="VirtualMachinePlatform"; Display="Virtual Machine Platform"},
        @{Name="Microsoft-Windows-Subsystem-Linux"; Display="WSL2"},
        @{Name="Containers"; Display="Containers"},
        @{Name="Microsoft-Hyper-V-All"; Display="Hyper-V"}
    )
    
    foreach ($Feature in $Features) {
        if (Install-WindowsFeatureIfNeeded -FeatureName $Feature.Name -DisplayName $Feature.Display) {
            # Features may require reboot
            $NeedReboot = $true
        }
    }
    
    # ========================================================================
    # STEP 3: Install Docker Desktop
    # ========================================================================
    $DockerInstalled = Get-Command "docker" -ErrorAction SilentlyContinue
    if ($DockerInstalled) {
        Write-Log "Docker is already installed" -Level "INFO"
    } else {
        Install-MSI -InstallerPath $DockerDesktopMSI -ProductName "Docker Desktop" `
                    -Arguments "/qn /norestart ACCEPT_EULA=1"
    }
    
    # ========================================================================
    # STEP 4: Install Git
    # ========================================================================
    $GitInstalled = Get-Command "git" -ErrorAction SilentlyContinue
    if ($GitInstalled) {
        Write-Log "Git is already installed" -Level "INFO"
    } else {
        if (Test-Path $GitInstaller) {
            Write-Log "Installing Git..." -Level "INFO"
            $Process = Start-Process -FilePath $GitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait -PassThru
            if ($Process.ExitCode -eq 0) {
                Write-Log "Git installed successfully" -Level "INFO"
            } else {
                Write-Log "Git installation failed with exit code: $($Process.ExitCode)" -Level "ERROR"
            }
        } else {
            Write-Log "Git installer not found: $GitInstaller" -Level "WARN"
        }
    }
    
    # ========================================================================
    # STEP 5: Install Node.js (for NPX/Context7 MCP)
    # ========================================================================
    $NodeInstalled = Get-Command "node" -ErrorAction SilentlyContinue
    if ($NodeInstalled) {
        Write-Log "Node.js is already installed" -Level "INFO"
    } else {
        Install-MSI -InstallerPath $NodeJSInstaller -ProductName "Node.js"
    }
    
    # ========================================================================
    # STEP 6: Configure Firewall Rules
    # ========================================================================
    Write-Log "Configuring firewall rules..." -Level "INFO"
    
    $FirewallRules = @(
        @{Name="BPO-Postgres"; Port=5432; Description="BPO Postgres Database"},
        @{Name="BPO-Temporal"; Port=7233; Description="BPO Temporal gRPC"},
        @{Name="BPO-Temporal-UI"; Port=8233; Description="BPO Temporal UI"},
        @{Name="BPO-API"; Port=8000; Description="BPO API Service"},
        @{Name="BPO-LabelStudio"; Port=8082; Description="BPO Label Studio"}
    )
    
    foreach ($Rule in $FirewallRules) {
        $Existing = Get-NetFirewallRule -DisplayName $Rule.Name -ErrorAction SilentlyContinue
        if ($Existing) {
            Write-Log "Firewall rule already exists: $($Rule.Name)" -Level "INFO"
        } else {
            New-NetFirewallRule -DisplayName $Rule.Name `
                               -Direction Inbound `
                               -LocalPort $Rule.Port `
                               -Protocol TCP `
                               -Action Allow `
                               -Profile Private,Domain `
                               -Description $Rule.Description | Out-Null
            Write-Log "Created firewall rule: $($Rule.Name)" -Level "INFO"
        }
    }
    
    # ========================================================================
    # STEP 7: Set Ulimits (if applicable on Windows)
    # ========================================================================
    # Note: Windows doesn't have ulimit, but we can configure Docker settings
    # This would typically be done via Docker Desktop settings JSON
    
    # ========================================================================
    # STEP 8: Summary
    # ========================================================================
    Write-Log "========================================" -Level "INFO"
    Write-Log "Prerequisites installation completed" -Level "INFO"
    
    if ($NeedReboot) {
        Write-Log "*** SYSTEM REBOOT REQUIRED ***" -Level "WARN"
        Write-Log "Windows features have been enabled that require a reboot" -Level "WARN"
        Write-Log "The system will reboot automatically after this script completes" -Level "WARN"
    } else {
        Write-Log "No reboot required" -Level "INFO"
    }
    
    Write-Log "========================================" -Level "INFO"
    
    # Schedule a reboot if needed (GPO can handle this)
    if ($NeedReboot) {
        # Let GPO handle the reboot, or uncomment to force:
        # shutdown /r /t 300 /c "Rebooting to complete BPO Prerequisites installation"
    }
    
    exit 0
    
} catch {
    Write-Log "Unexpected error: $($_.Exception.Message)" -Level "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
    exit 1
}

