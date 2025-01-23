Communication using clear-text protocols allows an attacker to sniff or tamper with the transported data.

This codemod will replace any detected clear text protocol with their cryptographic enabled version.

Our changes look like the following:
```diff
- url = "http://example.com"
+ url = "https://example.com"

- ftp_con = ftplib.FTP("ftp.example.com")
+ ftp_con = ftplib.FTP_TLS("ftp.example.com")
+ smtp_context = ssl.create_default_context()
+ smtp_context.verify_mode = ssl.CERT_REQUIRED
+ smtp_context.check_hostname = True
smtp_con = smtplib.SMTP("smtp.example.com", port=587)
+ smtp.starttls(context=smtp_context)


+ smtp_context_1 = ssl.create_default_context()
+ smtp_context_1.verify_mode = ssl.CERT_REQUIRED
+ smtp_context_1.check_hostname = True
- smtp_con_2 = smtplib.SMTP("smtp.gmail.com")
+ smtp_con_2 = smtplib.SMTP_SSL("smtp.gmail.com", context=smtp_context_1)
```
