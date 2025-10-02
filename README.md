# Meal_planning-app
A recipe generator app based on available ingredients
![Meal Suggestion App Use case](https://github.com/user-attachments/assets/f1040b8c-0ed8-4b96-b367-87eec3cb3a00)

![meal app 2 1 drawio](https://github.com/user-attachments/assets/f7ec8bc0-8c90-4772-a02a-74dec6f60aca)

![meal app 3 1 drawio](https://github.com/user-attachments/assets/6030f561-66c8-4ee8-a13c-a2b1f06c29cb)

![meal app 1 1 drawio](https://github.com/user-attachments/assets/1805b460-806d-4581-a9b2-d11dccc1b1ad)

![SEquence Diagram ''  00](https://github.com/user-attachments/assets/09970a3f-dabc-4c41-901c-53fd556d4a76)
![meal planning app Er diagram](https://github.com/user-attachments/assets/fe72e74f-05c3-43f5-b363-f840a0b686ce)

![class diagram](https://github.com/user-attachments/assets/de6364cd-85ce-4b7a-ad7e-49296556eaae)

## Production HTTPS + Security Checklist

The backend is already running behind Daphne and Nginx. Follow the steps below to finish the hardening work and issue a TLS certificate.

1. **Install Certbot and request a certificate** (replace `<domain>` with your real domain name once DNS records point to the server):

	```bash
	sudo apt update
	sudo apt install -y certbot python3-certbot-nginx
	sudo certbot --nginx -d <domain> -d www.<domain>
	```

	Certbot will prompt you to redirect all HTTP traffic to HTTPS. Answer “Yes” so Nginx updates the server block automatically. Certificates renew automatically via the systemd timer installed by Certbot.

2. **Update your environment variables** (`/home/ubuntu/chopsmo/.env`) now that HTTPS is in place:

	```bash
	# Enforce secure cookies and HTTPS redirects
	DEBUG=False
	SECURE_SSL_REDIRECT=True
	SESSION_COOKIE_SECURE=True
	CSRF_COOKIE_SECURE=True
	CSRF_COOKIE_SAMESITE=Lax
	ALLOW_INSECURE_COOKIES=False
	DATABASE_SSL_REQUIRE=True
	CSRF_TRUSTED_ORIGINS=https://<domain>
	ALLOWED_HOSTS=<domain>,www.<domain>
	```

	Remove any temporary overrides that set `SESSION_COOKIE_SECURE` or `CSRF_COOKIE_SECURE` to `False`. The new `ALLOW_INSECURE_COOKIES` flag in `meal_project/settings.py` exists only for emergency troubleshooting—leave it `False` for production.

3. **Reload services so the new settings take effect**:

	```bash
	sudo systemctl restart chopsmo
	sudo systemctl reload nginx
	```

4. **Smoke test the deployment**:

	```bash
	curl -I https://<domain>/
	curl -I https://<domain>/admin/
	sudo systemctl status chopsmo
	sudo tail -n 50 /var/log/nginx/access.log
	```

5. **Set up monitoring** (optional but recommended):

	- Add a UptimeRobot check on `https://<domain>/admin/login/`.
	- Subscribe to Certbot renewal emails (sent to the address you supplied in step 1).

With HTTPS enabled, you can safely remove port 8001 from any public-facing security groups and rely solely on port 80/443 through Nginx.

