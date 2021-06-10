import unittest

from email.mime.text import MIMEText

from fedflow.mail.send_mail import send_mail


class MailTestCase(unittest.TestCase):

    def test_send(self):
        message = MIMEText("Fedflow mail test", "plain", "utf-8")
        message["Subject"] = "TTTTT"
        self.assertTrue(send_mail(message))


if __name__ == '__main__':
    unittest.main()
