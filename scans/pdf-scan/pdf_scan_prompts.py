"""
PDF Accessibility Scan Prompts for GPT-5 Vision Analysis
=========================================================

This module contains the system prompts used for GPT-5 Vision API calls
to analyze PDF documents for accessibility compliance.

The prompts are designed to:
- Guide GPT-5 to perform comprehensive accessibility analysis
- Ensure compliance with WCAG 2.1 AA standards and EU regulations
- Generate structured, actionable results
- Maintain consistency across different PDF types and sizes

Available in: English, French, German, Spanish, Italian, Portuguese
"""

# English (default)
PDF_SCAN_PROMPT_EN = r"""
    You are performing an accessibility review based solely on a screenshot of a PDF page. 
    Evaluate strictly under WCAG 2.1 AA and Directive (EU) 2019/882 requirements *that are visually inferable from an image*.

    Do NOT assess:
    - Tags, alt text, machine readability, or interactivity
    - Any hidden or embedded document structure

    Focus ONLY on elements visible in the screenshot, including:
    - Color contrast and cases where color alone conveys meaning
    - Text size (flag any text approximately below ~9pt equivalent)
    - Font legibility (style, spacing, readability)
    - Layout and visual reading order based on spatial hierarchy
    - Link appearance and distinguishability (if visible)
    - Cognitive load (clutter, excessive variety, confusing structure)
    - Visual clarity of icons/symbols and presence of accompanying text labels

    For each issue, reference its location (e.g., "header", "bottom left sidebar").

    Output format — in this order, nothing else:
    1. "Accessibility Score": honest and encouraging score out of 100
    2. "Summary of Issues": group issues by type with bullet points
    3. "Recommendations": bullet points aligned to each issue type
    """

# French
PDF_SCAN_PROMPT_FR = r"""
    Vous effectuez une évaluation d'accessibilité basée uniquement sur une capture d'écran d'une page PDF.
    Évaluez strictement selon les exigences WCAG 2.1 AA et la Directive (UE) 2019/882 *qui sont visuellement déductibles d'une image*.

    N'évaluez PAS :
    - Les balises, le texte alternatif, la lisibilité machine ou l'interactivité
    - Toute structure de document cachée ou intégrée

    Concentrez-vous UNIQUEMENT sur les éléments visibles dans la capture d'écran, notamment :
    - Le contraste des couleurs et les cas où la couleur seule transmet une signification
    - La taille du texte (signalez tout texte approximativement en dessous de ~9pt équivalent)
    - La lisibilité de la police (style, espacement, lisibilité)
    - La mise en page et l'ordre de lecture visuel basé sur la hiérarchie spatiale
    - L'apparence et la distinguabilité des liens (si visibles)
    - La charge cognitive (encombrement, variété excessive, structure confuse)
    - La clarté visuelle des icônes/symboles et la présence d'étiquettes textuelles associées

    Pour chaque problème, référencez son emplacement (ex. : "en-tête", "barre latérale en bas à gauche").

    Format de sortie — dans cet ordre, rien d'autre :
    1. "Score d'accessibilité" : score honnête et encourageant sur 100
    2. "Résumé des problèmes" : regroupez les problèmes par type avec des puces
    3. "Recommandations" : puces alignées sur chaque type de problème
    """

# German
PDF_SCAN_PROMPT_DE = r"""
    Sie führen eine Barrierefreiheitsprüfung basierend ausschließlich auf einem Screenshot einer PDF-Seite durch.
    Bewerten Sie streng nach den Anforderungen von WCAG 2.1 AA und der Richtlinie (EU) 2019/882, *die visuell aus einem Bild ableitbar sind*.

    Bewerten Sie NICHT:
    - Tags, Alternativtext, maschinelle Lesbarkeit oder Interaktivität
    - Jegliche versteckte oder eingebettete Dokumentstruktur

    Konzentrieren Sie sich NUR auf im Screenshot sichtbare Elemente, einschließlich:
    - Farbkontrast und Fälle, in denen Farbe allein Bedeutung vermittelt
    - Textgröße (markieren Sie Text unter ca. ~9pt Äquivalent)
    - Schriftlesbarkeit (Stil, Abstände, Lesbarkeit)
    - Layout und visuelle Lesereihenfolge basierend auf räumlicher Hierarchie
    - Erscheinungsbild und Unterscheidbarkeit von Links (falls sichtbar)
    - Kognitive Belastung (Unordnung, übermäßige Vielfalt, verwirrende Struktur)
    - Visuelle Klarheit von Icons/Symbolen und Vorhandensein begleitender Textbeschriftungen

    Geben Sie für jedes Problem seinen Standort an (z.B. "Kopfzeile", "linke untere Seitenleiste").

    Ausgabeformat — in dieser Reihenfolge, nichts anderes:
    1. "Barrierefreiheits-Score": ehrliche und ermutigende Punktzahl von 100
    2. "Zusammenfassung der Probleme": Probleme nach Typ gruppiert mit Aufzählungspunkten
    3. "Empfehlungen": Aufzählungspunkte, die jedem Problemtyp zugeordnet sind
    """

