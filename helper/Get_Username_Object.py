from accounts_app.models import User
import re
from typing import Tuple
import logging

email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class GetUserObject:
    def __init__(self):
        self.user=None
        self.logger=logging.getLogger('accounts_app')

    def get_user_object_from_mail(self,mail_provided):
        try:
            user=User.objects.get(mail=mail_provided)
        except Exception as e:
            print(type(e))
            self.logger.error(f"Email: {mail_provided} not exist as registerd email, the folowing exception was raised {e}")
            return None
        return user
    
    def get_user_from_form(self,form)->Tuple[str,str]:
        username_or_email = form.cleaned_data.get('username_or_email')
        print(f"---->{username_or_email}")
        password = form.cleaned_data.get('password')
        #Check if user Authenticated with email or username
        try:
            if re.match(email_regex,username_or_email):
                self.user=User.objects.get(mail=username_or_email)
            else:
                self.user=User.objects.get(username=username_or_email)
        except Exception as e:
            self.logger.error(f"User: {username_or_email} not exist as registerd email or username, the folowing exception was raised {e}")
            return None,None
        #Return username and password
        return self.user.username,password
