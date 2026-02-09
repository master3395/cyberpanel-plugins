# Deploy Fail2ban simple settings page (dashboard button)

If **https://your-server:2087/plugins/fail2ban/settings/** still shows the full tabbed UI instead of the PM2-style simple page with **"Go to Fail2ban Security Manager Dashboard"**, the server is running the old plugin. Deploy the updated plugin **on the server** (e.g. 207.180.193.210).

## On the server (SSH into 207.180.193.210)

If the plugin source is at `/home/cyberpanel-plugins/fail2ban/` on the same server:

```bash
sudo cp -r /home/cyberpanel-plugins/fail2ban/* /usr/local/CyberCP/fail2ban/
```

Then restart the panel so Django reloads the app (if needed):

```bash
sudo systemctl restart lscpd
```

## From your dev machine (this workspace) to the server

If the updated plugin is only on your dev machine, copy it to the server first, then on the server copy into CyberCP:

```bash
# From your dev machine (adjust user@207.180.193.210)
rsync -avz --delete /home/cyberpanel-plugins/fail2ban/ root@207.180.193.210:/usr/local/CyberCP/fail2ban/
# Then on the server:
# sudo systemctl restart lscpd
```

Or SCP:

```bash
scp -r /home/cyberpanel-plugins/fail2ban/* root@207.180.193.210:/usr/local/CyberCP/fail2ban/
```

Then SSH to the server and restart:

```bash
ssh root@207.180.193.210 "sudo systemctl restart lscpd"
```

## Verify on the server

After deploy, on the server check:

1. **URLs** – settings route points to simple view:
   ```bash
   grep "settings_simple" /usr/local/CyberCP/fail2ban/urls.py
   ```
   Should show: `re_path(r'^settings/$', views.settings_simple, ...)`

2. **Template exists**:
   ```bash
   ls -la /usr/local/CyberCP/fail2ban/templates/fail2ban/settings_simple.html
   ```

3. **View exists**:
   ```bash
   grep "def settings_simple" /usr/local/CyberCP/fail2ban/views.py
   ```

Then open **https://207.180.193.210:2087/plugins/fail2ban/settings/** — you should see the simple page with plugin info and **"Go to Fail2ban Security Manager Dashboard"** (like PM2 Manager).
