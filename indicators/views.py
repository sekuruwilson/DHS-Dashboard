from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Avg
from .models import Indicator, Category, District, Province, IndicatorValue
from django.contrib import messages
import json
from .insights import generate_insights
from .analytics import get_ranking_data, get_gap_analysis_data

import csv
import os
import requests
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_allowed_numbers(context_data, query):
    """Extract all valid numbers from query and context data, plus safe default list numbers."""
    allowed_floats = set()
    
    # Extract numbers (with commas removed) from context and query
    all_source_text = f"{context_data} {query}"
    source_nums = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', all_source_text)
    
    for num_str in source_nums:
        try:
            cleaned = num_str.replace(',', '')
            allowed_floats.add(float(cleaned))
        except ValueError:
            pass
            
    # Add safe defaults (0 to 10 for list item markers, and 100 for percentages)
    for safe in range(0, 11):
        allowed_floats.add(float(safe))
    allowed_floats.add(100.0)
    
    return allowed_floats

def verify_no_hallucinated_numbers(text, allowed_floats, is_streaming=False):
    """
    Checks if there are any completed numbers in the text that are not in allowed_floats.
    If is_streaming is True, we skip validating a number that is at the very end of the text
    to avoid false positives on incomplete numbers while they are being typed.
    Returns (is_ok, offending_number).
    """
    matches = list(re.finditer(r'\b\d+(?:,\d+)*(?:\.\d+)?\b(?!\d|\.|,)', text))
    text_len = len(text)
    
    for match in matches:
        if is_streaming and match.end() == text_len:
            continue
            
        num_str = match.group(0)
        try:
            val = float(num_str.replace(',', ''))
            if val not in allowed_floats:
                return False, val
        except ValueError:
            pass
            
    return True, None


def build_system_message(context_data=""):
    """Build the system message string with strict rules and few-shot examples to prevent hallucination."""
    msg = (
        "You are the RDHS AI Assistant for Rwanda's Demographic and Health Survey (RDHS) portal.\n"
        "Your ONLY source of truth is the DATA CONTEXT provided below. You must rely strictly and ONLY on the facts, numbers, and years listed in the DATA CONTEXT. Do not use any external knowledge about Rwanda DHS statistics or other external data.\n\n"
        "## ABSOLUTE CONSTRAINTS — NEITHER DEFLECT NOR VIOLATE:\n"
        "1. **Zero Hallucination of Numbers**: NEVER state any percentage, average, count, or year that is not explicitly present in the DATA CONTEXT below. Do NOT make up national averages or compare with other years/districts unless those exact numbers are present in the DATA CONTEXT.\n"
        "2. **No Speculation**: If the user asks 'why' a trend is happening or what the 'implications' are, you must state that the database only contains the raw statistics and does not explain the underlying causes or policy reasons. DO NOT make up reasons, hypotheses, or external factors (like internet cafes, mobile network coverage, etc.) unless they are literally written in the DATA CONTEXT.\n"
        "3. **Refuse Missing Data**: If the user asks for data, years, or categories that are not listed in the DATA CONTEXT, respond: \"This information is not available in our database.\" Do not guess or extrapolate.\n"
        "4. **No Extrapolations**: If you have data for 2022 and 2025, do NOT assume or state anything about 2023 or 2024.\n"
        "5. **Conciseness and Formatting**: Keep your answers concise, clear, and factual. Use Markdown tables or bullet lists to present the data if multiple data points are available, but do not add columns or rows that are not in the context.\n\n"
        "## FEW-SHOT EXAMPLES:\n\n"
        "### Example 1: Successful Data Match\n"
        "**Context:**\n"
        "District: Nyagatare\n"
        "Indicator: Computer Ownership\n"
        "Values:\n"
        "  - Year: 2022\n"
        "    Value: 1.0%\n"
        "    Label: Total\n"
        "  - Year: 2025\n"
        "    Value: 1.2%\n"
        "    Label: Total\n"
        "**User Query:** \"Tell me about computer ownership in Nyagatare\"\n"
        "**Response:** In Nyagatare, the computer ownership rate (Total) was 1.0% in 2022 and 1.2% in 2025. No other years are recorded in the database.\n\n"
        "### Example 2: User asks 'Why' (Speculation Prevention)\n"
        "**Context:**\n"
        "District: Nyagatare\n"
        "Indicator: Computer Ownership\n"
        "Values:\n"
        "  - Year: 2022\n"
        "    Value: 1.0%\n"
        "    Label: Total\n"
        "**User Query:** \"Why is computer ownership so low in Nyagatare?\"\n"
        "**Response:** In Nyagatare, the computer ownership rate was 1.0% in 2022. The database contains only the raw statistical records and does not provide qualitative information or explanations for why the ownership rate is at this level. Therefore, I cannot speculate on the underlying causes.\n\n"
        "### Example 3: Missing District / Missing Indicator\n"
        "**Context:**\n"
        "District matched: None\n"
        "Indicator matched: Computer Ownership\n"
        "Instructions: The user asked about 'Computer Ownership', but didn't specify a district. Ask them which district of Rwanda they are interested in.\n"
        "**User Query:** \"Show me the computer ownership rates\"\n"
        "**Response:** I can help you with computer ownership rates, but I need to know which district of Rwanda you are interested in. Could you please specify a district (for example, Nyagatare, Gasabo, Gicumbi, etc.)?\n"
    )
    if context_data:
        msg += f"\n\n## DATA CONTEXT (Your ONLY source of truth):\n{context_data}"
    else:
        msg += "\n\n## DATA CONTEXT:\nNo specific data was found in the database for this query."
    return msg


