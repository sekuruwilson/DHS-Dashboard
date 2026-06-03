from django import template

register = template.Library()

@register.filter(name='chapter_name_only')
def chapter_name_only(value):
    """
    Extract only the chapter name without the 'Chapter X:' prefix.
    Example: 'Chapter 1: Household characteristics' -> 'Household characteristics'
    If no colon exists, returns the full value.
    """
    if ':' in str(value):
        return str(value).split(':', 1)[1].strip()
    return str(value)

@register.filter(name='chapter_icon')
def chapter_icon(value):
    """Maps a chapter name to a Bootstrap Icon class based on keywords."""
    name = str(value).lower()
    icon_map = [
        ('household',       'bi-house-heart-fill'),
        ('population',      'bi-people-fill'),
        ('fertility',       'bi-gender-female'),
        ('birth',           'bi-gender-female'),
        ('family planning', 'bi-heart-pulse-fill'),
        ('family',          'bi-heart-pulse-fill'),
        ('infant',          'bi-emoji-smile-fill'),
        ('child',           'bi-emoji-smile-fill'),
        ('mortality',       'bi-activity'),
        ('nutrition',       'bi-egg-fried'),
        ('malaria',         'bi-bug-fill'),
        ('hiv',             'bi-shield-plus'),
        ('aids',            'bi-shield-plus'),
        ('health',          'bi-heart-pulse-fill'),
        ('education',       'bi-book-fill'),
        ('literacy',        'bi-journal-text'),
        ('employment',      'bi-briefcase-fill'),
        ('work',            'bi-briefcase-fill'),
        ('water',           'bi-droplet-fill'),
        ('sanitation',      'bi-water'),
        ('housing',         'bi-building-fill'),
        ('wealth',          'bi-cash-coin'),
        ('economic',        'bi-cash-coin'),
        ('women',           'bi-gender-female'),
        ('gender',          'bi-gender-ambiguous'),
        ('disability',      'bi-accessibility'),
        ('environment',     'bi-tree-fill'),
        ('migration',       'bi-geo-alt-fill'),
        ('violence',        'bi-shield-exclamation'),
        ('maternal',        'bi-gender-female'),
    ]
    for keyword, icon in icon_map:
        if keyword in name:
            return icon
    return 'bi-bar-chart-fill'

@register.filter(name='indicator_icon')
def indicator_icon(value):
    """Maps an indicator name to a Bootstrap Icon class based on keywords."""
    name = str(value).lower()
    icon_map = [
        # Demography & population
        ('population',       'bi-people-fill'),
        ('household',        'bi-house-heart-fill'),
        ('migration',        'bi-geo-alt-fill'),
        ('birth',            'bi-gender-female'),
        ('fertility',        'bi-gender-female'),
        ('marriage',         'bi-heart-fill'),
        ('divorce',          'bi-heartbreak-fill'),
        ('age',              'bi-person-fill'),
        # Health
        ('mortality',        'bi-activity'),
        ('death',            'bi-activity'),
        ('malaria',          'bi-bug-fill'),
        ('hiv',              'bi-shield-plus'),
        ('aids',             'bi-shield-plus'),
        ('tuberculosis',     'bi-lungs-fill'),
        ('vaccine',          'bi-capsule-pill'),
        ('vaccination',      'bi-capsule-pill'),
        ('immunization',     'bi-capsule-pill'),
        ('antenatal',        'bi-gender-female'),
        ('maternal',         'bi-gender-female'),
        ('delivery',         'bi-gender-female'),
        ('skilled',          'bi-person-badge-fill'),
        ('nutrition',        'bi-egg-fried'),
        ('stunting',         'bi-graph-down'),
        ('wasting',          'bi-graph-down'),
        ('anaemia',          'bi-droplet-half'),
        ('anemia',           'bi-droplet-half'),
        ('breastfeed',       'bi-heart-pulse-fill'),
        ('diarrhoea',        'bi-droplet-fill'),
        ('diarrhea',         'bi-droplet-fill'),
        ('hospital',         'bi-hospital-fill'),
        ('health',           'bi-heart-pulse-fill'),
        ('contracepti',      'bi-shield-check'),
        ('family planning',  'bi-shield-check'),
        # Education
        ('school',           'bi-mortarboard-fill'),
        ('education',        'bi-book-fill'),
        ('literacy',         'bi-journal-text'),
        ('reading',          'bi-journal-text'),
        ('attendance',       'bi-person-check-fill'),
        ('dropout',          'bi-person-x-fill'),
        # Water & sanitation
        ('water',            'bi-droplet-fill'),
        ('sanitation',       'bi-water'),
        ('toilet',           'bi-water'),
        ('handwash',         'bi-hand-index-fill'),
        # Housing & assets
        ('electricity',      'bi-lightning-fill'),
        ('internet',         'bi-wifi'),
        ('phone',            'bi-phone-fill'),
        ('computer',         'bi-laptop-fill'),
        ('television',       'bi-tv-fill'),
        ('radio',            'bi-broadcast'),
        ('housing',          'bi-building-fill'),
        ('floor',            'bi-building-fill'),
        ('roof',             'bi-building-fill'),
        ('cooking',          'bi-fire'),
        # Economic
        ('wealth',           'bi-cash-coin'),
        ('income',           'bi-cash-coin'),
        ('employment',       'bi-briefcase-fill'),
        ('work',             'bi-briefcase-fill'),
        ('poverty',          'bi-graph-down-arrow'),
        # Gender & women
        ('women',            'bi-gender-female'),
        ('gender',           'bi-gender-ambiguous'),
        ('violence',         'bi-shield-exclamation'),
        ('disability',       'bi-accessibility'),
        # Environment
        ('environment',      'bi-tree-fill'),
        ('land',             'bi-map-fill'),
        ('agriculture',      'bi-flower1'),
    ]
    for keyword, icon in icon_map:
        if keyword in name:
            return icon
    return 'bi-bar-chart-fill'

@register.filter(name='indicator_values_to_dict')
def indicator_values_to_dict(values):
    """
    Converts a queryset of IndicatorValues into a dict indexed by district name.
    """
    return {v.district.name: v.value for v in values if v.data_label == 'Total'}
