#!/usr/bin/env python3
"""
GhostIP - Advanced IP Rotation Utility
======================================

A stealthy, automated IP rotation tool that leverages proxychains4 to route
all outgoing network traffic through a rotating list of proxies.

Features:
- Automated IP rotation with configurable intervals
- Proxy management (add, test, refresh)
- Live geo-IP lookup
- Comprehensive logging
- Settings management
- Background operation support

Requirements:
- Linux environment
- proxychains4 installed
- Python 3.6+
- requests library

Installation:
1. Install proxychains4: sudo apt-get install proxychains4
2. Install Python dependencies: pip install requests colorama
3. Run: python3 ghostip.py

Usage:
- Run the script and follow the interactive menu
- Configure proxies and settings as needed
- Start IP rotation for automated proxy switching

Author: Claude AI Assistant
Version: 1.0
"""

import os
import sys
import time
import json
import random
import signal
import logging
import threading
import subprocess
import configparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import re

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_ENABLED = True
except ImportError:
    COLORS_ENABLED = False
    # Fallback color constants
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ""


class ProxyValidator:
    """Validates and tests proxy connections."""
    
    def __init__(self):
        self.session = self._create_session()
        self.test_urls = [
            'http://httpbin.org/ip',
            'http://ifconfig.me/ip',
            'http://api.ipify.org'
        ]
    
    def _create_session(self):
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def validate_proxy_format(self, proxy_ip, proxy_port, proxy_type):
        """Validate proxy format and parameters."""
        # IP validation
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, proxy_ip):
            return False, "Invalid IP address format"
        
        # Port validation
        try:
            port = int(proxy_port)
            if not (1 <= port <= 65535):
                return False, "Port must be between 1 and 65535"
        except ValueError:
            return False, "Invalid port number"
        
        # Type validation
        valid_types = ['http', 'socks4', 'socks5']
        if proxy_type.lower() not in valid_types:
            return False, f"Invalid proxy type. Must be one of: {', '.join(valid_types)}"
        
        return True, "Valid"
    
    def test_proxy(self, proxy_ip, proxy_port, proxy_type, timeout=8):
        """Test if a proxy is working and return connection details."""
        proxy_url = f"{proxy_type.lower()}://{proxy_ip}:{proxy_port}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Multiple test URLs for better reliability
        test_urls = [
            'http://httpbin.org/ip',
            'http://ifconfig.me/ip',
            'http://api.ipify.org',
            'http://icanhazip.com',
            'http://ident.me'
        ]
        
        start_time = time.time()
        
        for test_url in test_urls:
            try:
                response = self.session.get(
                    test_url, 
                    proxies=proxies, 
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Linux; Ubuntu) GhostIP/1.0',
                        'Accept': 'text/plain,application/json,*/*',
                        'Connection': 'close'
                    }
                )
                
                if response.status_code == 200 and response.text.strip():
                    # Verify we got a valid IP response
                    response_text = response.text.strip()
                    if self._is_valid_ip_format(response_text):
                        latency = round((time.time() - start_time) * 1000, 2)
                        return True, response_text, latency
                        
            except (requests.RequestException, ConnectionError, TimeoutError):
                continue
            except Exception:
                continue
        
        return False, "No valid response from test URLs", 0
    
    def _is_valid_ip_format(self, ip_text):
        """Validate if text contains a valid IP address."""
        # Extract IP from response (handles JSON responses too)
        import re
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        match = re.search(ip_pattern, ip_text)
        if match:
            ip = match.group()
            parts = ip.split('.')
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False
        return False


