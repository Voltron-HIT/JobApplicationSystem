ACCOUNT SID = AC8249feaaecc818aeb21b14a247ce55d9
AUTH TOKEN = fdb6a568e30826bc66bba1b57e2bb3cc
phone number = (620) 374-9698

compile group: "com.twilio.sdk", name: "twilio", version: "7.30.0"


import com.twilio.Twilio;
import com.twilio.rest.api.v2010.account.Message;
import com.twilio.type.PhoneNumber;

public class Example {
  // Find your Account Sid and Token at twilio.com/user/account
  public static final String ACCOUNT_SID = "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
  public static final String AUTH_TOKEN = "your_auth_token";

  public static void main(String[] args) {
    Twilio.init(ACCOUNT_SID, AUTH_TOKEN);

    Message message = Message.creator(new PhoneNumber("+15558675309"),
        new PhoneNumber("+15017250604"), 
        "This is the ship that made the Kessel Run in fourteen parsecs?").create();

    System.out.println(message.getSid());
  }
}