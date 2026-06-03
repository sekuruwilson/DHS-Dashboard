from django.core.management.base import BaseCommand
from indicators.models import Category, Indicator

class Command(BaseCommand):
    help = 'Load sample RDHS data'

    def handle(self, *args, **options):
        # Create Category
        cat1, created = Category.objects.get_or_create(name="Chapter 1: Household characteristics")
        
        data_samples = [
            {
                "indicator": "Handwashing Facilities",
                "unit": "Percentage (%)",
                "data": {
                    "Rwamagana": {"Observed, Fixed place": 13.6, "Observed, Mobile place": 62.1, "Total": 75.7},
                    "Nyagatare": {"Observed, Fixed place": 14.3, "Observed, Mobile place": 70.9, "Total": 85.2},
                    "Gatsibo": {"Observed, Fixed place": 8.9, "Observed, Mobile place": 77.0, "Total": 85.9},
                    "Kayonza": {"Observed, Fixed place": 14.0, "Observed, Mobile place": 77.4, "Total": 91.4},
                    "Kirehe": {"Observed, Fixed place": 20.8, "Observed, Mobile place": 77.3, "Total": 98.1},
                    "Ngoma": {"Observed, Fixed place": 11.5, "Observed, Mobile place": 86.8, "Total": 98.4},
                    "Bugesera": {"Observed, Fixed place": 7.7, "Observed, Mobile place": 67.2, "Total": 75.0},
                    "Eastern Province": {"Observed, Fixed place": 12.8393256941264, "Observed, Mobile place": 73.83860490333089, "Total": 86.6779305974573},
                    "Rwanda": {"Observed, Fixed place": 11.0064838589123, "Observed, Mobile place": 72.63615759716286, "Total": 83.64264145607517}
                }
            },
            {
                "indicator": "Computer",
                "unit": "Percentage (%)",
                "data": {
                    "Rwamagana": 6.4, "Nyagatare": 1.0, "Gatsibo": 1.3, "Kayonza": 1.6, "Kirehe": 1.9, "Ngoma": 2.2, "Bugesera": 4.5, "Eastern Province": 2.584606717049491, "Rwanda": 4.568355807256838
                }
            },
            {
                "indicator": "Electricity Access",
                "unit": "Percentage (%)",
                "data": {
                    "Rwamagana": 48.8, "Nyagatare": 36.4, "Gatsibo": 38.0, "Kayonza": 28.1, "Kirehe": 49.9, "Ngoma": 52.7, "Bugesera": 47.7, "Eastern Province": 42.48215923808324, "Rwanda": 45.74807693274696
                }
            },
            {
                "indicator": "Mobile Phone",
                "unit": "Percentage (%)",
                "data": {
                    "Rwamagana": 75.4, "Nyagatare": 78.2, "Gatsibo": 63.6, "Kayonza": 76.8, "Kirehe": 69.7, "Ngoma": 73.7, "Bugesera": 74.7, "Eastern Province": 73.01585745565653, "Rwanda": 71.00214835181721
                }
            },
            {
                "indicator": "Radio",
                "unit": "Percentage (%)",
                "data": {
                    "Rwamagana": 47.1, "Nyagatare": 34.8, "Gatsibo": 38.8, "Kayonza": 37.9, "Kirehe": 37.3, "Ngoma": 37.6, "Bugesera": 39.8, "Eastern Province": 38.90310248224673, "Rwanda": 40.363575627095024
                }
            },
            {
                "indicator": "Television",
                "unit": "Percentage (%)",
                "data": {
                    "Rwamagana": 17.3, "Nyagatare": 7.9, "Gatsibo": 9.0, "Kayonza": 11.0, "Kirehe": 5.7, "Ngoma": 11.0, "Bugesera": 16.1, "Eastern Province": 10.972476826968563, "Rwanda": 13.640096434003443
                }
            }
        ]

        for item in data_samples:
            Indicator.objects.update_or_create(
                name=item["indicator"],
                category=cat1,
                defaults={
                    "unit": item["unit"],
                    "data": item["data"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded indicator "{item["indicator"]}"'))
