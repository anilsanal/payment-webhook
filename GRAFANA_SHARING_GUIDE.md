# Grafana Dashboard Sharing & Publishing Guide

## 📊 Dashboard Information
- **Dashboard Name:** Payment Gateway Monitoring
- **URL:** http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring
- **Current Login:** admin / admin123

---

## 🎯 Publishing Options (Ranked by Ease)

### **Option 1: Direct Link Sharing** ⭐ Easiest
**Best for:** Small team with trusted members

**How to:**
1. Share this URL: `http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring`
2. Share login credentials: `admin` / `admin123`

**Pros:**
- ✅ No setup required
- ✅ Real-time data
- ✅ Full dashboard features

**Cons:**
- ❌ Everyone shares admin password
- ❌ No access control
- ❌ IP-based URL (not friendly)

---

### **Option 2: Create Viewer Accounts** ⭐ Recommended
**Best for:** Professional team environment

**How to create accounts:**

#### Via Web UI:
1. Login to Grafana as admin
2. Click gear icon (⚙️) → **Server Admin** → **Users**
3. Click **New user**
4. Fill in details:
   - Name: Team member name
   - Email: Their email
   - Username: Their login
   - Password: Secure password
   - **Role:** Viewer (read-only)
5. Click **Create user**
6. Share credentials with team member

#### Via Command Line:
```bash
curl -s -u admin:admin123 -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@company.com",
    "login": "john.doe",
    "password": "SecurePassword123",
    "role": "Viewer"
  }' \
  http://localhost:3001/api/admin/users
```

**Roles:**
- **Viewer:** Can view dashboards only (recommended)
- **Editor:** Can edit dashboards
- **Admin:** Full control

**Pros:**
- ✅ Individual accounts
- ✅ Access control
- ✅ Audit trail (who viewed what)
- ✅ Can revoke access

**Cons:**
- ❌ Requires user management
- ❌ Still requires login

---

### **Option 3: Enable Anonymous Access** ⭐ Public Dashboard
**Best for:** Internal company dashboard on private network

**How to enable:**
```bash
# Backup config
sudo cp /etc/grafana/grafana.ini /etc/grafana/grafana.ini.backup

# Edit Grafana config
sudo nano /etc/grafana/grafana.ini
```

Find `[auth.anonymous]` section and change:
```ini
[auth.anonymous]
enabled = true
org_name = Main Org.
org_role = Viewer
```

Restart Grafana:
```bash
sudo systemctl restart grafana-server
```

**Result:** Anyone with URL can view without login!

**Pros:**
- ✅ No login required
- ✅ Easy to share
- ✅ Real-time data

**Cons:**
- ❌ Anyone with URL can access
- ❌ No access control
- ⚠️ **Security risk** if exposed to internet

**Security Note:** Only use this on private networks or with firewall restrictions!

---

### **Option 4: Share as Snapshot** ⭐ External Sharing
**Best for:** Sharing with clients/partners outside your network

**How to:**
1. Open dashboard in Grafana
2. Click **Share** icon (top-right toolbar)
3. Select **Snapshot** tab
4. Choose settings:
   - **Snapshot name:** Give it a name
   - **Expire:** Set expiration (7 days, 30 days, never)
   - **Timeout:** Leave default
5. Click **Local Snapshot** or **Publish to snapshots.raintank.io**
6. Copy the generated URL
7. Share URL with anyone

**Example URL:** `http://23.88.104.43:3001/dashboard/snapshot/xxxxx`

**Pros:**
- ✅ No login required
- ✅ Works for external users
- ✅ Can set expiration
- ✅ Data is static (no live changes)

**Cons:**
- ❌ Not real-time (frozen snapshot)
- ❌ Must recreate for updates
- ❌ Uses snapshot storage

---

### **Option 5: Embed in Website/App** ⭐ Integration
**Best for:** Internal company portal or application

**HTML Code:**
```html
<!-- Basic Embed -->
<iframe
  src="http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring?orgId=1&kiosk=tv"
  width="100%"
  height="800"
  frameborder="0">
</iframe>

<!-- Full-screen Kiosk Mode -->
<iframe
  src="http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring?orgId=1&kiosk"
  width="100%"
  height="100vh"
  frameborder="0">
</iframe>
```

**URL Parameters:**
- `kiosk=tv` - Hide menu, show full dashboard
- `kiosk` - Complete kiosk mode (no UI at all)
- `from=now-6h&to=now` - Set time range
- `refresh=30s` - Auto-refresh
- `theme=dark` - Dark theme
- `theme=light` - Light theme