# Spanish
PDF_SCAN_PROMPT_ES = r"""
    Está realizando una revisión de accesibilidad basada únicamente en una captura de pantalla de una página PDF.
    Evalúe estrictamente según los requisitos de WCAG 2.1 AA y la Directiva (UE) 2019/882 *que son visualmente deducibles de una imagen*.

    NO evalúe:
    - Etiquetas, texto alternativo, legibilidad de máquina o interactividad
    - Cualquier estructura de documento oculta o incrustada

    Concéntrese SOLO en elementos visibles en la captura de pantalla, incluyendo:
    - Contraste de colores y casos donde solo el color transmite significado
    - Tamaño del texto (señale cualquier texto aproximadamente por debajo de ~9pt equivalente)
    - Legibilidad de la fuente (estilo, espaciado, legibilidad)
    - Diseño y orden de lectura visual basado en jerarquía espacial
    - Apariencia y distinguibilidad de enlaces (si son visibles)
    - Carga cognitiva (desorden, variedad excesiva, estructura confusa)
    - Claridad visual de iconos/símbolos y presencia de etiquetas de texto acompañantes

    Para cada problema, haga referencia a su ubicación (ej.: "encabezado", "barra lateral inferior izquierda").

    Formato de salida — en este orden, nada más:
    1. "Puntuación de Accesibilidad": puntuación honesta y alentadora sobre 100
    2. "Resumen de Problemas": agrupe problemas por tipo con viñetas
    3. "Recomendaciones": viñetas alineadas con cada tipo de problema
    """

# Italian
PDF_SCAN_PROMPT_IT = r"""
    Stai eseguendo una revisione dell'accessibilità basata esclusivamente su uno screenshot di una pagina PDF.
    Valuta rigorosamente secondo i requisiti WCAG 2.1 AA e la Direttiva (UE) 2019/882 *che sono visivamente deducibili da un'immagine*.

    NON valutare:
    - Tag, testo alternativo, leggibilità automatica o interattività
    - Qualsiasi struttura di documento nascosta o incorporata

    Concentrati SOLO sugli elementi visibili nello screenshot, inclusi:
    - Contrasto dei colori e casi in cui solo il colore trasmette significato
    - Dimensione del testo (segnala qualsiasi testo approssimativamente sotto ~9pt equivalente)
    - Leggibilità del carattere (stile, spaziatura, leggibilità)
    - Layout e ordine di lettura visivo basato sulla gerarchia spaziale
    - Aspetto e distinguibilità dei link (se visibili)
    - Carico cognitivo (disordine, varietà eccessiva, struttura confusa)
    - Chiarezza visiva di icone/simboli e presenza di etichette testuali di accompagnamento

    Per ogni problema, fai riferimento alla sua posizione (es.: "intestazione", "barra laterale in basso a sinistra").

    Formato di output — in questo ordine, nient'altro:
    1. "Punteggio di Accessibilità": punteggio onesto e incoraggiante su 100
    2. "Riepilogo dei Problemi": raggruppa i problemi per tipo con punti elenco
    3. "Raccomandazioni": punti elenco allineati a ciascun tipo di problema
    """

# Portuguese
PDF_SCAN_PROMPT_PT = r"""
    Você está realizando uma revisão de acessibilidade baseada unicamente em uma captura de tela de uma página PDF.
    Avalie rigorosamente segundo os requisitos WCAG 2.1 AA e a Diretiva (UE) 2019/882 *que são visualmente deduzíveis de uma imagem*.

    NÃO avalie:
    - Tags, texto alternativo, legibilidade de máquina ou interatividade
    - Qualquer estrutura de documento oculta ou incorporada

    Concentre-se APENAS em elementos visíveis na captura de tela, incluindo:
    - Contraste de cores e casos onde apenas a cor transmite significado
    - Tamanho do texto (sinalize qualquer texto aproximadamente abaixo de ~9pt equivalente)
    - Legibilidade da fonte (estilo, espaçamento, legibilidade)
    - Layout e ordem de leitura visual baseada na hierarquia espacial
    - Aparência e distinguibilidade de links (se visíveis)
    - Carga cognitiva (desordem, variedade excessiva, estrutura confusa)
    - Clareza visual de ícones/símbolos e presença de rótulos de texto acompanhantes

    Para cada problema, faça referência à sua localização (ex.: "cabeçalho", "barra lateral inferior esquerda").

    Formato de saída — nesta ordem, nada mais:
    1. "Pontuação de Acessibilidade": pontuação honesta e encorajadora de 100
    2. "Resumo dos Problemas": agrupe problemas por tipo com marcadores
    3. "Recomendações": marcadores alinhados a cada tipo de problema
    """