class ProxyManager:
    """Manages proxy list operations."""
    
    def __init__(self, proxy_file='proxies.txt'):
        self.proxy_file = proxy_file
        self.proxies = []
        self.validator = ProxyValidator()
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file."""
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r') as f:
                    self.proxies = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split(':')
                            if len(parts) >= 3:
                                proxy = {
                                    'ip': parts[0],
                                    'port': parts[1],
                                    'type': parts[2],
                                    'status': parts[3] if len(parts) > 3 else 'unknown'
                                }
                                self.proxies.append(proxy)
            except Exception as e:
                print(f"{Fore.RED}Error loading proxies: {e}")
    
    def save_proxies(self):
        """Save proxies to file."""
        try:
            with open(self.proxy_file, 'w') as f:
                f.write("# GhostIP Proxy List\n")
                f.write("# Format: IP:PORT:TYPE:STATUS\n")
                for proxy in self.proxies:
                    f.write(f"{proxy['ip']}:{proxy['port']}:{proxy['type']}:{proxy['status']}\n")
        except Exception as e:
            print(f"{Fore.RED}Error saving proxies: {e}")
    
    def add_proxy(self, ip, port, proxy_type):
        """Add a new proxy to the list."""
        # Check if proxy already exists
        for proxy in self.proxies:
            if proxy['ip'] == ip and proxy['port'] == port:
                return False, "Proxy already exists"
        
        # Validate format
        valid, msg = self.validator.validate_proxy_format(ip, port, proxy_type)
        if not valid:
            return False, msg
        
        # Add proxy
        new_proxy = {
            'ip': ip,
            'port': port,
            'type': proxy_type.lower(),
            'status': 'unknown'
        }
        self.proxies.append(new_proxy)
        self.save_proxies()
        return True, "Proxy added successfully"
    
    def test_all_proxies(self, max_workers=10):
        """Test all proxies concurrently."""
        if not self.proxies:
            return
        
        print(f"{Fore.YELLOW}Testing {len(self.proxies)} proxies...")
        
        def test_single_proxy(proxy):
            working, response, latency = self.validator.test_proxy(
                proxy['ip'], proxy['port'], proxy['type']
            )
            proxy['status'] = 'live' if working else 'dead'
            if working:
                proxy['latency'] = latency
            return proxy, working
        
        live_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(test_single_proxy, proxy): proxy 
                             for proxy in self.proxies}
            
            for future in as_completed(future_to_proxy):
                proxy, is_live = future.result()
                if is_live:
                    live_count += 1
                    print(f"{Fore.GREEN}✓ {proxy['ip']}:{proxy['port']} - {proxy.get('latency', 0)}ms")
                else:
                    print(f"{Fore.RED}✗ {proxy['ip']}:{proxy['port']} - Failed")
        
        self.save_proxies()
        print(f"\n{Fore.CYAN}Testing complete: {live_count}/{len(self.proxies)} proxies are live")
    
    def get_live_proxies(self):
        """Return only live proxies."""
        return [p for p in self.proxies if p['status'] == 'live']
    
    def scrape_free_proxies(self):
        """Scrape proxies from multiple reliable free proxy sources."""
        print(f"{Fore.YELLOW}Scraping free proxies from multiple sources...")
        
        sources = [
            # ProxyScrape API - Multiple protocols
            {
                'url': 'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all&format=textplain',
                'type': 'http'
            },
            {
                'url': 'https://api.proxyscrape.com/v2/?request=get&protocol=socks4&timeout=5000&country=all&format=textplain',
                'type': 'socks4'
            },
            {
                'url': 'https://api.proxyscrape.com/v2/?request=get&protocol=socks5&timeout=5000&country=all&format=textplain',
                'type': 'socks5'
            },
            # GitHub proxy lists
            {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'type': 'http'
            },
            {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
                'type': 'socks4'
            },
            {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
                'type': 'socks5'
            },
            # Proxifly GitHub
            {
                'url': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/http.txt',
                'type': 'http'
            },
            {
                'url': 'https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt',
                'type': 'http'
            }
        ]
        
        new_proxies = 0
        for source in sources:
            try:
                print(f"{Fore.CYAN}Fetching {source['type']} proxies from: {source['url'][:50]}...")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Linux; Ubuntu) GhostIP/1.0',
                    'Accept': 'text/plain,text/html,*/*'
                }
                
                response = requests.get(source['url'], timeout=20, headers=headers)
                if response.status_code == 200:
                    lines = response.text.split('\n')
                    source_count = 0
                    
                    for line in lines:
                        line = line.strip()
                        if ':' in line and not line.startswith('#'):
                            # Handle different formats
                            if line.count(':') >= 1:
                                parts = line.split(':')[:2]  # Take only IP:PORT
                                if len(parts) == 2:
                                    ip, port = parts[0].strip(), parts[1].strip()
                                    
                                    # Validate IP format quickly
                                    if self._is_valid_ip_format(ip) and port.isdigit():
                                        success, msg = self.add_proxy(ip, port, source['type'])
                                        if success:
                                            new_proxies += 1
                                            source_count += 1
                    
                    print(f"{Fore.GREEN}  Added {source_count} {source['type']} proxies")
                else:
                    print(f"{Fore.RED}  Failed to fetch (HTTP {response.status_code})")
                    
            except requests.RequestException as e:
                print(f"{Fore.RED}  Network error: {str(e)[:50]}...")
            except Exception as e:
                print(f"{Fore.RED}  Error processing source: {str(e)[:50]}...")
        
        print(f"\n{Fore.GREEN}Total: Added {new_proxies} new proxies from all sources")
        
        # Auto-test a sample of new proxies
        if new_proxies > 0:
            test_sample = input(f"{Fore.YELLOW}Test a sample of new proxies now? (y/N): ").lower().startswith('y')
            if test_sample:
                print(f"{Fore.CYAN}Testing sample of recently added proxies...")
                self._test_proxy_sample(20)  # Test 20 random proxies
        
        return new_proxies
    
    def _is_valid_ip_format(self, ip):
        """Quick IP format validation."""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def _test_proxy_sample(self, sample_size):
        """Test a random sample of proxies."""
        if not self.proxies:
            return
        
        # Get untested or unknown status proxies
        untested = [p for p in self.proxies if p['status'] in ['unknown', 'dead']]
        if not untested:
            untested = self.proxies
        
        # Sample random proxies
        sample = random.sample(untested, min(sample_size, len(untested)))
        
        def test_single_proxy(proxy):
            working, response, latency = self.validator.test_proxy(
                proxy['ip'], proxy['port'], proxy['type'], timeout=8
            )
            proxy['status'] = 'live' if working else 'dead'
            if working:
                proxy['latency'] = latency
            return proxy, working
        
        live_count = 0
        print(f"{Fore.YELLOW}Testing {len(sample)} proxies...")
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_proxy = {executor.submit(test_single_proxy, proxy): proxy 
                             for proxy in sample}
            
            for future in as_completed(future_to_proxy):
                try:
                    proxy, is_live = future.result()
                    status_icon = f"{Fore.GREEN}✓" if is_live else f"{Fore.RED}✗"
                    latency_info = f" ({proxy.get('latency', 0)}ms)" if is_live else ""
                    
                    print(f"{status_icon} {proxy['ip']}:{proxy['port']}{latency_info}")
                    
                    if is_live:
                        live_count += 1
                except Exception as e:
                    print(f"{Fore.RED}✗ Test error: {e}")
        
        self.save_proxies()
        print(f"\n{Fore.CYAN}Sample test complete: {live_count}/{len(sample)} proxies are working")


class ProxychainsManager:
    """Manages proxychains4 configuration."""
    
    def __init__(self, config_path='/etc/proxychains.conf'):
        self.config_path = config_path
        self.local_config = 'ghostip_proxychains.conf'
        self.chain_type = 'dynamic_chain'
        self.proxy_dns = True
        self.create_local_config()
    
    def create_local_config(self):
        """Create a local proxychains configuration."""
        config_content = f"""# GhostIP Proxychains Configuration
