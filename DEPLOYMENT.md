# Production Deployment Guide - WhatsApp Shopping Bot

## Prerequisites

- Ubuntu 20.04+ or similar Linux server
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Domain with SSL certificate
- Shopify Partner account
- WhatsApp Business API access

## 1. Server Setup

### 1.1 System Updates
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx postgresql redis-server supervisor -y
```

### 1.2 Create Application User
```bash
sudo adduser whatsappbot --disabled-password
sudo usermod -aG sudo whatsappbot
```

## 2. Database Setup

### 2.1 PostgreSQL Configuration
```bash
sudo -u postgres psql

CREATE DATABASE whatsapp_shopify_bot;
CREATE USER whatsappbot WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE whatsapp_shopify_bot TO whatsappbot;
\q
```

### 2.2 Redis Configuration
```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## 3. Application Deployment

### 3.1 Clone Repository
```bash
cd /opt
sudo git clone https://github.com/your-repo/ShopifyWhatsappBotApp.git
sudo chown -R whatsappbot:whatsappbot ShopifyWhatsappBotApp
cd ShopifyWhatsappBotApp
```

### 3.2 Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Environment Configuration
```bash
cp .env.example .env
nano .env
```

Update the following in `.env`:
```
DATABASE_URL=postgresql://whatsappbot:your_secure_password@localhost/whatsapp_shopify_bot
REDIS_HOST=localhost
REDIS_PORT=6379
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
REDIRECT_URI=https://yourdomain.com/shopify/callback
SECRET_KEY=generate_strong_secret_key_here
ENVIRONMENT=production
DEBUG=false
```

### 3.4 Database Migrations
```bash
alembic upgrade head
```

## 4. Nginx Configuration

### 4.1 Create Nginx Config
```bash
sudo nano /etc/nginx/sites-available/whatsappbot
```

Add the following configuration:
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

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        proxy_connect_timeout 90;
        proxy_redirect off;
    }

    location /static {
        alias /opt/ShopifyWhatsappBotApp/static;
        expires 30d;
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### 4.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/whatsappbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.3 SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```

## 5. Supervisor Configuration

### 5.1 Create Supervisor Config
```bash
sudo nano /etc/supervisor/conf.d/whatsappbot.conf
```

Add the following:
```ini
[program:whatsappbot]
command=/opt/ShopifyWhatsappBotApp/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8080 --workers 4
directory=/opt/ShopifyWhatsappBotApp
user=whatsappbot
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/whatsappbot/app.log
environment=PATH="/opt/ShopifyWhatsappBotApp/venv/bin",HOME="/home/whatsappbot",USER="whatsappbot"
```

### 5.2 Create Log Directory
```bash
sudo mkdir -p /var/log/whatsappbot
sudo chown whatsappbot:whatsappbot /var/log/whatsappbot
```

### 5.3 Start Application
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start whatsappbot
```

## 6. Monitoring Setup

### 6.1 Application Logs
```bash
# View application logs
sudo tail -f /var/log/whatsappbot/app.log

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 6.2 Health Check Endpoint
Create a health check endpoint:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

### 6.3 Monitoring Script
```bash
#!/bin/bash
# /opt/ShopifyWhatsappBotApp/scripts/health_check.sh

response=$(curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com/health)
if [ $response != "200" ]; then
    echo "Health check failed with status $response"
    # Send alert (email, Slack, etc.)
fi
```

Add to crontab:
```bash
*/5 * * * * /opt/ShopifyWhatsappBotApp/scripts/health_check.sh
```

## 7. Backup Strategy

### 7.1 Database Backup
```bash
#!/bin/bash
# /opt/ShopifyWhatsappBotApp/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/whatsappbot"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump whatsapp_shopify_bot > $BACKUP_DIR/db_$DATE.sql

# Compress and encrypt
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/db_$DATE.sql
rm $BACKUP_DIR/db_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/ShopifyWhatsappBotApp/scripts/backup.sh
```

## 8. Security Hardening

### 8.1 Firewall Configuration
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 8.2 Fail2ban Setup
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 8.3 Environment Variables Security
```bash
# Restrict .env file permissions
chmod 600 /opt/ShopifyWhatsappBotApp/.env
chown whatsappbot:whatsappbot /opt/ShopifyWhatsappBotApp/.env
```

## 9. Performance Optimization

### 9.1 Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_stores_url ON shopify_stores(store_url);
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_subscriptions_store ON store_subscriptions(store_id);
```

### 9.2 Redis Configuration
```bash
sudo nano /etc/redis/redis.conf

# Add/modify:
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 9.3 Application Optimization
- Enable response caching for product listings
- Implement connection pooling for database
- Use async/await properly throughout

## 10. Deployment Checklist

### Pre-Deployment
- [ ] Update all dependencies to latest stable versions
- [ ] Run security audit: `pip audit`
- [ ] Test all critical paths
- [ ] Update documentation
- [ ] Create database backup

### Deployment
- [ ] Deploy code to production
- [ ] Run database migrations
- [ ] Update environment variables
- [ ] Restart application services
- [ ] Clear caches

### Post-Deployment
- [ ] Verify application is running
- [ ] Test critical functionality
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Notify team of deployment

## 11. Rollback Procedure

If issues occur:
```bash
# Stop application
sudo supervisorctl stop whatsappbot

# Restore previous version
cd /opt/ShopifyWhatsappBotApp
git checkout previous_version_tag

# Restore database if needed
psql whatsapp_shopify_bot < /backups/whatsappbot/last_known_good.sql

# Restart application
sudo supervisorctl start whatsappbot
```

## 12. Scaling Considerations

### Horizontal Scaling
- Use load balancer (HAProxy/Nginx)
- Deploy multiple application instances
- Use Redis for session management
- Implement database read replicas

### Vertical Scaling
- Increase server resources as needed
- Monitor CPU and memory usage
- Optimize database queries
- Implement caching strategies

## 13. Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check logs
sudo tail -f /var/log/whatsappbot/app.log
# Check supervisor status
sudo supervisorctl status whatsappbot
```

**Database connection errors:**
```bash
# Test connection
psql -U whatsappbot -h localhost whatsapp_shopify_bot
# Check PostgreSQL status
sudo systemctl status postgresql
```

**High memory usage:**
```bash
# Check memory usage
free -h
# Restart application
sudo supervisorctl restart whatsappbot
```

## 14. Support

For deployment support:
- Email: support@ecommercexpart.com
- Documentation: https://yourdomain.com/docs
- Emergency: [Your emergency contact]

---

**Version**: 1.0  
**Last Updated**: January 2025