# Dictionary of all prompts by language code
PDF_SCAN_PROMPTS = {
    "en": PDF_SCAN_PROMPT_EN,
    "fr": PDF_SCAN_PROMPT_FR,
    "de": PDF_SCAN_PROMPT_DE,
    "es": PDF_SCAN_PROMPT_ES,
    "it": PDF_SCAN_PROMPT_IT,
    "pt": PDF_SCAN_PROMPT_PT,
}

# =============================================================================
# Report Text Translations (for PDF accessibility analysis report output)
# =============================================================================

REPORT_TEXT_TRANSLATIONS = {
    "en": {
        "report_title": "PDF ACCESSIBILITY ANALYSIS REPORT",
        "document": "Document",
        "analysis_date": "Analysis Date",
        "total_pages": "Total Pages Analyzed",
        "analysis_method": "Analysis Method",
        "page_analysis": "PAGE {page_num} ANALYSIS",
        "source": "Source",
        "analysis_summary": "ANALYSIS SUMMARY",
        "summary_intro": "This accessibility analysis was completed using GPT-5 Vision AI technology with parallel processing (up to {max_concurrent} concurrent scans). Each page has been analyzed for:",
        "visual_compliance": "Visual accessibility compliance",
        "color_contrast": "Color contrast issues",
        "text_readability": "Text readability and structure",
        "image_accessibility": "Image accessibility",
        "navigation_layout": "Navigation and layout concerns",
        "wcag_compliance": "WCAG 2.1 AA compliance factors",
        "recommendations_note": "For detailed recommendations, please refer to the individual page analyses above.",
        "generated_by": "Analysis generated by LumTrails GPT-5 Vision Scanner v2.0.0",
    },
    "fr": {
        "report_title": "RAPPORT D'ANALYSE D'ACCESSIBILITÉ PDF",
        "document": "Document",
        "analysis_date": "Date d'analyse",
        "total_pages": "Nombre total de pages analysées",
        "analysis_method": "Méthode d'analyse",
        "page_analysis": "ANALYSE DE LA PAGE {page_num}",
        "source": "Source",
        "analysis_summary": "RÉSUMÉ DE L'ANALYSE",
        "summary_intro": "Cette analyse d'accessibilité a été réalisée grâce à la technologie IA GPT-5 Vision avec traitement parallèle (jusqu'à {max_concurrent} analyses simultanées). Chaque page a été analysée pour :",
        "visual_compliance": "Conformité en matière d'accessibilité visuelle",
        "color_contrast": "Problèmes de contraste des couleurs",
        "text_readability": "Lisibilité et structure du texte",
        "image_accessibility": "Accessibilité des images",
        "navigation_layout": "Problèmes de navigation et de mise en page",
        "wcag_compliance": "Facteurs de conformité WCAG 2.1 AA",
        "recommendations_note": "Pour des recommandations détaillées, veuillez consulter les analyses individuelles des pages ci-dessus.",
        "generated_by": "Analyse générée par LumTrails GPT-5 Vision Scanner v2.0.0",
    },
    "de": {
        "report_title": "PDF-BARRIEREFREIHEITS-ANALYSEBERICHT",
        "document": "Dokument",
        "analysis_date": "Analysedatum",
        "total_pages": "Gesamtzahl analysierter Seiten",
        "analysis_method": "Analysemethode",
        "page_analysis": "ANALYSE SEITE {page_num}",
        "source": "Quelle",
        "analysis_summary": "ANALYSEZUSAMMENFASSUNG",
        "summary_intro": "Diese Barrierefreiheitsanalyse wurde mit der GPT-5 Vision KI-Technologie mit paralleler Verarbeitung (bis zu {max_concurrent} gleichzeitige Scans) durchgeführt. Jede Seite wurde analysiert auf:",
        "visual_compliance": "Visuelle Barrierefreiheitskonformität",
        "color_contrast": "Farbkontrastprobleme",
        "text_readability": "Textlesbarkeit und -struktur",
        "image_accessibility": "Bildbarrierefreiheit",
        "navigation_layout": "Navigations- und Layoutprobleme",
        "wcag_compliance": "WCAG 2.1 AA Konformitätsfaktoren",
        "recommendations_note": "Für detaillierte Empfehlungen beachten Sie bitte die einzelnen Seitenanalysen oben.",
        "generated_by": "Analyse erstellt von LumTrails GPT-5 Vision Scanner v2.0.0",
    },
    "es": {
        "report_title": "INFORME DE ANÁLISIS DE ACCESIBILIDAD PDF",
        "document": "Documento",
        "analysis_date": "Fecha de análisis",
        "total_pages": "Total de páginas analizadas",
        "analysis_method": "Método de análisis",
        "page_analysis": "ANÁLISIS DE PÁGINA {page_num}",
        "source": "Fuente",
        "analysis_summary": "RESUMEN DEL ANÁLISIS",
        "summary_intro": "Este análisis de accesibilidad se completó utilizando la tecnología de IA GPT-5 Vision con procesamiento paralelo (hasta {max_concurrent} escaneos simultáneos). Cada página ha sido analizada para:",
        "visual_compliance": "Cumplimiento de accesibilidad visual",
        "color_contrast": "Problemas de contraste de colores",
        "text_readability": "Legibilidad y estructura del texto",
        "image_accessibility": "Accesibilidad de imágenes",
        "navigation_layout": "Problemas de navegación y diseño",
        "wcag_compliance": "Factores de cumplimiento WCAG 2.1 AA",
        "recommendations_note": "Para recomendaciones detalladas, consulte los análisis individuales de páginas anteriores.",
        "generated_by": "Análisis generado por LumTrails GPT-5 Vision Scanner v2.0.0",
    },
    "it": {
        "report_title": "RAPPORTO DI ANALISI DELL'ACCESSIBILITÀ PDF",
        "document": "Documento",
        "analysis_date": "Data di analisi",
        "total_pages": "Pagine totali analizzate",
        "analysis_method": "Metodo di analisi",
        "page_analysis": "ANALISI PAGINA {page_num}",
        "source": "Fonte",
        "analysis_summary": "RIEPILOGO DELL'ANALISI",
        "summary_intro": "Questa analisi di accessibilità è stata completata utilizzando la tecnologia IA GPT-5 Vision con elaborazione parallela (fino a {max_concurrent} scansioni simultanee). Ogni pagina è stata analizzata per:",
        "visual_compliance": "Conformità all'accessibilità visiva",
        "color_contrast": "Problemi di contrasto dei colori",
        "text_readability": "Leggibilità e struttura del testo",
        "image_accessibility": "Accessibilità delle immagini",
        "navigation_layout": "Problemi di navigazione e layout",
        "wcag_compliance": "Fattori di conformità WCAG 2.1 AA",
        "recommendations_note": "Per raccomandazioni dettagliate, fare riferimento alle analisi individuali delle pagine sopra.",
        "generated_by": "Analisi generata da LumTrails GPT-5 Vision Scanner v2.0.0",
    },
    "pt": {
        "report_title": "RELATÓRIO DE ANÁLISE DE ACESSIBILIDADE PDF",
        "document": "Documento",
        "analysis_date": "Data de análise",
        "total_pages": "Total de páginas analisadas",
        "analysis_method": "Método de análise",
        "page_analysis": "ANÁLISE DA PÁGINA {page_num}",
        "source": "Fonte",
        "analysis_summary": "RESUMO DA ANÁLISE",
        "summary_intro": "Esta análise de acessibilidade foi concluída utilizando a tecnologia IA GPT-5 Vision com processamento paralelo (até {max_concurrent} verificações simultâneas). Cada página foi analisada para:",
        "visual_compliance": "Conformidade com acessibilidade visual",
        "color_contrast": "Problemas de contraste de cores",
        "text_readability": "Legibilidade e estrutura do texto",
        "image_accessibility": "Acessibilidade de imagens",
        "navigation_layout": "Problemas de navegação e layout",
        "wcag_compliance": "Fatores de conformidade WCAG 2.1 AA",
        "recommendations_note": "Para recomendações detalhadas, consulte as análises individuais das páginas acima.",
        "generated_by": "Análise gerada por LumTrails GPT-5 Vision Scanner v2.0.0",
    },
}


def get_report_text(language: str = "en") -> dict:
    """
    Get the report text translations for the specified language.
    
    Args:
        language: Language code (en, fr, de, es, it, pt). Defaults to English.
        
    Returns:
        Dictionary of report text translations in the specified language.
    """
    return REPORT_TEXT_TRANSLATIONS.get(language, REPORT_TEXT_TRANSLATIONS["en"])


def get_pdf_scan_prompt(language: str = "en") -> str:
    """
    Get the PDF scan prompt for the specified language.
    
    Args:
        language: Language code (en, fr, de, es, it, pt). Defaults to English.
        
    Returns:
        The PDF scan prompt in the specified language.
    """
    return PDF_SCAN_PROMPTS.get(language, PDF_SCAN_PROMPT_EN)


# Keep backwards compatibility - default to English
PDF_SCAN_PROMPT = PDF_SCAN_PROMPT_EN
