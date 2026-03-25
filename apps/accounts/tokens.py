from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email verification that does NOT include last_login
    in the hash, so the token stays valid even after the user logs in/out.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.email_verified}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()
