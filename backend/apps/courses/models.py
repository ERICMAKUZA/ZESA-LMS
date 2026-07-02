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
