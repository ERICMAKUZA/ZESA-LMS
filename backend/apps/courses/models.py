import uuid

from django.db import models


class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    moodle_id = models.IntegerField(unique=True)

    class Meta:
        verbose_name = "Course Category"
        verbose_name_plural = "Course Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL_BEGINNER = 'BEGINNER'
    LEVEL_INTERMEDIATE = 'INTERMEDIATE'
    LEVEL_ADVANCED = 'ADVANCED'
    LEVEL_ALL = 'ALL_LEVELS'
    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, 'Beginner'),
        (LEVEL_INTERMEDIATE, 'Intermediate'),
        (LEVEL_ADVANCED, 'Advanced'),
        (LEVEL_ALL, 'All Levels'),
    ]

    moodle_course_id = models.IntegerField(unique=True)
    shortname = models.CharField(max_length=255)
    fullname = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, null=True, blank=True
    )
    category = models.ForeignKey(
        CourseCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="courses",
    )
    enrolled_count = models.PositiveIntegerField(default=0)
    max_capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    thumbnail_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["fullname"]

    def __str__(self):
        return f"{self.shortname} – {self.fullname}"

    @property
    def is_full(self):
        return self.max_capacity is not None and self.enrolled_count >= self.max_capacity


class CourseSchedule(models.Model):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
    ]
    WEEK_CHOICES = [(1, 'Week 1'), (2, 'Week 2'), (3, 'Week 3'), (4, 'Week 4')]
    STATUS_CHOICES = [
        ('OPEN', 'Open — Accepting Applications'),
        ('FULL', 'Full'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='schedules'
    )
    year = models.PositiveIntegerField(default=2026)
    month = models.IntegerField(choices=MONTH_CHOICES)
    week_in_month = models.IntegerField(choices=WEEK_CHOICES)
    max_capacity = models.PositiveIntegerField(
        default=20,
        help_text="Override course default capacity for this specific intake",
    )
    enrolled_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='OPEN')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['year', 'month', 'week_in_month']
        unique_together = [['course', 'year', 'month', 'week_in_month']]

    def __str__(self):
        return (
            f"{self.course.shortname} — "
            f"{self.get_month_display()} Week {self.week_in_month} {self.year}"
        )

    @property
    def is_full(self):
        return self.enrolled_count >= self.max_capacity

    @property
    def places_remaining(self):
        return max(0, self.max_capacity - self.enrolled_count)

    def get_approximate_start_date(self):
        import datetime
        first = datetime.date(self.year, self.month, 1)
        days_until_monday = (7 - first.weekday()) % 7
        first_monday = first + datetime.timedelta(days=days_until_monday)
        return first_monday + datetime.timedelta(weeks=self.week_in_month - 1)

    def get_approximate_end_date(self):
        import datetime
        start = self.get_approximate_start_date()
        return start + datetime.timedelta(days=self.course.duration_days - 1)


class Enquiry(models.Model):
    ENQUIRY_TYPE_CHOICES = [
        ('GENERAL',     'General Information'),
        ('COURSE_INFO', 'Course Details & Requirements'),
        ('FEES',        'Fees & Payment'),
        ('ADMISSION',   'Admission & Application'),
        ('CORPORATE',   'Corporate / Group Booking'),
    ]
    STATUS_CHOICES = [
        ('NEW',         'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED',    'Resolved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    organisation = models.CharField(
        max_length=200, blank=True,
        help_text="Company or organisation name (for corporate enquiries)",
    )
    enquiry_type = models.CharField(
        max_length=15, choices=ENQUIRY_TYPE_CHOICES, default='GENERAL',
    )
    course = models.ForeignKey(
        'Course', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='enquiries',
        help_text="Specific course the enquiry relates to (optional)",
    )
    message = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='NEW')
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name_plural = 'Enquiries'

    def __str__(self):
        return f"{self.full_name} — {self.get_enquiry_type_display()} ({self.submitted_at.date()})"
