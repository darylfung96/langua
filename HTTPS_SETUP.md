# HTTPS Configuration for Language Learner

This document explains how to run the application with HTTPS using self-signed certificates.

## Quick Start

1. **Generate SSL certificates** (already done in `backend/`):
   - `backend/cert.pem` - SSL certificate
   - `backend/key.pem` - SSL private key

2. **Configure the backend** (`backend/.env`):
   ```env
   SSL_CERT_FILE=./cert.pem
   SSL_KEY_FILE=./key.pem
   # Optional: change port if 8000 is in use
   API_PORT=8000
   ```

3. **Configure the frontend** (`frontend/.env`):
   ```env
   VITE_BACKEND_URL=https://localhost:8000
   ```

4. **Enable HTTPS in Vite dev server** (optional but recommended for full HTTPS experience):
   The Vite dev server by default runs on HTTP. To avoid mixed content warnings, either:
   - Keep frontend on HTTP (browser allows HTTPS backend from HTTP frontend, but shows "mixed content" warning for non-secure page)
   - Or configure Vite to use HTTPS (see below)

5. **Run the application**:
   ```bash
   # Terminal 1 - Start backend
   cd backend
   source .env  # or manually export the variables
   python main.py
   ```

   ```bash
   # Terminal 2 - Start frontend
   cd frontend
   source .env
   npm run dev
   ```

6. **Access the site**:
   - Frontend: https://localhost:5173 (if configured with HTTPS) or http://localhost:5173
   - Backend API: https://localhost:8000
   - API docs: https://localhost:8000/docs

## Browser Security Warnings

Since these are self-signed certificates, your browser will show a security warning. You'll need to:
1. Click "Advanced" → "Proceed to localhost (unsafe)" (Chrome) or similar
2. Or add the certificate to your system's trusted store to remove the warning

To trust the certificate:

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain backend/cert.pem
```

**Linux:**
```bash
sudo cp backend/cert.pem /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

**Windows:**
- Double-click the `.pem` file, click "Install Certificate", choose "Local Machine", place in "Trusted Root Certification Authorities"

## HTTPS Frontend with Vite (Optional)

To serve the frontend over HTTPS as well, modify `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: '../backend/key.pem',
      cert: '../backend/cert.pem'
    },
    port: 5173
  }
})
```

Then access: https://localhost:5173 (no browser warnings after trusting the cert).

## Production Deployment

For production, use a proper certificate from Let's Encrypt or a certificate authority. Recommended setup:

1. **Use nginx as a reverse proxy** with automatic Let's Encrypt certificates
2. **Configure environment variables**:
   ```env
   # Backend .env
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   FRONTEND_URL=https://yourdomain.com
   GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
   # No SSL_CERT_FILE/SSL_KEY_FILE needed - nginx handles HTTPS
   ```

3. **Example nginx configuration**:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name yourdomain.com;

       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## Troubleshooting

- **"Mixed Content" warnings**: Ensure both frontend and backend use HTTPS, or use relative URLs in the frontend.
- **Cookies not working**: In production, cookies are set with `Secure` and `SameSite=Lax`. Ensure you're accessing via HTTPS.
- **CORS errors**: Check that `CORS_ORIGINS` includes your frontend URL with the correct protocol (http vs https).
- **Certificate errors**: Self-signed certificates will show warnings. Trust the certificate or use a CA-signed cert in production.

## Files Modified

- `backend/config.py` - Added SSL_CERT_FILE and SSL_KEY_FILE config
- `backend/main.py` - Added HTTPS server startup with SSL
- `backend/.env.template` - Added SSL configuration documentation
- `frontend/.env.template` - Added VITE_BACKEND_URL guidance
- `frontend/vite.config.ts` - Ready for HTTPS configuration if needed
