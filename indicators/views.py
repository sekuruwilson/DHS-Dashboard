from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.urls import reverse
from django.db.models import Avg
from .models import Indicator, Category, District, Province, IndicatorValue
from .forms import SingleIndicatorDataForm, IndicatorJSONUploadForm
from django.contrib import messages
import json, csv, os, re, requests
from .insights import generate_insights
from .analytics import get_ranking_data, get_gap_analysis_data
from dotenv import load_dotenv
from urllib.parse import quote

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

def get_ai_response(query, context_data="", request=None):
    """Consult the Hugging Face AI for a response (non-streaming fallback)."""
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    system_message = build_system_message(context_data)
    
    # Load conversational history from session if request is provided
    chat_history = []
    if request is not None:
        chat_history = request.session.get('chat_history', [])

    messages_payload = [
        {"role": "system", "content": system_message}
    ]
    for msg in chat_history:
        messages_payload.append(msg)
    messages_payload.append({"role": "user", "content": query})

    payload = {
        "messages": messages_payload,
        "model": "moonshotai/Kimi-K2-Instruct",
        "max_tokens": 600
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        if "choices" in result:
            ans = result["choices"][0]["message"]["content"].strip()
            allowed = get_allowed_numbers(context_data, query)
            is_ok, offending = verify_no_hallucinated_numbers(ans, allowed)
            if not is_ok:
                return f"Verification check triggered: An unauthorized data value ({offending}) was detected. Here is the verified database context:\n\n{context_data.strip()}"
            
            # Save history to session if request is provided
            if request is not None:
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": ans})
                request.session['chat_history'] = chat_history[-10:]
                request.session.save()
                
            return ans
        return f"I found this in our records:\n\n{context_data}"
    except Exception as e:
        return f"I found this in our records:\n\n{context_data}\n\n(AI module offline: {str(e)})"


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


def stream_ai_response(request, query, context_data="", mode="chatbot"):
    """Generator that streams tokens from Hugging Face API via SSE.
    mode='chatbot'  → strict hallucination checks (for chatbot widget)
    mode='analytics' → interpretation mode (for analytics insights panel)
    """
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
        "Content-Type": "application/json"
    }

    if mode == 'analytics':
        system_msg = (
            "You are a public health data analyst interpreting Rwanda DHS 2019/2020 survey results "
            "for the Eastern Province.\n"
            "You will be given exact district-level data. Your job is to:\n"
            "1. Summarise the key findings clearly and concisely.\n"
            "2. Identify the highest and lowest performing districts.\n"
            "3. Note any significant disparities or patterns.\n"
            "4. Provide a brief public-health interpretation (1-2 sentences).\n"
            "Use Markdown formatting. Only reference numbers that appear in the data provided. "
            "Do NOT invent or extrapolate any figures.\n\n"
            f"DATA:\n{context_data}"
        )
        messages_payload = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": query}
        ]
    else:
        chat_history = request.session.get('chat_history', [])
        messages_payload = [{"role": "system", "content": build_system_message(context_data)}]
        for msg in chat_history:
            messages_payload.append(msg)
        messages_payload.append({"role": "user", "content": query})

    payload = {
        "messages": messages_payload,
        "model": "moonshotai/Kimi-K2-Instruct",
        "max_tokens": 700,
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
                                # Only apply number verification in chatbot mode
                                if mode == 'chatbot':
                                    is_ok, offending = verify_no_hallucinated_numbers(accumulated_text, allowed_floats, is_streaming=True)
                                    if not is_ok:
                                        yield f"data: {json.dumps({'token': f' [Verification failed: unexpected value {offending}]'})}\n\n"
                                        yield "data: [DONE]\n\n"
                                        return
                                yield f"data: {json.dumps({'token': delta})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            if mode == 'chatbot':
                is_ok, offending = verify_no_hallucinated_numbers(accumulated_text, allowed_floats, is_streaming=False)
                if not is_ok:
                    yield f"data: {json.dumps({'token': f' [Verification failed: unexpected value {offending}]'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                chat_history = request.session.get('chat_history', [])
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": accumulated_text})
                request.session['chat_history'] = chat_history[-10:]
                request.session.save()

    except Exception as e:
        yield f"data: {json.dumps({'token': f'(Error: {str(e)})', 'error': True})}\n\n"
    yield "data: [DONE]\n\n"


def indicator_list(request):
    categories = Category.objects.prefetch_related('indicators').all().order_by('name')
    all_years = sorted(Indicator.objects.values_list('year', flat=True).distinct(), reverse=True)
    selected_year = request.GET.get('year')
    try:
        selected_year = int(selected_year) if selected_year else all_years[0]
    except (ValueError, IndexError):
        selected_year = all_years[0] if all_years else 2020

    # Prefetch only indicators for the selected year
    from django.db.models import Prefetch
    year_indicators = Prefetch(
        'indicators',
        queryset=Indicator.objects.filter(year=selected_year),
        to_attr='year_indicators'
    )
    categories = categories.prefetch_related(year_indicators)

    context = {
        'categories': categories,
        'all_years': all_years,
        'selected_year': selected_year,
        'total_chapters': categories.count(),
        'total_indicators': Indicator.objects.filter(year=selected_year).count(),
        'total_values': IndicatorValue.objects.filter(year=selected_year).count(),
    }
    return render(request, 'indicators/dashboard.html', context)



# District display order: districts first, then province, then national
DISTRICT_ORDER = ['Rwamagana','Nyagatare','Gatsibo','Kayonza','Kirehe','Ngoma','Bugesera','Eastern Province','Rwanda']

def _sort_key(name):
    try:
        return DISTRICT_ORDER.index(name)
    except ValueError:
        return 99

def indicator_detail(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)

    # All years available for this indicator (same name + category)
    all_years = sorted(
        Indicator.objects.filter(name=indicator.name, category=indicator.category)
        .values_list('year', flat=True).distinct(), reverse=True
    )

    # Allow switching year via ?year=
    selected_year_str = request.GET.get('year')
    if selected_year_str:
        try:
            target_year = int(selected_year_str)
            target = Indicator.objects.filter(name=indicator.name, category=indicator.category, year=target_year).first()
            if target and target.pk != indicator.pk:
                return redirect(f"{reverse('indicator_detail', args=[target.pk])}")
        except ValueError:
            pass

    values = indicator.values.all().select_related('district').order_by('district__name')

    all_locations = list({v.district.name for v in values})
    all_locations.sort(key=_sort_key)

    datasets_map = {}
    for val in values:
        if val.data_label not in datasets_map:
            datasets_map[val.data_label] = {loc: None for loc in all_locations}
        datasets_map[val.data_label][val.district.name] = val.value

    datasets = []
    for label, loc_values in datasets_map.items():
        datasets.append({'label': label, 'data': [loc_values.get(loc) for loc in all_locations], 'borderWidth': 1})

    district_names = set(DISTRICT_ORDER[:7])
    district_values = [v for v in values if v.district.name in district_names]

    context = {
        'indicator': indicator,
        'labels': all_locations,
        'datasets': datasets,
        'raw_values': district_values,
        'all_years': all_years,
        'selected_year': indicator.year,
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

    # Store context in session, pass only a short key via URL
    import uuid
    ctx_key = str(uuid.uuid4())[:8]
    request.session[f'ctx_{ctx_key}'] = data_context
    request.session.modified = True
    stream_url = f"/chatbot/stream/?q={quote(query)}&ctx_key={ctx_key}"
    return render(request, 'indicators/partials/chatbot_response.html', {'stream_url': stream_url})


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def store_context(request):
    """Stores AI context in session, returns a short key. Used by analytics AI button."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    import uuid
    data = json.loads(request.body)
    ctx_key = str(uuid.uuid4())[:8]
    request.session[f'ctx_{ctx_key}'] = data.get('context', '')
    request.session.modified = True
    return JsonResponse({'key': ctx_key})


def stream_chatbot_response(request):
    """SSE endpoint: streams AI tokens to the browser as they arrive."""
    query = request.GET.get('q', '')
    ai_mode = request.GET.get('mode', 'chatbot')

    # Retrieve context — either from session key (chatbot) or direct ctx param (analytics)
    ctx_key = request.GET.get('ctx_key', '')
    if ctx_key:
        context_data = request.session.get(f'ctx_{ctx_key}', '')
    else:
        context_data = request.GET.get('ctx', '')

    response = StreamingHttpResponse(
        stream_ai_response(request, query, context_data, mode=ai_mode),
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
    categories = Category.objects.prefetch_related('indicators').all().order_by('name')
    all_years = sorted(Indicator.objects.values_list('year', flat=True).distinct(), reverse=True)
    indicators = Indicator.objects.all().order_by('name')

    indicator_id  = request.GET.get('indicator')
    district1_id  = request.GET.get('district1')
    district2_id  = request.GET.get('district2')
    compare_all   = request.GET.get('compare_all') == '1'

    # Year selection
    selected_year_str = request.GET.get('year')
    try:
        selected_year = int(selected_year_str) if selected_year_str else all_years[0]
    except (ValueError, IndexError):
        selected_year = 2020

    eastern_districts = District.objects.filter(province__name='Eastern Province').exclude(name='Eastern Province').order_by('name')

    context = {
        'categories': categories,
        'indicators': indicators,
        'eastern_districts': eastern_districts,
        'all_years': all_years,
        'year': selected_year,
    }

    if not indicator_id:
        return render(request, 'indicators/analytics.html', context)

    # Find the indicator for the selected year
    indicator = Indicator.objects.filter(pk=indicator_id).first()
    if not indicator:
        return render(request, 'indicators/analytics.html', context)

    # If a different year is selected, find matching indicator
    if indicator.year != selected_year:
        alt = Indicator.objects.filter(name=indicator.name, category=indicator.category, year=selected_year).first()
        if alt:
            indicator = alt

    values = indicator.values.filter(year=selected_year).select_related('district')
    available_labels = sorted(set(v.data_label for v in values))
    active_label = request.GET.get('label', available_labels[0] if available_labels else 'Total')

    if compare_all:
        district_names = ['Rwamagana','Nyagatare','Gatsibo','Kayonza','Kirehe','Ngoma','Bugesera']
        chart_values = [
            {'district': d, 'value': next((v.value for v in values if v.district.name == d and v.data_label == active_label), None)}
            for d in district_names
        ]
        chart_values = [x for x in chart_values if x['value'] is not None]
        vals_only = [x['value'] for x in chart_values]
        avg = round(sum(vals_only)/len(vals_only), 1) if vals_only else 0
        top = max(chart_values, key=lambda x: x['value'], default=None)
        bottom = min(chart_values, key=lambda x: x['value'], default=None)
        context.update({
            'indicator': indicator,
            'chart_data': chart_values,
            'compare_all': True,
            'active_label': active_label,
            'available_labels': available_labels,
            'average': avg,
            'top_district': top,
            'bottom_district': bottom,
        })

    elif district1_id and district2_id:
        d1 = get_object_or_404(District, pk=district1_id)
        d2 = get_object_or_404(District, pk=district2_id)
        d1_vals = {v.data_label: v.value for v in values if v.district_id == d1.id}
        d2_vals = {v.data_label: v.value for v in values if v.district_id == d2.id}
        all_labels = sorted(set(list(d1_vals.keys()) + list(d2_vals.keys())))
        chart_data = [{'label': lbl, 'd1': d1_vals.get(lbl), 'd2': d2_vals.get(lbl)} for lbl in all_labels]
        context.update({
            'indicator': indicator,
            'chart_data': chart_data,
            'compare_two': True,
            'district1': d1,
            'district2': d2,
            'active_label': active_label,
            'available_labels': available_labels,
        })

    else:
        district_names = ['Rwamagana','Nyagatare','Gatsibo','Kayonza','Kirehe','Ngoma','Bugesera','Eastern Province','Rwanda']
        chart_values = [
            {'district': d, 'value': next((v.value for v in values if v.district.name == d and v.data_label == active_label), None)}
            for d in district_names
        ]
        chart_values = [x for x in chart_values if x['value'] is not None]
        context.update({
            'indicator': indicator,
            'chart_data': chart_values,
            'active_label': active_label,
            'available_labels': available_labels,
        })

    return render(request, 'indicators/analytics.html', context)

def public_settings(request):
    """Renders the public settings page where users configure their preferences."""
    provinces = Province.objects.all().order_by('name')
    return render(request, 'indicators/settings.html', {'provinces': provinces})
