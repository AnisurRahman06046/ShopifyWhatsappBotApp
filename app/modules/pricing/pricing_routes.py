from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/free")
async def free_plan(shop: str = Query(None)):
    """Free plan details for Shopify App Store listing"""
    
    # If shop parameter is provided, redirect to setup
    if shop:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/shopify/setup?shop={shop}")
    
    plan_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Free Plan - WhatsApp Shopping Bot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 20px; }
            .plan-header { background: linear-gradient(135deg, #25D366, #128C7E); color: white; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 30px; }
            .plan-title { font-size: 2.5rem; margin-bottom: 10px; }
            .plan-price { font-size: 3rem; font-weight: bold; margin-bottom: 15px; }
            .plan-description { font-size: 1.2rem; opacity: 0.9; }
            .features-list { background: white; border: 1px solid #e1e8ed; border-radius: 10px; padding: 30px; }
            .feature-item { padding: 15px 0; border-bottom: 1px solid #f1f1f1; display: flex; align-items: center; }
            .feature-item:last-child { border-bottom: none; }
            .feature-icon { color: #25D366; font-size: 1.2rem; margin-right: 15px; }
            .feature-text { flex: 1; }
            .limitation { color: #666; font-style: italic; }
            .cta-button { background: #25D366; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block; margin-top: 30px; font-weight: 600; text-align: center; }
            .cta-button:hover { background: #128C7E; }
        </style>
    </head>
    <body>
        <div class="plan-header">
            <div class="plan-title">Free Plan</div>
            <div class="plan-price">$0<span style="font-size: 1rem;">/month</span></div>
            <div class="plan-description">Perfect for testing and small stores</div>
        </div>

        <div class="features-list">
            <h3>What's Included:</h3>
            
            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>100 WhatsApp messages per month</strong>
                    <div class="limitation">Includes both incoming and outgoing messages</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Product catalog browsing</strong>
                    <div class="limitation">Customers browse your Shopify products via WhatsApp</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Shopping cart functionality</strong>
                    <div class="limitation">Add/remove items, quantity management, view cart</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Secure Shopify checkout</strong>
                    <div class="limitation">Direct integration with Shopify checkout system</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Real-time product sync</strong>
                    <div class="limitation">Automatic inventory, price, and product updates</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Basic welcome message</strong>
                    <div class="limitation">Customizable greeting for new customers</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Order tracking</strong>
                    <div class="limitation">Coming soon - Track order status via WhatsApp</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">❌</div>
                <div class="feature-text">
                    <strong>Analytics dashboard</strong>
                    <div class="limitation">Available in Basic plan</div>
                </div>
            </div>

        </div>

        <div style="text-align: center; margin-top: 40px;">
            <p><a href="/basic" style="color: #25D366;">View Basic Plan →</a> | <a href="/premium" style="color: #25D366;">View Premium Plan →</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=plan_html)

@router.get("/basic")
async def basic_plan():
    """Basic plan details for Shopify App Store listing"""
    plan_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Basic Plan - WhatsApp Shopping Bot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 20px; }
            .plan-header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 30px; }
            .plan-title { font-size: 2.5rem; margin-bottom: 10px; }
            .plan-price { font-size: 3rem; font-weight: bold; margin-bottom: 15px; }
            .plan-description { font-size: 1.2rem; opacity: 0.9; }
            .features-list { background: white; border: 1px solid #e1e8ed; border-radius: 10px; padding: 30px; }
            .feature-item { padding: 15px 0; border-bottom: 1px solid #f1f1f1; display: flex; align-items: center; }
            .feature-item:last-child { border-bottom: none; }
            .feature-icon { color: #667eea; font-size: 1.2rem; margin-right: 15px; }
            .feature-text { flex: 1; }
            .limitation { color: #666; font-style: italic; }
            .cta-button { background: #667eea; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block; margin-top: 30px; font-weight: 600; text-align: center; }
            .cta-button:hover { background: #5a67d8; }
            .badge { background: #667eea; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="plan-header">
            <div style="margin-bottom: 15px;"><span class="badge">MOST POPULAR</span></div>
            <div class="plan-title">Basic Plan</div>
            <div class="plan-price">$4.99<span style="font-size: 1rem;">/month</span></div>
            <div class="plan-description">Ideal for growing businesses</div>
        </div>

        <div class="features-list">
            <h3>Everything in Free Plan, plus:</h3>
            
            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>1,000 WhatsApp messages per month</strong>
                    <div class="limitation">10x more messages than Free plan</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Order tracking via WhatsApp</strong>
                    <div class="limitation">Customers can check order status through chat</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Enhanced welcome messages</strong>
                    <div class="limitation">More customization options and templates</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>Email support</strong>
                    <div class="limitation">Priority support within 24 hours</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Basic analytics dashboard</strong>
                    <div class="limitation">Coming soon - Message counts, basic metrics</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Product collections support</strong>
                    <div class="limitation">Coming soon - Browse products by categories</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Order notifications</strong>
                    <div class="limitation">Coming soon - Automatic order status updates</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">❌</div>
                <div class="feature-text">
                    <strong>Advanced features</strong>
                    <div class="limitation">Available in Premium plan</div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #666; font-size: 0.9rem;">
                    $4.99/month or $49.99/year • 7-day free trial
                </p>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <p><a href="/free" style="color: #667eea;">View Free Plan →</a> | <a href="/premium" style="color: #667eea;">View Premium Plan →</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=plan_html)

@router.get("/premium")
async def premium_plan():
    """Premium plan details for Shopify App Store listing"""
    plan_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Premium Plan - WhatsApp Shopping Bot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 20px; }
            .plan-header { background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 30px; }
            .plan-title { font-size: 2.5rem; margin-bottom: 10px; }
            .plan-price { font-size: 3rem; font-weight: bold; margin-bottom: 15px; }
            .plan-description { font-size: 1.2rem; opacity: 0.9; }
            .features-list { background: white; border: 1px solid #e1e8ed; border-radius: 10px; padding: 30px; }
            .feature-item { padding: 15px 0; border-bottom: 1px solid #f1f1f1; display: flex; align-items: center; }
            .feature-item:last-child { border-bottom: none; }
            .feature-icon { color: #ff6b6b; font-size: 1.2rem; margin-right: 15px; }
            .feature-text { flex: 1; }
            .limitation { color: #666; font-style: italic; }
            .cta-button { background: #ff6b6b; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block; margin-top: 30px; font-weight: 600; text-align: center; }
            .cta-button:hover { background: #ee5a52; }
            .badge { background: #ffd700; color: #333; padding: 5px 15px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="plan-header">
            <div style="margin-bottom: 15px;"><span class="badge">ENTERPRISE READY</span></div>
            <div class="plan-title">Premium Plan</div>
            <div class="plan-price">$79<span style="font-size: 1rem;">/month</span></div>
            <div class="plan-description">For high-volume stores and advanced features</div>
        </div>

        <div class="features-list">
            <h3>Everything in Basic Plan, plus:</h3>
            
            <div class="feature-item">
                <div class="feature-icon">✅</div>
                <div class="feature-text">
                    <strong>10,000 WhatsApp messages per month</strong>
                    <div class="limitation">Perfect for high-traffic stores</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Advanced analytics dashboard</strong>
                    <div class="limitation">Coming soon - Detailed conversation metrics and sales insights</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Priority support</strong>
                    <div class="limitation">Coming soon - Fast response time, dedicated support</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Abandoned cart recovery</strong>
                    <div class="limitation">Coming soon - Automatic follow-up messages</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Advanced product search</strong>
                    <div class="limitation">Coming soon - Smart search and filtering</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Customer segmentation</strong>
                    <div class="limitation">Coming soon - Targeted messaging features</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Broadcast messaging</strong>
                    <div class="limitation">Coming soon - Send promotions to customer lists</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Multi-language support</strong>
                    <div class="limitation">Coming soon - Support for multiple languages</div>
                </div>
            </div>

            <div class="feature-item">
                <div class="feature-icon">⏳</div>
                <div class="feature-text">
                    <strong>Custom webhooks & API</strong>
                    <div class="limitation">Coming soon - Advanced automation capabilities</div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #666; font-size: 0.9rem;">
                    $79/month or $599/year • 7-day free trial
                </p>
            </div>
        </div>

        <div style="background: #f8f9fa; padding: 30px; border-radius: 10px; margin-top: 30px;">
            <h3 style="text-align: center; margin-bottom: 20px;">💼 Enterprise Solutions</h3>
            <p style="text-align: center; margin-bottom: 20px;">
                Need more than 10,000 messages per month? Custom integrations? Dedicated infrastructure?
            </p>
            <div style="text-align: center;">
                <a href="mailto:enterprise@ecommercexpart.com" style="background: #333; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: 600;">
                    Contact Enterprise Sales
                </a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <p><a href="/free" style="color: #ff6b6b;">View Free Plan →</a> | <a href="/basic" style="color: #ff6b6b;">View Basic Plan →</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=plan_html)