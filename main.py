# main.py
from fastapi import FastAPI
from app.modules.botConfig.bot_routes import router as bot_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="WhatsApp Shopify Bot",
    description="A WhatsApp bot for Shopify stores",
    version="1.0.0"
)

# Serve static HTML files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(bot_router)

# WhatsApp and Shopify routes
from app.modules.whatsapp.shopify_auth import router as shopify_router
from app.modules.whatsapp.webhook_handler import router as whatsapp_router

app.include_router(shopify_router)
app.include_router(whatsapp_router)

@app.get("/")
async def root():
    from fastapi.responses import HTMLResponse
    
    landing_page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WhatsApp Shopping Bot - Transform Your Shopify Store</title>
        <meta name="description" content="Enable WhatsApp shopping for your Shopify store. Let customers browse, cart, and checkout directly through WhatsApp conversations.">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                overflow-x: hidden;
            }
            
            .hero {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #25D366 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                align-items: center;
                position: relative;
                overflow: hidden;
            }
            
            .hero::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="%23ffffff" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
                opacity: 0.1;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                position: relative;
                z-index: 1;
            }
            
            .hero-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 60px;
                align-items: center;
                min-height: 80vh;
            }
            
            .hero-text h1 {
                font-size: 3.5rem;
                font-weight: 700;
                margin-bottom: 1.5rem;
                line-height: 1.1;
                background: linear-gradient(45deg, #ffffff, #f0f0f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .hero-text p {
                font-size: 1.25rem;
                margin-bottom: 2rem;
                opacity: 0.9;
                font-weight: 300;
            }
            
            .hero-stats {
                display: flex;
                gap: 30px;
                margin-bottom: 2.5rem;
            }
            
            .stat {
                text-align: center;
            }
            
            .stat-number {
                font-size: 2.5rem;
                font-weight: 700;
                color: #25D366;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .cta-buttons {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .btn {
                padding: 15px 30px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .btn-primary {
                background: #25D366;
                color: white;
                box-shadow: 0 8px 25px rgba(37, 211, 102, 0.4);
            }
            
            .btn-primary:hover {
                background: #128C7E;
                transform: translateY(-2px);
                box-shadow: 0 12px 35px rgba(37, 211, 102, 0.6);
            }
            
            .btn-secondary {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
            }
            
            .btn-secondary:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-2px);
            }
            
            .hero-visual {
                position: relative;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .phone-mockup {
                width: 280px;
                height: 560px;
                background: #1f1f1f;
                border-radius: 30px;
                padding: 20px;
                box-shadow: 0 25px 50px rgba(0,0,0,0.3);
                position: relative;
                overflow: hidden;
            }
            
            .phone-screen {
                width: 100%;
                height: 100%;
                background: #e5ddd5;
                border-radius: 20px;
                position: relative;
                overflow: hidden;
            }
            
            .whatsapp-header {
                background: #075e54;
                color: white;
                padding: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .store-avatar {
                width: 35px;
                height: 35px;
                background: #25D366;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
            }
            
            .chat-messages {
                padding: 15px;
                height: calc(100% - 140px);
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .message {
                max-width: 80%;
                padding: 10px 12px;
                border-radius: 8px;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .message-bot {
                background: #dcf8c6;
                align-self: flex-end;
                border-bottom-right-radius: 3px;
            }
            
            .message-user {
                background: white;
                align-self: flex-start;
                border-bottom-left-radius: 3px;
            }
            
            .features {
                background: white;
                padding: 100px 0;
            }
            
            .section-header {
                text-align: center;
                margin-bottom: 80px;
            }
            
            .section-header h2 {
                font-size: 3rem;
                color: #2c3e50;
                margin-bottom: 20px;
                font-weight: 700;
            }
            
            .section-header p {
                font-size: 1.25rem;
                color: #666;
                max-width: 600px;
                margin: 0 auto;
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 40px;
                margin-top: 60px;
            }
            
            .feature-card {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border: 1px solid #f0f0f0;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .feature-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #25D366, #128C7E);
            }
            
            .feature-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 50px rgba(0,0,0,0.15);
            }
            
            .feature-icon {
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #25D366, #128C7E);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                margin-bottom: 25px;
                box-shadow: 0 8px 25px rgba(37, 211, 102, 0.3);
            }
            
            .feature-card h3 {
                font-size: 1.5rem;
                color: #2c3e50;
                margin-bottom: 15px;
                font-weight: 600;
            }
            
            .feature-card p {
                color: #666;
                font-size: 1rem;
                line-height: 1.6;
            }
            
            .how-it-works {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 100px 0;
            }
            
            .steps {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 40px;
                margin-top: 60px;
            }
            
            .step {
                text-align: center;
                position: relative;
            }
            
            .step-number {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #25D366, #128C7E);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                font-weight: 700;
                color: white;
                margin: 0 auto 25px auto;
                box-shadow: 0 10px 30px rgba(37, 211, 102, 0.3);
            }
            
            .step h3 {
                font-size: 1.25rem;
                color: #2c3e50;
                margin-bottom: 15px;
                font-weight: 600;
            }
            
            .step p {
                color: #666;
            }
            
            .footer {
                background: #2c3e50;
                color: white;
                padding: 60px 0 30px 0;
            }
            
            .footer-content {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 40px;
                margin-bottom: 40px;
            }
            
            .footer-section h4 {
                font-size: 1.25rem;
                margin-bottom: 20px;
                color: #25D366;
            }
            
            .footer-section a {
                color: #ecf0f1;
                text-decoration: none;
                display: block;
                margin-bottom: 10px;
                transition: color 0.3s ease;
            }
            
            .footer-section a:hover {
                color: #25D366;
            }
            
            .footer-bottom {
                border-top: 1px solid #34495e;
                padding-top: 30px;
                text-align: center;
                color: #bdc3c7;
            }
            
            @media (max-width: 768px) {
                .hero-content {
                    grid-template-columns: 1fr;
                    gap: 40px;
                    text-align: center;
                }
                
                .hero-text h1 {
                    font-size: 2.5rem;
                }
                
                .phone-mockup {
                    width: 240px;
                    height: 480px;
                }
                
                .cta-buttons {
                    flex-direction: column;
                    width: 100%;
                }
                
                .btn {
                    width: 100%;
                    justify-content: center;
                }
                
                .features-grid {
                    grid-template-columns: 1fr;
                }
                
                .steps {
                    grid-template-columns: 1fr;
                }
            }
            
            .floating-elements {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                overflow: hidden;
            }
            
            .floating-element {
                position: absolute;
                opacity: 0.1;
                animation: float 6s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px) rotate(0deg); }
                50% { transform: translateY(-20px) rotate(10deg); }
            }
        </style>
    </head>
    <body>
        <!-- Hero Section -->
        <section class="hero">
            <div class="floating-elements">
                <div class="floating-element" style="top: 10%; left: 10%; font-size: 3rem;">💬</div>
                <div class="floating-element" style="top: 20%; right: 15%; font-size: 2.5rem;">🛍️</div>
                <div class="floating-element" style="bottom: 30%; left: 5%; font-size: 2rem;">📱</div>
                <div class="floating-element" style="bottom: 10%; right: 10%; font-size: 2.5rem;">🚀</div>
            </div>
            
            <div class="container">
                <div class="hero-content">
                    <div class="hero-text">
                        <h1>Transform Your Shopify Store with WhatsApp</h1>
                        <p>Enable customers to browse products, manage their cart, and complete purchases directly through WhatsApp conversations. Increase sales with the world's most popular messaging platform.</p>
                        
                        <div class="hero-stats">
                            <div class="stat">
                                <div class="stat-number">2B+</div>
                                <div class="stat-label">WhatsApp Users</div>
                            </div>
                            <div class="stat">
                                <div class="stat-number">85%</div>
                                <div class="stat-label">Higher Engagement</div>
                            </div>
                            <div class="stat">
                                <div class="stat-number">3x</div>
                                <div class="stat-label">Conversion Rate</div>
                            </div>
                        </div>
                        
                        <div class="cta-buttons">
                            <a href="https://apps.shopify.com/whatsapp-shopping-bot" class="btn btn-primary">
                                🚀 Install App
                            </a>
                            <a href="/shopify/privacy" class="btn btn-secondary">
                                📋 View Documentation
                            </a>
                        </div>
                    </div>
                    
                    <div class="hero-visual">
                        <div class="phone-mockup">
                            <div class="phone-screen">
                                <div class="whatsapp-header">
                                    <div class="store-avatar">S</div>
                                    <div>
                                        <div style="font-weight: 600;">Your Store</div>
                                        <div style="font-size: 12px; opacity: 0.8;">Online</div>
                                    </div>
                                </div>
                                <div class="chat-messages">
                                    <div class="message message-bot">👋 Welcome! Browse our products:</div>
                                    <div class="message message-user">Show me sneakers</div>
                                    <div class="message message-bot">🏃‍♂️ Nike Air Max - $129.99<br>📦 Qty: 1 | 💵 Total: $129.99<br><br>➖ Less | ➕ More | 🛒 Add to Cart</div>
                                    <div class="message message-user">Add to cart</div>
                                    <div class="message message-bot">✅ Added to cart!<br>🛒 Cart: 1 item ($129.99)<br><br>🛍️ Checkout | 📦 View Cart</div>
                                    <div class="message message-user">Checkout</div>
                                    <div class="message message-bot">🛒 Complete your order:<br><a href="#" style="color: #25D366;">👉 Secure Checkout Link</a></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Features Section -->
        <section class="features">
            <div class="container">
                <div class="section-header">
                    <h2>Powerful Features for Modern Commerce</h2>
                    <p>Everything you need to turn WhatsApp into your ultimate sales channel</p>
                </div>
                
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">💬</div>
                        <h3>Interactive Product Catalog</h3>
                        <p>Customers can browse your entire Shopify inventory directly through WhatsApp. Rich product cards with images, descriptions, and real-time pricing.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">🛒</div>
                        <h3>Smart Cart Management</h3>
                        <p>Built-in shopping cart with quantity controls, item management, and persistent sessions. Customers can easily modify quantities and view totals.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">🔒</div>
                        <h3>Secure Checkout</h3>
                        <p>Seamless integration with Shopify's checkout system. Generate secure checkout links that maintain cart state and customer data.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">⚡</div>
                        <h3>Real-time Sync</h3>
                        <p>Automatic synchronization with your Shopify store. Inventory updates, price changes, and new products are reflected instantly.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <h3>Analytics & Insights</h3>
                        <p>Track conversation metrics, conversion rates, and customer engagement. Understand how WhatsApp drives your sales.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">🎯</div>
                        <h3>Custom Messages</h3>
                        <p>Personalize welcome messages, automated responses, and product descriptions to match your brand voice and customer needs.</p>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- How It Works -->
        <section class="how-it-works">
            <div class="container">
                <div class="section-header">
                    <h2>Get Started in Minutes</h2>
                    <p>Simple setup process to connect your Shopify store with WhatsApp</p>
                </div>
                
                <div class="steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <h3>Install the App</h3>
                        <p>Add WhatsApp Shopping Bot to your Shopify store with one click. No technical knowledge required.</p>
                    </div>
                    
                    <div class="step">
                        <div class="step-number">2</div>
                        <h3>Connect WhatsApp</h3>
                        <p>Link your WhatsApp Business account using the simple configuration wizard. We'll guide you through each step.</p>
                    </div>
                    
                    <div class="step">
                        <div class="step-number">3</div>
                        <h3>Configure Settings</h3>
                        <p>Customize welcome messages, enable product categories, and set up your brand preferences.</p>
                    </div>
                    
                    <div class="step">
                        <div class="step-number">4</div>
                        <h3>Go Live!</h3>
                        <p>Share your WhatsApp number with customers and start selling through conversations. It's that simple!</p>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Footer -->
        <footer class="footer">
            <div class="container">
                <div class="footer-content">
                    <div class="footer-section">
                        <h4>Product</h4>
                        <a href="/features">Features</a>
                        <a href="/pricing">Pricing</a>
                        <a href="/integrations">Integrations</a>
                        <a href="/api-docs">API Documentation</a>
                    </div>
                    
                    <div class="footer-section">
                        <h4>Support</h4>
                        <a href="/shopify/support">Help Center</a>
                        <a href="/tutorials">Tutorials</a>
                        <a href="/troubleshooting">Troubleshooting</a>
                        <a href="mailto:support@ecommercexpart.com">Contact Support</a>
                    </div>
                    
                    <div class="footer-section">
                        <h4>Legal</h4>
                        <a href="/shopify/privacy">Privacy Policy</a>
                        <a href="/shopify/terms">Terms of Service</a>
                        <a href="/gdpr">GDPR Compliance</a>
                        <a href="/security">Security</a>
                    </div>
                    
                    <div class="footer-section">
                        <h4>Company</h4>
                        <a href="/about">About Us</a>
                        <a href="/blog">Blog</a>
                        <a href="/careers">Careers</a>
                        <a href="/press">Press Kit</a>
                    </div>
                </div>
                
                <div class="footer-bottom">
                    <p>&copy; 2025 WhatsApp Shopping Bot. All rights reserved. | Built for Shopify merchants worldwide.</p>
                </div>
            </div>
        </footer>
    </body>
    </html>
    """
    
    return HTMLResponse(content=landing_page)
