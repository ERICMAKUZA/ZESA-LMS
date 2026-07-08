from django.core.management.base import BaseCommand

from apps.courses.models import Course, CourseSchedule

# Source: Official ZNTC Training Calendar (COURSES.pdf)
# (shortname, month, week_in_month)
SCHEDULE_2026 = [
    # JANUARY
    ("ARC-WELD",      1, 1), ("SOLAR-PV",     1, 1), ("CLIENT-CARE",  1, 1),
    ("LSMAN1",        1, 1), ("33KV-SWITCH",  1, 1),
    ("CABLE-XPLE",    1, 2),
    ("SUB-MAINT",     1, 3), ("VFD-SS",       1, 3), ("WORKERS-COM",  1, 3),
    ("OHS-PS",        1, 3), ("TRANSPORT",    1, 3),
    ("PSP1",          1, 4), ("ISO-50001",    1, 4), ("PRINCE2",      1, 4),
    ("INVENTORY",     1, 4), ("INT-CTRL",     1, 4), ("LSMAN2",       1, 4),
    # FEBRUARY
    ("PSP1",          2, 1), ("SUB-MAINT",    2, 2), ("LSMAN2",       2, 2),
    ("CORP-GOV-MGR",  2, 3), ("LABOUR-LAW",   2, 3), ("VFL",          2, 3),
    ("PRE-RET",       2, 3), ("ISO-31000",    2, 3), ("IRBM",         2, 3),
    ("MIN-WRITE",     2, 3), ("CABLE-XPLE",   2, 3), ("DIST-PLAN",    2, 3),
    ("CONCRETE",      2, 3), ("CIVIL-CONT",   2, 3),
    # MARCH
    ("LSMAN2",        3, 1), ("WORKERS-COM",  3, 2),
    ("CIVIL-NCE",     3, 3), ("33KV-SWITCH",  3, 3), ("RPA-DRONE",    3, 3),
    ("PSP1",          3, 4), ("PUMP-TECH",    3, 4), ("CONCRETE",     3, 4),
    ("CORP-GOV-ETH",  3, 4), ("FIN-REP",      3, 4), ("LSMAN1",       3, 4),
    ("DOM-INST",      3, 4), ("LOAD-FCST",    3, 4), ("SOLAR-PV",     3, 4),
    ("EMP-REL",       3, 4), ("ESG",          3, 4), ("NSSA",         3, 4),
    ("VIB-ANLYS",     3, 4), ("ARC-WELD",     3, 4), ("CIVIL-TX",     3, 4),
    ("RIGGING",       3, 4), ("GRIEVANCE",    3, 4), ("PROJ-CM",      3, 4),
    ("VAT-TRAIN",     3, 4), ("ENERGY-EFF",   3, 4),
    # APRIL
    ("CIVIL-TX",      4, 1), ("SUB-MAINT",    4, 1), ("132KV-SWITCH", 4, 1),
    ("VIB-ANLYS",     4, 2), ("VFD-SS",       4, 2),
    ("LSMAN2",        4, 3), ("DOM-INST",     4, 3), ("RIGGING",      4, 3),
    ("SUST-ENG",      4, 3),
    ("SUB-MAINT",     4, 4), ("33KV-SWITCH",  4, 4),
    # MAY
    ("VALVE-TECH",    5, 1),
    ("LL-MAINT",      5, 2),
    ("LSMAN1",        5, 3), ("DOM-INST",     5, 3),
    ("DIG-PWR",       5, 4), ("CABLE-XPLE",   5, 4), ("CONCRETE",     5, 4),
    ("PS-COMM",       5, 4), ("METERING",     5, 4), ("RIGGING",      5, 4),
    ("MINIGRID",      5, 4), ("ENG-PM",       5, 4),
    # JUNE
    ("ARC-WELD",      6, 1), ("CIVIL-NCE",    6, 1),
    ("LSMAN2",        6, 2),
    ("PUMP-TECH",     6, 3), ("TIG-MIG",      6, 3), ("CONCRETE",     6, 3),
    ("ENG-PM",        6, 4), ("CABLE-XPLE",   6, 4), ("DOM-INST",     6, 4),
    # JULY
    ("SUB-MAINT",     7, 1), ("33KV-SWITCH",  7, 1), ("LSMAN1",       7, 1),
    ("CABLE-XPLE",    7, 2), ("PSP1",         7, 2), ("CIVIL-NCE",    7, 2),
    ("SUB-MAINT",     7, 3), ("CIVIL-TX",     7, 3), ("RPA-DRONE",    7, 3),
    ("VFD-SS",        7, 4), ("SOLAR-PV",     7, 4), ("ENERGY-EFF",   7, 4),
    ("33KV-SWITCH",   7, 4),
    # AUGUST
    ("SUB-MAINT",     8, 1), ("LSMAN2",       8, 1),
    ("HYDRAULICS",    8, 2),
    ("DOM-INST",      8, 3), ("PSP2",         8, 3), ("PUMP-TECH",    8, 3),
    ("TIG-MIG",       8, 3),
    ("LOAD-FCST",     8, 4), ("PSP1",         8, 4), ("CONCRETE",     8, 4),
    ("CIVIL-CONT",    8, 4), ("SOLAR-PV",     8, 4),
    # SEPTEMBER
    ("PSP1",          9, 1), ("RIGGING",      9, 1),
    ("33KV-SWITCH",   9, 2), ("LSMAN1",       9, 2), ("CIVIL-NCE",    9, 2),
    ("SOLAR-PV",      9, 3), ("LOAD-FCST",    9, 3),
    ("EE-AUDIT",      9, 4),
    # OCTOBER
    ("PSP1",         10, 1), ("RIGGING",     10, 1), ("CIVIL-TX",    10, 1),
    ("SUB-MAINT",    10, 2), ("ARC-WELD",    10, 2),
    ("DOM-INST",     10, 3), ("VFD-SS",      10, 3),
    ("132KV-SWITCH", 10, 4), ("LSMAN1",      10, 4), ("LSMAN2",      10, 4),
    ("SUST-ENG",     10, 4), ("CIVIL-NCE",   10, 4),
    # NOVEMBER
    ("33KV-SWITCH",  11, 1), ("SOLAR-PV",    11, 1),
    ("CORP-GOV-ETH", 11, 2), ("FIN-REP",     11, 2),
    ("LSMAN1",       11, 3), ("DOM-INST",    11, 3), ("HYDRAULICS",  11, 3),
    ("LSMAN2",       11, 4),
    # DECEMBER
    ("METERING",     12, 1), ("SUB-MAINT",   12, 1),
    ("CABLE-XPLE",   12, 2), ("LSMAN2",      12, 2),
    ("CIVIL-CONT",   12, 3), ("PS-COMM",     12, 3),
]


class Command(BaseCommand):
    help = "Seed 2026 course schedule from the official ZNTC training calendar"

    def add_arguments(self, parser):
        parser.add_argument(
            '--year', type=int, default=2026,
            help='Year for the schedule (default: 2026)',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete existing schedules for the year before seeding',
        )

    def handle(self, *args, **options):
        year = options['year']
        if options['clear']:
            deleted, _ = CourseSchedule.objects.filter(year=year).delete()
            self.stdout.write(f"Cleared {deleted} existing {year} schedules.")

        created = skipped = missing = 0
        for shortname, month, week in SCHEDULE_2026:
            try:
                course = Course.objects.get(shortname=shortname)
            except Course.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Course not found: {shortname}"))
                missing += 1
                continue

            obj, was_created = CourseSchedule.objects.get_or_create(
                course=course, year=year, month=month, week_in_month=week,
                defaults={'max_capacity': course.max_capacity or 20, 'status': 'OPEN'},
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created: {created}  |  Already existed: {skipped}  "
            f"|  Missing courses: {missing}"
        ))
