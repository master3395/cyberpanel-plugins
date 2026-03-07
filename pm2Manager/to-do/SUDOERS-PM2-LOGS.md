# Sudoers for PM2 logs fallback

If `pm2 logs` fails (e.g. permission issues), the plugin can read log files via `sudo tail`.
Add this so the panel user can run the fallback (optional):

```bash
# Create /etc/sudoers.d/pm2-logs (mode 0440)
echo 'lscpd ALL=(root) NOPASSWD: /usr/bin/tail * /root/.pm2/logs/*
cyberpanel ALL=(root) NOPASSWD: /usr/bin/tail * /root/.pm2/logs/*
nobody ALL=(root) NOPASSWD: /usr/bin/tail * /root/.pm2/logs/*' | sudo tee /etc/sudoers.d/pm2-logs
sudo chmod 440 /etc/sudoers.d/pm2-logs
```

Then the logs API will use `tail` on `/root/.pm2/logs/<app>-out.log` and `-error.log` when `pm2 logs` fails.
