from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email verification.
    By not including `email_verified` in the hash, the token remains valid
    even after the email is verified, preventing errors on repeated clicks.
    The timestamp in the token ensures it still expires.
    """
    def _make_hash_value(self, user, timestamp):
        # The hash is made of stable user data.
        return f"{user.pk}{timestamp}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()
