import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class EmailService:
    """Email sending service"""
    
    def __init__(self):
        self.config = Config()
    
    def send_email(self, to_email, subject, html_body, text_body=None):
        """
        Send email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of email
            text_body: Plain text fallback (optional)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.MAIL_DEFAULT_SENDER
            msg['To'] = to_email
            
            # Add plain text version
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Check if email is configured
            if not self.config.MAIL_USERNAME or not self.config.MAIL_PASSWORD:
                print("\n" + "="*70)
                print("⚠️  EMAIL SERVICE NOT CONFIGURED")
                print("="*70)
                print("📧 MOCK EMAIL (Development Mode)")
                print("-"*70)
                print(f"To: {to_email}")
                print(f"From: {self.config.MAIL_DEFAULT_SENDER}")
                print(f"Subject: {subject}")
                print("-"*70)
                print("\n" + (text_body or "See HTML version in production"))
                print("\n" + "="*70)
                print("💡 To enable real emails:")
                print("   1. Create .env file from .env.example")
                print("   2. Add your SMTP credentials")
                print("   3. See EMAIL_SETUP.md for detailed instructions")
                print("="*70 + "\n")
                return True
            
            # Send email via SMTP
            print(f"📤 Sending email to {to_email}...")
            
            if self.config.MAIL_USE_SSL:
                server = smtplib.SMTP_SSL(self.config.MAIL_SERVER, self.config.MAIL_PORT)
            else:
                server = smtplib.SMTP(self.config.MAIL_SERVER, self.config.MAIL_PORT)
                if self.config.MAIL_USE_TLS:
                    server.starttls()
            
            server.login(self.config.MAIL_USERNAME, self.config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {to_email}\n")
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to send email: {str(e)}")
            print("\n" + "="*70)
            print("📧 EMAIL MOCK (Fallback - SMTP Failed)")
            print("="*70)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("-"*70)
            print(text_body or "See HTML version")
            print("="*70 + "\n")
            return False
    
    def send_password_reset_email(self, to_email, reset_link, username=None):
        """
        Send password reset email
        
        Args:
            to_email: User's email address
            reset_link: Password reset URL
            username: User's username (optional)
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"{self.config.APP_NAME} - Password Reset Request"
        
        # Plain text version
        text_body = f"""
Hello {username or 'User'},

You requested to reset your password for {self.config.APP_NAME}.

Click the link below to reset your password:
{reset_link}

This link will expire in {self.config.RESET_TOKEN_EXPIRY_HOURS} hour(s).

If you did not request this password reset, please ignore this email.

Best regards,
{self.config.APP_NAME} Team
        """.strip()
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .button {{
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            background: #f1f1f1;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-radius: 0 0 10px 10px;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔐 Password Reset Request</h1>
    </div>
    
    <div class="content">
        <p>Hello <strong>{username or 'User'}</strong>,</p>
        
        <p>You requested to reset your password for <strong>{self.config.APP_NAME}</strong>.</p>
        
        <p>Click the button below to reset your password:</p>
        
        <center>
            <a href="{reset_link}" class="button">Reset Password</a>
        </center>
        
        <p style="font-size: 12px; color: #666;">
            Or copy and paste this link into your browser:<br>
            <a href="{reset_link}">{reset_link}</a>
        </p>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This link will expire in {self.config.RESET_TOKEN_EXPIRY_HOURS} hour(s).
        </div>
        
        <p style="margin-top: 30px;">If you did not request this password reset, please ignore this email and your password will remain unchanged.</p>
        
        <p>Best regards,<br>
        <strong>{self.config.APP_NAME} Team</strong></p>
    </div>
    
    <div class="footer">
        <p>This is an automated email. Please do not reply.</p>
        <p>For support, contact: {self.config.SUPPORT_EMAIL}</p>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(to_email, subject, html_body, text_body)
    
    def send_welcome_email(self, to_email, username):
        """
        Send welcome email to new users
        
        Args:
            to_email: User's email address
            username: User's username
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"Welcome to {self.config.APP_NAME}!"
        
        text_body = f"""
Hello {username},

Welcome to {self.config.APP_NAME}!

Your account has been successfully created. You can now log in and start monitoring your piezoelectric tile energy production.

Dashboard: http://localhost:5000/dashboard

Thank you for joining us in the journey towards sustainable energy!

Best regards,
{self.config.APP_NAME} Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .footer {{
            background: #f1f1f1;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-radius: 0 0 10px 10px;
        }}
        .feature {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Welcome to Smart Tile!</h1>
    </div>
    
    <div class="content">
        <p>Hello <strong>{username}</strong>,</p>
        
        <p>Welcome to <strong>{self.config.APP_NAME}</strong>!</p>
        
        <p>Your account has been successfully created. You can now monitor your piezoelectric tile energy production in real-time.</p>
        
        <h3>What you can do:</h3>
        
        <div class="feature">
            <strong>📊 Monitor Energy Production</strong><br>
            Track total energy generated from footsteps
        </div>
        
        <div class="feature">
            <strong>👣 Count Footsteps</strong><br>
            See real-time footstep analytics
        </div>
        
        <div class="feature">
            <strong>💰 Calculate Value</strong><br>
            Estimate energy value in rupees
        </div>
        
        <div class="feature">
            <strong>📈 View Trends</strong><br>
            Analyze historical performance data
        </div>
        
        <p style="margin-top: 30px;">Thank you for joining us in the journey towards sustainable energy!</p>
        
        <p>Best regards,<br>
        <strong>{self.config.APP_NAME} Team</strong></p>
    </div>
    
    <div class="footer">
        <p>For support, contact: {self.config.SUPPORT_EMAIL}</p>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(to_email, subject, html_body, text_body)