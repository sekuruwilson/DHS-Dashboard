from django.test import TestCase, Client
from django.urls import reverse
from indicators.models import Category, Province, District, Indicator, IndicatorValue
from indicators.views import (
    build_system_message,
    get_allowed_numbers,
    verify_no_hallucinated_numbers
)
import re

class ChatbotHallucinationTests(TestCase):
    def setUp(self):
        # Create category, province, district, indicator and values
        self.category = Category.objects.create(name="Chapter 1: Demographic and Socioeconomic Characteristics")
        self.province = Province.objects.create(name="Eastern Province")
        self.district = District.objects.create(name="Nyagatare", province=self.province)
        
        self.indicator = Indicator.objects.create(
            name="Computer Ownership",
            category=self.category,
            unit="%",
            year=2022
        )
        
        # 2022 Value
        self.val_2022 = IndicatorValue.objects.create(
            indicator=self.indicator,
            district=self.district,
            data_label="Total",
            year=2022,
            value=1.0
        )
        
        # 2025 Value
        self.val_2025 = IndicatorValue.objects.create(
            indicator=self.indicator,
            district=self.district,
            data_label="Total",
            year=2025,
            value=1.2
        )

    def test_get_allowed_numbers(self):
        context_data = "District: Nyagatare\nIndicator: Computer Ownership\nValues:\n  - Year: 2022\n    Value: 1.0%\n  - Year: 2025\n    Value: 1.2%"
        query = "Show me computer ownership in Nyagatare for 2022"
        
        allowed = get_allowed_numbers(context_data, query)
        
        # Verify years and data values are allowed
        self.assertIn(2022.0, allowed)
        self.assertIn(2025.0, allowed)
        self.assertIn(1.0, allowed)
        self.assertIn(1.2, allowed)
        
        # Verify list helper numbers and standard percentages are allowed
        self.assertIn(0.0, allowed)
        self.assertIn(5.0, allowed)
        self.assertIn(10.0, allowed)
        self.assertIn(100.0, allowed)
        
        # Verify an arbitrary non-present number is NOT allowed
        self.assertNotIn(15.0, allowed)
        self.assertNotIn(99.9, allowed)

    def test_verify_no_hallucinated_numbers(self):
        context_data = "District: Nyagatare\nIndicator: Computer Ownership\nValues:\n  - Year: 2022\n    Value: 1.0%\n  - Year: 2025\n    Value: 1.2%"
        query = "Show computer ownership in Nyagatare"
        allowed = get_allowed_numbers(context_data, query)
        
        # Safe response
        safe_response = "In Nyagatare, computer ownership was 1.0% in 2022 and 1.2% in 2025."
        is_ok, offending = verify_no_hallucinated_numbers(safe_response, allowed)
        self.assertTrue(is_ok)
        self.assertIsNone(offending)
        
        # Hallucinated response
        hallucinated_response = "In Nyagatare, computer ownership was 1.0% in 2022 and 1.2% in 2025. This is lower than the 15% national average."
        is_ok, offending = verify_no_hallucinated_numbers(hallucinated_response, allowed)
        self.assertFalse(is_ok)
        self.assertEqual(offending, 15.0)

    def test_system_prompt_contains_rules(self):
        msg = build_system_message("Test Context")
        self.assertIn("Your ONLY source of truth is the DATA CONTEXT provided below.", msg)
        self.assertIn("Zero Hallucination of Numbers", msg)
        self.assertIn("No Speculation", msg)
        self.assertIn("Refuse Missing Data", msg)
        self.assertIn("FEW-SHOT EXAMPLES", msg)
        self.assertIn("Test Context", msg)

    def test_chatbot_query_post_matching(self):
        client = Client()
        
        # Test full match (Nyagatare + Computer)
        response = client.post(reverse('chatbot_query'), {'message': 'Tell me about computer ownership in Nyagatare'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-stream-url')
        self.assertIn('stream', response.context['stream_url'])
        
        # Verify the context in the stream url
        stream_url = response.context['stream_url']
        self.assertIn('Nyagatare', stream_url)
        self.assertIn('Computer', stream_url)
        self.assertIn('1.0', stream_url)
        self.assertIn('1.2', stream_url)


class ChatbotConversationalMemoryTests(TestCase):
    def setUp(self):
        # Create category, province, district, indicator and values
        self.category = Category.objects.create(name="Chapter 1: Demographic and Socioeconomic Characteristics")
        self.province = Province.objects.create(name="Eastern Province")
        self.district = District.objects.create(name="Nyagatare", province=self.province)
        self.indicator = Indicator.objects.create(
            name="Computer Ownership",
            category=self.category,
            unit="%",
            year=2022
        )
        self.val_2022 = IndicatorValue.objects.create(
            indicator=self.indicator,
            district=self.district,
            data_label="Total",
            year=2022,
            value=1.0
        )

    def test_conversational_slot_filling_and_memory(self):
        client = Client()
        
        # Turn 1: Ask about computer ownership (without specifying a district)
        response1 = client.post(reverse('chatbot_query'), {'message': 'I want to know about computer ownership'})
        self.assertEqual(response1.status_code, 200)
        
        # Verify the session saved the indicator ID but no district ID yet
        self.assertEqual(client.session.get('last_indicator_id'), self.indicator.id)
        self.assertIsNone(client.session.get('last_district_id'))
        
        # Turn 2: Reply with the district (without specifying the indicator again)
        response2 = client.post(reverse('chatbot_query'), {'message': 'Nyagatare'})
        self.assertEqual(response2.status_code, 200)
        
        # Verify the session now has both the indicator ID and the district ID
        self.assertEqual(client.session.get('last_indicator_id'), self.indicator.id)
        self.assertEqual(client.session.get('last_district_id'), self.district.id)
        
        # Verify the generated stream URL context contains the values for both
        stream_url = response2.context['stream_url']
        self.assertIn('Nyagatare', stream_url)
        self.assertIn('Computer', stream_url)
        self.assertIn('1.0', stream_url)

    def test_reset_command(self):
        client = Client()
        
        # Set some initial session state
        session = client.session
        session['last_indicator_id'] = self.indicator.id
        session['last_district_id'] = self.district.id
        session['chat_history'] = [{'role': 'user', 'content': 'hello'}]
        session.save()
        
        # Send reset message
        response = client.post(reverse('chatbot_query'), {'message': 'reset'})
        self.assertEqual(response.status_code, 200)
        
        # Verify session state is completely cleared
        self.assertIsNone(client.session.get('last_indicator_id'))
        self.assertIsNone(client.session.get('last_district_id'))
        self.assertEqual(client.session.get('chat_history'), [])


from indicators.admin_views import resolve_district_by_name, save_indicators_from_json
import os
import tempfile
import json

class DHSComputationTests(TestCase):
    def setUp(self):
        # Setup province, districts, and categories matching resolved names
        self.province = Province.objects.create(name="Eastern Province")
        self.district = District.objects.create(name="Nyagatare", province=self.province)
        # In this dashboard database schema, province-level aggregates are stored as District objects
        self.prov_district = District.objects.create(name="Eastern Province", province=self.province)
        # Rwanda is a District object in the DB for national tracking
        self.national = District.objects.create(name="Rwanda", province=self.province) 
        self.category = Category.objects.create(name="Chapter 2: Respondent characteristics")

    def test_resolve_district_by_name(self):
        # Exact match
        self.assertEqual(resolve_district_by_name("Nyagatare"), self.district)
        
        # Mapped names
        self.assertEqual(resolve_district_by_name("East Province"), self.prov_district)
        self.assertEqual(resolve_district_by_name("Rwanda (National)"), self.national)
        self.assertEqual(resolve_district_by_name("National"), self.national)
        
        # Case insensitive and whitespace
        self.assertEqual(resolve_district_by_name("  nyagatare  "), self.district)

    def test_save_indicators_from_json(self):
        # Create a temporary JSON output file mimicking a notebook calculation output
        output_data = {
            "indicator": "Percentage of Children under 5 with Birth Certificate or Registered",
            "unit": "Percentage (%)",
            "figure": "Dummy figure info",
            "data": {
                "Nyagatare": 72.0,
                "East Province": 78.0,
                "Rwanda (National)": 82.0
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False, encoding="utf-8") as temp_f:
            json.dump(output_data, temp_f)
            temp_f_path = temp_f.name
            
        try:
            # Process the temporary JSON file
            count = save_indicators_from_json(temp_f_path, self.category, 2025)
            self.assertEqual(count, 3)
            
            # Check database objects created
            ind = Indicator.objects.filter(name="Percentage of Children under 5 with Birth Certificate or Registered", category=self.category, year=2025).first()
            self.assertIsNotNone(ind)
            self.assertEqual(ind.unit, "Percentage (%)")
            
            val_nyagatare = IndicatorValue.objects.filter(indicator=ind, district=self.district, year=2025).first()
            self.assertIsNotNone(val_nyagatare)
            self.assertEqual(val_nyagatare.value, 72.0)
            
            val_prov = IndicatorValue.objects.filter(indicator=ind, district=self.prov_district, year=2025).first()
            self.assertIsNotNone(val_prov)
            self.assertEqual(val_prov.value, 78.0)
            
            val_nat = IndicatorValue.objects.filter(indicator=ind, district=self.national, year=2025).first()
            self.assertIsNotNone(val_nat)
            self.assertEqual(val_nat.value, 82.0)
        finally:
            if os.path.exists(temp_f_path):
                os.remove(temp_f_path)
