import smtplib
import csv
import time
import random
import threading
import email.utils
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Set TESTING_MODE = True for testing (short delays) and False for production (1 and 2 days)
TESTING_MODE = False
followup_delay = 10 if TESTING_MODE else 86400  # 86400 seconds = 1 day

def spin_email_template(person_name, company, is_followup=False, followup_number=None):
    """
    Creates both a plain text and an HTML email body.
    The email includes:
      - A greeting  
      - sentence1_options  
      - sentence2_options  
      - sentence3_options  
      - A Loom GIF thumbnail (or link for plain text)  
      - "Looking forward to hearing from you"  
      - "Best regards"  
      - "Your Company"
      
    If it's a follow-up, an extra line is appended indicating follow-up number.
    """
    # Randomize greeting and sentences
    greetings = [
        f"Hi {person_name},",
        f"Hello {person_name},",
        f"Dear {person_name},"
    ]
    sentence1_options = [
        "I see you booked your new domain, marking an important step toward establishing a strong online presence.",
        "I noticed you secured your new domain—an essential move toward building a reliable online identity.",
        "I noticed you secured your domain. This marks the beginning of your online journey."
    ]
    sentence2_options = [
        "In the past six months, we’ve worked with several businesses to build websites, improve their search performance, and refine their social media presence. Consider how a well-designed digital platform can support your goals.",
        "Over the past six months, we’ve assisted a number of companies with website design, search optimization, and social media strategy. Think about how a customized digital solution could benefit your business.",
        "Recently, we’ve helped several businesses develop websites, enhance their search performance, and improve their social media efforts. Imagine a digital solution that aligns with your business needs."
    ]
    sentence3_options = [
        "I’m contacting you personally to share how our services may be of benefit. Please take a moment to watch the brief video I recorded, which explains our approach.",
        "I’m contacting you directly to share more about our services. I’ve prepared a brief video introduction outlining our process.",
        "I’m reaching out personally to share how our services may help. I’ve recorded a short video to introduce myself and explain our approach."
    ]
    
    greeting = random.choice(greetings)
    sentence1 = random.choice(sentence1_options)
    sentence2 = random.choice(sentence2_options)
    sentence3 = random.choice(sentence3_options)
    
    # Extra line for follow-ups
    extra_line = f"\nThis is follow-up #{followup_number}. Just checking in regarding my previous email." if is_followup and followup_number else ""
    
    # Plain text version: Loom GIF cannot be embedded so include the link instead.
    loom_link = "https://www.loom.com/share/1915f664b7f145f193d7b0fd6873ecb1"
    text_body = f"""{greeting}

{sentence1}

{sentence2}

{sentence3}

{extra_line}

{loom_link}

Looking forward to hearing from you.

Best regards,  
Neal  
https://filldesigngroup.com/
"""
    
    # HTML version: Embed the Loom GIF thumbnail.
    html_body = f"""\
<html>
  <body>
    <p>{greeting}</p>
    <p>{sentence1}</p>
    <p>{sentence2}</p>
    <p>{sentence3}</p>
    {f"<p>{extra_line}</p>" if extra_line else ""}
    <div>
      <a href="{loom_link}">
        <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/1915f664b7f145f193d7b0fd6873ecb1-12ee91ac978e3ba5-full-play.gif" alt="Watch Video">
      </a>
    </div>
    <p>
      Looking forward to hearing from you.<br>
      Best regards,<br>
      Neal<br>
      <a href="https://filldesigngroup.com/">Fill Design Group</a>
    </p>
  </body>
</html>
"""
    return text_body, html_body

def choose_subject(company):
    """
    Randomly selects and personalizes a subject line with the company name.
    """
    subject_templates = [
        "Question for {Company}",
        "See this for {Company}",
        "Quick Question for {Company}"
    ]
    template = random.choice(subject_templates)
    return template.format(Company=company)

def check_reply(recipient_email):
    """
    Placeholder for reply checking.
    In production, integrate with IMAP or a CRM to detect a reply.
    """
    return False