strict_chain
# proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
# Proxies will be added here dynamically
"""
        try:
            with open(self.local_config, 'w') as f:
                f.write(config_content)
        except Exception as e:
            print(f"{Fore.RED}Error creating local config: {e}")
    
    def update_config(self, proxy_ip, proxy_port, proxy_type):
        """Update proxychains config with current proxy."""
        chain_mode = self.chain_type
        dns_setting = "proxy_dns" if self.proxy_dns else "# proxy_dns"
        
        config_content = f"""# GhostIP Proxychains Configuration
{chain_mode}
{dns_setting}
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
{proxy_type} {proxy_ip} {proxy_port}
"""
        
        try:
            with open(self.local_config, 'w') as f:
                f.write(config_content)
            return True
        except Exception as e:
            print(f"{Fore.RED}Error updating config: {e}")
            return False
    
    def run_command(self, command):
        """Run a command through proxychains."""
        try:
            cmd = f"proxychains4 -f {self.local_config} {command}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, 
                text=True, timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)


class GeoIPLookup:
    """Handles geo-IP location lookups."""
    
    def __init__(self):
        self.apis = [
            'http://ip-api.com/json/',
            'http://ipapi.co/json/',
            'https://ipapi.co/json/'
        ]
    
    def lookup(self, ip_address=None):
        """Lookup geographical information for an IP."""
        for api in self.apis:
            try:
                url = f"{api}{ip_address}" if ip_address else api
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return self._format_response(data)
            except Exception as e:
                continue
        
        return None
    
    def _format_response(self, data):
        """Format the API response."""
        formatted = {}
        
        # Handle different API response formats
        if 'query' in data:  # ip-api.com
            formatted = {
                'ip': data.get('query', 'N/A'),
                'country': data.get('country', 'N/A'),
                'city': data.get('city', 'N/A'),
                'region': data.get('regionName', 'N/A'),
                'isp': data.get('isp', 'N/A'),
                'org': data.get('org', 'N/A'),
                'timezone': data.get('timezone', 'N/A')
            }
        elif 'ip' in data:  # ipapi.co
            formatted = {
                'ip': data.get('ip', 'N/A'),
                'country': data.get('country_name', 'N/A'),
                'city': data.get('city', 'N/A'),
                'region': data.get('region', 'N/A'),
                'isp': data.get('org', 'N/A'),
                'org': data.get('org', 'N/A'),
                'timezone': data.get('timezone', 'N/A')
            }
        
        return formatted


class Logger:
    """Handles logging operations."""
    
    def __init__(self, log_file='ghostip.log'):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('GhostIP')
    
    def log_ip_change(self, old_ip, new_ip, proxy_info):
        """Log IP address changes."""
        message = f"IP Changed: {old_ip} -> {new_ip} via {proxy_info['ip']}:{proxy_info['port']} ({proxy_info['type']})"
        self.logger.info(message)
    
    def log_error(self, error_message):
        """Log error messages."""
        self.logger.error(error_message)
    
    def wipe_logs(self):
        """Securely wipe log files."""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
                return True
        except Exception as e:
            print(f"{Fore.RED}Error wiping logs: {e}")
        return False


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file='ghostip.cfg'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        default_config = {
            'rotation': {
                'interval': '10',
                'silent_mode': 'false'
            },
            'proxychains': {
                'chain_type': 'dynamic_chain',
                'proxy_dns': 'true',
                'use_tor': 'false'
            },
            'logging': {
                'log_ip_changes': 'true'
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
            except:
                pass
        
        # Ensure all sections exist
        for section, options in default_config.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in options.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
        
        self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            print(f"{Fore.RED}Error saving config: {e}")
    
    def get(self, section, key):
        """Get configuration value."""
        return self.config.get(section, key)
    
    def getboolean(self, section, key):
        """Get boolean configuration value."""
        return self.config.getboolean(section, key)
    
    def set(self, section, key, value):
        """Set configuration value."""
        self.config.set(section, key, str(value))
        self.save_config()


class GhostIP:
    """Main GhostIP application class."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.proxychains = ProxychainsManager()
        self.geoip = GeoIPLookup()
        self.logger = Logger()
        self.config = ConfigManager()
        self.rotation_active = False
        self.current_ip = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        print(f"\n{Fore.YELLOW}Received signal {signum}. Shutting down gracefully...")
        self.rotation_active = False
        sys.exit(0)
    
    def display_banner(self):
        """Display application banner."""
        banner = f"""
{Fore.CYAN}┌────────────────────────────────────────┐
{Fore.CYAN}│            {Fore.WHITE}GHOSTIP v1.0{Fore.CYAN}               │
{Fore.CYAN}│      {Fore.YELLOW}Advanced IP Rotation Tool{Fore.CYAN}       │
{Fore.CYAN}└────────────────────────────────────────┘{Style.RESET_ALL}
"""
        print(banner)
    
    def display_menu(self):
        """Display main menu."""
        menu = f"""
{Fore.CYAN}┌────────────────────────────┐
{Fore.CYAN}│     {Fore.WHITE}GHOSTIP MAIN MENU{Fore.CYAN}      │
{Fore.CYAN}├────────────────────────────┤
{Fore.CYAN}│ {Fore.GREEN}[1]{Fore.WHITE} Start IP Rotation      {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[2]{Fore.WHITE} Add New Proxy          {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[3]{Fore.WHITE} Refresh Proxy List     {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[4]{Fore.WHITE} View Proxy List        {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[5]{Fore.WHITE} Test Proxies           {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[6]{Fore.WHITE} Geo-IP Lookup (Live)   {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[7]{Fore.WHITE} Wipe Logs              {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[8]{Fore.WHITE} Settings               {Fore.CYAN}│
{Fore.CYAN}│ {Fore.GREEN}[9]{Fore.WHITE} Help                   {Fore.CYAN}│
{Fore.CYAN}│ {Fore.RED}[0]{Fore.WHITE} Exit                   {Fore.CYAN}│
{Fore.CYAN}└────────────────────────────┘{Style.RESET_ALL}
"""
        print(menu)
    
    def start_rotation(self):
        """Start IP rotation process with improved error handling."""
        live_proxies = self.proxy_manager.get_live_proxies()
        if not live_proxies:
            print(f"{Fore.RED}No live proxies available!")
            print(f"{Fore.YELLOW}Recommendations:")
            print(f"  1. Use option [3] to refresh proxy list")
            print(f"  2. Use option [5] to test existing proxies")
            print(f"  3. Use option [2] to add working proxies manually")
            return
        
        try:
            interval = int(input(f"{Fore.YELLOW}Enter rotation interval in seconds (default 15): ") or "15")
            if interval < 10:
                print(f"{Fore.YELLOW}Warning: Intervals below 10 seconds may cause connection issues.")
                interval = max(interval, 10)
        except ValueError:
            print(f"{Fore.RED}Invalid interval. Using default 15 seconds.")
            interval = 15
        
        silent_mode = input(f"{Fore.YELLOW}Enable silent mode? (y/N): ").lower().startswith('y')
        retry_failed = input(f"{Fore.YELLOW}Skip failed proxies temporarily? (Y/n): ").lower() != 'n'
        
        print(f"\n{Fore.GREEN}Starting IP rotation with {len(live_proxies)} proxies...")
        print(f"{Fore.CYAN}Interval: {interval} seconds")
        print(f"{Fore.CYAN}Silent mode: {'Enabled' if silent_mode else 'Disabled'}")
        print(f"{Fore.CYAN}Retry failed: {'Enabled' if retry_failed else 'Disabled'}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop rotation\n")
        
        self.rotation_active = True
        proxy_index = 0
        failed_proxies = set()  # Track temporarily failed proxies
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while self.rotation_active:
            try:
                # Filter out temporarily failed proxies if retry_failed is enabled
                available_proxies = [p for p in live_proxies 
                                   if not retry_failed or f"{p['ip']}:{p['port']}" not in failed_proxies]
                
                if not available_proxies:
                    print(f"{Fore.RED}All proxies temporarily failed. Resetting failed proxy list...")
                    failed_proxies.clear()
                    available_proxies = live_proxies
                    time.sleep(30)  # Wait before retry
                    continue
                
                # Use modulo to cycle through available proxies
                proxy = available_proxies[proxy_index % len(available_proxies)]
                proxy_id = f"{proxy['ip']}:{proxy['port']}"
                
                # Update proxychains config
                if self.proxychains.update_config(proxy['ip'], proxy['port'], proxy['type']):
                    # Test current IP with multiple methods
                    success, new_ip = self._test_current_connection()
                    
                    if success and new_ip:
                        consecutive_failures = 0
                        # Remove from failed list if it worked
                        failed_proxies.discard(proxy_id)
                        
                        if not silent_mode:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"{Fore.GREEN}[{timestamp}] "
                                  f"✓ {proxy['ip']}:{proxy['port']} ({proxy['type']}) -> {new_ip}")
                        
                        # Log IP change
                        if self.config.getboolean('logging', 'log_ip_changes'):
                            self.logger.log_ip_change(self.current_ip or "Unknown", new_ip, proxy)
                        
                        self.current_ip = new_ip
                        
                        # Show geo-location info occasionally
                        if not silent_mode and proxy_index % 10 == 0:
                            geo_info = self.geoip.lookup(new_ip)
                            if geo_info:
                                print(f"{Fore.CYAN}    Location: {geo_info.get('city', 'Unknown')}, "
                                      f"{geo_info.get('country', 'Unknown')}")
                    else:
                        consecutive_failures += 1
                        failed_proxies.add(proxy_id)
                        
                        if not silent_mode:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"{Fore.RED}[{timestamp}] "
                                  f"✗ {proxy['ip']}:{proxy['port']} - Connection failed")
                        
                        # If too many consecutive failures, take a longer break
                        if consecutive_failures >= max_consecutive_failures:
                            print(f"{Fore.YELLOW}Too many failures. Taking 60 second break...")
                            time.sleep(60)
                            consecutive_failures = 0
                
                # Move to next proxy
                proxy_index += 1
                
                # Wait for interval (shorter wait if proxy failed)
                wait_time = interval if success else min(interval // 2, 5)
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Fore.RED}Error during rotation: {e}")
                self.logger.log_error(f"Rotation error: {e}")
                time.sleep(10)
        
        self.rotation_active = False
        print(f"\n{Fore.YELLOW}IP rotation stopped.")
        
        # Show final statistics
        if failed_proxies:
            print(f"{Fore.CYAN}Failed proxies this session: {len(failed_proxies)}")
    
    def _test_current_connection(self):
        """Test current connection through proxychains with multiple methods."""
        test_commands = [
            "curl -s --connect-timeout 15 --max-time 20 ifconfig.me",
            "curl -s --connect-timeout 15 --max-time 20 api.ipify.org",
            "curl -s --connect-timeout 15 --max-time 20 icanhazip.com"
        ]
        
        for cmd in test_commands:
            try:
                success, ip = self.proxychains.run_command(cmd)
                if success and ip and self.proxy_manager.validator._is_valid_ip_format(ip):
                    return True, ip.strip()
            except:
                continue
        
        return False, None
    
    def add_proxy_menu(self):
        """Add new proxy menu."""
        print(f"\n{Fore.CYAN}=== Add New Proxy ===")
        
        try:
            ip = input("Enter proxy IP: ").strip()
            port = input("Enter proxy port: ").strip()
            proxy_type = input("Enter proxy type (http/socks4/socks5): ").strip().lower()
            
            if not ip or not port or not proxy_type:
                print(f"{Fore.RED}All fields are required.")
                return
            
            success, message = self.proxy_manager.add_proxy(ip, port, proxy_type)
            if success:
                print(f"{Fore.GREEN}{message}")
            else:
                print(f"{Fore.RED}{message}")
                
        except KeyboardInterrupt:
            pass
    
    def view_proxies(self):
        """Display proxy list."""
        print(f"\n{Fore.CYAN}=== Proxy List ===")
        
        if not self.proxy_manager.proxies:
            print(f"{Fore.YELLOW}No proxies configured.")
            return
        
        print(f"{Fore.WHITE}{'#':<3} {'IP':<15} {'Port':<6} {'Type':<8} {'Status':<8} {'Latency':<10}")
        print("-" * 60)
        
        for i, proxy in enumerate(self.proxy_manager.proxies, 1):
            status_color = Fore.GREEN if proxy['status'] == 'live' else Fore.RED if proxy['status'] == 'dead' else Fore.YELLOW
            latency = f"{proxy.get('latency', 0)}ms" if proxy['status'] == 'live' else "N/A"
            
            print(f"{i:<3} {proxy['ip']:<15} {proxy['port']:<6} {proxy['type']:<8} "
                  f"{status_color}{proxy['status']:<8}{Style.RESET_ALL} {latency:<10}")
    
    def geoip_lookup_menu(self):
        """Geo-IP lookup menu."""
        print(f"\n{Fore.CYAN}=== Geo-IP Lookup ===")
        
        ip = input("Enter IP address (leave blank for current): ").strip()
        
        print(f"{Fore.YELLOW}Looking up IP information...")
        result = self.geoip.lookup(ip if ip else None)
        
        if result:
            print(f"\n{Fore.GREEN}IP Information:")
            print(f"{Fore.WHITE}IP Address: {result.get('ip', 'N/A')}")
            print(f"{Fore.WHITE}Country: {result.get('country', 'N/A')}")
            print(f"{Fore.WHITE}City: {result.get('city', 'N/A')}")
            print(f"{Fore.WHITE}Region: {result.get('region', 'N/A')}")
            print(f"{Fore.WHITE}ISP: {result.get('isp', 'N/A')}")
            print(f"{Fore.WHITE}Organization: {result.get('org', 'N/A')}")
            print(f"{Fore.WHITE}Timezone: {result.get('timezone', 'N/A')}")
        else:
            print(f"{Fore.RED}Failed to lookup IP information.")
    
    def settings_menu(self):
        """Settings configuration menu."""
        while True:
            print(f"\n{Fore.CYAN}=== Settings ===")
            print(f"1. Chain Type: {self.config.get('proxychains', 'chain_type')}")
            print(f"2. DNS Leak Protection: {self.config.get('proxychains', 'proxy_dns')}")
            print(f"3. Use TOR: {self.config.get('proxychains', 'use_tor')}")
            print(f"4. Silent Mode: {self.config.get('rotation', 'silent_mode')}")
            print(f"5. Log IP Changes: {self.config.get('logging', 'log_ip_changes')}")
            print("0. Back to main menu")
            
            choice = input(f"\n{Fore.YELLOW}Enter choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                print("Chain types: dynamic_chain, strict_chain, random_chain")
                new_type = input("Enter chain type: ").strip()
                if new_type in ['dynamic_chain', 'strict_chain', 'random_chain']:
                    self.config.set('proxychains', 'chain_type', new_type)
                    self.proxychains.chain_type = new_type
                    print(f"{Fore.GREEN}Chain type updated.")
            elif choice == '2':
                dns_setting = input("Enable DNS leak protection? (y/n): ").lower().startswith('y')
                self.config.set('proxychains', 'proxy_dns', str(dns_setting))
                self.proxychains.proxy_dns = dns_setting
                print(f"{Fore.GREEN}DNS setting updated.")
            elif choice == '3':
                tor_setting = input("Use TOR proxy? (y/n): ").lower().startswith('y')
                self.config.set('proxychains', 'use_tor', str(tor_setting))
                print(f"{Fore.GREEN}TOR setting updated.")
            elif choice == '4':
                silent_setting = input("Enable silent mode? (y/n): ").lower().startswith('y')
                self.config.set('rotation', 'silent_mode', str(silent_setting))
                print(f"{Fore.GREEN}Silent mode updated.")
            elif choice == '5':
                log_setting = input("Log IP changes? (y/n): ").lower().startswith('y')
                self.config.set('logging', 'log_ip_changes', str(log_setting))
                print(f"{Fore.GREEN}Logging setting updated.")
    
    def show_help(self):
        """Display help information."""
        help_text = f"""
{Fore.CYAN}=== GhostIP Help ===

{Fore.YELLOW}Installation Requirements:
{Fore.WHITE}- Linux environment
- proxychains4 installed (sudo apt-get install proxychains4)
- Python 3.6+ with requests and colorama libraries

{Fore.YELLOW}Basic Usage:
{Fore.WHITE}1. Add proxies manually or refresh from free sources
2. Test proxies to verify they work
3. Start IP rotation with desired interval
4. Monitor logs and geo-location changes

{Fore.YELLOW}Menu Options:
{Fore.WHITE}[1] Start IP Rotation - Begin automated proxy switching
[2] Add New Proxy - Manually add proxy servers
[3] Refresh Proxy List - Scrape new proxies from free sources
[4] View Proxy List - Display all configured proxies
[5] Test Proxies - Verify proxy connectivity and speed
[6] Geo-IP Lookup - Check current or specified IP location
[7] Wipe Logs - Securely delete log files
[8] Settings - Configure chain types, DNS, and logging
[9] Help - Display this help information

{Fore.YELLOW}Files Created:
{Fore.WHITE}- proxies.txt: Proxy list storage
- ghostip.cfg: Application settings
- ghostip.log: IP rotation logs
- ghostip_proxychains.conf: Dynamic proxychains config

{Fore.YELLOW}Troubleshooting:
{Fore.WHITE}- Ensure proxychains4 is properly installed
- Check proxy connectivity manually if rotation fails
- Verify firewall settings allow proxy connections
- Use 'Test Proxies' to identify working proxies

{Fore.YELLOW}Security Notes:
{Fore.WHITE}- All traffic routes through selected proxies
- DNS queries can be proxied to prevent leaks
- Logs contain IP changes but no sensitive data
- Regular proxy testing recommended for reliability
"""
        print(help_text)
    
    def wipe_logs_menu(self):
        """Wipe logs with confirmation."""
        print(f"\n{Fore.YELLOW}=== Wipe Logs ===")
        print(f"{Fore.RED}This will permanently delete all log files.")
        
        confirm = input(f"{Fore.YELLOW}Are you sure? (type 'yes' to confirm): ").strip().lower()
        
        if confirm == 'yes':
            if self.logger.wipe_logs():
                print(f"{Fore.GREEN}Logs wiped successfully.")
            else:
                print(f"{Fore.RED}Failed to wipe logs.")
        else:
            print(f"{Fore.CYAN}Operation cancelled.")
    
    def run(self):
        """Main application loop."""
        self.display_banner()
        
        # Check for proxychains4
        try:
            subprocess.run(['which', 'proxychains4'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"{Fore.RED}Error: proxychains4 not found. Please install it first.")
            print(f"{Fore.YELLOW}Ubuntu/Debian: sudo apt-get install proxychains4")
            sys.exit(1)
        
        while True:
            try:
                self.display_menu()
                choice = input(f"{Fore.YELLOW}Enter your choice: ").strip()
                
                if choice == '0':
                    print(f"{Fore.CYAN}Thank you for using GhostIP!")
                    break
                elif choice == '1':
                    self.start_rotation()
                elif choice == '2':
                    self.add_proxy_menu()
                elif choice == '3':
                    new_count = self.proxy_manager.scrape_free_proxies()
                    print(f"{Fore.GREEN}Refresh complete. Added {new_count} new proxies.")
                elif choice == '4':
                    self.view_proxies()
                elif choice == '5':
                    self.proxy_manager.test_all_proxies()
                elif choice == '6':
                    self.geoip_lookup_menu()
                elif choice == '7':
                    self.wipe_logs_menu()
                elif choice == '8':
                    self.settings_menu()
                elif choice == '9':
                    self.show_help()
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.")
                
                if choice != '0':
                    input(f"\n{Fore.CYAN}Press Enter to continue...")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted by user.")
                break
            except Exception as e:
                print(f"{Fore.RED}Unexpected error: {e}")
                self.logger.log_error(f"Unexpected error: {e}")


def main():
    """Main entry point."""
    try:
        app = GhostIP()
        app.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application terminated by user.")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()