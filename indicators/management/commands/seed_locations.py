from django.core.management.base import BaseCommand
from indicators.models import Province, District

class Command(BaseCommand):
    help = 'Seeds all Rwanda provinces and districts including national and province-level aggregate locations'

    def handle(self, *args, **options):
        # 1. Define Provinces
        provinces_data = [
            "Kigali City",
            "Southern Province",
            "Western Province",
            "Northern Province",
            "Eastern Province",
            "National"
        ]

        provinces = {}
        for p_name in provinces_data:
            prov, created = Province.objects.get_or_create(name=p_name)
            provinces[p_name] = prov
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Province: "{p_name}"'))

        # 2. Define Districts grouped by Province
        districts_data = {
            "Kigali City": ["Nyarugenge", "Gasabo", "Kicukiro", "Kigali City"],
            "Southern Province": ["Nyanza", "Gisagara", "Nyaruguru", "Huye", "Ruhango", "Nyamagabe", "Kamonyi", "Muhanga", "Southern Province"],
            "Western Province": ["Karongi", "Rutsiro", "Rubavu", "Nyabihu", "Ngororero", "Rusizi", "Nyamasheke", "Western Province"],
            "Northern Province": ["Rulindo", "Gakenke", "Musanze", "Burera", "Gicumbi", "Northern Province"],
            "Eastern Province": ["Rwamagana", "Nyagatare", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Bugesera", "Eastern Province"],
            "National": ["Rwanda"]
        }

        total_created = 0
        for prov_name, dist_list in districts_data.items():
            province = provinces[prov_name]
            for dist_name in dist_list:
                district, created = District.objects.get_or_create(
                    name=dist_name,
                    province=province
                )
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created District: "{dist_name}" in {prov_name}'))

        self.stdout.write(self.style.SUCCESS(f'Seeding complete. Created {total_created} new districts.'))
