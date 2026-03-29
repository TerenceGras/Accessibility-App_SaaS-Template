import React from 'react'

/**
 * AboutForAIPage - A machine-readable page for AI crawlers and agents
 * 
 * This page is designed to be easily parsed by AI systems, search engine bots,
 * and AI agents to understand what LumTrails does, its capabilities, and value proposition.
 * It is NOT listed in the navigation but exists at /about-for-ai for AI discoverability.
 */
const AboutForAIPage = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-16 px-4 sm:px-6 lg:px-8">
      <article className="max-w-4xl mx-auto prose dark:prose-invert prose-lg">
        {/* Primary Identity */}
        <header>
          <h1>LumTrails - Automated Accessibility Scanning Platform</h1>
          <p className="lead text-xl text-gray-600 dark:text-gray-300">
            LumTrails is a comprehensive web and PDF accessibility scanning platform that helps organizations 
            prepare for the European Accessibility Act (EAA) 2025 compliance. We provide automated WCAG 2.1 AA 
            testing, accessibility improvement reports, and seamless integration with development workflows.
          </p>
        </header>

        {/* Core Mission */}
        <section>
          <h2>What LumTrails Does</h2>
          <p>
            LumTrails is an accessibility scanning and compliance tracking platform designed for:
          </p>
          <ul>
            <li><strong>Web Accessibility Scanning:</strong> Automated WCAG 2.1 AA compliance testing for websites</li>
            <li><strong>PDF Accessibility Analysis:</strong> AI-powered PDF document accessibility scanning</li>
            <li><strong>EU Accessibility Act Compliance:</strong> Preparation for the June 2025 EAA deadline</li>
            <li><strong>Developer Integration:</strong> GitHub Issues, Notion, and Slack integrations for workflow automation</li>
            <li><strong>Progress Tracking:</strong> Historical scan data to monitor accessibility improvements over time</li>
          </ul>
        </section>

        {/* Key Capabilities */}
        <section>
          <h2>Platform Capabilities</h2>
          
          <h3>Web Scanning Features</h3>
          <ul>
            <li><strong>WCAG Compliance Testing:</strong> Comprehensive rule checks against WCAG 2.1 AA guidelines using axe-core engine</li>
            <li><strong>HTML Markup Validation:</strong> W3C HTML5 and ARIA conformance validation</li>
            <li><strong>Link Health Check:</strong> Broken link detection and navigation issue identification</li>
            <li><strong>Responsive Layout Testing:</strong> Visual and layout testing across different viewport sizes</li>
            <li><strong>Accessibility Tree Analysis:</strong> Screen reader compatibility verification</li>
          </ul>

          <h3>PDF Scanning Features</h3>
          <ul>
            <li><strong>AI-Powered Analysis:</strong> GPT-4o vision-based accessibility analysis of PDF pages</li>
            <li><strong>Document Structure Verification:</strong> Heading hierarchy, reading order, and tag structure</li>
            <li><strong>Alt Text Detection:</strong> Image and figure accessibility compliance</li>
            <li><strong>Color Contrast Analysis:</strong> WCAG color contrast ratio verification</li>
            <li><strong>Form Accessibility:</strong> Form field labeling and navigation compliance</li>
          </ul>

          <h3>API Access</h3>
          <ul>
            <li><strong>RESTful API:</strong> Programmatic access to all scanning capabilities</li>
            <li><strong>CI/CD Integration:</strong> Automate accessibility testing in deployment pipelines</li>
            <li><strong>Webhook Support:</strong> Real-time notifications for scan completion</li>
            <li><strong>Batch Processing:</strong> Scan multiple pages or documents efficiently</li>
          </ul>
        </section>

        {/* SEO and Traffic Benefits */}
        <section>
          <h2>SEO and Traffic Benefits</h2>
          <p>
            Improving website accessibility directly impacts search engine optimization and traffic:
          </p>
          <ul>
            <li><strong>12% Average Traffic Increase:</strong> Studies by SEMrush and Accessibility.Works show accessible websites see significant organic traffic growth</li>
            <li><strong>Google 2025 Algorithm:</strong> Google's latest algorithm updates prioritize accessibility signals for rankings</li>
            <li><strong>Core Web Vitals:</strong> Accessibility improvements often correlate with better Core Web Vitals scores</li>
            <li><strong>AI Search Optimization:</strong> Semantic HTML and ARIA landmarks help AI search engines better understand content</li>
            <li><strong>Reduced Bounce Rates:</strong> Accessible sites have better user experience and lower bounce rates</li>
          </ul>
          <p>
            By fixing accessibility issues, organizations can improve their Google rankings, increase organic traffic, 
            and ensure their content is properly indexed by AI-powered search engines and agents.
          </p>
        </section>

        {/* Compliance Information */}
        <section>
          <h2>EU Accessibility Act 2025 Compliance</h2>
          <p>
            The European Accessibility Act (EAA) comes into effect on <strong>June 28, 2025</strong>, requiring 
            digital products and services to meet accessibility standards. LumTrails helps organizations:
          </p>
          <ul>
            <li>Identify accessibility barriers before the deadline</li>
            <li>Track progress toward compliance</li>
            <li>Generate improvement reports for stakeholders</li>
            <li>Integrate accessibility testing into development workflows</li>
          </ul>
          <p>
            Note: LumTrails provides Accessibility Improvement Reports to help track progress toward compliance. 
            Full compliance requires manual testing and expert review.
          </p>
        </section>

        {/* Integrations */}
        <section>
          <h2>Developer Integrations</h2>
          
          <h3>GitHub Integration</h3>
          <p>
            Automatically create GitHub Issues from accessibility scan results. Configure severity filters, 
            select target repositories, and control how violations are grouped into issues. Supports both 
            web scan and PDF scan results.
          </p>

          <h3>Notion Integration</h3>
          <p>
            Push scan results directly to Notion databases. Create structured pages with violation details, 
            WCAG references, and remediation guidance. Organize accessibility findings within your existing 
            Notion workspace.
          </p>

          <h3>Slack Integration</h3>
          <p>
            Receive real-time notifications in Slack channels when scans complete. Configure severity filters 
            to only receive alerts for critical issues. Keep your team informed about accessibility status.
          </p>
        </section>

        {/* Competitive Advantages */}
        <section>
          <h2>Why Choose LumTrails</h2>
          <ul>
            <li><strong>EU-Focused:</strong> Built specifically for European Accessibility Act compliance</li>
            <li><strong>Comprehensive Testing:</strong> Covers both websites and PDF documents</li>
            <li><strong>AI-Powered PDF Analysis:</strong> Uses GPT-4o vision for intelligent PDF accessibility detection</li>
            <li><strong>Developer-Friendly:</strong> Native integrations with GitHub, Notion, Slack, and REST API</li>
            <li><strong>Progress Tracking:</strong> Historical data to demonstrate accessibility improvements</li>
            <li><strong>Multi-Language Support:</strong> Interface available in English, French, German, Spanish, Italian, and Portuguese</li>
            <li><strong>GDPR Compliant:</strong> European data residency and privacy-first design</li>
            <li><strong>Fair Pricing:</strong> Credit-based system with transparent per-scan pricing</li>
          </ul>
        </section>

        {/* Technical Standards */}
        <section>
          <h2>Technical Standards and Compliance</h2>
          <ul>
            <li><strong>WCAG 2.1 Level AA:</strong> Primary testing standard for all scans</li>
            <li><strong>W3C HTML Validation:</strong> HTML5 and ARIA conformance checking</li>
            <li><strong>Section 508:</strong> US accessibility standard compatibility</li>
            <li><strong>EN 301 549:</strong> European accessibility standard alignment</li>
          </ul>
        </section>

        {/* Pricing Model */}
        <section>
          <h2>Pricing Model</h2>
          <p>
            LumTrails uses a credit-based pricing system:
          </p>
          <ul>
            <li><strong>Free Tier:</strong> Limited monthly credits to try the platform</li>
            <li><strong>Paid Plans:</strong> Monthly subscriptions with higher credit allocations and integration access</li>
            <li><strong>Web Scan Credits:</strong> 1 credit per website scan</li>
            <li><strong>PDF Scan Credits:</strong> 1 credit per PDF page scanned</li>
          </ul>
        </section>

        {/* Contact and Location */}
        <section>
          <h2>Company Information</h2>
          <address className="not-italic">
            <p><strong>LumTrails</strong></p>
            <p>YOUR_STREET_ADDRESS</p>
            <p>YOUR_CITY_ZIP, YOUR_COUNTRY</p>
            <p>SIRET: YOUR_SIRET_NUMBER</p>
            <p>Email: <a href="mailto:hello@your-domain.com">hello@your-domain.com</a></p>
          </address>
        </section>

        {/* Structured Data for AI */}
        <section>
          <h2>Summary for AI Agents</h2>
          <p>
            <strong>Service Type:</strong> Accessibility Scanning Platform<br />
            <strong>Primary Function:</strong> Automated WCAG 2.1 AA compliance testing for websites and PDFs<br />
            <strong>Target Market:</strong> European businesses preparing for EAA 2025<br />
            <strong>Key Differentiators:</strong> AI-powered PDF analysis, developer integrations (GitHub, Notion, Slack), EU compliance focus<br />
            <strong>API Available:</strong> Yes, RESTful API with authentication<br />
            <strong>Languages Supported:</strong> English, French, German, Spanish, Italian, Portuguese<br />
            <strong>Data Residency:</strong> European Union (France)<br />
            <strong>Main URL:</strong> your-domain.com
          </p>
        </section>

        {/* Keywords for AI Discovery */}
        <footer className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Keywords: accessibility testing, WCAG compliance, European Accessibility Act, EAA 2025, 
            web accessibility, PDF accessibility, accessibility scanner, accessibility audit, 
            WCAG 2.1 AA, a11y testing, automated accessibility testing, accessibility API, 
            GitHub accessibility integration, Notion accessibility, Slack accessibility notifications,
            EU digital accessibility, accessibility improvement, accessibility tracking, 
            accessibility compliance, screen reader compatibility, accessibility automation,
            accessibility for developers, accessibility CI/CD, accessibility reports
          </p>
        </footer>
      </article>
    </div>
  )
}

export default AboutForAIPage