**Example with parameters:**
```
http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring?orgId=1&kiosk=tv&from=now-1h&to=now&refresh=30s&theme=dark
```

**Pros:**
- ✅ Seamless integration
- ✅ Real-time data
- ✅ Customizable appearance

**Cons:**
- ❌ Requires web development
- ❌ May need anonymous access enabled

---

### **Option 6: Setup Domain Name & SSL** ⭐⭐ Professional
**Best for:** Production environment, external clients

**Result:** `https://dashboard.yourcompany.com` instead of `http://23.88.104.43:3001`

**Prerequisites:**
- Domain name (e.g., dashboard.yourcompany.com)
- Domain DNS pointing to 23.88.104.43

**Setup Steps:**

#### 1. Install Nginx
```bash
sudo apt update
sudo apt install -y nginx
```

#### 2. Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/grafana
```

Add:
```nginx
server {
    listen 80;
    server_name dashboard.yourcompany.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/grafana /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'
```

#### 4. Add SSL Certificate (Free with Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.yourcompany.com
```

**Result:**
- HTTP: `http://dashboard.yourcompany.com`
- HTTPS: `https://dashboard.yourcompany.com` ✨

**Pros:**
- ✅ Professional URL
- ✅ SSL encryption (HTTPS)
- ✅ Better SEO/trust
- ✅ Hides port number

**Cons:**
- ❌ Requires domain ownership
- ❌ DNS configuration needed
- ❌ More complex setup

---

### **Option 7: Export Dashboard JSON** ⭐ Backup/Transfer
**Best for:** Sharing dashboard configuration (not data)

**How to:**
1. Open dashboard
2. Click settings (gear icon) in top-right
3. Select **JSON Model** from left menu
4. Click **Copy to Clipboard** or **Save to file**
5. Share JSON file

**Import on another Grafana:**
1. Go to Dashboards → Import
2. Paste JSON or upload file
3. Configure datasource
4. Click Import

**Pros:**
- ✅ Portable dashboard config
- ✅ Version control friendly
- ✅ Easy backup

**Cons:**
- ❌ No data included
- ❌ Requires Grafana instance
- ❌ Must configure datasources

---

## 🔒 Security Recommendations

### **Low Security (Internal Network Only):**
- Use anonymous access
- Direct IP sharing

### **Medium Security (Team Environment):**
- Create viewer accounts for each person
- Change admin password
- Use firewall rules

### **High Security (Production/External):**
- Use domain with SSL (HTTPS)
- Individual user accounts
- Enable two-factor authentication (Grafana Enterprise)
- Use VPN or IP whitelist
- Regular password rotation

---

## 📱 Mobile Access

All options work on mobile browsers! The dashboard is responsive.

**Best mobile experience:**
- Add `&kiosk=tv` to URL for cleaner view
- Use landscape orientation
- Enable auto-refresh

---

## 🎬 TV Display / Kiosk Mode

For displaying on office TV/monitor:

**Full-screen URL:**
```
http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring?orgId=1&kiosk&refresh=30s
```

**Setup:**
1. Open URL in browser on TV/monitor
2. Press F11 for full-screen
3. Dashboard will auto-refresh every 30 seconds

---

## 🔧 Troubleshooting

### "Cannot connect" error:
- Check firewall: `sudo ufw status`
- Verify Grafana is running: `sudo systemctl status grafana-server`
- Check if port 3001 is accessible from your network

### Slow loading:
- Reduce time range (use last 1h instead of 24h)
- Increase refresh interval
- Check database performance

### Permission denied:
- Verify user role (must be Viewer or higher)
- Check anonymous access is enabled if needed

---

## 📞 Quick Reference

**Dashboard URL:** http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring

**Login:** admin / admin123

**Create Viewer Account:**
```bash
curl -s -u admin:admin123 -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Name","email":"email@example.com","login":"username","password":"password","role":"Viewer"}' \
  http://localhost:3001/api/admin/users
```

**Enable Anonymous Access:**
Edit `/etc/grafana/grafana.ini` → Set `[auth.anonymous] enabled = true` → Restart

**Kiosk URL:**
```
http://23.88.104.43:3001/d/payment-monitoring/payment-gateway-monitoring?kiosk
```

---

**Last Updated:** 2025-10-28
