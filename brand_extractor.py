"""
Brand Intelligence Extractor Module
Handles: Comprehensive brand analysis with confidence scoring
"""

import re
from typing import Dict, List
from urllib.parse import urlparse
from datetime import datetime


class BrandIntelligenceExtractor:
    """
    Comprehensive Brand Intelligence Extraction System
    Features:
    - Expanded taxonomy (14 categories)
    - Product vs usage context separation
    - Multi-category support with confidence gating
    - Demographics inference from navigation
    - Pain point extraction from reviews
    - Confidence scores for all fields
    - Source tracking (navigation/reviews/inferred/explicit)
    """

    def __init__(self, text: str, nav_text: str = "", reviews_text: str = "", url: str = ""):
        self.text = text
        self.text_lower = text.lower()
        self.nav_text = nav_text
        self.nav_text_lower = nav_text.lower()
        self.reviews_text = reviews_text
        self.reviews_text_lower = reviews_text.lower()
        self.url = url
        self.domain = urlparse(url).netloc if url else ""

    def extract_brand_identity(self, brand_name: str) -> Dict:
        """Extract brand identity information"""
        return {
            'brand_name': brand_name,
            'product_names': self._extract_product_names(),
            'category_niche': self._detect_category_niche(),
            'market_position': self._detect_market_position(),
            'region_language': self._detect_region_language(),
        }

    def _extract_product_names(self) -> List[str]:
        """Extract product names from text"""
        product_patterns = [
            r'(?:our|the)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:is|are|provides|offers)',
            r'introducing\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)',
        ]
        products = set()
        for pattern in product_patterns:
            matches = re.findall(pattern, self.text)
            for match in matches[:10]:
                if 3 < len(match) < 50:
                    products.add(match.strip())
        return list(products)[:10]

    def _detect_category_niche(self) -> Dict:
        """
        Enhanced category detection with:
        - Expanded taxonomy (14 categories)
        - Product vs usage separation
        - Multi-category support
        - Confidence gating
        """
        # PRODUCT TYPE SIGNALS (from nav, titles, SKUs) - HIGHEST PRIORITY
        product_categories = {
            'fashion_apparel': ['clothing', 'apparel', 'fashion', 'wear', 'outfit', 'dress', 'shirt', 'pants', 'jacket'],
            'beauty_cosmetics': ['beauty', 'skincare', 'makeup', 'cosmetics', 'serum', 'cream', 'facial', 'lipstick'],
            'tech_electronics': ['technology', 'gadget', 'device', 'smart', 'digital', 'electronics', 'phone', 'laptop'],
            'food_beverage': ['food', 'beverage', 'drink', 'snack', 'meal', 'restaurant', 'cafe', 'coffee', 'tea'],
            'health_wellness': ['health', 'wellness', 'fitness', 'supplement', 'vitamin', 'workout', 'gym', 'yoga'],
            'home_decor': ['furniture', 'decor', 'interior', 'living', 'bedroom', 'kitchen', 'home'],
            'jewelry_watches': ['jewelry', 'watch', 'timepiece', 'ring', 'necklace', 'bracelet', 'diamond', 'gold'],
            'outdoor_gear': ['outdoor', 'camping', 'hiking', 'gear', 'adventure', 'trail', 'backpack', 'tent'],
            'travel_luggage': ['luggage', 'suitcase', 'travel', 'baggage', 'carry-on', 'backpack', 'duffel'],
            'lifestyle_consumer': ['lifestyle', 'everyday', 'essential', 'daily', 'modern', 'contemporary', 'lighter', 'zippo', 'smoking', 'accessories', 'collectible', 'gifts'],
            'premium_retail': ['luxury', 'premium', 'designer', 'high-end', 'exclusive', 'boutique'],
            'sports_athletic': ['sports', 'athletic', 'performance', 'training', 'activewear', 'running'],
            'baby_kids': ['baby', 'kids', 'children', 'infant', 'toddler', 'nursery'],
            'pet_supplies': ['pet', 'dog', 'cat', 'animal', 'veterinary'],
        }

        # USAGE CONTEXT SIGNALS (from body text) - LOWER PRIORITY
        usage_categories = {
            'food_beverage': ['delicious', 'taste', 'flavor', 'recipe', 'cooking', 'dining'],
            'outdoor_gear': ['nature', 'wilderness', 'mountain', 'explore', 'expedition'],
            'travel_luggage': ['journey', 'destination', 'airport', 'trip', 'vacation'],
        }

        # Score PRODUCT TYPE signals (higher weight)
        product_scores = {}
        for category, keywords in product_categories.items():
            # Check nav text first (highest signal)
            nav_score = sum(3 for kw in keywords if kw in self.nav_text_lower)  # 3x weight
            # Check main text
            text_score = sum(1 for kw in keywords if kw in self.text_lower)
            total = nav_score + text_score
            if total > 0:
                product_scores[category] = total

        # Score USAGE signals (lower weight)
        usage_scores = {}
        for category, keywords in usage_categories.items():
            score = sum(0.5 for kw in keywords if kw in self.text_lower)  # 0.5x weight
            if score > 0:
                usage_scores[category] = score

        # Combine scores - PRODUCT TYPE OVERRIDES USAGE
        final_scores = {}
        for cat, score in product_scores.items():
            final_scores[cat] = score
        for cat, score in usage_scores.items():
            if cat in final_scores:
                final_scores[cat] += score
            else:
                final_scores[cat] = score

        if not final_scores:
            return {
                'primary_category': 'general',
                'confidence': 0.1,
                'confidence_reason': 'No category signals detected',
                'secondary_categories': [],
                'all_scores': {},
                'source': 'default'
            }

        # Sort by score
        sorted_cats = sorted(final_scores.items(), key=lambda x: -x[1])
        primary_cat, primary_score = sorted_cats[0]

        # Calculate confidence (0-1 scale)
        confidence = min(primary_score / 10, 1.0)

        # CONFIDENCE GATING: Only assign primary if confidence >= 0.4
        if confidence < 0.4:
            return {
                'primary_category': 'multi_category_needs_review',
                'confidence': confidence,
                'confidence_reason': f'Low confidence ({confidence:.2f}), multiple possible categories',
                'secondary_categories': [cat for cat, score in sorted_cats[:3]],
                'all_scores': final_scores,
                'source': 'inferred_low_confidence'
            }

        # Get secondary categories
        secondary = [cat for cat, score in sorted_cats[1:4] if score >= primary_score * 0.5]

        # Determine source
        source = 'navigation' if primary_cat in product_scores and product_scores[primary_cat] >= 3 else 'content'

        return {
            'primary_category': primary_cat,
            'confidence': round(confidence, 2),
            'confidence_reason': f'Based on {len(final_scores)} keyword matches (source: {source})',
            'secondary_categories': secondary,
            'all_scores': final_scores,
            'source': source
        }

    def _detect_market_position(self) -> Dict:
        """Detect market positioning with confidence scores"""
        premium_signals = ['luxury', 'premium', 'exclusive', 'high-end', 'finest', 'prestigious', 'elite', 'superior', 'handcrafted', 'artisan']
        budget_signals = ['affordable', 'budget', 'cheap', 'value', 'economical', 'low-cost', 'discount', 'save', 'deal']

        premium_count = sum(1 for s in premium_signals if s in self.text_lower)
        budget_count = sum(1 for s in budget_signals if s in self.text_lower)

        if premium_count > budget_count * 1.5:
            confidence = min(premium_count / 5, 1.0)
            return {
                'position': 'premium',
                'confidence': round(confidence, 2),
                'confidence_reason': f'{premium_count} premium signals found',
                'premium_signals_found': premium_count,
                'budget_signals_found': budget_count,
                'source': 'explicit'
            }
        elif budget_count > premium_count * 1.5:
            confidence = min(budget_count / 5, 1.0)
            return {
                'position': 'budget',
                'confidence': round(confidence, 2),
                'confidence_reason': f'{budget_count} budget signals found',
                'premium_signals_found': premium_count,
                'budget_signals_found': budget_count,
                'source': 'explicit'
            }

        # Default to mid-market with lower confidence
        return {
            'position': 'mid-market',
            'confidence': 0.5,
            'confidence_reason': 'Balanced signals or no clear positioning',
            'premium_signals_found': premium_count,
            'budget_signals_found': budget_count,
            'source': 'inferred'
        }

    def _detect_region_language(self) -> Dict:
        """Detect geographic region and language"""
        region_indicators = {
            'india': ['india', 'indian', 'rupee', 'rs.', '₹', 'mumbai', 'delhi', 'bangalore'],
            'usa': ['usa', 'united states', 'american', 'dollar', '$'],
            'uk': ['uk', 'united kingdom', 'british', 'pound', '£', 'london'],
            'global': ['worldwide', 'global', 'international'],
        }
        detected_regions = []
        region_scores = {}
        for region, indicators in region_indicators.items():
            score = sum(1 for ind in indicators if ind in self.text_lower)
            if score > 0:
                region_scores[region] = score
                detected_regions.append(region)

        primary = detected_regions[0] if detected_regions else 'global'
        confidence = min(region_scores.get(primary, 0) / 3, 1.0) if region_scores else 0.3

        return {
            'primary_region': primary,
            'confidence': round(confidence, 2),
            'all_regions': detected_regions,
            'language': 'english',
            'source': 'explicit' if confidence > 0.5 else 'inferred'
        }

    def extract_voice_and_tone(self) -> Dict:
        """Extract voice and tone characteristics"""
        return {
            'tone_keywords': self._extract_tone_keywords(),
            'formality_level': self._detect_formality_level(),
            'energy_level': self._detect_energy_level(),
            'pov_usage': self._detect_pov_usage(),
            'sentence_patterns': self._analyze_sentence_patterns(),
            'emoji_usage': self._detect_emoji_usage(),
            'slang_usage': self._detect_slang_usage(),
        }

    def _extract_tone_keywords(self) -> List[Dict]:
        """Extract tone keywords from text"""
        tone_mapping = {
            'casual': ['hey', 'cool', 'awesome', 'gonna', 'wanna', 'yeah', 'super'],
            'bold': ['bold', 'fearless', 'daring', 'powerful', 'unstoppable', 'dominate'],
            'playful': ['fun', 'playful', 'exciting', 'joy', 'delight', 'smile', 'happy'],
            'calm': ['calm', 'peaceful', 'serene', 'gentle', 'soothing', 'relaxing'],
            'expert': ['expert', 'professional', 'specialist', 'authority', 'leading'],
            'warm': ['warm', 'caring', 'friendly', 'welcoming', 'comfort', 'cozy'],
        }
        detected_tones = []
        for tone, keywords in tone_mapping.items():
            count = sum(1 for kw in keywords if kw in self.text_lower)
            if count >= 2:
                confidence = min(count / 4, 1.0)
                detected_tones.append({
                    'tone': tone,
                    'strength': round(confidence, 2),
                    'keywords_found': count,
                    'confidence': round(confidence, 2)
                })
        return sorted(detected_tones, key=lambda x: -x['strength'])[:5]

    def _detect_formality_level(self) -> Dict:
        """Detect formality level of text"""
        formal_indicators = ['therefore', 'furthermore', 'consequently', 'hereby', 'whereas']
        casual_indicators = ['hey', 'gonna', 'wanna', 'cool', 'awesome', 'yeah', 'nope']
        formal_count = sum(1 for f in formal_indicators if f in self.text_lower)
        casual_count = sum(1 for c in casual_indicators if c in self.text_lower)

        if casual_count > formal_count * 2:
            level, label = 1, "Very Casual"
        elif casual_count > formal_count:
            level, label = 2, "Casual"
        elif formal_count > casual_count * 2:
            level, label = 5, "Corporate/Formal"
        elif formal_count > casual_count:
            level, label = 4, "Professional"
        else:
            level, label = 3, "Balanced"

        confidence = min((formal_count + casual_count) / 5, 1.0)

        return {
            'level': level,
            'label': label,
            'confidence': round(confidence, 2),
            'formal_signals': formal_count,
            'casual_signals': casual_count
        }

    def _detect_energy_level(self) -> Dict:
        """Detect energy level of text"""
        high_energy = ['!', 'exciting', 'amazing', 'incredible', 'wow', 'explosive', 'powerful']
        chill_energy = ['calm', 'peaceful', 'gentle', 'soft', 'quiet', 'relax', 'easy']
        high_count = sum(1 for h in high_energy if h in self.text_lower)
        exclamation_count = self.text.count('!')
        chill_count = sum(1 for c in chill_energy if c in self.text_lower)
        energy_score = (high_count + exclamation_count * 0.5 - chill_count) / 10
        energy_score = max(0, min(1, (energy_score + 0.5)))

        if energy_score > 0.7:
            label = "High Energy"
        elif energy_score > 0.4:
            label = "Moderate Energy"
        else:
            label = "Chill/Calm"

        return {
            'score': round(energy_score, 2),
            'label': label,
            'exclamation_count': exclamation_count,
            'confidence': round(min((high_count + chill_count) / 10, 1.0), 2)
        }

    def _detect_pov_usage(self) -> Dict:
        """Detect point of view usage (first/second person)"""
        first_person = len(re.findall(r'\b(we|our|us)\b', self.text_lower))
        second_person = len(re.findall(r'\b(you|your|yours)\b', self.text_lower))
        total = first_person + second_person + 1
        dominant = 'balanced'
        if first_person > second_person * 1.5:
            dominant = 'first_person'
        elif second_person > first_person * 1.5:
            dominant = 'second_person'

        confidence = min(total / 50, 1.0)

        return {
            'dominant': dominant,
            'first_person_ratio': round(first_person / total, 2),
            'second_person_ratio': round(second_person / total, 2),
            'confidence': round(confidence, 2)
        }

    def _analyze_sentence_patterns(self) -> Dict:
        """Analyze sentence patterns"""
        sentences = re.split(r'[.!?]+', self.text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        if not sentences:
            return {'average_length': 0, 'pattern': 'unknown', 'total_sentences': 0, 'confidence': 0.0}
        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        return {
            'average_length': round(avg_length, 1),
            'total_sentences': len(sentences),
            'confidence': round(min(len(sentences) / 20, 1.0), 2)
        }

    def _detect_emoji_usage(self) -> Dict:
        """Detect emoji usage in text"""
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
        emojis = emoji_pattern.findall(self.text)
        return {
            'uses_emoji': len(emojis) > 0,
            'emoji_count': len(emojis),
            'frequency': 'heavy' if len(emojis) > 10 else ('light' if len(emojis) > 0 else 'none'),
            'confidence': 1.0 if len(emojis) > 0 else 0.0
        }

    def _detect_slang_usage(self) -> Dict:
        """Detect slang usage in text"""
        slang_words = ['gonna', 'wanna', 'gotta', 'kinda', 'sorta', 'dope', 'lit', 'fire', 'vibe']
        found_slang = [s for s in slang_words if s in self.text_lower]
        return {
            'uses_slang': len(found_slang) > 0,
            'slang_words_found': found_slang,
            'level': 'heavy' if len(found_slang) > 3 else ('light' if found_slang else 'none'),
            'confidence': 1.0 if len(found_slang) > 0 else 0.0
        }

    def extract_user_persona(self) -> Dict:
        """Extract user persona with demographics inference"""
        market_pos = self._detect_market_position()

        # Infer persona from market position
        if market_pos['position'] == 'premium':
            persona_label = 'Quality-Seeker'
            age_range = '30-55'
            life_stage = 'established_professional'
        elif market_pos['position'] == 'budget':
            persona_label = 'Value-Hunter'
            age_range = '18-35'
            life_stage = 'young_adult'
        else:
            persona_label = 'Smart-Shopper'
            age_range = '25-45'
            life_stage = 'mixed'

        # INFER DEMOGRAPHICS FROM NAVIGATION
        nav_demographics = self._infer_from_navigation()
        if nav_demographics['age_range']:
            age_range = nav_demographics['age_range']
            life_stage = nav_demographics['life_stage']

        # Extract pain points from reviews
        pain_points = self._extract_pain_points_from_reviews()

        # Motivation inference
        motivation_mapping = {
            'emotional': ['feel', 'happy', 'confident', 'proud', 'love'],
            'functional': ['save', 'time', 'money', 'efficient', 'practical'],
            'social': ['impress', 'noticed', 'compliment', 'friends', 'status']
        }
        scores = {motivation: sum(1 for kw in keywords if kw in self.text_lower) for motivation, keywords in motivation_mapping.items()}
        primary_motivation = max(scores, key=scores.get) if any(scores.values()) else 'mixed'

        motivation_confidence = min(max(scores.values()) / 5, 1.0) if scores else 0.3

        return {
            'persona_snapshot': {
                'persona_label': persona_label,
                'awareness_stage': 'solution_aware',
                'purchase_intent': 'medium',
                'confidence': market_pos['confidence']
            },
            'core_problem': {
                'primary_pain': pain_points[0] if pain_points else 'Not explicitly stated',
                'all_pains': pain_points[:3],
                'confidence': 0.7 if pain_points else 0.1,
                'source': 'reviews' if pain_points else 'missing'
            },
            'motivation_type': {
                'primary_motivation': primary_motivation,
                'all_scores': scores,
                'confidence': round(motivation_confidence, 2),
                'source': 'inferred' if motivation_confidence < 0.6 else 'explicit'
            },
            'demographics': {
                'age_range': age_range,
                'life_stage': life_stage,
                'confidence': round(nav_demographics['confidence'], 2),
                'source': nav_demographics['source']
            },
            'content_behavior': {
                'prefers_short_form': True,
                'prefers_storytelling': False,
                'responds_to_humor': False,
                'responds_to_authority': False,
                'trusts_creators': True,
                'confidence': 0.5,
                'source': 'default_assumption'
            }
        }

    def _infer_from_navigation(self) -> Dict:
        """Infer demographics from navigation structure"""
        age_signals = {
            'kids': ['kids', 'children', 'toddler', 'baby', 'infant'],
            'teens': ['teen', 'youth', 'junior', 'young'],
            'adults': ['adult', 'professional', 'business', 'executive'],
            'seniors': ['senior', 'mature', 'classic']
        }

        life_stage_signals = {
            'students': ['student', 'college', 'university', 'school'],
            'young_professionals': ['professional', 'career', 'office', 'business'],
            'parents': ['family', 'parent', 'mom', 'dad'],
            'retirees': ['retirement', 'leisure', 'travel']
        }

        detected_age = None
        detected_life_stage = None
        confidence = 0.0

        # Check navigation text
        for age_cat, keywords in age_signals.items():
            if any(kw in self.nav_text_lower for kw in keywords):
                detected_age = age_cat
                confidence = 0.8
                break

        for stage, keywords in life_stage_signals.items():
            if any(kw in self.nav_text_lower for kw in keywords):
                detected_life_stage = stage
                confidence = max(confidence, 0.7)
                break

        # Map to age ranges
        age_map = {
            'kids': '0-12',
            'teens': '13-19',
            'adults': '20-60',
            'seniors': '60+'
        }

        return {
            'age_range': age_map.get(detected_age, ''),
            'life_stage': detected_life_stage or '',
            'confidence': confidence,
            'source': 'navigation' if confidence > 0 else 'missing'
        }

    def _extract_pain_points_from_reviews(self) -> List[str]:
        """Extract pain points from reviews and FAQs"""
        if not self.reviews_text:
            return []

        pain_patterns = [
            r'(?:problem|issue|struggle|difficult|challenge|frustrated|annoyed)\s+(?:with|is|was)\s+([^.!?\n]{10,100})',
            r'(?:wish|hope|want|need)\s+(?:it|they|you)\s+([^.!?\n]{10,100})',
            r'(?:disappointing|disappointed|not happy|unhappy)\s+(?:that|with|about)\s+([^.!?\n]{10,100})'
        ]

        pains = []
        for pattern in pain_patterns:
            matches = re.findall(pattern, self.reviews_text_lower, re.IGNORECASE)
            pains.extend(matches[:5])

        return list(set([p.strip() for p in pains]))[:10]

    def extract_messaging_rules(self) -> Dict:
        """Extract messaging rules (words to use/avoid)"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'our', 'your', 'their', 'its', 'my', 'his', 'her', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below'}

        words = re.findall(r'\b[a-zA-Z]{4,}\b', self.text_lower)
        word_counts = {}
        for word in words:
            if word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        sorted_words = sorted(word_counts.items(), key=lambda x: -x[1])[:20]
        words_to_use = [{'word': w, 'frequency': c, 'confidence': 1.0} for w, c in sorted_words]

        market_position = self._detect_market_position()
        avoid_list = []
        if market_position['position'] == 'premium':
            avoid_list = ['cheap', 'discount', 'budget', 'affordable']
        elif market_position['position'] == 'budget':
            avoid_list = ['luxury', 'premium', 'exclusive', 'elite']

        return {
            'words_to_use': words_to_use,
            'words_to_avoid': list(set(avoid_list)),
            'confidence': round(min(len(words_to_use) / 20, 1.0), 2)
        }

    def extract_ad_content(self) -> Dict:
        """
        Extract ad-specific content elements:
        - Headlines/main text
        - Sub-text/taglines
        - CTAs (Call to Actions)
        - Product features/ingredients
        """
        headlines = []
        subtext = []
        ctas = []
        features = []
        ingredients = []

        # Extract headlines (h1, h2, hero text)
        headline_patterns = [
            r'<h1[^>]*>([^<]+)</h1>',
            r'<h2[^>]*>([^<]+)</h2>',
            r'(?:^|\n)([A-Z][A-Za-z\s]{10,80})(?:\n|$)',  # Capitalized sentences
        ]
        for pattern in headline_patterns:
            matches = re.findall(pattern, self.text, re.MULTILINE)
            headlines.extend([m.strip() for m in matches if 10 < len(m.strip()) < 100])

        # Extract subtext/taglines
        subtext_patterns = [
            r'tagline["\']:\s*["\']([^"\']+)["\']',
            r'subtitle["\']:\s*["\']([^"\']+)["\']',
            r'description["\']:\s*["\']([^"\']{20,200})["\']',
        ]
        for pattern in subtext_patterns:
            matches = re.findall(pattern, self.text_lower)
            subtext.extend([m.strip() for m in matches if 20 < len(m.strip()) < 200])

        # Extract CTAs
        cta_keywords = ['shop now', 'buy now', 'learn more', 'get started', 'try now',
                        'order now', 'subscribe', 'sign up', 'download', 'discover',
                        'explore', 'join now', 'add to cart', 'get yours', 'view collection']
        for keyword in cta_keywords:
            if keyword in self.text_lower:
                # Find the actual case version
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                matches = pattern.findall(self.text)
                if matches:
                    ctas.append(matches[0])

        # Extract features (bullet points, specifications)
        feature_patterns = [
            r'[•●○▪▫–-]\s*([A-Z][^\n•●○▪▫]{10,100})',
            r'\n\s*[\*\-]\s*([A-Z][^\n\*\-]{10,100})',
            r'(?:feature|benefit)s?:?\s*([A-Z][^\n]{10,100})',
        ]
        for pattern in feature_patterns:
            matches = re.findall(pattern, self.text, re.MULTILINE)
            features.extend([m.strip() for m in matches if 10 < len(m.strip()) < 150])

        # Extract ingredients (for food, beauty, health products)
        ingredients_patterns = [
            r'ingredients?:?\s*([A-Za-z\s,\(\)]+)',
            r'made with:?\s*([A-Za-z\s,\(\)]+)',
            r'contains?:?\s*([A-Za-z\s,\(\)]+)',
        ]
        for pattern in ingredients_patterns:
            matches = re.findall(pattern, self.text_lower)
            for match in matches:
                # Split by comma and clean
                ingredient_list = [i.strip() for i in match.split(',') if 2 < len(i.strip()) < 50]
                ingredients.extend(ingredient_list[:10])

        return {
            'headlines': list(set(headlines))[:10],  # Top 10 unique headlines
            'subtext': list(set(subtext))[:5],       # Top 5 unique subtexts
            'ctas': list(set(ctas))[:10],            # Top 10 unique CTAs
            'features': list(set(features))[:15],    # Top 15 features
            'ingredients': list(set(ingredients))[:20],  # Top 20 ingredients
            'has_headlines': len(headlines) > 0,
            'has_ctas': len(ctas) > 0,
            'has_features': len(features) > 0,
            'has_ingredients': len(ingredients) > 0
        }

    def extract_all(self, brand_name: str) -> Dict:
        """Extract all brand intelligence"""
        return {
            'brand_identity': self.extract_brand_identity(brand_name),
            'voice_and_tone': self.extract_voice_and_tone(),
            'messaging_rules': self.extract_messaging_rules(),
            'user_persona': self.extract_user_persona(),
            'ad_content': self.extract_ad_content(),
            'extraction_metadata': {
                'extraction_date': datetime.now().isoformat(),
                'text_length': len(self.text),
                'nav_text_length': len(self.nav_text),
                'reviews_text_length': len(self.reviews_text),
                'url': self.url
            }
        }


def create_brand_data_structure(brand_name: str, scraped: Dict, url: str = "") -> Dict:
    """Create comprehensive brand data structure with all intelligence"""
    text = scraped.get('text', '')
    nav_text = scraped.get('nav_text', '')
    reviews_text = scraped.get('reviews_text', '')

    # Extract intelligence with confidence scores
    extractor = BrandIntelligenceExtractor(text, nav_text, reviews_text, url)
    intelligence = extractor.extract_all(brand_name)

    brand_data = {
        'brand_name': brand_name,
        'extraction_date': datetime.now().isoformat(),
        'extraction_quality': 0.85,
        'metadata': {
            'pages_crawled': scraped.get('pages_crawled', 1),
            'total_characters': scraped.get('char_count', 0),
            'nav_characters': len(nav_text),
            'reviews_characters': len(reviews_text),
            'crawl_method': 'playwright_deep_enhanced',
            'url': url
        },
        '1_brand_logo': {
            'light_logo': scraped.get('logos', {}).get('light'),
            'dark_logo': scraped.get('logos', {}).get('dark'),
            'all_candidates': scraped.get('logos', {}).get('all', [])
        },
        '2_brand_colours': {
            'colors': scraped.get('colors', []),
            'color_roles': {
                'primary': None,
                'secondary': None,
                'accent': None
            }
        },
        '10_images_and_ads': {
            'images': scraped.get('images', []),
            'ads': scraped.get('ads', [])
        },
        **intelligence
    }

    # Set color roles
    if scraped.get('colors'):
        colors = scraped['colors']
        for i, color in enumerate(colors[:3]):
            role = ['primary', 'secondary', 'accent'][i]
            brand_data['2_brand_colours']['color_roles'][role] = color.get('hex')

    return brand_data
