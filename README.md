# 👻 GhostIP - Advanced IP Rotation Utility

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Platform-Linux-green.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen.svg" alt="Status">
</div>

A stealthy, automated IP rotation tool that leverages proxychains4 to route all outgoing network traffic through a rotating list of proxies. Perfect for privacy-conscious users, penetration testers, and researchers who need to frequently change their IP address.

## 🌟 Features

- 🔄 **Automated IP Rotation** - Configurable rotation intervals
- 🎯 **Proxy Management** - Add, test, and refresh proxy lists
- 🌍 **Geo-IP Lookup** - Live location tracking for IP addresses
- 📊 **Comprehensive Logging** - Track all IP changes and errors
- ⚙️ **Settings Management** - Customizable chain types and DNS settings
- 🤖 **Background Operation** - Silent mode for uninterrupted operation
- 🧪 **Proxy Testing** - Concurrent proxy validation with latency metrics
- 🔍 **Free Proxy Scraping** - Automatic proxy list updates from multiple sources

## 📋 Table of Contents

- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Adding Proxies](#-adding-proxies)
- [Configuration](#-configuration)
- [Advanced Features](#-advanced-features)
- [Troubleshooting](#-troubleshooting)
- [File Structure](#-file-structure)
- [Contributing](#-contributing)

## 🔧 Requirements

### System Requirements
- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.6 or higher
- **Network**: Internet connection for proxy testing and updates

### Dependencies
- `proxychains4` - For routing traffic through proxies
- `python3-pip` - Python package manager
- `curl` - For IP testing (usually pre-installed)

## 📥 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/ghostip.git
cd ghostip
```

### Step 2: Install System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install proxychains4 python3-pip curl

# Fedora/CentOS/RHEL
sudo dnf install proxychains-ng python3-pip curl
# or for older versions:
sudo yum install proxychains-ng python3-pip curl
```

### Step 3: Install Python Dependencies
```bash
pip3 install requests colorama
```

### Step 4: Make Script Executable
```bash
chmod +x ghostip_tool.py
```

### Step 5: Verify Installation
```bash
python3 ghostip_tool.py
```

## 🚀 Quick Start

1. **Launch GhostIP**:
   ```bash
   python3 ghostip_tool.py
   ```

2. **Refresh Proxy List** (Option 3):
   - Select option `[3]` to automatically scrape free proxies
   - Wait for the process to complete

3. **Test Proxies** (Option 5):
   - Select option `[5]` to test all proxies
   - This identifies working proxies with latency metrics

4. **Start IP Rotation** (Option 1):
   - Select option `[1]` to begin rotation
   - Set your desired interval (recommended: 15+ seconds)
   - Press `Ctrl+C` to stop rotation

## 📖 Usage Guide

### 🖥️ Main Menu Options

| Option | Description | Usage |
|--------|------------|-------|
| `[1]` | **Start IP Rotation** | Begin automated proxy switching |
| `[2]` | **Add New Proxy** | Manually add proxy servers |
| `[3]` | **Refresh Proxy List** | Scrape new proxies from free sources |
| `[4]` | **View Proxy List** | Display all configured proxies |
| `[5]` | **Test Proxies** | Verify proxy connectivity and speed |
| `[6]` | **Geo-IP Lookup** | Check current or specified IP location |
| `[7]` | **Wipe Logs** | Securely delete log files |
| `[8]` | **Settings** | Configure chain types, DNS, and logging |
| `[9]` | **Help** | Display help information |
| `[0]` | **Exit** | Quit the application |

### 🎮 Interactive Controls

- **Start Rotation**: Configure interval, silent mode, and failure handling
- **Stop Rotation**: Press `Ctrl+C` during rotation
- **Navigation**: Use number keys to select menu options
- **Exit**: Type `0` or `Ctrl+C` from main menu

## 🔌 Adding Proxies

### 🎯 Method 1: Through the Application (Recommended)

#### Option A: Automatic Proxy Scraping
1. Select `[3] Refresh Proxy List` from main menu
2. Wait for automatic scraping from multiple sources:
   - ProxyScrape API
   - GitHub proxy repositories
   - Fresh proxy lists
3. Optionally test a sample of new proxies

#### Option B: Manual Proxy Addition
1. Select `[2] Add New Proxy` from main menu
2. Enter proxy details:
   ```
   Enter proxy IP: 192.168.1.100
   Enter proxy port: 8080
   Enter proxy type: http
   ```
3. Supported types: `http`, `socks4`, `socks5`

### 🗂️ Method 2: External File Editing

#### Direct File Modification
Edit the `proxies.txt` file directly:

```bash
nano proxies.txt
```

**File Format:**
```
# GhostIP Proxy List
# Format: IP:PORT:TYPE:STATUS
192.168.1.100:8080:http:unknown
203.0.113.1:1080:socks5:unknown
198.51.100.1:1080:socks4:unknown
```

#### Bulk Import Script
Create a bulk import script:

```bash
#!/bin/bash
# bulk_import.sh

echo "192.168.1.100:8080:http:unknown" >> proxies.txt
echo "203.0.113.1:1080:socks5:unknown" >> proxies.txt
echo "198.51.100.1:1080:socks4:unknown" >> proxies.txt
```

#### Import from External Lists
```bash
# Download and format external proxy lists
curl -s "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all" | \
awk '{print $1":http:unknown"}' >> proxies.txt
```

### 🧪 Testing Added Proxies

After adding proxies through any method:

1. **Test All Proxies**: Select `[5]` from main menu
2. **Test Sample**: During refresh, choose to test a sample
3. **View Results**: Select `[4]` to see proxy status and latency

## ⚙️ Configuration

### 🔧 Settings Menu Options

Access via `[8] Settings` from main menu:

| Setting | Options | Description |
|---------|---------|-------------|
| **Chain Type** | `dynamic_chain`, `strict_chain`, `random_chain` | How proxies are chained |
| **DNS Leak Protection** | `true`, `false` | Route DNS queries through proxy |
| **Use TOR** | `true`, `false` | Include TOR in proxy chain |
| **Silent Mode** | `true`, `false` | Minimize rotation output |
| **Log IP Changes** | `true`, `false` | Record IP transitions |

### 📁 Configuration Files

#### `ghostip.cfg` - Main Configuration
```ini
[rotation]
interval = 15
silent_mode = false

[proxychains]
chain_type = dynamic_chain
proxy_dns = true
use_tor = false

[logging]
log_ip_changes = true
```

#### `ghostip_proxychains.conf` - Proxychains Configuration
Automatically managed, but can be manually edited:
```
# GhostIP Proxychains Configuration
dynamic_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
http 192.168.1.100 8080
```

## 🔥 Advanced Features

### 🌐 Geo-IP Location Tracking

Monitor your IP location changes:
```bash
# Select [6] Geo-IP Lookup
# Leave blank for current IP or enter specific IP
```

**Sample Output:**
```
IP Information:
IP Address: 203.0.113.1
Country: United States
City: New York
Region: New York
ISP: Example ISP
Organization: Example Org
Timezone: America/New_York
```

### 📊 Logging and Monitoring

#### View Live Logs
```bash
tail -f ghostip.log
```

#### Log Format
```
2025-06-05 10:30:15 - INFO - IP Changed: 192.168.1.1 -> 203.0.113.1 via 192.168.1.100:8080 (http)
2025-06-05 10:30:45 - ERROR - Rotation error: Connection timeout
```

### 🔄 Advanced Rotation Options

#### Custom Rotation Intervals
- **Fast Rotation**: 10-30 seconds (higher detection risk)
- **Balanced**: 30-60 seconds (recommended)
- **Stealth**: 120+ seconds (lower detection risk)

#### Failure Handling
- **Skip Failed**: Temporarily avoid non-working proxies
- **Retry Failed**: Continue attempting failed proxies
- **Auto-Reset**: Clear failed proxy list after all fail

### 🧵 Concurrent Proxy Testing

Modify testing parameters in the code:
```python
# In ProxyManager.test_all_proxies()
max_workers = 20  # Increase for faster testing
timeout = 10      # Increase for slower proxies
```

## 🐛 Troubleshooting

### 🚨 Common Issues

#### Issue: "proxychains4 not found"
**Solution:**
```bash
# Ubuntu/Debian
sudo apt install proxychains4

# Verify installation
which proxychains4
```

#### Issue: "No live proxies available"
**Solutions:**
1. Refresh proxy list: Select `[3]`
2. Add working proxies manually: Select `[2]`
3. Check internet connection
4. Try different proxy sources

#### Issue: "Connection timeouts during rotation"
**Solutions:**
1. Increase rotation interval (30+ seconds)
2. Test proxies first: Select `[5]`
3. Enable "Skip failed proxies" option
4. Check proxy quality and location

#### Issue: "Permission denied errors"
**Solutions:**
```bash
# Make script executable
chmod +x ghostip_tool.py

# Fix file permissions
chmod 644 proxies.txt ghostip.cfg
```

### 🔍 Debug Mode

Enable verbose logging by modifying the script:
```python
# In Logger.__init__()
level=logging.DEBUG  # Change from INFO
```

### 🧪 Manual Testing

Test proxychains configuration manually:
```bash
# Test current configuration
proxychains4 -f ghostip_proxychains.conf curl ifconfig.me

# Test specific proxy
echo "http 192.168.1.100 8080" > test.conf
proxychains4 -f test.conf curl ifconfig.me
```

## 📂 File Structure

```
ghostip/
├── ghostip_tool.py              # Main application script
├── proxies.txt                  # Proxy list storage
├── ghostip.cfg                  # Application configuration
├── ghostip.log                  # IP rotation logs
├── ghostip_proxychains.conf     # Dynamic proxychains config
├── README.md                    # This documentation
├── requirements.txt             # Python dependencies
└── examples/
    ├── bulk_import.sh           # Bulk proxy import script
    ├── proxy_sources.txt        # List of proxy sources
    └── sample_config.cfg        # Sample configuration
```

### 📝 Generated Files

| File | Purpose | Auto-Generated |
|------|---------|----------------|
| `proxies.txt` | Stores proxy list | ✅ |
| `ghostip.cfg` | Application settings | ✅ |
| `ghostip.log` | IP change logs | ✅ |
| `ghostip_proxychains.conf` | Proxychains config | ✅ |

## 🔒 Security Considerations

### 🛡️ Privacy Features
- **DNS Leak Protection**: Routes DNS queries through proxies
- **Log Wiping**: Secure deletion of rotation logs
- **No Data Storage**: No sensitive information stored
- **Chain Randomization**: Supports random proxy chaining

### ⚠️ Important Notes
- Use only legitimate proxy sources
- Respect website terms of service
- Monitor for IP leaks during rotation
- Regularly update proxy lists for reliability
- Consider legal implications in your jurisdiction

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🔀 Development Setup
```bash
git clone https://github.com/yourusername/ghostip.git
cd ghostip
git checkout -b feature/your-feature-name
```

### 📋 Contribution Guidelines
1. **Code Style**: Follow PEP 8 Python style guidelines
2. **Testing**: Test new features with multiple proxy types
3. **Documentation**: Update README for new features
4. **Commits**: Use clear, descriptive commit messages

### 🐛 Bug Reports
Please include:
- Operating system and version
- Python version
- Complete error messages
- Steps to reproduce
- Proxy types being used

### 💡 Feature Requests
- Check existing issues first
- Provide detailed use case descriptions
- Consider implementation complexity
- Suggest backward compatibility approaches

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **proxychains4** - Core proxy chaining functionality
- **Free Proxy Sources** - Community-maintained proxy lists
- **Python Community** - Excellent libraries and tools
- **Security Researchers** - Inspiration for privacy tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ghostip/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ghostip/discussions)
- **Documentation**: This README and inline code comments

---

<div align="center">
  <strong>Made with ❤️ for privacy and security enthusiasts</strong>
  <br>
  <small>Remember to use responsibly and respect others' resources</small>
</div>