from django.contrib.auth.mixins import UserPassesTestMixin

class TeacherOrAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only teacher or admin users can access the view."""
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_admin or self.request.user.is_teacher)
