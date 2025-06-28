"""
Email notification system for verification status updates
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_verification_approval_email(user):
    """Send approval notification email to user."""
    subject = '🎉 Congratulations! Your ChopSmo Verification Has Been Approved!'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container {{
                max-width: 600px;
                margin: 0 auto;
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                text-align: center;
                background-color: #4CAF50;
                color: white;
                padding: 30px;
                border-radius: 10px 10px 0 0;
            }}
            .logo {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 0 0 10px 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .benefits {{
                background-color: #e8f5e8;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .benefit-item {{
                margin: 10px 0;
                padding-left: 20px;
                position: relative;
            }}
            .benefit-item:before {{
                content: "✅";
                position: absolute;
                left: 0;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 30px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🍽️ ChopSmo</div>
                <h1>Welcome to the Verified Contributors Community!</h1>
            </div>
            
            <div class="content">
                <h2>Hi {user.first_name or user.username}!</h2>
                
                <p>We're thrilled to let you know that your verification application has been <strong>approved</strong>! 🎉</p>
                
                <p>You are now a <strong>Verified Contributor</strong> on ChopSmo, which means you can now enjoy all the exclusive benefits of our contributor community.</p>
                
                <div class="benefits">
                    <h3>🌟 Your New Verified Contributor Benefits:</h3>
                    <div class="benefit-item">Create and share your own recipes with the ChopSmo community</div>
                    <div class="benefit-item">Get a verified badge (✅) displayed on your profile</div>
                    <div class="benefit-item">Access to advanced recipe management tools</div>
                    <div class="benefit-item">Priority support from our team</div>
                    <div class="benefit-item">Early access to new features</div>
                    <div class="benefit-item">Join our exclusive contributor community discussions</div>
                </div>
                
                <p>Ready to start creating amazing recipes? Head over to your dashboard and begin sharing your culinary expertise!</p>
                
                <a href="https://frontendsmo.vercel.app/dashboard" class="cta-button">Start Creating Recipes →</a>
                
                <p>Thank you for being part of the ChopSmo family. We can't wait to see the amazing recipes you'll create!</p>
                
                <p>Happy cooking! 👨‍🍳👩‍🍳</p>
                
                <p><strong>The ChopSmo Team</strong></p>
            </div>
            
            <div class="footer">
                <p>Questions? Contact us at support@chopsmo.com</p>
                <p>© 2025 ChopSmo. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Congratulations {user.first_name or user.username}!
    
    Your ChopSmo verification application has been approved! 🎉
    
    You are now a Verified Contributor with access to:
    ✅ Create and share recipes
    ✅ Verified badge on your profile  
    ✅ Advanced recipe management tools
    ✅ Priority support
    ✅ Early access to new features
    
    Start creating recipes at: https://frontendsmo.vercel.app/dashboard
    
    Happy cooking!
    The ChopSmo Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send approval email to {user.email}: {e}")
        return False

def send_verification_rejection_email(user, reason=""):
    """Send rejection notification email to user."""
    subject = 'ChopSmo Verification Application Update'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container {{
                max-width: 600px;
                margin: 0 auto;
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                text-align: center;
                background-color: #ff6b6b;
                color: white;
                padding: 30px;
                border-radius: 10px 10px 0 0;
            }}
            .logo {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 0 0 10px 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .reason-box {{
                background-color: #fff5f5;
                border-left: 4px solid #ff6b6b;
                padding: 15px;
                margin: 20px 0;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 30px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🍽️ ChopSmo</div>
                <h1>Verification Application Update</h1>
            </div>
            
            <div class="content">
                <h2>Hi {user.first_name or user.username},</h2>
                
                <p>Thank you for your interest in becoming a verified contributor on ChopSmo.</p>
                
                <p>After careful review, we're unable to approve your verification application at this time.</p>
                
                {f'<div class="reason-box"><strong>Feedback:</strong><br>{reason}</div>' if reason else ''}
                
                <p><strong>Don't worry - you can reapply!</strong></p>
                
                <p>We encourage you to:</p>
                <ul>
                    <li>Continue engaging with the ChopSmo community</li>
                    <li>Build your cooking portfolio</li>
                    <li>Address any feedback provided above</li>
                    <li>Reapply when you feel ready</li>
                </ul>
                
                <a href="https://frontendsmo.vercel.app/verification" class="cta-button">Apply Again</a>
                
                <p>We appreciate your passion for cooking and look forward to potentially welcoming you as a verified contributor in the future.</p>
                
                <p>Keep cooking! 👨‍🍳👩‍🍳</p>
                
                <p><strong>The ChopSmo Team</strong></p>
            </div>
            
            <div class="footer">
                <p>Questions? Contact us at support@chopsmo.com</p>
                <p>© 2025 ChopSmo. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Hi {user.first_name or user.username},
    
    Thank you for your ChopSmo verification application.
    
    After review, we're unable to approve your application at this time.
    
    {f'Feedback: {reason}' if reason else ''}
    
    You're welcome to reapply in the future. Keep cooking!
    
    The ChopSmo Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send rejection email to {user.email}: {e}")
        return False
