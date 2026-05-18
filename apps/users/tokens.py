from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

class ReactivationTokenGenerator(PasswordResetTokenGenerator):
    # Set timeout from Django settings (3600 seconds = 1 hour)
    def __init__(self):
        super().__init__()
        self.timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
    
    def _make_hash_value(self, user, timestamp):
        # Use date only (no microseconds) for deactivated_at to ensure stable hash
        deactivated_date = (
            user.deactivated_at.date() if user.deactivated_at else None
        )
        return (
            str(user.pk)
            + str(timestamp)
            + str(user.is_active)
            + str(deactivated_date)
        )

reactivation_token = ReactivationTokenGenerator()