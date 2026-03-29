"""
PDF Report Translations

Translations for the common areas of PDF exports.
Technical terms (WCAG, HTML, etc.) are NOT translated.
"""

# Analysis type translations - maps internal type to translated display name
ANALYSIS_TYPE_TRANSLATIONS = {
    "en": {
        "ai_vision_free_text": "AI Analysis",
        "ai_vision": "AI Analysis",
        "automated": "Automated Analysis",
        "manual": "Manual Analysis",
    },
    "fr": {
        "ai_vision_free_text": "Analyse IA",
        "ai_vision": "Analyse IA",
        "automated": "Analyse automatisée",
        "manual": "Analyse manuelle",
    },
    "de": {
        "ai_vision_free_text": "KI-Analyse",
        "ai_vision": "KI-Analyse",
        "automated": "Automatisierte Analyse",
        "manual": "Manuelle Analyse",
    },
    "es": {
        "ai_vision_free_text": "Análisis IA",
        "ai_vision": "Análisis IA",
        "automated": "Análisis automatizado",
        "manual": "Análisis manual",
    },
    "it": {
        "ai_vision_free_text": "Analisi IA",
        "ai_vision": "Analisi IA",
        "automated": "Analisi automatizzata",
        "manual": "Analisi manuale",
    },
    "pt": {
        "ai_vision_free_text": "Análise IA",
        "ai_vision": "Análise IA",
        "automated": "Análise automatizada",
        "manual": "Análise manual",
    },
}


def get_analysis_type_display(analysis_type: str, language: str) -> str:
    """
    Get the translated display name for an analysis type.
    
    Args:
        analysis_type: The internal analysis type (e.g., 'ai_vision_free_text')
        language: Language code (en, fr, de, es, it, pt)
    
    Returns:
        Translated display name
    """
    lang_translations = ANALYSIS_TYPE_TRANSLATIONS.get(language, ANALYSIS_TYPE_TRANSLATIONS["en"])
    return lang_translations.get(analysis_type, lang_translations.get("ai_vision_free_text", "AI Analysis"))