def stream_ai_response(request, query, context_data=""):
    """Generator that streams tokens from Hugging Face API via SSE with real-time verification and multi-turn history."""
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    # Load conversational history from session
    chat_history = request.session.get('chat_history', [])
    
    messages_payload = [
        {"role": "system", "content": build_system_message(context_data)}
    ]
    for msg in chat_history:
        messages_payload.append(msg)
    messages_payload.append({"role": "user", "content": query})
    
    payload = {
        "messages": messages_payload,
        "model": "moonshotai/Kimi-K2-Instruct",
        "max_tokens": 600,
        "stream": True
    }
    
    allowed_floats = get_allowed_numbers(context_data, query)
    accumulated_text = ""
    
    try:
        with requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=60) as resp:
            for line in resp.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        data_str = decoded[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk['choices'][0]['delta'].get('content', '')
                            if delta:
                                accumulated_text += delta
                                
                                # Real-time check on completed numbers (not followed by a digit, period, or comma)
                                is_ok, offending = verify_no_hallucinated_numbers(accumulated_text, allowed_floats, is_streaming=True)
                                if not is_ok:
                                    yield f"data: {json.dumps({'token': f' [Data verification failed: Hallucinated number {offending} detected]'})}\n\n"
                                    yield "data: [DONE]\n\n"
                                    return
                                
                                yield f"data: {json.dumps({'token': delta})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
            
            # Final check once stream is complete to validate the last number
            is_ok, offending = verify_no_hallucinated_numbers(accumulated_text, allowed_floats, is_streaming=False)
            if not is_ok:
                yield f"data: {json.dumps({'token': f' [Data verification failed: Hallucinated number {offending} detected]'})}\n\n"
                yield "data: [DONE]\n\n"
                return
                
            # Append successful response to conversation history in the session
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": accumulated_text})
            request.session['chat_history'] = chat_history[-10:] # rolling log of last 10 messages
            request.session.save()
            
    except Exception as e:
        yield f"data: {json.dumps({'token': f'(Error: {str(e)})', 'error': True})}\n\n"
    yield "data: [DONE]\n\n"


def indicator_list(request):
    categories = Category.objects.prefetch_related('indicators').all()
    all_indicators = Indicator.objects.all().order_by('name')
    
    # Calculate stats for the dashboard
    total_chapters = categories.count()
    total_indicators = all_indicators.count()
    total_values = IndicatorValue.objects.count()

    context = {
        'categories': categories,
        'all_indicators': all_indicators,
        'total_chapters': total_chapters,
        'total_indicators': total_indicators,
        'total_values': total_values,
    }
    return render(request, 'indicators/dashboard.html', context)



def indicator_detail(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    
    # Query unique years available (other Indicator records with the same name & category)
    other_indicators = Indicator.objects.filter(name=indicator.name, category=indicator.category).order_by('-year')
    available_years = [ind.year for ind in other_indicators]
    selected_year = indicator.year
    
    # Redirect if a different year was selected via query param
    selected_year_str = request.GET.get('year')
    if selected_year_str:
        try:
            target_year = int(selected_year_str)
            target_ind = other_indicators.filter(year=target_year).first()
            if target_ind and target_ind.pk != indicator.pk:
                # Preserve other query params when redirecting
                import urllib.parse
                params = request.GET.copy()
                if 'year' in params:
                    del params['year']
                query_string = urllib.parse.urlencode(params)
                url = reverse('indicator_detail', args=[target_ind.pk])
                if query_string:
                    url += f"?{query_string}"
                return redirect(url)
        except ValueError:
            pass
            
    # Provinces for filtering
    provinces = Province.objects.all().order_by('name')
    selected_province = request.GET.get('province', '')
    
    # Labels for filtering
    all_values = indicator.values.all().select_related('district')
    available_labels = list(all_values.values_list('data_label', flat=True).distinct())
    selected_label = request.GET.get('label', '')
        
    # Apply filters
    values = all_values
    if selected_province:
        values = values.filter(district__province_id=selected_province)
    if selected_label:
        values = values.filter(data_label=selected_label)
    
    labels = []
    datasets_map = {} # label -> [values]
    
    # Process values into labels and datasets
    for val in values:
        if val.district.name not in labels:
            labels.append(val.district.name)
            
    # Ensure all districts are present in labels if they have data
    for val in values:
        if val.data_label not in datasets_map:
            datasets_map[val.data_label] = [0] * len(labels)
        
        dist_index = labels.index(val.district.name)
        datasets_map[val.data_label][dist_index] = val.value

    datasets = []
    for label, data_points in datasets_map.items():
        datasets.append({
            'label': label,
            'data': data_points,
            'borderWidth': 1
        })

    context = {
        'indicator': indicator,
        'labels': labels,
        'datasets': datasets,
        'raw_values': values,
        'available_years': available_years,
        'selected_year': selected_year,
        'provinces': provinces,
        'selected_province': selected_province,
        'available_labels': available_labels,
        'selected_label': selected_label,
    }
    return render(request, 'indicators/detail.html', context)



def chatbot_query(request):
    if request.method != 'POST':
        return redirect('indicator_list')
    
    query = request.POST.get('message', '').strip()
    if not query:
        return render(request, 'indicators/partials/chatbot_response.html', {'response': "Please ask a question!"})

    query_lower = query.lower()
    greetings = ['hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening']
    questions = ['how are you', "how's it going", 'how do you do']
    reset_words = ['clear', 'reset', 'start over', 'new conversation', 'new topic']

    # --- Initialize Context String & Reset session if needed ---
    data_context = ""

    if any(reset in query_lower for reset in reset_words) or (any(greet in query_lower for greet in greetings) and len(query_lower.split()) < 4):
        request.session['chat_history'] = []
        request.session['last_district_id'] = None
        request.session['last_indicator_id'] = None
        request.session.modified = True
        
        if any(greet in query_lower for greet in greetings):
            data_context = "User said hello. Respond with a welcoming message as the RDHS Assistant."
        else:
            data_context = "Conversation history has been reset. Tell the user you have cleared the chat history and are ready for a new topic."
    
    elif any(q in query_lower for q in questions):
        data_context = "User asked how you are. Respond that you are ready to help with health data."

    # 2. Handle Aggregate Statistics (New)
    elif any(q in query_lower for q in ['how many indicators', 'total indicators', 'number of indicators', 'active indicators']):
        count = Indicator.objects.count()
        data_context = f"There are exactly {count} indicators in the system."
    
    elif any(q in query_lower for q in ['how many chapters', 'total chapters', 'number of chapters', 'how many categories']):
        count = Category.objects.count()
        data_context = f"The dataset is organized into {count} chapters/categories."
    
    elif any(q in query_lower for q in ['how many districts', 'total districts', 'number of districts']):
        count = District.objects.count()
        data_context = f"The portal covers all {count} districts of Rwanda."
    
    elif any(q in query_lower for q in ['how many data points', 'total values', 'total data points', 'number of records']):
        count = IndicatorValue.objects.count()
        data_context = f"There are {count:,} individual data values stored."

    else:
        # 3. Advanced Data Context Extraction (Districts and Indicators)
        districts = District.objects.all()
        indicators = Indicator.objects.all().select_related('category')
        
        # Pre-clean query
        clean_query = query.lower().replace('?', '').replace('.', '').replace(',', '')
        query_words = set(clean_query.split())

        # Find District
        found_district = None
        for d in districts:
            if d.name.lower() in clean_query:
                found_district = d
                break
                
        # Find Indicator with Scoring
        synonyms = {
            "mobile phone": ["cell", "telephone", "gsm"],
            "computer": ["laptop", "pc", "desktop"],
            "handwashing": ["soap", "hygiene", "sanitation"],
            "electricity": ["power", "utility", "grid"],
            "insurance": ["medical", "mutuelle", "coverage"],
            "household": ["family", "residents"]
        }
        
        indicator_scores = []
        for i in indicators:
            score = 0
            name_lower = i.name.lower()
            if name_lower in clean_query: score += 100
            indicator_words = set(name_lower.split())
            overlap = query_words.intersection(indicator_words)
            for word in overlap: score += len(word) * 10 
            for base_term, syn_list in synonyms.items():
                if base_term in name_lower:
                    syn_overlap = query_words.intersection(set(syn_list))
                    for s_word in syn_overlap: score += len(s_word) * 5
            if score > 0: indicator_scores.append((score, i))
                
        indicator_scores.sort(key=lambda x: x[0], reverse=True)
        found_indicator = indicator_scores[0][1] if indicator_scores else None
                
        # --- Context Fallback / Slot Filling via Session memory ---
        if found_district:
            request.session['last_district_id'] = found_district.id
        else:
            last_district_id = request.session.get('last_district_id')
            if last_district_id:
                found_district = District.objects.filter(id=last_district_id).first()

        if found_indicator:
            request.session['last_indicator_id'] = found_indicator.id
        else:
            last_indicator_id = request.session.get('last_indicator_id')
            if last_indicator_id:
                found_indicator = Indicator.objects.filter(id=last_indicator_id).first()
                
        request.session.modified = True

        if found_district and found_indicator:
            # Query all indicators with the same name (covers all years) to get full trend data
            indicators_all_years = Indicator.objects.filter(name=found_indicator.name, category=found_indicator.category)
            all_values = IndicatorValue.objects.filter(indicator__in=indicators_all_years, district=found_district).select_related('indicator')
            if all_values.exists():
                context_lines = [
                    f"District: {found_district.name}",
                    f"Indicator: {found_indicator.name}",
                    "Values:"
                ]
                for v in all_values:
                    year = v.year or v.indicator.year
                    context_lines.append(f"  - Year: {year}")
                    context_lines.append(f"    Value: {v.value}%")
                    context_lines.append(f"    Label: {v.data_label}")
                data_context = "\n".join(context_lines)
            else:
                data_context = (
                    f"District matched: {found_district.name}\n"
                    f"Indicator matched: {found_indicator.name}\n"
                    f"Values: None\n"
                    f"Instructions: The district and indicator were identified, but no specific numbers were found in the database."
                )
        elif found_district:
            data_context = (
                f"District matched: {found_district.name}\n"
                f"Indicator matched: None\n"
                f"Instructions: The user asked about {found_district.name} but didn't specify a clear indicator. Ask them which indicator or metric they need."
            )
        elif found_indicator:
            data_context = (
                f"District matched: None\n"
                f"Indicator matched: {found_indicator.name}\n"
                f"Instructions: The user asked about '{found_indicator.name}' but didn't specify a district. Ask them which district of Rwanda they are interested in."
            )
        else:
            data_context = (
                f"District matched: None\n"
                f"Indicator matched: None\n"
                f"Instructions: No specific district or indicator was matched in the database. Provide a general helpful response about the RDHS portal and ask them to specify a district and/or health/demographic metric."
            )

    # --- Return streaming placeholder (JS will connect to SSE stream) ---
    from urllib.parse import quote
    stream_url = f"/chatbot/stream/?q={quote(query)}&ctx={quote(data_context)}"
    return render(request, 'indicators/partials/chatbot_response.html', {'stream_url': stream_url})


def stream_chatbot_response(request):
    """SSE endpoint: streams AI tokens to the browser as they arrive."""
    from django.http import StreamingHttpResponse
    query = request.GET.get('q', '')
    context_data = request.GET.get('ctx', '')
    
    response = StreamingHttpResponse(
        stream_ai_response(request, query, context_data),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

def about_rdhs(request):
    # Renders the RDHS Information page with dynamic national stats
    
    # Calculate National averages for specific indicators
    # These are usually stored under a 'Rwanda' district or national aggregate in RDHS
    # If not specifically found as 'Rwanda', we calculate the mean of all districts
    
    def get_national_avg(indicator_name):
        try:
            # First try to find the 'Rwanda' total entry if it exists
            rwanda_val = IndicatorValue.objects.filter(
                indicator__name__icontains=indicator_name,
                district__name="Rwanda",
                data_label="Total"
            ).first()
            
            if rwanda_val:
                return f"{rwanda_val.value}%"
            
            # Fallback: Calculate mean of all districts for that indicator
            avg = IndicatorValue.objects.filter(
                indicator__name__icontains=indicator_name,
                data_label="Total"
            ).aggregate(Avg('value'))['value__avg']
            
            if avg is not None:
                return f"{round(avg, 1)}%"
            return "N/A"
        except Exception:
            return "N/A"

    context = {
        'national_computer': get_national_avg("Computer"),
        'national_handwashing': get_national_avg("Handwashing"),
        'national_hsize': "4.3", # National estimate
    }
    
    return render(request, 'indicators/about.html', context)

def indicator_insights(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    
    # Query unique years available for this indicator's data
    available_years = sorted(list(set(indicator.values.values_list('year', flat=True))), reverse=True)
    default_year = available_years[0] if available_years else 2022
    selected_year_str = request.GET.get('year')
    try:
        selected_year = int(selected_year_str) if selected_year_str else default_year
    except ValueError:
        selected_year = default_year
        
    values = indicator.values.filter(year=selected_year).select_related('district')
    
    insights = generate_insights(indicator, values)
    
    return render(request, 'indicators/partials/insights.html', {
        'insights': insights,
        'indicator': indicator
    })

def export_indicator_csv(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    values = indicator.values.all().select_related('district').order_by('-year', 'district__name')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{indicator.name.replace(" ", "_")}_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['District', 'Label', 'Year', 'Value', 'Unit'])
    
    for val in values:
        writer.writerow([val.district.name, val.data_label, val.year, val.value, indicator.unit])
    
    return response

def advanced_analytics(request):
    indicators = Indicator.objects.all().order_by('name')
    indicator_id = request.GET.get('indicator')
    indicator2_id = request.GET.get('indicator2')
    analysis_type = request.GET.get('type', 'ranking') # ranking, gap, or correlation
    year_str = request.GET.get('year')
    
    available_years = []
    selected_year = None
    
    if indicator_id:
        available_years = sorted(list(set(IndicatorValue.objects.filter(indicator_id=indicator_id).values_list('year', flat=True))), reverse=True)
        if available_years:
            try:
                selected_year = int(year_str) if year_str else available_years[0]
            except ValueError:
                selected_year = available_years[0]

    context = {
        'indicators': indicators,
        'analysis_type': analysis_type,
        'available_years': available_years,
        'selected_year': selected_year,
    }
    
    if analysis_type == 'correlation' and indicator_id and indicator2_id:
        from .analytics import get_correlation_data
        results = get_correlation_data(indicator_id, indicator2_id, year=selected_year)
        context.update({
            'indicator': results.get('ind1'),
            'indicator2': results.get('ind2'),
            'data_json': json.dumps(results.get('data', [])),
            'insight': results.get('insight'),
            'correlation': results.get('correlation'),
            'selected_year': results.get('year'),
        })

    elif indicator_id:
        if analysis_type == 'gap':
            results = get_gap_analysis_data(indicator_id, year=selected_year)
        else:
            label = request.GET.get('label', 'Total')
            results = get_ranking_data(indicator_id, label, year=selected_year)
            context['active_label'] = results.get('label', 'Total')
            
        context.update({
            'indicator': results.get('indicator'),
            'analysis_data': results.get('data', []),
            'data_json': json.dumps(results.get('data', [])),
            'insight': results.get('insight'),
            'average': results.get('average'),
            'error': results.get('error'),
            'labels': results.get('labels'), # for gap analysis
            'selected_year': results.get('year'),
        })
        
    return render(request, 'indicators/analytics.html', context)

def public_settings(request):
    """Renders the public settings page where users configure their preferences."""
    provinces = Province.objects.all().order_by('name')
    return render(request, 'indicators/settings.html', {'provinces': provinces})
