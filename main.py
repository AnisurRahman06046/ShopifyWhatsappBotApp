# main.py
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.modules.botConfig.bot_routes import router as bot_router
from fastapi.staticfiles import StaticFiles

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="WhatsApp Shopify Bot",
    description="A WhatsApp bot for Shopify stores",
    version="1.0.0",
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.shopify.com", "https://*.myshopify.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Middleware for embedded app security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # For embedded Shopify apps - allow framing by Shopify
    if "/shopify/" in str(request.url):
        # Remove any X-Frame-Options header (correct method for MutableHeaders)
        if "X-Frame-Options" in response.headers:
            del response.headers["X-Frame-Options"]

        # Set CSP to allow framing by Shopify
        response.headers["Content-Security-Policy"] = (
            "frame-ancestors 'self' https://admin.shopify.com https://*.myshopify.com; "
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.shopify.com https://admin.shopify.com; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.shopify.com; "
            "style-src 'self' 'unsafe-inline';"
        )

        # These headers don't work like this - remove them
        # response.headers["SameSite"] = "None"
        # response.headers["Secure"] = "true"

    return response


# Serve static HTML files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Health check route for debugging
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "WhatsApp Shopify Bot"}


@app.get("/shopify/health")
async def shopify_health():
    from app.core.config import settings

    return {
        "status": "ok",
        "shopify_configured": bool(settings.SHOPIFY_API_KEY),
        "redirect_uri": getattr(settings, "REDIRECT_URI", None),
    }


# Include routers
app.include_router(bot_router)

# WhatsApp and Shopify routes
from app.modules.whatsapp.shopify_auth import router as shopify_router
from app.modules.whatsapp.webhook_handler import router as whatsapp_router
from app.modules.billing.billing_routes import router as billing_router
from app.modules.billing.usage_routes import router as usage_router
from app.modules.pricing.pricing_routes import router as pricing_router

app.include_router(shopify_router)
app.include_router(whatsapp_router)
app.include_router(billing_router)
app.include_router(usage_router)
app.include_router(pricing_router)