def send_followup(recipient_email, original_msg_id, person_name, company, followup_number,
                  sender_email, sender_password, smtp_server, smtp_port, original_subject):
    """
    Sends a follow-up email in the same thread.
    """
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Re: " + original_subject
    msg['In-Reply-To'] = original_msg_id
    msg['References'] = original_msg_id

    text_body, html_body = spin_email_template(person_name, company, is_followup=True, followup_number=followup_number)
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            print(f"Follow-up #{followup_number} sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending follow-up #{followup_number} to {recipient_email}: {e}")

def followup_scheduler(recipient_email, original_msg_id, person_name, company,
                       sender_email, sender_password, smtp_server, smtp_port, original_subject):
    """
    Waits for followup_delay seconds then sends follow-ups if no reply is detected.
    First follow-up after followup_delay seconds, second follow-up after another followup_delay.
    """
    print(f"Waiting {followup_delay} seconds for follow-up #1 for {recipient_email}")
    time.sleep(followup_delay)
    if not check_reply(recipient_email):
        send_followup(recipient_email, original_msg_id, person_name, company, 1,
                      sender_email, sender_password, smtp_server, smtp_port, original_subject)
    else:
        print(f"Reply received from {recipient_email}. No first follow-up sent.")
        return

    print(f"Waiting {followup_delay} seconds for follow-up #2 for {recipient_email}")
    time.sleep(followup_delay)
    if not check_reply(recipient_email):
        send_followup(recipient_email, original_msg_id, person_name, company, 2,
                      sender_email, sender_password, smtp_server, smtp_port, original_subject)
    else:
        print(f"Reply received from {recipient_email}. No second follow-up sent.")



def send_initial_email(row, sender_email, sender_password, smtp_server, smtp_port):
    """
    Sends the initial email and returns the Message-ID and subject.
    """
    company = row['company']
    person_name = row['name']
    recipient_email = row['email']
    subject = choose_subject(company)
    text_body, html_body = spin_email_template(person_name, company)
    
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg_id = email.utils.make_msgid()
    msg['Message-ID'] = msg_id
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            print(f"Initial email sent to {recipient_email} from {sender_email}")
    except Exception as e:
        print(f"Error sending initial email to {recipient_email} from {sender_email}: {e}")
        return None, None
    return msg_id, subject

SENDER_OPTIONS = [
    {
        "sender_email": "neal@filldesigngroup.net",
        "sender_password": "Fdg@9874#",
        "smtp_server": "smtp.office365.com",
        "smtp_port": 587
    },
    {
        "sender_email": "neal@filldesignprojects.com",
        "sender_password": "Fdg@9874#",
        "smtp_server": "smtp.office365.com",
        "smtp_port": 587
    }
]

def send_emails(csv_path):
    try:
        with open(csv_path, newline='', encoding='cp1252') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                company = row['company']
                person_name = row['name']
                recipient_email = row['email']
                print(f"Processing: Company: {company}, Name: {person_name}, Email: {recipient_email}")
                
                # Randomly choose one sender option from SENDER_OPTIONS.
                sender_option = random.choice(SENDER_OPTIONS)
                sender_email = sender_option["sender_email"]
                sender_password = sender_option["sender_password"]
                smtp_server = sender_option["smtp_server"]
                smtp_port = sender_option["smtp_port"]
                
                msg_id, subject = send_initial_email(row, sender_email, sender_password, smtp_server, smtp_port)
                if msg_id is None:
                    continue
                
                # Start a thread to schedule follow-ups for this recipient.
                threading.Thread(
                    target=followup_scheduler,
                    args=(recipient_email, msg_id, person_name, company,
                          sender_email, sender_password, smtp_server, smtp_port, subject)
                ).start()
                
                # Delay between sending initial emails
                time.sleep(60)
                
    except FileNotFoundError:
        print("Error: CSV file not found. Please check the file path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Path to your CSV file with headers: company, name, email
csv_path = "test Email.csv"

send_emails(csv_path)

