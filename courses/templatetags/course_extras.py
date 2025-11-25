from django import template

register = template.Library()

@register.filter
def filter_active(enrollments):
    """
    Filter enrollments to only include active ones.
    """
    return [enrollment for enrollment in enrollments if enrollment.status == 'active']

@register.filter
def filter_completed(enrollments):
    """
    Filter enrollments to only include completed ones.
    """
    return [enrollment for enrollment in enrollments if enrollment.status == 'completed']

@register.filter
def filter_dropped(enrollments):
    """
    Filter enrollments to only include dropped ones.
    """
    return [enrollment for enrollment in enrollments if enrollment.status == 'dropped']

@register.filter
def filter_status(attendances, status):
    """
    Filter attendances by status.
    """
    return [attendance for attendance in attendances if attendance.status == status]