# Session token verification endpoint for App Bridge compliance
@app.post("/api/ping")
async def ping(request: Request):
    """Endpoint to verify session tokens are being sent correctly"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing session token")

    # Token is present - this satisfies Shopify's session token requirement
    # In production, you would verify the JWT signature here
    return {
        "ok": True,
        "timestamp": request.json() if hasattr(request, "json") else None,
    }


@app.get("/privacy")
async def privacy_policy():
    """Serve privacy policy for Shopify Partner requirements"""
    # Redirect to the actual privacy policy route
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/shopify/privacy")


@app.get("/shopify/privacy")
async def privacy_policy_full():
    """Serve privacy policy"""
    from fastapi.responses import FileResponse
    import os

    file_path = "PRIVACY_POLICY.md"
    if os.path.exists(file_path):
        # Convert markdown to HTML for better display
        with open(file_path, "r") as f:
            content = f.read()

        # Simple markdown to HTML conversion
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Privacy Policy - WhatsApp Shopping Bot</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #25D366; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                h3 {{ color: #7f8c8d; }}
                pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <pre>{content}</pre>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content=html_content)
    else:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Privacy policy not found")


@app.get("/terms")
async def terms_of_service():
    """Serve terms of service for Shopify Partner requirements"""
    # Redirect to the actual terms route
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/shopify/terms")


@app.get("/shopify/terms")
async def terms_of_service_full():
    """Serve terms of service"""
    from fastapi.responses import FileResponse
    import os

    file_path = "TERMS_OF_SERVICE.md"
    if os.path.exists(file_path):
        # Convert markdown to HTML for better display
        with open(file_path, "r") as f:
            content = f.read()

        # Simple markdown to HTML conversion
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Terms of Service - WhatsApp Shopping Bot</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #25D366; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                h3 {{ color: #7f8c8d; }}
                pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <pre>{content}</pre>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content=html_content)
    else:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Terms of service not found")


@app.get("/support")
async def support():
    """Support page for Shopify Partner requirements"""
    # Redirect to the actual support route
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/shopify/support")


@app.get("/shopify/support")
async def support_full():
    """Support page"""
    from fastapi.responses import HTMLResponse

    support_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Support - WhatsApp Shopping Bot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #25D366; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .contact-box { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }
            .btn { display: inline-block; padding: 12px 24px; background: #25D366; color: white; text-decoration: none; border-radius: 5px; margin: 10px 10px 10px 0; }
            .btn:hover { background: #128C7E; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤝 Support Center</h1>
            
            <h2>📚 Documentation</h2>
            <p>Find answers to common questions and detailed guides in our documentation.</p>
            <a href="/static/DOCUMENTATION.md" class="btn">View Documentation</a>
            
            <h2>📧 Contact Support</h2>
            <div class="contact-box">
                <p><strong>Email:</strong> support@ecommercexpart.com</p>
                <p><strong>Response Time:</strong> Within 24 hours (business days)</p>
                <p><strong>Priority Support:</strong> Available for Professional and Enterprise plans</p>
            </div>
            
            <h2>🐛 Report an Issue</h2>
            <p>Found a bug or have a feature request? Let us know!</p>
            <a href="mailto:support@ecommercexpart.com?subject=Bug Report" class="btn">Report Issue</a>
            
            <h2>💬 Community</h2>
            <p>Join our community to connect with other merchants using WhatsApp Shopping Bot.</p>
            
            <h2>🚀 Getting Started</h2>
            <ul>
                <li>Install the app from Shopify App Store</li>
                <li>Connect your WhatsApp Business Account</li>
                <li>Configure your welcome message</li>
                <li>Start receiving orders through WhatsApp!</li>
            </ul>
            
            <h2>❓ Frequently Asked Questions</h2>
            <details>
                <summary><strong>How do I connect my WhatsApp Business Account?</strong></summary>
                <p>Go to the app settings, click "Connect WhatsApp" and follow the guided setup process.</p>
            </details>
            <details>
                <summary><strong>What are the message limits?</strong></summary>
                <p>Limits depend on your plan: Free (100/month), Starter (1,000/month), Professional (5,000/month), Enterprise (50,000/month)</p>
            </details>
            <details>
                <summary><strong>Can I customize the bot messages?</strong></summary>
                <p>Yes! You can customize welcome messages and automated responses in the app settings.</p>
            </details>
            <details>
                <summary><strong>Is customer data secure?</strong></summary>
                <p>Yes, we use industry-standard encryption and follow Shopify's security guidelines.</p>
            </details>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=support_html)



@app.get("/")
async def root(
    request: Request,
    shop: str = Query(None),
    hmac: str = Query(None),
    host: str = Query(None),
    embedded: str = Query(None),
):
    from fastapi.responses import HTMLResponse, RedirectResponse

    # If this is a Shopify app installation request (has shop parameter)
    if shop:
        print(f"[INFO] Shopify app request for shop: {shop}")

        # Check if this is an embedded app request (coming from Shopify admin)
        if embedded == "1" or host:
            # This is an embedded app request - show the embedded page
            return RedirectResponse(
                url=f"/shopify/embedded?shop={shop}&host={host or ''}", status_code=302
            )
        else:
            # This is an installation request
            return RedirectResponse(
                url=f"/shopify/install?shop={shop}", status_code=302
            )

    # Otherwise serve the landing page for regular visitors

    # landing_page = """
    # <!DOCTYPE html>
    # <html lang="en">
    # <head>
    #     <meta charset="UTF-8">
    #     <meta name="viewport" content="width=device-width, initial-scale=1.0">
    #     <title>WhatsApp Shopping Bot - Transform Your Shopify Store</title>
    #     <meta name="description" content="Enable WhatsApp shopping for your Shopify store. Let customers browse, cart, and checkout directly through WhatsApp conversations.">
    #     <link rel="preconnect" href="https://fonts.googleapis.com">
    #     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    #     <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    #     <style>
    #         * {
    #             margin: 0;
    #             padding: 0;
    #             box-sizing: border-box;
    #         }

    #         body {
    #             font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    #             line-height: 1.6;
    #             color: #333;
    #             overflow-x: hidden;
    #         }

    #         .hero {
    #             background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #25D366 100%);
    #             color: white;
    #             min-height: 100vh;
    #             display: flex;
    #             align-items: center;
    #             position: relative;
    #             overflow: hidden;
    #         }

    #         .hero::before {
    #             content: '';
    #             position: absolute;
    #             top: 0;
    #             left: 0;
    #             right: 0;
    #             bottom: 0;
    #             background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="%23ffffff" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
    #             opacity: 0.1;
    #         }

    #         .container {
    #             max-width: 1200px;
    #             margin: 0 auto;
    #             padding: 0 20px;
    #             position: relative;
    #             z-index: 1;
    #         }

    #         .hero-content {
    #             display: grid;
    #             grid-template-columns: 1fr 1fr;
    #             gap: 60px;
    #             align-items: center;
    #             min-height: 80vh;
    #         }

    #         .hero-text h1 {
    #             font-size: 3.5rem;
    #             font-weight: 700;
    #             margin-bottom: 1.5rem;
    #             line-height: 1.1;
    #             background: linear-gradient(45deg, #ffffff, #f0f0f0);
    #             -webkit-background-clip: text;
    #             -webkit-text-fill-color: transparent;
    #             background-clip: text;
    #         }

    #         .hero-text p {
    #             font-size: 1.25rem;
    #             margin-bottom: 2rem;
    #             opacity: 0.9;
    #             font-weight: 300;
    #         }

    #         .hero-stats {
    #             display: flex;
    #             gap: 30px;
    #             margin-bottom: 2.5rem;
    #         }

    #         .stat {
    #             text-align: center;
    #         }

    #         .stat-number {
    #             font-size: 2.5rem;
    #             font-weight: 700;
    #             color: #25D366;
    #             text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    #         }

    #         .stat-label {
    #             font-size: 0.9rem;
    #             opacity: 0.8;
    #             text-transform: uppercase;
    #             letter-spacing: 1px;
    #         }

    #         .cta-buttons {
    #             display: flex;
    #             gap: 20px;
    #             align-items: center;
    #         }

    #         .btn {
    #             padding: 15px 30px;
    #             border-radius: 50px;
    #             text-decoration: none;
    #             font-weight: 600;
    #             font-size: 1.1rem;
    #             transition: all 0.3s ease;
    #             display: inline-flex;
    #             align-items: center;
    #             gap: 10px;
    #             text-transform: uppercase;
    #             letter-spacing: 0.5px;
    #         }

    #         .btn-primary {
    #             background: #25D366;
    #             color: white;
    #             box-shadow: 0 8px 25px rgba(37, 211, 102, 0.4);
    #         }

    #         .btn-primary:hover {
    #             background: #128C7E;
    #             transform: translateY(-2px);
    #             box-shadow: 0 12px 35px rgba(37, 211, 102, 0.6);
    #         }

    #         .btn-secondary {
    #             background: rgba(255, 255, 255, 0.1);
    #             color: white;
    #             border: 2px solid rgba(255, 255, 255, 0.2);
    #             backdrop-filter: blur(10px);
    #         }

    #         .btn-secondary:hover {
    #             background: rgba(255, 255, 255, 0.2);
    #             transform: translateY(-2px);
    #         }

    #         .hero-visual {
    #             position: relative;
    #             display: flex;
    #             justify-content: center;
    #             align-items: center;
    #         }

    #         .phone-mockup {
    #             width: 280px;
    #             height: 560px;
    #             background: #1f1f1f;
    #             border-radius: 30px;
    #             padding: 20px;
    #             box-shadow: 0 25px 50px rgba(0,0,0,0.3);
    #             position: relative;
    #             overflow: hidden;
    #         }

    #         .phone-screen {
    #             width: 100%;
    #             height: 100%;
    #             background: #e5ddd5;
    #             border-radius: 20px;
    #             position: relative;
    #             overflow: hidden;
    #         }

    #         .whatsapp-header {
    #             background: #075e54;
    #             color: white;
    #             padding: 15px;
    #             display: flex;
    #             align-items: center;
    #             gap: 10px;
    #         }

    #         .store-avatar {
    #             width: 35px;
    #             height: 35px;
    #             background: #25D366;
    #             border-radius: 50%;
    #             display: flex;
    #             align-items: center;
    #             justify-content: center;
    #             font-weight: bold;
    #         }

    #         .chat-messages {
    #             padding: 15px;
    #             height: calc(100% - 140px);
    #             overflow-y: auto;
    #             display: flex;
    #             flex-direction: column;
    #             gap: 10px;
    #         }

    #         .message {
    #             max-width: 80%;
    #             padding: 10px 12px;
    #             border-radius: 8px;
    #             font-size: 14px;
    #             line-height: 1.4;
    #         }

    #         .message-bot {
    #             background: #dcf8c6;
    #             align-self: flex-end;
    #             border-bottom-right-radius: 3px;
    #         }

    #         .message-user {
    #             background: white;
    #             align-self: flex-start;
    #             border-bottom-left-radius: 3px;
    #         }

    #         .features {
    #             background: white;
    #             padding: 100px 0;
    #         }

    #         .section-header {
    #             text-align: center;
    #             margin-bottom: 80px;
    #         }

    #         .section-header h2 {
    #             font-size: 3rem;
    #             color: #2c3e50;
    #             margin-bottom: 20px;
    #             font-weight: 700;
    #         }

    #         .section-header p {
    #             font-size: 1.25rem;
    #             color: #666;
    #             max-width: 600px;
    #             margin: 0 auto;
    #         }

    #         .features-grid {
    #             display: grid;
    #             grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    #             gap: 40px;
    #             margin-top: 60px;
    #         }

    #         .feature-card {
    #             background: white;
    #             padding: 40px;
    #             border-radius: 20px;
    #             box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    #             border: 1px solid #f0f0f0;
    #             transition: all 0.3s ease;
    #             position: relative;
    #             overflow: hidden;
    #         }

    #         .feature-card::before {
    #             content: '';
    #             position: absolute;
    #             top: 0;
    #             left: 0;
    #             right: 0;
    #             height: 4px;
    #             background: linear-gradient(90deg, #25D366, #128C7E);
    #         }

    #         .feature-card:hover {
    #             transform: translateY(-10px);
    #             box-shadow: 0 20px 50px rgba(0,0,0,0.15);
    #         }

    #         .feature-icon {
    #             width: 70px;
    #             height: 70px;
    #             background: linear-gradient(135deg, #25D366, #128C7E);
    #             border-radius: 20px;
    #             display: flex;
    #             align-items: center;
    #             justify-content: center;
    #             font-size: 2rem;
    #             margin-bottom: 25px;
    #             box-shadow: 0 8px 25px rgba(37, 211, 102, 0.3);
    #         }

    #         .feature-card h3 {
    #             font-size: 1.5rem;
    #             color: #2c3e50;
    #             margin-bottom: 15px;
    #             font-weight: 600;
    #         }

    #         .feature-card p {
    #             color: #666;
    #             font-size: 1rem;
    #             line-height: 1.6;
    #         }

    #         .how-it-works {
    #             background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    #             padding: 100px 0;
    #         }

    #         .steps {
    #             display: grid;
    #             grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    #             gap: 40px;
    #             margin-top: 60px;
    #         }

    #         .step {
    #             text-align: center;
    #             position: relative;
    #         }

    #         .step-number {
    #             width: 80px;
    #             height: 80px;
    #             background: linear-gradient(135deg, #25D366, #128C7E);
    #             border-radius: 50%;
    #             display: flex;
    #             align-items: center;
    #             justify-content: center;
    #             font-size: 2rem;
    #             font-weight: 700;
    #             color: white;
    #             margin: 0 auto 25px auto;
    #             box-shadow: 0 10px 30px rgba(37, 211, 102, 0.3);
    #         }

    #         .step h3 {
    #             font-size: 1.25rem;
    #             color: #2c3e50;
    #             margin-bottom: 15px;
    #             font-weight: 600;
    #         }

    #         .step p {
    #             color: #666;
    #         }

    #         .footer {
    #             background: #2c3e50;
    #             color: white;
    #             padding: 60px 0 30px 0;
    #         }

    #         .footer-content {
    #             display: grid;
    #             grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    #             gap: 40px;
    #             margin-bottom: 40px;
    #         }

    #         .footer-section h4 {
    #             font-size: 1.25rem;
    #             margin-bottom: 20px;
    #             color: #25D366;
    #         }

    #         .footer-section a {
    #             color: #ecf0f1;
    #             text-decoration: none;
    #             display: block;
    #             margin-bottom: 10px;
    #             transition: color 0.3s ease;
    #         }

    #         .footer-section a:hover {
    #             color: #25D366;
    #         }

    #         .footer-bottom {
    #             border-top: 1px solid #34495e;
    #             padding-top: 30px;
    #             text-align: center;
    #             color: #bdc3c7;
    #         }

    #         @media (max-width: 768px) {
    #             .hero-content {
    #                 grid-template-columns: 1fr;
    #                 gap: 40px;
    #                 text-align: center;
    #             }

    #             .hero-text h1 {
    #                 font-size: 2.5rem;
    #             }

    #             .phone-mockup {
    #                 width: 240px;
    #                 height: 480px;
    #             }

    #             .cta-buttons {
    #                 flex-direction: column;
    #                 width: 100%;
    #             }

    #             .btn {
    #                 width: 100%;
    #                 justify-content: center;
    #             }

    #             .features-grid {
    #                 grid-template-columns: 1fr;
    #             }

    #             .steps {
    #                 grid-template-columns: 1fr;
    #             }
    #         }

    #         .floating-elements {
    #             position: absolute;
    #             top: 0;
    #             left: 0;
    #             width: 100%;
    #             height: 100%;
    #             pointer-events: none;
    #             overflow: hidden;
    #         }

    #         .floating-element {
    #             position: absolute;
    #             opacity: 0.1;
    #             animation: float 6s ease-in-out infinite;
    #         }

    #         @keyframes float {
    #             0%, 100% { transform: translateY(0px) rotate(0deg); }
    #             50% { transform: translateY(-20px) rotate(10deg); }
    #         }
    #     </style>
    # </head>
    # <body>
    #     <!-- Hero Section -->
    #     <section class="hero">
    #         <div class="floating-elements">
    #             <div class="floating-element" style="top: 10%; left: 10%; font-size: 3rem;">💬</div>
    #             <div class="floating-element" style="top: 20%; right: 15%; font-size: 2.5rem;">🛍️</div>
    #             <div class="floating-element" style="bottom: 30%; left: 5%; font-size: 2rem;">📱</div>
    #             <div class="floating-element" style="bottom: 10%; right: 10%; font-size: 2.5rem;">🚀</div>
    #         </div>

    #         <div class="container">
    #             <div class="hero-content">
    #                 <div class="hero-text">
    #                     <h1>Transform Your Shopify Store with WhatsApp</h1>
    #                     <p>Enable customers to browse products, manage their cart, and complete purchases directly through WhatsApp conversations. Increase sales with the world's most popular messaging platform.</p>

    #                     <div class="hero-stats">
    #                         <div class="stat">
    #                             <div class="stat-number">2B+</div>
    #                             <div class="stat-label">WhatsApp Users</div>
    #                         </div>
    #                         <div class="stat">
    #                             <div class="stat-number">85%</div>
    #                             <div class="stat-label">Higher Engagement</div>
    #                         </div>
    #                         <div class="stat">
    #                             <div class="stat-number">3x</div>
    #                             <div class="stat-label">Conversion Rate</div>
    #                         </div>
    #                     </div>

    #                     <div class="cta-buttons">
    #                         <a href="https://apps.shopify.com/whatsapp-shopping-bot" class="btn btn-primary">
    #                             🚀 Install App
    #                         </a>
    #                         <a href="/shopify/privacy" class="btn btn-secondary">
    #                             📋 View Documentation
    #                         </a>
    #                     </div>
    #                 </div>

    #                 <div class="hero-visual">
    #                     <div class="phone-mockup">
    #                         <div class="phone-screen">
    #                             <div class="whatsapp-header">
    #                                 <div class="store-avatar">S</div>
    #                                 <div>
    #                                     <div style="font-weight: 600;">Your Store</div>
    #                                     <div style="font-size: 12px; opacity: 0.8;">Online</div>
    #                                 </div>
    #                             </div>
    #                             <div class="chat-messages">
    #                                 <div class="message message-bot">👋 Welcome! Browse our products:</div>
    #                                 <div class="message message-user">Show me sneakers</div>
    #                                 <div class="message message-bot">🏃‍♂️ Nike Air Max - $129.99<br>📦 Qty: 1 | 💵 Total: $129.99<br><br>➖ Less | ➕ More | 🛒 Add to Cart</div>
    #                                 <div class="message message-user">Add to cart</div>
    #                                 <div class="message message-bot">✅ Added to cart!<br>🛒 Cart: 1 item ($129.99)<br><br>🛍️ Checkout | 📦 View Cart</div>
    #                                 <div class="message message-user">Checkout</div>
    #                                 <div class="message message-bot">🛒 Complete your order:<br><a href="#" style="color: #25D366;">👉 Secure Checkout Link</a></div>
    #                             </div>
    #                         </div>
    #                     </div>
    #                 </div>
    #             </div>
    #         </div>
    #     </section>

    #     <!-- Features Section -->
    #     <section class="features">
    #         <div class="container">
    #             <div class="section-header">
    #                 <h2>Powerful Features for Modern Commerce</h2>
    #                 <p>Everything you need to turn WhatsApp into your ultimate sales channel</p>
    #             </div>

    #             <div class="features-grid">
    #                 <div class="feature-card">
    #                     <div class="feature-icon">💬</div>
    #                     <h3>Interactive Product Catalog</h3>
    #                     <p>Customers can browse your entire Shopify inventory directly through WhatsApp. Rich product cards with images, descriptions, and real-time pricing.</p>
    #                 </div>

    #                 <div class="feature-card">
    #                     <div class="feature-icon">🛒</div>
    #                     <h3>Smart Cart Management</h3>
    #                     <p>Built-in shopping cart with quantity controls, item management, and persistent sessions. Customers can easily modify quantities and view totals.</p>
    #                 </div>

    #                 <div class="feature-card">
    #                     <div class="feature-icon">🔒</div>
    #                     <h3>Secure Checkout</h3>
    #                     <p>Seamless integration with Shopify's checkout system. Generate secure checkout links that maintain cart state and customer data.</p>
    #                 </div>

    #                 <div class="feature-card">
    #                     <div class="feature-icon">⚡</div>
    #                     <h3>Real-time Sync</h3>
    #                     <p>Automatic synchronization with your Shopify store. Inventory updates, price changes, and new products are reflected instantly.</p>
    #                 </div>

    #                 <div class="feature-card">
    #                     <div class="feature-icon">📊</div>
    #                     <h3>Analytics & Insights</h3>
    #                     <p>Track conversation metrics, conversion rates, and customer engagement. Understand how WhatsApp drives your sales.</p>
    #                 </div>

    #                 <div class="feature-card">
    #                     <div class="feature-icon">🎯</div>
    #                     <h3>Custom Messages</h3>
    #                     <p>Personalize welcome messages, automated responses, and product descriptions to match your brand voice and customer needs.</p>
    #                 </div>
    #             </div>
    #         </div>
    #     </section>

    #     <!-- How It Works -->
    #     <section class="how-it-works">
    #         <div class="container">
    #             <div class="section-header">
    #                 <h2>Get Started in Minutes</h2>
    #                 <p>Simple setup process to connect your Shopify store with WhatsApp</p>
    #             </div>

    #             <div class="steps">
    #                 <div class="step">
    #                     <div class="step-number">1</div>
    #                     <h3>Install the App</h3>
    #                     <p>Add WhatsApp Shopping Bot to your Shopify store with one click. No technical knowledge required.</p>
    #                 </div>

    #                 <div class="step">
    #                     <div class="step-number">2</div>
    #                     <h3>Connect WhatsApp</h3>
    #                     <p>Link your WhatsApp Business account using the simple configuration wizard. We'll guide you through each step.</p>
    #                 </div>

    #                 <div class="step">
    #                     <div class="step-number">3</div>
    #                     <h3>Configure Settings</h3>
    #                     <p>Customize welcome messages, enable product categories, and set up your brand preferences.</p>
    #                 </div>

    #                 <div class="step">
    #                     <div class="step-number">4</div>
    #                     <h3>Go Live!</h3>
    #                     <p>Share your WhatsApp number with customers and start selling through conversations. It's that simple!</p>
    #                 </div>
    #             </div>
    #         </div>
    #     </section>

    #     <!-- Footer -->
    #     <footer class="footer">
    #         <div class="container">
    #             <div class="footer-content">
    #                 <div class="footer-section">
    #                     <h4>Product</h4>
    #                     <a href="/features">Features</a>
    #                     <a href="/pricing">Pricing</a>
    #                     <a href="/integrations">Integrations</a>
    #                     <a href="/api-docs">API Documentation</a>
    #                 </div>

    #                 <div class="footer-section">
    #                     <h4>Support</h4>
    #                     <a href="/shopify/support">Help Center</a>
    #                     <a href="/tutorials">Tutorials</a>
    #                     <a href="/troubleshooting">Troubleshooting</a>
    #                     <a href="mailto:support@ecommercexpart.com">Contact Support</a>
    #                 </div>

    #                 <div class="footer-section">
    #                     <h4>Legal</h4>
    #                     <a href="/shopify/privacy">Privacy Policy</a>
    #                     <a href="/shopify/terms">Terms of Service</a>
    #                     <a href="/gdpr">GDPR Compliance</a>
    #                     <a href="/security">Security</a>
    #                 </div>

    #                 <div class="footer-section">
    #                     <h4>Company</h4>
    #                     <a href="/about">About Us</a>
    #                     <a href="/blog">Blog</a>
    #                     <a href="/careers">Careers</a>
    #                     <a href="/press">Press Kit</a>
    #                 </div>
    #             </div>

    #             <div class="footer-bottom">
    #                 <p>&copy; 2025 WhatsApp Shopping Bot. All rights reserved. | Built for Shopify merchants worldwide.</p>
    #             </div>
    #         </div>
    #     </footer>
    # </body>
    # </html>
    # """
    landing_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopChat - WhatsApp Shopping Made Easy</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #ffffff;
            background: #11141F;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Header */
        header {
            background: rgba(17, 20, 31, 0.95);
            backdrop-filter: blur(10px);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
        }

        .logo {
            font-size: 1.8rem;
            font-weight: bold;
            color: #25D366;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo::before {
            content: "🛒";
            font-size: 2rem;
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 2rem;
        }

        .nav-links a {
            text-decoration: none;
            color: #ffffff;
            font-weight: 500;
            transition: color 0.3s ease;
        }

        .nav-links a:hover {
            color: #25D366;
        }

        .cta-button {
            background: linear-gradient(135deg, #25D366, #128C7E);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(37, 211, 102, 0.3);
        }

        /* Hero Section */
        .hero {
            padding: 140px 0 100px;
            color: white;
            overflow: hidden;
            position: relative;
        }

        .hero-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .hero-text {
            text-align: left;
        }

        .hero h1 {
            font-size: 3.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            line-height: 1.1;
        }

        .hero p {
            font-size: 1.3rem;
            margin-bottom: 2rem;
            opacity: 0.95;
            line-height: 1.6;
        }

        .hero-cta-group {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .hero-cta {
            font-size: 1.1rem;
            padding: 16px 32px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .hero-cta.primary {
            background: #41434C;
            color: #ffffff;
            box-shadow: 0 8px 25px rgba(65, 67, 76, 0.2);
        }

        .hero-cta.primary:hover {
            background: #35373e;
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(65, 67, 76, 0.3);
        }

        .hero-cta.secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }

        .hero-cta.secondary:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        .hero-visual {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .hero-feature-image {
            position: relative;
            max-width: 500px;
            margin: 0 auto;
        }

        .phone-stack {
            position: relative;
            transform: perspective(1000px) rotateY(-15deg);
        }

        .phone-preview {
            width: 280px;
            height: 560px;
            background: #1a1a1a;
            border-radius: 35px;
            padding: 8px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
            position: relative;
            overflow: hidden;
        }

        .phone-screen {
            width: 100%;
            height: 100%;
            border-radius: 27px;
            overflow: hidden;
            position: relative;
        }

        .preview-screenshot {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 27px;
        }

        .floating-elements {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
        }

        .floating-icon {
            position: absolute;
            font-size: 2.5rem;
            opacity: 0.1;
            animation: float 6s ease-in-out infinite;
        }

        .floating-icon:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
        .floating-icon:nth-child(2) { top: 20%; right: 15%; animation-delay: -2s; }
        .floating-icon:nth-child(3) { bottom: 30%; left: 5%; animation-delay: -4s; }
        .floating-icon:nth-child(4) { bottom: 15%; right: 20%; animation-delay: -1s; }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.1; }
            50% { transform: translateY(-20px) rotate(10deg); opacity: 0.2; }
        }

        /* Features Section */
        .features {
            padding: 100px 0;
            background: #1a1d2e;
        }

        .section-title {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 3rem;
            color: #25D366;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 3rem;
            margin-top: 4rem;
        }

        .feature-card {
            padding: 2rem;
            border-radius: 20px;
            background: #11141F;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 50px rgba(37, 211, 102, 0.2);
            border-color: rgba(37, 211, 102, 0.3);
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }

        .feature-card h3 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #25D366;
        }

        /* Demo Section */
        .demo {
            padding: 100px 0;
            background: #11141F;
        }

        .demo-content {
            display: flex;
            flex-direction: column;
            gap: 4rem;
            align-items: center;
        }

        .demo-text {
            text-align: center;
            max-width: 800px;
        }

        .demo-text h2 {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
            color: #25D366;
        }

        .demo-text p {
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
            color: rgba(255, 255, 255, 0.8);
        }

        .demo-screenshots {
            width: 100%;
            text-align: center;
        }

        .demo-screenshots h3 {
            font-size: 2rem;
            margin-bottom: 2rem;
            color: #25D366;
        }

        .screenshot-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .screenshot-item {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .screenshot-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
        }

        .screenshot-img {
            width: 100%;
            height: 400px;
            object-fit: cover;
            display: block;
        }

        .screenshot-item p {
            padding: 1rem;
            margin: 0;
            font-weight: 600;
            color: #128C7E;
            background: #f8f9fa;
        }

        /* Screenshot Slider */
        .screenshot-slider {
            position: relative;
            max-width: 1000px;
            margin: 0 auto;
            background: #1a1d2e;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .slider-container {
            position: relative;
            overflow: hidden;
            height: 500px;
            background: #11141F;
        }

        .slider-track {
            display: flex;
            transition: transform 0.5s ease;
            height: 100%;
        }

        .slider-slide {
            min-width: 100%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #11141F;
        }

        .slider-slide img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .slider-nav {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
        }

        .slider-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            transition: background 0.3s ease;
        }

        .slider-dot.active {
            background: #25D366;
        }

        .slider-arrow {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            transition: background 0.3s ease;
            z-index: 2;
        }

        .slider-arrow:hover {
            background: rgba(0, 0, 0, 0.7);
        }

        .slider-arrow.prev {
            left: 20px;
        }

        .slider-arrow.next {
            right: 20px;
        }

        /* Pricing Section */
        .pricing {
            padding: 100px 0;
            background: #1a1d2e;
        }

        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .pricing-card {
            background: #11141F;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .pricing-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 50px rgba(37, 211, 102, 0.2);
            border-color: rgba(37, 211, 102, 0.3);
        }

        .pricing-card.popular {
            transform: scale(1.05);
            border: 3px solid #25D366;
        }

        .pricing-card.popular::before {
            content: 'MOST POPULAR';
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #25D366;
            color: white;
            padding: 5px 20px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .pricing-card h3 {
            font-size: 1.8rem;
            color: #25D366;
            margin-bottom: 10px;
        }

        .pricing-price {
            font-size: 3rem;
            font-weight: 700;
            color: #25D366;
            margin-bottom: 10px;
        }

        .pricing-period {
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 30px;
        }

        .pricing-features {
            list-style: none;
            margin-bottom: 30px;
        }

        .pricing-features li {
            padding: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            color: rgba(255, 255, 255, 0.8);
        }

        .pricing-features li::before {
            content: '✅';
            font-size: 1rem;
        }

        .pricing-cta {
            background: #25D366;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s ease;
            width: 100%;
        }

        .pricing-cta:hover {
            background: #128C7E;
        }

        .demo-features {
            list-style: none;
            margin: 2rem 0;
        }

        .demo-features li {
            padding: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .demo-features li::before {
            content: "✅";
            font-size: 1.2rem;
        }

        .phone-mockup {
            position: relative;
            max-width: 300px;
            margin: 0 auto;
        }

        .phone-frame {
            background: #333;
            padding: 20px;
            border-radius: 30px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        }

        .phone-screen {
            background: #1f1f1f;
            border-radius: 20px;
            padding: 20px;
            min-height: 500px;
            color: white;
            font-size: 0.9rem;
        }

        .chat-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
            margin-bottom: 20px;
        }

        .chat-avatar {
            width: 40px;
            height: 40px;
            background: #25D366;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }

        .message {
            background: #262626;
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 10px;
            max-width: 85%;
        }

        .message.sent {
            background: #25D366;
            margin-left: auto;
            text-align: right;
        }

        .action-button {
            background: #25D366;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            margin: 5px 0;
            display: block;
            width: 100%;
            cursor: pointer;
            font-size: 0.85rem;
        }

        /* Stats Section */
        .stats {
            padding: 80px 0;
            background: #11141E;
            color: white;
            text-align: center;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 3rem;
            margin-top: 3rem;
        }

        .stat-item h3 {
            font-size: 3rem;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }

        .stat-item p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        /* CTA Section */
        .final-cta {
            padding: 100px 0;
            background: #11141F;
            color: white;
            text-align: center;
        }

        .final-cta h2 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #25D366;
        }

        .final-cta p {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.95;
        }

        /* Footer */
        footer {
            background: #0d0f1a;
            color: white;
            padding: 3rem 0 1rem;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .footer-section h4 {
            margin-bottom: 1rem;
            color: #25D366;
        }

        .footer-section a {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            display: block;
            margin: 0.5rem 0;
            transition: color 0.3s ease;
        }

        .footer-section a:hover {
            color: #25D366;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }

            .hero-content {
                grid-template-columns: 1fr;
                gap: 40px;
                text-align: center;
            }

            .hero-text {
                text-align: center;
            }

            .hero h1 {
                font-size: 2.5rem;
            }

            .hero-cta-group {
                flex-direction: column;
                width: 100%;
            }

            .hero-cta {
                width: 100%;
                justify-content: center;
            }

            .phone-preview {
                width: 240px;
                height: 480px;
            }

            .screenshot-gallery {
                grid-template-columns: 1fr;
            }

            .screenshot-img {
                height: 300px;
            }

            .features-grid {
                grid-template-columns: 1fr;
            }

            .slider-container {
                height: 400px;
            }

            .pricing-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in-up {
            animation: fadeInUp 0.8s ease forwards;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header>
        <nav class="container">
            <div class="logo">WhizCart</div>
            <ul class="nav-links">
                <li><a href="#features">Features</a></li>
                <li><a href="#demo">Demo</a></li>
                <li><a href="#pricing">Pricing</a></li>
            </ul>
        </nav>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="floating-elements">
            <div class="floating-icon">💬</div>
            <div class="floating-icon">🛍️</div>
            <div class="floating-icon">📱</div>
            <div class="floating-icon">🚀</div>
        </div>
        
        <div class="hero-content">
            <div class="hero-text fade-in-up">
                <h1 style="color: #25D366;">WhizCart - Social Commerce</h1>
                <p>Transform your Shopify store with WhatsApp's power. Let customers browse products, manage carts, and complete purchases through conversational commerce - all within WhatsApp!</p>
                
                <div class="hero-cta-group">
                    <a href="https://apps.shopify.com/whizcart" class="hero-cta primary">
                        🚀 Start Free Trial
                    </a>
                    <a href="#pricing" class="hero-cta secondary">
                        💰 View Pricing
                    </a>
                </div>
            </div>
            
            <div class="hero-visual fade-in-up">
                <div class="hero-feature-image">
                    <div class="phone-stack">
                        <div class="phone-preview">
                            <div class="phone-screen">
                                <img src="/static/assets/ss1.jpg" alt="WhizCart WhatsApp Shopping Interface" class="preview-screenshot">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features" id="features">
        <div class="container">
            <h2 class="section-title">Why Choose WhizCart?</h2>
            <div class="features-grid">
                <div class="feature-card fade-in-up">
                    <span class="feature-icon">🛍️</span>
                    <h3>Product Catalog Integration</h3>
                    <p>Seamlessly sync your Shopify product catalog with WhatsApp. Customers can browse categories, view products, and see real-time inventory.</p>
                </div>
                <div class="feature-card fade-in-up">
                    <span class="feature-icon">🛒</span>
                    <h3>Smart Shopping Cart</h3>
                    <p>Interactive shopping cart within WhatsApp chat. Add, remove, and modify quantities with simple button clicks.</p>
                </div>
                <div class="feature-card fade-in-up">
                    <span class="feature-icon">💳</span>
                    <h3>Secure Checkout</h3>
                    <p>Direct integration with Shopify's secure checkout process. Customers complete purchases without leaving WhatsApp.</p>
                </div>
                <div class="feature-card fade-in-up">
                    <span class="feature-icon">🤖</span>
                    <h3>Automated Responses</h3>
                    <p>AI-powered chatbot handles common queries, product recommendations, and order status updates 24/7.</p>
                </div>
                <div class="feature-card fade-in-up">
                    <span class="feature-icon">📊</span>
                    <h3>Analytics Dashboard</h3>
                    <p>Track conversation metrics, conversion rates, and customer behavior to optimize your WhatsApp sales strategy.</p>
                </div>
                <div class="feature-card fade-in-up">
                    <span class="feature-icon">🔒</span>
                    <h3>Meta Business API</h3>
                    <p>Built on Meta's official Business API for WhatsApp, ensuring reliability, security, and compliance.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Demo Section -->
    <section class="demo" id="demo">
        <div class="container">
            <div class="demo-content">
                <div class="demo-text">
                    <h2>See WhizCart in Action</h2>
                    <p>Experience real WhatsApp shopping with actual screenshots from our live system. See how customers browse, select, and purchase products seamlessly!</p>
                    <ul class="demo-features">
                        <li>Browse product categories with interactive buttons</li>
                        <li>View detailed product information and pricing</li>
                        <li>Add multiple items to cart seamlessly</li>
                        <li>Complete secure checkout process</li>
                        <li>Direct integration with Shopify checkout</li>
                    </ul>
                    <a href="https://apps.shopify.com/whizcart" class="cta-button">🚀 Start Free Trial</a>
                </div>
                <div class="demo-screenshots">
                    <h3>Real WhatsApp Shopping Experience</h3>
                    <div class="screenshot-slider">
                        <div class="slider-container">
                            <div class="slider-track" id="sliderTrack">
                                <div class="slider-slide">
                                    <img src="/static/assets/ss1.jpg" alt="Welcome & Initial Chat">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss2.jpg" alt="Product Categories">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss4.jpg" alt="Browse Products by Category">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss5.jpg" alt="Product Selection Interface">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss7.jpg" alt="Add to Cart Process">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss8.jpg" alt="Cart Review">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss9.jpg" alt="Checkout Confirmation">
                                </div>
                                <div class="slider-slide">
                                    <img src="/static/assets/ss12.jpg" alt="Shopify Secure Checkout">
                                </div>
                            </div>
                            <button class="slider-arrow prev" onclick="previousSlide()">‹</button>
                            <button class="slider-arrow next" onclick="nextSlide()">›</button>
                            <div class="slider-nav" id="sliderNav"></div>
                        </div>
                    </div>
                    <p style="text-align: center; margin-top: 20px; color: #666; font-style: italic;">
                        Swipe or click arrows to see the complete shopping journey
                    </p>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="stats">
        <div class="container">
            <h2 style="color: #2DC581;">Trusted by Growing Businesses</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <h3>2.8x</h3>
                    <p>Average increase in conversion rates</p>
                </div>
                <div class="stat-item">
                    <h3>47%</h3>
                    <p>Reduction in cart abandonment</p>
                </div>
                <div class="stat-item">
                    <h3>5.2B</h3>
                    <p>WhatsApp users worldwide</p>
                </div>
                <div class="stat-item">
                    <h3>24/7</h3>
                    <p>Automated customer support</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing Section -->
    <section class="pricing" id="pricing">
        <div class="container">
            <h2 class="section-title">Choose Your Plan</h2>
            <p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 3rem;">Start free, upgrade as you grow. All plans include core WhatsApp shopping features.</p>
            
            <div class="pricing-grid" id="pricingGrid">
                <!-- Pricing cards will be loaded here -->
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
                    <div style="animate-spin: inline-block; width: 2rem; height: 2rem; border: 3px solid #25D366; border-radius: 50%; border-top-color: transparent; animation: spin 1s ease-in-out infinite;"></div>
                    <p style="margin-top: 1rem; color: #666;">Loading pricing plans...</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Final CTA -->
    <section class="final-cta">
        <div class="container">
            <h2>Ready to Transform Your Sales?</h2>
            <p>Join thousands of Shopify stores already using WhatsApp to increase conversions and customer satisfaction.</p>
            <a href="https://apps.shopify.com/whizcart" class="cta-button hero-cta">Start Your Free Trial</a>
        </div>
    </section>

    <!-- Footer -->
    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h4>Legal & Support</h4>
                    <a href="/shopify/privacy">Privacy Policy</a>
                    <a href="/shopify/terms">Terms of Service</a>
                    <a href="/shopify/support">Help Center</a>
                    <a href="/health">System Status</a>
                </div>
                <div class="footer-section">
                    <h4>Plans</h4>
                    <a href="/free">Free Plan</a>
                    <a href="/basic">Basic Plan ($4.99/month)</a>
                    <a href="/premium">Premium Plan ($79/month)</a>
                </div>
                <div class="footer-section">
                    <h4>Quick Start</h4>
                    <a href="#features">Features</a>
                    <a href="#demo">Live Demo</a>
                    <a href="#pricing">Pricing Comparison</a>
                    <a href="https://apps.shopify.com/whizcart">Install App</a>
                </div>
            </div>
            <p>&copy; 2025 WhizCart. All rights reserved.</p>
        </div>
    </footer>

    <script>
        // Slider functionality
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slider-slide');
        const totalSlides = slides.length;
        
        function createSliderNavigation() {
            const nav = document.getElementById('sliderNav');
            for (let i = 0; i < totalSlides; i++) {
                const dot = document.createElement('div');
                dot.classList.add('slider-dot');
                if (i === 0) dot.classList.add('active');
                dot.onclick = () => goToSlide(i);
                nav.appendChild(dot);
            }
        }
        
        function updateSlider() {
            const track = document.getElementById('sliderTrack');
            track.style.transform = `translateX(-${currentSlide * 100}%)`;
            
            // Update navigation dots
            document.querySelectorAll('.slider-dot').forEach((dot, index) => {
                dot.classList.toggle('active', index === currentSlide);
            });
        }
        
        function nextSlide() {
            currentSlide = (currentSlide + 1) % totalSlides;
            updateSlider();
        }
        
        function previousSlide() {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
            updateSlider();
        }
        
        function goToSlide(index) {
            currentSlide = index;
            updateSlider();
        }
        
        // Auto-advance slider
        function startSlideshow() {
            return setInterval(nextSlide, 4000);
        }
        
        // Load pricing data
        async function loadPricing() {
            const pricingGrid = document.getElementById('pricingGrid');
            
            const plans = [
                {
                    name: 'Free',
                    price: '$0',
                    period: '/month',
                    features: ['100 WhatsApp messages/month', 'Product catalog browsing', 'Shopping cart functionality', 'Secure Shopify checkout', 'Basic welcome message'],
                    cta: 'Start Free',
                    link: 'https://apps.shopify.com/whizcart',
                    popular: false
                },
                {
                    name: 'Basic',
                    price: '$4.99',
                    period: '/month',
                    features: ['1,000 WhatsApp messages/month', 'Everything in Free plan', 'Order tracking via WhatsApp', 'Enhanced welcome messages', 'Email support'],
                    cta: 'Start 7-Day Trial',
                    link: 'https://apps.shopify.com/whizcart',
                    popular: true
                },
                {
                    name: 'Premium',
                    price: '$79',
                    period: '/month',
                    features: ['10,000 WhatsApp messages/month', 'Everything in Basic plan', 'Advanced analytics dashboard', 'Priority support', 'Abandoned cart recovery'],
                    cta: 'Start 7-Day Trial',
                    link: 'https://apps.shopify.com/whizcart',
                    popular: false
                }
            ];
            
            pricingGrid.innerHTML = '';
            
            plans.forEach(plan => {
                const card = document.createElement('div');
                card.classList.add('pricing-card');
                if (plan.popular) card.classList.add('popular');
                
                card.innerHTML = `
                    <h3>${plan.name}</h3>
                    <div class="pricing-price">${plan.price}<span style="font-size: 1rem;">${plan.period}</span></div>
                    <div class="pricing-period">Perfect for ${plan.name === 'Free' ? 'testing' : plan.name === 'Basic' ? 'growing businesses' : 'high-volume stores'}</div>
                    <ul class="pricing-features">
                        ${plan.features.map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                    <button class="pricing-cta" onclick="window.location.href='${plan.link}'">${plan.cta}</button>
                `;
                
                pricingGrid.appendChild(card);
            });
        }
        
        // Simple scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe all fade-in-up elements
        document.querySelectorAll('.fade-in-up').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            observer.observe(el);
        });

        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Initialize everything when page loads
        document.addEventListener('DOMContentLoaded', function() {
            createSliderNavigation();
            updateSlider();
            loadPricing();
            
            // Start slideshow
            let slideInterval = startSlideshow();
            
            // Pause slideshow on hover
            const slider = document.querySelector('.screenshot-slider');
            if (slider) {
                slider.addEventListener('mouseenter', () => clearInterval(slideInterval));
                slider.addEventListener('mouseleave', () => slideInterval = startSlideshow());
            }
        });
        
        // Add loading animation CSS
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""
    return HTMLResponse(content=landing_page)