REPORT_TRANSLATIONS = {
    "en": {
        # First page - Web Scan
        "web_scan_report_title": "Web Scan Accessibility Report",
        "scan_date": "Scan Date",
        "modules_enabled": "Modules Enabled",
        "summary": "Summary",
        "wcag_violations": "WCAG VIOLATIONS",
        "html_errors": "HTML ERRORS",
        "broken_links": "BROKEN LINKS",
        "tests_passed": "TESTS PASSED",
        "page": "Page",
        
        # Section headers
        "wcag_compliance_testing": "WCAG Compliance Testing",
        "wcag_compliance_subtitle": "Element-level WCAG violations detected by automated testing",
        "issue": "issue",
        "issues": "issues",
        "error": "error",
        "errors": "errors",
        
        # WCAG success messages
        "no_wcag_violations": "No WCAG violations detected!",
        "wcag_passed_detail": "All automated accessibility tests passed successfully.",
        
        # HTML Markup Validation
        "html_markup_validation": "HTML Markup Validation",
        "html_markup_subtitle": "HTML5 and ARIA conformance checking",
        "no_html_errors": "No HTML validation errors!",
        "html_valid_detail": "All HTML markup passed validation checks.",
        
        # Accessibility Tree
        "accessibility_tree": "Accessibility Tree Analysis",
        "accessibility_tree_subtitle": "Document structure as interpreted by assistive technologies",
        "accessibility_tree_description": "The accessibility tree shows how screen readers and other assistive technologies interpret your page structure.",
        
        # Responsive Layout
        "responsive_layout_testing": "Responsive Layout Testing",
        "responsive_layout_subtitle": "Layout behavior across different viewport sizes",
        "horizontal_scroll": "Horizontal Scroll",
        "yes": "Yes",
        "no": "No",
        "visible_elements": "Visible Elements",
        "hidden_elements": "Hidden Elements",
        
        # Link Health Check
        "link_health_check": "Link Health Check",
        "link_health_subtitle": "Broken or unreachable links that may hinder navigation",
        "all_links_working": "All links are working correctly!",
        "links_checked_successfully": "links checked successfully",
        "link_text": "Link Text",
        "error": "Error",
        
        # Violation card
        "selector": "Selector",
        "html_snippet": "HTML Snippet",
        "learn_how_to_fix": "Learn how to fix this",
        "found_on": "Found on",
        "element": "element",
        "elements": "elements",
        
        # HTML errors
        "line": "Line",
        "column": "Column",
        
        # PDF Scan
        "pdf_scan_report_title": "PDF Accessibility Report",
        "analysis_date": "Analysis Date",
        "analysis_type": "Analysis Type",
        "accessibility_analysis": "Accessibility Analysis",
        "ai_powered_assessment": "AI-powered document accessibility assessment",
        "country": "Country",
        "company_name": "Company",
        
        # Company info
        "prepared_for": "Prepared for",
        "company": "Company",
        "address": "Address",
    },
    "fr": {
        # First page - Web Scan
        "web_scan_report_title": "Rapport d'accessibilité du scan web",
        "scan_date": "Date du scan",
        "modules_enabled": "Modules activés",
        "summary": "Résumé",
        "wcag_violations": "VIOLATIONS WCAG",
        "html_errors": "ERREURS HTML",
        "broken_links": "LIENS BRISÉS",
        "tests_passed": "TESTS RÉUSSIS",
        "page": "Page",
        
        # Section headers
        "wcag_compliance_testing": "Test de conformité WCAG",
        "wcag_compliance_subtitle": "Violations WCAG au niveau des éléments détectées par les tests automatisés",
        "issue": "problème",
        "issues": "problèmes",
        "error": "erreur",
        "errors": "erreurs",
        
        # WCAG success messages
        "no_wcag_violations": "Aucune violation WCAG détectée !",
        "wcag_passed_detail": "Tous les tests d'accessibilité automatisés ont réussi.",
        
        # HTML Markup Validation
        "html_markup_validation": "Validation du balisage HTML",
        "html_markup_subtitle": "Vérification de la conformité HTML5 et ARIA",
        "no_html_errors": "Aucune erreur de validation HTML !",
        "html_valid_detail": "Tout le balisage HTML a passé les vérifications de validation.",
        
        # Accessibility Tree
        "accessibility_tree": "Analyse de l'arbre d'accessibilité",
        "accessibility_tree_subtitle": "Structure du document telle qu'interprétée par les technologies d'assistance",
        "accessibility_tree_description": "L'arbre d'accessibilité montre comment les lecteurs d'écran et autres technologies d'assistance interprètent la structure de votre page.",
        
        # Responsive Layout
        "responsive_layout_testing": "Test de mise en page responsive",
        "responsive_layout_subtitle": "Comportement de la mise en page selon les différentes tailles d'écran",
        "horizontal_scroll": "Défilement horizontal",
        "yes": "Oui",
        "no": "Non",
        "visible_elements": "Éléments visibles",
        "hidden_elements": "Éléments masqués",
        
        # Link Health Check
        "link_health_check": "Vérification de l'état des liens",
        "link_health_subtitle": "Liens brisés ou inaccessibles pouvant entraver la navigation",
        "all_links_working": "Tous les liens fonctionnent correctement !",
        "links_checked_successfully": "liens vérifiés avec succès",
        "link_text": "Texte du lien",
        "error": "Erreur",
        
        # Violation card
        "selector": "Sélecteur",
        "html_snippet": "Extrait HTML",
        "learn_how_to_fix": "Découvrir comment corriger",
        "found_on": "Trouvé sur",
        "element": "élément",
        "elements": "éléments",
        
        # HTML errors
        "line": "Ligne",
        "column": "Colonne",
        
        # PDF Scan
        "pdf_scan_report_title": "Rapport d'accessibilité PDF",
        "analysis_date": "Date d'analyse",
        "analysis_type": "Type d'analyse",
        "accessibility_analysis": "Analyse d'accessibilité",
        "ai_powered_assessment": "Évaluation de l'accessibilité des documents par IA",
        "country": "Pays",
        "company_name": "Entreprise",
        
        # Company info
        "prepared_for": "Préparé pour",
        "company": "Entreprise",
        "address": "Adresse",
    },
    "de": {
        # First page - Web Scan
        "web_scan_report_title": "Web-Scan Barrierefreiheitsbericht",
        "scan_date": "Scan-Datum",
        "modules_enabled": "Aktivierte Module",
        "summary": "Zusammenfassung",
        "wcag_violations": "WCAG-VERSTÖSSE",
        "html_errors": "HTML-FEHLER",
        "broken_links": "DEFEKTE LINKS",
        "tests_passed": "BESTANDENE TESTS",
        "page": "Seite",
        
        # Section headers
        "wcag_compliance_testing": "WCAG-Konformitätstests",
        "wcag_compliance_subtitle": "WCAG-Verstöße auf Elementebene, die durch automatisierte Tests erkannt wurden",
        "issue": "Problem",
        "issues": "Probleme",
        "error": "Fehler",
        "errors": "Fehler",
        
        # WCAG success messages
        "no_wcag_violations": "Keine WCAG-Verstöße erkannt!",
        "wcag_passed_detail": "Alle automatisierten Barrierefreiheitstests erfolgreich bestanden.",
        
        # HTML Markup Validation
        "html_markup_validation": "HTML-Markup-Validierung",
        "html_markup_subtitle": "HTML5- und ARIA-Konformitätsprüfung",
        "no_html_errors": "Keine HTML-Validierungsfehler!",
        "html_valid_detail": "Das gesamte HTML-Markup hat die Validierungsprüfungen bestanden.",
        
        # Accessibility Tree
        "accessibility_tree": "Barrierefreiheitsbaum-Analyse",
        "accessibility_tree_subtitle": "Dokumentstruktur, wie sie von assistiven Technologien interpretiert wird",
        "accessibility_tree_description": "Der Barrierefreiheitsbaum zeigt, wie Screenreader und andere assistive Technologien die Struktur Ihrer Seite interpretieren.",
        
        # Responsive Layout
        "responsive_layout_testing": "Responsives Layout-Testing",
        "responsive_layout_subtitle": "Layout-Verhalten bei verschiedenen Bildschirmgrößen",
        "horizontal_scroll": "Horizontales Scrollen",
        "yes": "Ja",
        "no": "Nein",
        "visible_elements": "Sichtbare Elemente",
        "hidden_elements": "Versteckte Elemente",
        
        # Link Health Check
        "link_health_check": "Link-Integritätsprüfung",
        "link_health_subtitle": "Defekte oder nicht erreichbare Links, die die Navigation behindern können",
        "all_links_working": "Alle Links funktionieren korrekt!",
        "links_checked_successfully": "Links erfolgreich geprüft",
        "link_text": "Linktext",
        "error": "Fehler",
        
        # Violation card
        "selector": "Selektor",
        "html_snippet": "HTML-Ausschnitt",
        "learn_how_to_fix": "Erfahren Sie, wie Sie das beheben",
        "found_on": "Gefunden auf",
        "element": "Element",
        "elements": "Elemente",
        
        # HTML errors
        "line": "Zeile",
        "column": "Spalte",
        
        # PDF Scan
        "pdf_scan_report_title": "PDF-Barrierefreiheitsbericht",
        "analysis_date": "Analysedatum",
        "analysis_type": "Analysetyp",
        "accessibility_analysis": "Barrierefreiheitsanalyse",
        "ai_powered_assessment": "KI-gestützte Bewertung der Dokumentenbarrierefreiheit",
        "country": "Land",
        "company_name": "Unternehmen",
        
        # Company info
        "prepared_for": "Erstellt für",
        "company": "Unternehmen",
        "address": "Adresse",
    },
    "es": {
        # First page - Web Scan
        "web_scan_report_title": "Informe de accesibilidad del escaneo web",
        "scan_date": "Fecha del escaneo",
        "modules_enabled": "Módulos habilitados",
        "summary": "Resumen",
        "wcag_violations": "VIOLACIONES WCAG",
        "html_errors": "ERRORES HTML",
        "broken_links": "ENLACES ROTOS",
        "tests_passed": "PRUEBAS SUPERADAS",
        "page": "Página",
        
        # Section headers
        "wcag_compliance_testing": "Pruebas de conformidad WCAG",
        "wcag_compliance_subtitle": "Violaciones WCAG a nivel de elemento detectadas mediante pruebas automatizadas",
        "issue": "problema",
        "issues": "problemas",
        "error": "error",
        "errors": "errores",
        
        # WCAG success messages
        "no_wcag_violations": "¡No se detectaron violaciones WCAG!",
        "wcag_passed_detail": "Todas las pruebas de accesibilidad automatizadas se completaron con éxito.",
        
        # HTML Markup Validation
        "html_markup_validation": "Validación del marcado HTML",
        "html_markup_subtitle": "Verificación de conformidad HTML5 y ARIA",
        "no_html_errors": "¡Sin errores de validación HTML!",
        "html_valid_detail": "Todo el marcado HTML pasó las verificaciones de validación.",
        
        # Accessibility Tree
        "accessibility_tree": "Análisis del árbol de accesibilidad",
        "accessibility_tree_subtitle": "Estructura del documento según la interpretan las tecnologías de asistencia",
        "accessibility_tree_description": "El árbol de accesibilidad muestra cómo los lectores de pantalla y otras tecnologías de asistencia interpretan la estructura de su página.",
        
        # Responsive Layout
        "responsive_layout_testing": "Pruebas de diseño responsive",
        "responsive_layout_subtitle": "Comportamiento del diseño en diferentes tamaños de pantalla",
        "horizontal_scroll": "Desplazamiento horizontal",
        "yes": "Sí",
        "no": "No",
        "visible_elements": "Elementos visibles",
        "hidden_elements": "Elementos ocultos",
        
        # Link Health Check
        "link_health_check": "Verificación del estado de enlaces",
        "link_health_subtitle": "Enlaces rotos o inalcanzables que pueden dificultar la navegación",
        "all_links_working": "¡Todos los enlaces funcionan correctamente!",
        "links_checked_successfully": "enlaces verificados con éxito",
        "link_text": "Texto del enlace",
        "error": "Error",
        
        # Violation card
        "selector": "Selector",
        "html_snippet": "Fragmento HTML",
        "learn_how_to_fix": "Aprenda a corregir esto",
        "found_on": "Encontrado en",
        "element": "elemento",
        "elements": "elementos",
        
        # HTML errors
        "line": "Línea",
        "column": "Columna",
        
        # PDF Scan
        "pdf_scan_report_title": "Informe de accesibilidad PDF",
        "analysis_date": "Fecha de análisis",
        "analysis_type": "Tipo de análisis",
        "accessibility_analysis": "Análisis de accesibilidad",
        "ai_powered_assessment": "Evaluación de accesibilidad de documentos con IA",
        "country": "País",
        "company_name": "Empresa",
        
        # Company info
        "prepared_for": "Preparado para",
        "company": "Empresa",
        "address": "Dirección",
    },
    "it": {
        # First page - Web Scan
        "web_scan_report_title": "Rapporto di accessibilità della scansione web",
        "scan_date": "Data della scansione",
        "modules_enabled": "Moduli abilitati",
        "summary": "Riepilogo",
        "wcag_violations": "VIOLAZIONI WCAG",
        "html_errors": "ERRORI HTML",
        "broken_links": "LINK NON FUNZIONANTI",
        "tests_passed": "TEST SUPERATI",
        "page": "Pagina",
        
        # Section headers
        "wcag_compliance_testing": "Test di conformità WCAG",
        "wcag_compliance_subtitle": "Violazioni WCAG a livello di elemento rilevate dai test automatizzati",
        "issue": "problema",
        "issues": "problemi",
        "error": "errore",
        "errors": "errori",
        
        # WCAG success messages
        "no_wcag_violations": "Nessuna violazione WCAG rilevata!",
        "wcag_passed_detail": "Tutti i test di accessibilità automatizzati sono stati superati con successo.",
        
        # HTML Markup Validation
        "html_markup_validation": "Validazione del markup HTML",
        "html_markup_subtitle": "Verifica della conformità HTML5 e ARIA",
        "no_html_errors": "Nessun errore di validazione HTML!",
        "html_valid_detail": "Tutto il markup HTML ha superato le verifiche di validazione.",
        
        # Accessibility Tree
        "accessibility_tree": "Analisi dell'albero di accessibilità",
        "accessibility_tree_subtitle": "Struttura del documento come interpretata dalle tecnologie assistive",
        "accessibility_tree_description": "L'albero di accessibilità mostra come gli screen reader e altre tecnologie assistive interpretano la struttura della tua pagina.",
        
        # Responsive Layout
        "responsive_layout_testing": "Test del layout responsive",
        "responsive_layout_subtitle": "Comportamento del layout con diverse dimensioni dello schermo",
        "horizontal_scroll": "Scorrimento orizzontale",
        "yes": "Sì",
        "no": "No",
        "visible_elements": "Elementi visibili",
        "hidden_elements": "Elementi nascosti",
        
        # Link Health Check
        "link_health_check": "Verifica dello stato dei link",
        "link_health_subtitle": "Link non funzionanti o irraggiungibili che possono ostacolare la navigazione",
        "all_links_working": "Tutti i link funzionano correttamente!",
        "links_checked_successfully": "link verificati con successo",
        "link_text": "Testo del link",
        "error": "Errore",
        
        # Violation card
        "selector": "Selettore",
        "html_snippet": "Frammento HTML",
        "learn_how_to_fix": "Scopri come correggere",
        "found_on": "Trovato su",
        "element": "elemento",
        "elements": "elementi",
        
        # HTML errors
        "line": "Riga",
        "column": "Colonna",
        
        # PDF Scan
        "pdf_scan_report_title": "Rapporto di accessibilità PDF",
        "analysis_date": "Data di analisi",
        "analysis_type": "Tipo di analisi",
        "accessibility_analysis": "Analisi di accessibilità",
        "ai_powered_assessment": "Valutazione dell'accessibilità dei documenti basata su IA",
        "country": "Paese",
        "company_name": "Azienda",
        
        # Company info
        "prepared_for": "Preparato per",
        "company": "Azienda",
        "address": "Indirizzo",
    },
    "pt": {
        # First page - Web Scan
        "web_scan_report_title": "Relatório de acessibilidade da verificação web",
        "scan_date": "Data da verificação",
        "modules_enabled": "Módulos ativados",
        "summary": "Resumo",
        "wcag_violations": "VIOLAÇÕES WCAG",
        "html_errors": "ERROS HTML",
        "broken_links": "LINKS QUEBRADOS",
        "tests_passed": "TESTES APROVADOS",
        "page": "Página",
        
        # Section headers
        "wcag_compliance_testing": "Testes de conformidade WCAG",
        "wcag_compliance_subtitle": "Violações WCAG ao nível do elemento detetadas por testes automatizados",
        "issue": "problema",
        "issues": "problemas",
        "error": "erro",
        "errors": "erros",
        
        # WCAG success messages
        "no_wcag_violations": "Nenhuma violação WCAG detetada!",
        "wcag_passed_detail": "Todos os testes de acessibilidade automatizados foram aprovados com sucesso.",
        
        # HTML Markup Validation
        "html_markup_validation": "Validação de marcação HTML",
        "html_markup_subtitle": "Verificação de conformidade HTML5 e ARIA",
        "no_html_errors": "Sem erros de validação HTML!",
        "html_valid_detail": "Toda a marcação HTML passou nas verificações de validação.",
        
        # Accessibility Tree
        "accessibility_tree": "Análise da árvore de acessibilidade",
        "accessibility_tree_subtitle": "Estrutura do documento conforme interpretada por tecnologias assistivas",
        "accessibility_tree_description": "A árvore de acessibilidade mostra como os leitores de ecrã e outras tecnologias assistivas interpretam a estrutura da sua página.",
        
        # Responsive Layout
        "responsive_layout_testing": "Testes de layout responsivo",
        "responsive_layout_subtitle": "Comportamento do layout em diferentes tamanhos de ecrã",
        "horizontal_scroll": "Rolagem horizontal",
        "yes": "Sim",
        "no": "Não",
        "visible_elements": "Elementos visíveis",
        "hidden_elements": "Elementos ocultos",
        
        # Link Health Check
        "link_health_check": "Verificação do estado dos links",
        "link_health_subtitle": "Links quebrados ou inacessíveis que podem dificultar a navegação",
        "all_links_working": "Todos os links funcionam corretamente!",
        "links_checked_successfully": "links verificados com sucesso",
        "link_text": "Texto do link",
        "error": "Erro",
        
        # Violation card
        "selector": "Seletor",
        "html_snippet": "Fragmento HTML",
        "learn_how_to_fix": "Saiba como corrigir",
        "found_on": "Encontrado em",
        "element": "elemento",
        "elements": "elementos",
        
        # HTML errors
        "line": "Linha",
        "column": "Coluna",
        
        # PDF Scan
        "pdf_scan_report_title": "Relatório de acessibilidade PDF",
        "analysis_date": "Data de análise",
        "analysis_type": "Tipo de análise",
        "accessibility_analysis": "Análise de acessibilidade",
        "ai_powered_assessment": "Avaliação de acessibilidade de documentos com IA",
        "country": "País",
        "company_name": "Empresa",
        
        # Company info
        "prepared_for": "Preparado para",
        "company": "Empresa",
        "address": "Morada",
    },
}


def get_translations(language: str) -> dict:
    """
    Get translations for the specified language.
    Falls back to English if language is not supported.
    
    Args:
        language: Language code (en, fr, de, es, it, pt)
    
    Returns:
        Dictionary of translations
    """
    return REPORT_TRANSLATIONS.get(language, REPORT_TRANSLATIONS["en"])
