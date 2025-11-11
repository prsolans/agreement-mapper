"""
Agreement Map: Company Analysis Tool
Streamlit web application for automated company research and agreement landscape analysis
"""
import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from research_agent import CompanyResearchAgent
from export_manager import ExportManager
from supabase_storage import SupabaseStorageManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Agreement Map - Company Analysis",
    page_icon=":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Font Awesome CDN and Custom CSS
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #4a5568;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #718096;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #c6f6d5;
        border-left: 4px solid #38a169;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #2c5282;
        border-left: 4px solid #1a365d;
        color: white;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fef3c7;
        border-left: 4px solid #f6ad55;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
    .fa-icon {
        margin-right: 0.5rem;
    }
    /* Font Awesome icon styling for buttons */
    button[kind="secondary"] p {
        font-family: 'Font Awesome 6 Free', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif !important;
        font-weight: 900 !important;
    }
    /* Research Status Indicators */
    .research-status {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    .research-status.not-started {
        background-color: #f7fafc;
        border-left: 4px solid #cbd5e0;
        color: #718096;
    }
    .research-status.in-progress {
        background-color: #fef3c7;
        border-left: 4px solid #f6ad55;
        color: #744210;
        animation: pulse 2s ease-in-out infinite;
    }
    .research-status.completed {
        background-color: #c6f6d5;
        border-left: 4px solid #38a169;
        color: #22543d;
    }
    .research-status-icon {
        margin-right: 0.75rem;
        font-size: 1.1rem;
    }
    .research-status-title {
        font-weight: 600;
    }
    .research-status-message {
        margin-left: 0.5rem;
        font-size: 0.85rem;
        opacity: 0.8;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'research_status' not in st.session_state:
        st.session_state.research_status = {}


def render_research_status(task_name: str, title: str, icon: str, state: str = 'not-started', message: str = ''):
    """Render a research status indicator"""
    icon_map = {
        'not-started': '<i class="fas fa-circle" style="color: #cbd5e0;"></i>',
        'in-progress': '<i class="fas fa-spinner fa-pulse" style="color: #f6ad55;"></i>',
        'completed': '<i class="fas fa-check-circle" style="color: #38a169;"></i>'
    }

    status_icon = icon_map.get(state, '<i class="fas fa-circle" style="color: #cbd5e0;"></i>')
    message_html = f'<span class="research-status-message">- {message}</span>' if message else ''

    return f"""
    <div class="research-status {state}">
        <span class="research-status-icon">{status_icon}</span>
        <span class="research-status-title">{title}</span>
        {message_html}
    </div>
    """


def create_progress_callback(task_name: str, placeholder, title: str, icon: str):
    """Create a progress callback function for a specific task"""
    def callback(message: str):
        # Update session state
        if 'research_progress' not in st.session_state:
            st.session_state.research_progress = {}

        # Determine state from message
        if 'complete' in message.lower() or 'done' in message.lower():
            state = 'completed'
        else:
            state = 'in-progress'

        st.session_state.research_progress[task_name] = {
            'state': state,
            'message': message
        }

        # Update the placeholder with new status
        placeholder.markdown(
            render_research_status(task_name, title, icon, state, message),
            unsafe_allow_html=True
        )
    return callback


async def run_research(company_name: str, api_key: str, tavily_key: str, progress_containers: dict, status_obj):
    """Execute the research asynchronously with progress tracking"""

    agent = CompanyResearchAgent(api_key=api_key, tavily_api_key=tavily_key)

    # Define research categories with metadata
    research_categories = {
        'profile': {'title': 'Company Profile', 'icon': 'fas fa-building'},
        'business_units': {'title': 'Business Units', 'icon': 'fas fa-industry'},
        'priorities': {'title': 'Strategic Priorities', 'icon': 'fas fa-bullseye'},
        'landscape': {'title': 'Agreement Landscape', 'icon': 'fas fa-chart-bar'},
        'opportunities': {'title': 'Opportunities', 'icon': 'fas fa-lightbulb'},
        'matrix': {'title': 'Agreement Matrix', 'icon': 'fas fa-table'}
    }

    # Create progress callbacks with titles and icons
    callbacks = {
        task: create_progress_callback(
            task,
            progress_containers[task],
            research_categories[task]['title'],
            research_categories[task]['icon']
        )
        for task in research_categories
    }

    # Run research
    result = await agent.research_company_full(company_name, callbacks, status_obj)

    return result


def display_analysis_summary(analysis: dict):
    """Display summary metrics from analysis"""

    profile = analysis.get('company_profile', {})
    scale = profile.get('scale', {})
    portfolio = analysis.get('portfolio_summary', {})
    landscape = analysis.get('agreement_landscape_by_function', {})

    st.markdown('### <i class="fas fa-chart-line" style="color: rgb(255, 75, 75);"></i> Analysis Summary', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Annual Revenue",
            value=scale.get('annual_revenue', 'N/A')
        )

    with col2:
        st.metric(
            label="Employees",
            value=f"{scale.get('employees', 'N/A'):,}" if isinstance(scale.get('employees'), int) else scale.get('employees', 'N/A')
        )

    with col3:
        st.metric(
            label="Business Units",
            value=len(analysis.get('business_units', []))
        )

    with col4:
        # Show function count from new landscape structure
        functions = landscape.get('functions', [])
        st.metric(
            label="Business Functions",
            value=len(functions) if functions else 0
        )

    with col5:
        st.metric(
            label="Opportunities",
            value=portfolio.get('total_opportunities', 0)
        )

    # Portfolio value metrics
    if portfolio.get('total_opportunities', 0) > 0:
        st.markdown('### <i class="fas fa-dollar-sign" style="color: rgb(255, 75, 75);"></i> Optimization Portfolio', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Annual Value",
                value=portfolio.get('total_annual_value', 'N/A')
            )

        with col2:
            st.metric(
                label="Implementation Cost",
                value=portfolio.get('total_implementation_cost', 'N/A')
            )

        with col3:
            st.metric(
                label="Portfolio ROI",
                value=portfolio.get('portfolio_roi', 'N/A')
            )

        with col4:
            st.metric(
                label="Payback Period",
                value=portfolio.get('portfolio_payback', 'N/A')
            )


def display_company_profile(profile: dict):
    """Display company profile details"""

    with st.expander("Company Profile", expanded=False):
        
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Legal Name:** {profile.get('legal_name', 'N/A')}")
            st.markdown(f"**Industry:** {profile.get('industry', 'N/A')}")
            st.markdown(f"**Founded:** {profile.get('year_founded', 'N/A')}")
            st.markdown(f"**Headquarters:** {profile.get('headquarters', 'N/A')}")
            st.markdown(f"**Ownership:** {profile.get('ownership_structure', 'N/A')}")

        with col2:
            scale = profile.get('scale', {})
            st.markdown(f"**Revenue:** {scale.get('annual_revenue', 'N/A')}")
            st.markdown(f"**Employees:** {scale.get('employees', 'N/A')}")
            st.markdown(f"**Locations:** {scale.get('locations', 'N/A')}")
            st.markdown(f"**Countries:** {scale.get('countries', 'N/A')}")
            st.markdown(f"**Customers:** {scale.get('customers', 'N/A')}")

        # Business model
        business_model = profile.get('business_model', {})
        if business_model:
            st.markdown("**Business Model:**")
            st.markdown(business_model.get('primary_revenue_model', 'N/A'))

            if business_model.get('key_differentiators'):
                st.markdown("**Key Differentiators:**")
                for diff in business_model['key_differentiators']:
                    st.markdown(f"- {diff}")


def display_business_units(units: list):
    """Display business units details"""

    with st.expander("Business Units", expanded=False):
        for unit in units:
            st.markdown(f"### {unit.get('name', 'Unknown')}")
            st.markdown(f"*{unit.get('description', '')}*")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Revenue", unit.get('revenue_contribution', 'N/A'))

            with col2:
                st.metric("Agreements", unit.get('agreement_volume', 'N/A'))

            with col3:
                complexity = unit.get('complexity_level', 0)
                st.metric("Complexity", f"{complexity}/5")

            # Key agreement types
            if unit.get('key_agreement_types'):
                st.markdown("**Key Agreement Types:**")
                for agr in unit['key_agreement_types']:
                    st.markdown(f"- **{agr.get('type')}**: {agr.get('volume')} | Avg Value: {agr.get('avg_value')} | Term: {agr.get('avg_term')}")

            st.markdown("---")


def display_agreement_landscape_by_function(landscape: dict):
    """Display agreement landscape organized by business function"""

    with st.expander("Agreement Landscape by Function", expanded=False):
        functions = landscape.get('functions', [])
        summary = landscape.get('summary', {})

        if not functions:
            st.info("No function-based agreement landscape data available.")
            return

        # Summary
        st.markdown(f"**Total Functions:** {summary.get('total_functions', len(functions))} | **Total Agreements:** {summary.get('total_estimated_agreements', 'N/A')}")
        st.markdown("---")

        for func in functions:
            st.markdown(f"### {func.get('function_name', 'Unknown')}")
            st.markdown(f"*{func.get('description', '')}*")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Agreements", func.get('total_agreements', 'N/A'))

            with col2:
                complexity = func.get('complexity', 0)
                st.metric("Complexity", f"{complexity}/5")

            with col3:
                systems = func.get('systems_used', [])
                st.markdown("**Systems:**")
                if systems:
                    st.markdown(", ".join(systems[:3]))
                else:
                    st.markdown("N/A")

            # Agreement types
            if func.get('agreement_types'):
                st.markdown("**Key Agreement Types:**")
                for agr in func['agreement_types']:
                    managed_in = agr.get('managed_in', 'N/A')
                    st.markdown(f"- **{agr.get('type')}**: {agr.get('volume')} | Term: {agr.get('avg_term', 'N/A')} | System: {managed_in}")

            # Pain points
            if func.get('pain_points'):
                st.markdown("**Pain Points:**")
                for pain in func['pain_points']:
                    st.markdown(f"- {pain}")

            st.markdown("---")


def display_deep_research_findings(deep_research: dict):
    """Display deep research findings with sources"""

    with st.expander("📊 Deep Research Findings", expanded=False):
        if not deep_research or all(not v for k, v in deep_research.items() if k not in ['cache_used']):
            st.info("No deep research findings available.")
            return

        # Software Stack
        software_stack = deep_research.get('software_stack', [])
        if software_stack:
            st.markdown("### 💻 Software Stack Discovered")
            st.markdown("*Discovered from job postings and public information*")
            st.markdown("")

            for system in software_stack:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{system['system']}** ({system['category']})")
                with col2:
                    st.markdown(f"*{system['evidence']}*")
                with col3:
                    if system.get('source'):
                        st.markdown(f"[Source]({system['source']})")

            st.markdown("---")

        # Strategic Goals
        strategic_goals = deep_research.get('strategic_goals', [])
        if strategic_goals:
            st.markdown("### 🎯 Additional Strategic Context")
            st.markdown("*Discovered from recent announcements and initiatives*")
            st.markdown("")

            for goal in strategic_goals:
                confidence_icon = {
                    'high': '✅',
                    'medium': '⚠️',
                    'low': '❓'
                }.get(goal.get('confidence', 'low'), '❓')

                st.markdown(f"{confidence_icon} **{goal.get('goal', 'N/A')}**")
                if goal.get('source'):
                    st.markdown(f"   *Source: {goal['source']}*")
                st.markdown("")

            st.markdown("---")

        # Pain Points
        pain_points = deep_research.get('pain_points', [])
        if pain_points:
            st.markdown("### ⚠️ Identified Pain Points")
            st.markdown("*Discovered from research and industry analysis*")
            st.markdown("")

            for pain in pain_points:
                confidence_icon = {
                    'high': '✅',
                    'medium': '⚠️',
                    'low': '❓'
                }.get(pain.get('confidence', 'low'), '❓')

                st.markdown(f"{confidence_icon} {pain.get('pain', 'N/A')}")
                if pain.get('source'):
                    st.markdown(f"   *Source: {pain['source']}*")
                st.markdown("")

            st.markdown("---")

        # Industry Benchmarks
        benchmarks = deep_research.get('industry_benchmarks', {})
        if benchmarks and any(k not in ['source', 'applies_to'] for k in benchmarks.keys()):
            st.markdown("### 📈 Industry Benchmarks")
            if benchmarks.get('applies_to'):
                st.markdown(f"*{benchmarks['applies_to']}*")
            st.markdown("")

            for key, value in benchmarks.items():
                if key not in ['source', 'applies_to']:
                    formatted_key = key.replace('_', ' ').title()
                    st.markdown(f"**{formatted_key}:** {value}")

            if benchmarks.get('source'):
                st.markdown(f"\n*Source: {benchmarks['source']}*")

        # Cache indicator
        if deep_research.get('cache_used'):
            st.info("💾 Some data was loaded from cache to reduce research time and cost.")


def display_opportunities(opportunities: list):
    """Display optimization opportunities"""

    with st.expander("Optimization Opportunities", expanded=False):
        for i, opp in enumerate(opportunities, 1):
            priority = opp.get('implementation', {}).get('priority', 'medium')
            priority_icon = {
                'high': '<i class="fas fa-exclamation-circle" style="color: #e53e3e;"></i>',
                'medium': '<i class="fas fa-minus-circle" style="color: #f6ad55;"></i>',
                'low': '<i class="fas fa-check-circle" style="color: #38a169;"></i>'
            }.get(priority, '<i class="fas fa-circle"></i>')

            st.markdown(f"### {priority_icon} {i}. {opp.get('title', 'Unknown')}", unsafe_allow_html=True)
            st.markdown(opp.get('description', ''))

            # Function and Systems context
            business_function = opp.get('business_function')
            systems_impacted = opp.get('systems_impacted', [])

            if business_function or systems_impacted:
                col1, col2 = st.columns(2)
                with col1:
                    if business_function:
                        st.markdown(f"**Function:** {business_function}")
                with col2:
                    if systems_impacted:
                        st.markdown(f"**Systems:** {', '.join(systems_impacted)}")

            # Value metrics
            value_quant = opp.get('value_quantification', {})
            if value_quant:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Annual Value", value_quant.get('total_annual_value', 'N/A'))

                with col2:
                    st.metric("ROI", value_quant.get('roi_percentage', 'N/A'))

                with col3:
                    st.metric("Implementation Cost", value_quant.get('implementation_cost', 'N/A'))

                with col4:
                    st.metric("Payback", value_quant.get('payback_period', 'N/A'))

            # Implementation details
            impl = opp.get('implementation', {})
            st.markdown(f"**Timeline:** {impl.get('timeline', 'N/A')} | **Priority:** {impl.get('priority', 'N/A').upper()} | **Complexity:** {impl.get('complexity', 'N/A')}")

            st.markdown("---")


def display_agreement_matrix(matrix_data: dict):
    """Display agreement landscape matrix"""

    with st.expander("Agreement Landscape Matrix", expanded=False):
        agreement_types = matrix_data.get('agreement_types', [])
        metadata = matrix_data.get('matrix_metadata', {})

        if not agreement_types:
            st.info("No agreement matrix data available.")
            return

        # Summary metrics
        if metadata:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Agreement Types", metadata.get('total_types', len(agreement_types)))
            with col2:
                st.metric("Highest Volume", metadata.get('highest_volume_type', 'N/A'))
            with col3:
                st.metric("Most Complex", metadata.get('highest_complexity_type', 'N/A'))

        st.markdown("---")

        # Create sortable table
        st.markdown("### Agreement Types by Volume & Complexity")

        # Create dataframe for table display
        table_data = []
        for agr in agreement_types:
            table_data.append({
                'Agreement Type': agr.get('type', 'N/A'),
                'Volume (1-10)': agr.get('volume', 'N/A'),
                'Complexity (1-10)': agr.get('complexity', 'N/A'),
                'Classification': agr.get('classification', 'N/A'),
                'Business Unit': agr.get('business_unit', 'N/A'),
                'Est. Annual Volume': agr.get('estimated_annual_volume', 'N/A'),
                'Description': agr.get('description', 'N/A')
            })

        # Display table
        import pandas as pd
        df = pd.DataFrame(table_data)

        # Sort by complexity descending, then volume descending
        df_sorted = df.sort_values(by=['Complexity (1-10)', 'Volume (1-10)'], ascending=[False, False])

        st.dataframe(
            df_sorted,
            use_container_width=True,
            hide_index=True
        )

        # Quadrant analysis
        if metadata.get('quadrant_distribution'):
            st.markdown("### Quadrant Distribution")
            quad_dist = metadata['quadrant_distribution']

            col1, col2 = st.columns(2)
            with col1:
                st.metric("High Volume / High Complexity", quad_dist.get('high_vol_high_complex', 0))
                st.metric("Low Volume / High Complexity", quad_dist.get('low_vol_high_complex', 0))
            with col2:
                st.metric("High Volume / Low Complexity", quad_dist.get('high_vol_low_complex', 0))
                st.metric("Low Volume / Low Complexity", quad_dist.get('low_vol_low_complex', 0))


def display_visualization(analysis: dict):
    """Display visualization export options"""

    st.markdown("### Export Agreement Landscape")
    st.info("Download the visualization as a high-resolution image or PowerPoint presentation (importable to Google Slides)")

    company_analyzed = analysis.get('_meta', {}).get('company_name', 'Company')

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export to PNG", use_container_width=True, type="primary"):
            with st.spinner("Generating high-resolution image..."):
                try:
                    # Read visualization HTML
                    viz_path = Path(__file__).parent / "visualization.html"

                    if not viz_path.exists():
                        st.error("Visualization file not found")
                        return

                    with open(viz_path, 'r') as f:
                        viz_html = f.read()

                    # Inject analysis data
                    data_injection = f"""
                    <script>
                        window.addEventListener('load', function() {{
                            const data = {json.dumps(analysis)};
                            renderVisualization(data);
                        }});
                    </script>
                    """
                    complete_html = viz_html.replace('</body>', f'{data_injection}</body>')

                    # Capture as PNG
                    export_manager = ExportManager()
                    png_bytes = export_manager.capture_html_as_png(
                        complete_html,
                        width=2400,
                        height=2400,
                        scale=2
                    )

                    # Provide download button
                    filename = f"{company_analyzed.replace(' ', '_').lower()}_visualization.png"

                    st.download_button(
                        label="Download PNG",
                        data=png_bytes,
                        file_name=filename,
                        mime="image/png",
                        use_container_width=True,
                        key="download_png_viz"
                    )

                    st.success("PNG generated successfully!")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    st.exception(e)

    with col2:
        if st.button("Export to PowerPoint", use_container_width=True, type="primary"):
            with st.spinner("Creating PowerPoint presentation..."):
                try:
                    # Create PowerPoint with native shapes (fast, no browser needed)
                    export_manager = ExportManager()
                    pptx_bytes = export_manager.create_pptx_native(
                        company_analyzed,
                        analysis
                    )

                    # Provide download button
                    filename = f"{company_analyzed.replace(' ', '_').lower()}_presentation.pptx"

                    st.download_button(
                        label="Download PPTX",
                        data=pptx_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                        key="download_pptx_viz_col2"
                    )

                    st.success("PowerPoint created successfully! (Import to Google Slides)")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    st.exception(e)

    # Add Word document export in a new row
    st.markdown("---")
    if st.button("Export Slide Content as Word Doc", use_container_width=True, type="secondary"):
        with st.spinner("Creating Word document..."):
            try:
                # Create Word document with slide content
                export_manager = ExportManager()
                docx_bytes = export_manager.create_docx_content(
                    company_analyzed,
                    analysis
                )

                # Provide download button
                filename = f"{company_analyzed.replace(' ', '_').lower()}_slide_content.docx"

                st.download_button(
                    label="Download Word Doc",
                    data=docx_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="download_docx_viz_bottom"
                )

                st.success("Word document created successfully!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")
                st.exception(e)


def display_main_analysis_slides(analysis: dict):
    """
    Display analysis content organized by slides for easy copy/paste.
    Mirrors the Word Doc export structure.
    """
    company_name = analysis.get('_meta', {}).get('company_name', 'Company')
    profile = analysis.get('company_profile', {})
    scale = profile.get('scale', {})
    business_units = analysis.get('business_units', [])
    landscape = analysis.get('agreement_landscape_by_function', {})
    functions = landscape.get('functions', []) if isinstance(landscape, dict) else []
    opportunities = analysis.get('optimization_opportunities', [])
    priority_mappings = analysis.get('priority_mappings', [])
    strategic_priorities = analysis.get('strategic_priorities', [])
    agreement_matrix = analysis.get('agreement_matrix', {})
    matrix_types = agreement_matrix.get('agreement_types', [])

    # ===== EXECUTIVE SUMMARY =====
    executive_summary = analysis.get('executive_summary', {})
    bullets = executive_summary.get('bullets', [])

    st.markdown("### 📌 Executive Summary")
    if bullets:
        for bullet in bullets:
            st.markdown(f"- {bullet}")
    else:
        st.info("Executive summary not available for this analysis.")
    st.markdown("---")

    # ===== SLIDE 1: COMPANY HEADER & PROFILE =====
    with st.expander("📄 SLIDE 1: Company Header & Profile", expanded=False):
        st.markdown(f"**Company:** {company_name}")
        st.markdown(f"**Industry:** {profile.get('industry', 'N/A')}")
        st.markdown("")

        # Metrics table
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Metric**")
            st.markdown("Annual Revenue")
            st.markdown("Employees")
            st.markdown("Locations")
        with col2:
            st.markdown("**Value**")
            st.markdown(scale.get('annual_revenue', 'N/A'))
            st.markdown(str(scale.get('employees', 'N/A')))
            st.markdown(str(scale.get('locations', 'N/A')))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("Countries")
            st.markdown("Business Units")
        with col2:
            st.markdown(str(scale.get('countries', 'N/A')))
            st.markdown(str(len(business_units)))

    # ===== SLIDE 2: AGREEMENT LANDSCAPE BY FUNCTION =====
    with st.expander("📄 SLIDE 2: Agreement Landscape by Function", expanded=False):
        st.markdown("**Business functions and their agreement management**")
        st.markdown("")

        if functions:
            import pandas as pd
            table_data = []
            for func in functions:
                complexity = func.get('complexity', 3)
                complexity_text = "Complex, Negotiated" if complexity >= 4 else "Moderate Complexity"
                systems = func.get('systems_used', [])

                table_data.append({
                    'Function': func.get('function_name', 'N/A'),
                    'Complexity': complexity_text,
                    'Total Agreements': str(func.get('total_agreements', 'N/A')),
                    'Systems': ', '.join(systems) if systems else 'N/A'
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No function data available in this analysis.")

    # ===== SLIDE 3: PRIORITIES MAPPED TO CAPABILITIES =====
    with st.expander("📄 SLIDE 3: Priorities Mapped to Capabilities", expanded=False):
        st.markdown("**Strategic Alignment**")
        st.markdown("")

        if priority_mappings:
            for idx, mapping in enumerate(priority_mappings[:3], start=1):
                priority_name = mapping.get('priority_name', f'Priority {idx}')
                priority_description = mapping.get('priority_description', '')
                priority_id = mapping.get('priority_id', '')
                capability_name = mapping.get('capability_name', f'Capability {idx}')
                capability_description = mapping.get('capability_description', '')

                st.markdown(f"#### {idx}. {priority_name} → {capability_name}")
                st.markdown(f"**Priority:** {priority_description}")
                st.markdown(f"**Capability:** {capability_description}")
                st.markdown("")

                # Find strategic priority data for notes
                priority_data = None
                if strategic_priorities:
                    for priority in strategic_priorities:
                        if priority.get('priority_id') == priority_id or priority.get('priority_name') == priority_name:
                            priority_data = priority
                            break

                # SLIDE NOTES section
                if priority_data:
                    st.markdown("---")
                    st.markdown("**SLIDE NOTES (Copy to Slide Notes):**")

                    executive_owner = priority_data.get('executive_owner', '')
                    if executive_owner:
                        st.markdown(f"**Executive Owner:** {executive_owner}")

                    executive_responsibility = priority_data.get('executive_responsibility', '')
                    if executive_responsibility:
                        st.markdown(f"**Executive Responsibility:** {executive_responsibility}")

                    executive_quotes = priority_data.get('executive_quotes', [])
                    if executive_quotes:
                        st.markdown("**Executive Quotes:**")
                        for quote in executive_quotes:
                            quote_text = quote.get('quote', '')
                            exec_name = quote.get('executive', 'Unknown')
                            source = quote.get('source', '')
                            date = quote.get('date', '')
                            url = quote.get('url', '')

                            # Verification indicators
                            confidence_score = quote.get('confidence_score', None)
                            verified = quote.get('verified', None)
                            verification_status = quote.get('verification_status', None)

                            # Build confidence indicator
                            confidence_indicator = ""
                            if confidence_score is not None:
                                if confidence_score >= 0.8:
                                    confidence_indicator = f"🟢 High confidence ({confidence_score})"
                                elif confidence_score >= 0.6:
                                    confidence_indicator = f"🟡 Medium confidence ({confidence_score})"
                                else:
                                    confidence_indicator = f"🔴 Low confidence ({confidence_score})"

                            # Build verification indicator
                            verification_indicator = ""
                            if verified is not None:
                                if verified:
                                    verification_indicator = "✓ Verified"
                                else:
                                    verification_indicator = "⚠ Unverified"

                            st.markdown(f"- *\"{quote_text}\"*")
                            st.markdown(f"  — {exec_name}, {source}, {date}")
                            if confidence_indicator or verification_indicator:
                                indicators = " | ".join(filter(None, [confidence_indicator, verification_indicator]))
                                st.markdown(f"  {indicators}")
                            if url:
                                st.markdown(f"  Source: {url}")

                    business_impact = priority_data.get('business_impact', '')
                    if business_impact:
                        st.markdown(f"**Business Impact:** {business_impact}")

                    related_initiatives = priority_data.get('related_initiatives', [])
                    if related_initiatives:
                        if isinstance(related_initiatives, list):
                            st.markdown(f"**Related Initiatives:** {', '.join(related_initiatives)}")
                        else:
                            st.markdown(f"**Related Initiatives:** {related_initiatives}")

                    sources = priority_data.get('sources', [])
                    if sources:
                        if isinstance(sources, list):
                            st.markdown(f"**Sources:** {'; '.join(sources)}")
                        else:
                            st.markdown(f"**Sources:** {sources}")

                st.markdown("")
        else:
            st.info("No priority mapping data available in this analysis.")

    # ===== SLIDE 4: TOP 3 IDENTIFIED USE CASES =====
    with st.expander("📄 SLIDE 4: Top 3 Identified Use Cases", expanded=False):
        st.markdown("**Intelligent Agreement Management**")
        st.markdown("")

        if opportunities:
            for idx, opp in enumerate(opportunities[:3], start=1):
                use_case_name = opp.get('use_case_name', opp.get('title', f'Use Case {idx}'))
                capabilities = opp.get('capabilities', opp.get('description', 'N/A'))
                agreement_types = opp.get('agreement_types', [])
                risk_reduction = opp.get('risk_reduction', '')
                compliance = opp.get('compliance_benefits', '')
                metrics = opp.get('metrics', [])

                st.markdown(f"#### {idx}. {use_case_name}")
                st.markdown(f"**Capabilities:** {capabilities}")

                if agreement_types:
                    st.markdown(f"**Agreements:** {', '.join(agreement_types)}")

                if risk_reduction:
                    st.markdown(f"*Risk Reduction: {risk_reduction}*")

                if compliance:
                    st.markdown(f"*Compliance Benefits: {compliance}*")

                if metrics:
                    st.markdown("**Metrics:**")
                    cols = st.columns(min(len(metrics), 4))
                    for i, metric in enumerate(metrics[:4]):
                        with cols[i]:
                            st.metric(
                                label=metric.get('label', ''),
                                value=metric.get('value', 'N/A')
                            )

                # SLIDE NOTES: Executive Alignment
                exec_alignment = opp.get('executive_alignment', {})
                if exec_alignment:
                    st.markdown("---")
                    st.markdown("**SLIDE NOTES (Copy to Slide Notes):**")
                    st.markdown("**Executive Alignment:**")

                    priority_name = exec_alignment.get('priority_name', '')
                    if priority_name:
                        st.markdown(f"**Supports Priority:** {priority_name}")

                    exec_champion = exec_alignment.get('executive_champion', '')
                    if exec_champion:
                        st.markdown(f"**Executive Champion:** {exec_champion}")

                    alignment_statement = exec_alignment.get('alignment_statement', '')
                    if alignment_statement:
                        st.markdown(f"**Alignment:** {alignment_statement}")

                    supporting_quote = exec_alignment.get('supporting_quote', '')
                    if supporting_quote:
                        st.markdown(f"**Supporting Quote:** *\"{supporting_quote}\"*")

                        # If there's a full quote object with verification data
                        supporting_quote_data = exec_alignment.get('supporting_quote_data', {})
                        if supporting_quote_data:
                            confidence_score = supporting_quote_data.get('confidence_score', None)
                            verified = supporting_quote_data.get('verified', None)

                            # Build indicators
                            indicators = []
                            if confidence_score is not None:
                                if confidence_score >= 0.8:
                                    indicators.append(f"🟢 High confidence ({confidence_score})")
                                elif confidence_score >= 0.6:
                                    indicators.append(f"🟡 Medium confidence ({confidence_score})")
                                else:
                                    indicators.append(f"🔴 Low confidence ({confidence_score})")

                            if verified is not None:
                                if verified:
                                    indicators.append("✓ Verified")
                                else:
                                    indicators.append("⚠ Unverified")

                            if indicators:
                                st.markdown(f"  {' | '.join(indicators)}")

                st.markdown("")
        else:
            st.info("No optimization opportunities available in this analysis.")

    # ===== SLIDE 5: AGREEMENT LANDSCAPE MATRIX =====
    with st.expander("📄 SLIDE 5: Agreement Landscape Matrix", expanded=False):
        st.markdown("**Agreement types by business unit, volume, and complexity**")
        st.markdown("")

        if matrix_types:
            import pandas as pd
            table_data = []
            for agr in matrix_types[:18]:  # First 18
                table_data.append({
                    'Agreement Type': agr.get('type', 'Unknown'),
                    'Business Unit': agr.get('business_unit', 'Other'),
                    'Volume (1-10)': str(agr.get('volume', 5)),
                    'Complexity (1-10)': str(agr.get('complexity', 5))
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No agreement matrix data available in this analysis.")

    st.markdown("---")

    # ===== DISCOVERY QUESTIONS =====
    discovery_questions = analysis.get('discovery_questions', [])

    with st.expander("🎯 Discovery Questions", expanded=False):
        if discovery_questions:
            for idx, question in enumerate(discovery_questions, start=1):
                st.markdown(f"{idx}. {question}")
        else:
            st.info("Discovery questions not available for this analysis.")

    # ===== DOCUSIGN PRODUCT DETAILS =====
    docusign_product_summary = analysis.get('docusign_product_summary', {})
    products = docusign_product_summary.get('products', [])

    with st.expander("📦 DocuSign Product Recommendations", expanded=False):
        if products:
            for product in products:
                st.markdown(f"### {product.get('product_name', 'Unknown Product')}")
                st.markdown(f"**Category:** {product.get('category', 'N/A')}")

                use_cases = product.get('use_cases_enabled', [])
                if use_cases:
                    st.markdown(f"**Use Cases Enabled:**")
                    for uc in use_cases:
                        st.markdown(f"- {uc}")

                capabilities = product.get('key_capabilities_relevant', [])
                if capabilities:
                    st.markdown(f"**Key Capabilities:**")
                    for cap in capabilities:
                        st.markdown(f"- {cap}")

                estimated_value = product.get('estimated_value_enabled', 'N/A')
                st.markdown(f"**Estimated Value Enabled:** {estimated_value}")

                why_recommended = product.get('why_recommended', '')
                if why_recommended:
                    st.markdown(f"**Why Recommended:** {why_recommended}")

                st.markdown("---")

            # Implementation approach
            implementation_approach = docusign_product_summary.get('implementation_approach', '')
            if implementation_approach:
                st.markdown("### Implementation Approach")
                st.markdown(implementation_approach)
        else:
            st.info("DocuSign product recommendations not available for this analysis.")


def main():
    """Main application"""

    init_session_state()

    # Initialize Supabase storage
    if 'storage' not in st.session_state:
        st.session_state.storage = SupabaseStorageManager()

    # Header
    st.markdown('<h1 class="main-header">Agreement Map</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Company Analysis & Agreement Landscape Research</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        # Saved Analyses Section
        st.markdown('### <i class="fas fa-database"></i> Saved Analyses', unsafe_allow_html=True)

        # Custom CSS for fixed-width buttons that wrap together
        st.markdown("""
        <style>
        .analysis-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 0.5rem;
        }
        .analysis-text {
            flex: 1 1 auto;
            min-width: 150px;
        }
        .analysis-buttons {
            display: flex;
            gap: 0.25rem;
            flex-shrink: 0;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.session_state.storage.is_configured():
            saved_analyses = st.session_state.storage.list_analyses()

            if saved_analyses:
                st.caption(f"{len(saved_analyses)} saved analyses")

                # Search box for filtering analyses
                search_query = st.text_input("🔍 Search analyses", placeholder="Filter by company name...", label_visibility="collapsed", key="search_analyses")

                # Filter analyses if search query provided
                if search_query:
                    filtered_analyses = [a for a in saved_analyses if search_query.lower() in a['company_name'].lower()]
                else:
                    filtered_analyses = saved_analyses[:10]  # Show last 10

                for analysis in filtered_analyses:
                    # Use container with fixed-width buttons
                    container = st.container()

                    with container:
                        # Text in one column, buttons in another with min-width
                        col1, col2 = st.columns([7, 3])

                        with col1:
                            st.write(analysis["display_name"])

                        with col2:
                            # Buttons side by side with fixed width
                            btn_col1, btn_col2 = st.columns(2)

                            with btn_col1:
                                if st.button("📂", key=f"load_{analysis['id']}", help="Load analysis"):
                                    loaded_data = st.session_state.storage.load_analysis(analysis['id'])
                                    if loaded_data:
                                        st.session_state.analysis_result = loaded_data
                                        st.success(f"Loaded: {analysis['company_name']}")
                                        st.rerun()

                            with btn_col2:
                                if st.button("🗑️", key=f"del_{analysis['id']}", help="Delete analysis"):
                                    if st.session_state.storage.delete_analysis(analysis['id']):
                                        st.success("Deleted!")
                                        st.rerun()
            else:
                st.caption("No saved analyses yet")
        else:
            st.caption("Supabase not configured")
            st.caption("Add Supabase credentials to .streamlit/secrets.toml")

        st.markdown("---")

        # About & Features Section (plain, not in expander)
        st.markdown('### <i class="fas fa-info-circle"></i> About & Features', unsafe_allow_html=True)
        st.markdown("""
        This tool uses AI to research companies and generate comprehensive agreement landscape analyses.

        **Features:**
        - Parallel research agents (4x faster)
        - Company profile analysis
        - Business unit breakdown
        - Agreement landscape mapping
        - Optimization opportunities
        - Interactive visualization
        - Web search via Tavily (optional)
        - Save to Supabase (optional)
        """)

    # Load API keys from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    tavily_key = os.environ.get('TAVILY_API_KEY')

    # Main content
    if not api_key:
        st.markdown('<div class="warning-box"><i class="fas fa-exclamation-triangle"></i> OpenAI API key not found. Please add OPENAI_API_KEY to your .env file or environment variables.</div>', unsafe_allow_html=True)
        return

    # Company input
    col1, col2 = st.columns([3, 1])

    with col1:
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Salesforce, Microsoft, Stripe",
            help="Enter the name of the company you want to analyze"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("Analyze Company", type="primary", use_container_width=True)

    # Run analysis
    if analyze_button and company_name:
        st.markdown(f'<div class="info-box">Starting analysis for <strong>{company_name}</strong>...</div>', unsafe_allow_html=True)

        # Create progress containers
        st.markdown('### <i class="fas fa-chart-bar" style="color: rgb(255, 75, 75);"></i> Research Progress', unsafe_allow_html=True)

        # Define research categories with metadata
        research_categories = [
            {'key': 'profile', 'title': 'Company Profile', 'icon': 'fas fa-building'},
            {'key': 'business_units', 'title': 'Business Units', 'icon': 'fas fa-industry'},
            {'key': 'priorities', 'title': 'Strategic Priorities', 'icon': 'fas fa-bullseye'},
            {'key': 'landscape', 'title': 'Agreement Landscape', 'icon': 'fas fa-chart-bar'},
            {'key': 'deep_research', 'title': 'Deep Research', 'icon': 'fas fa-search'},
            {'key': 'opportunities', 'title': 'Opportunities', 'icon': 'fas fa-lightbulb'},
            {'key': 'matrix', 'title': 'Agreement Matrix', 'icon': 'fas fa-table'}
        ]

        col1, col2 = st.columns(2)

        progress_containers = {}

        # Create containers and render initial "not-started" state for all categories
        for i, category in enumerate(research_categories):
            # Alternate between columns
            with col1 if i % 2 == 0 else col2:
                container = st.empty()
                progress_containers[category['key']] = container
                # Render initial not-started state
                container.markdown(
                    render_research_status(
                        category['key'],
                        category['title'],
                        category['icon'],
                        state='not-started'
                    ),
                    unsafe_allow_html=True
                )

        # Run research with progress tracking
        try:
            # Run async research (no status accordion)
            result = asyncio.run(run_research(company_name, api_key, tavily_key, progress_containers, None))

            st.session_state.analysis_result = result

            # Auto-save to Supabase
            if st.session_state.storage.is_configured():
                try:
                    if st.session_state.storage.save_analysis(company_name, result):
                        st.markdown('<div class="success-box"><i class="fas fa-check-circle" style="color: rgb(255, 75, 75);"></i> Analysis complete and saved to Supabase!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="success-box"><i class="fas fa-check-circle" style="color: rgb(255, 75, 75);"></i> Analysis complete!</div>', unsafe_allow_html=True)
                        st.warning("Could not save to Supabase")
                except Exception as save_error:
                    st.markdown('<div class="success-box"><i class="fas fa-check-circle" style="color: rgb(255, 75, 75);"></i> Analysis complete!</div>', unsafe_allow_html=True)
                    st.warning(f"Save to Supabase failed: {save_error}")
            else:
                st.markdown('<div class="success-box"><i class="fas fa-check-circle" style="color: rgb(255, 75, 75);"></i> Analysis complete!</div>', unsafe_allow_html=True)
                st.info("Configure Supabase to save analyses")

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.exception(e)
            return

    # Display results
    if st.session_state.analysis_result:
        analysis = st.session_state.analysis_result
        company_analyzed = analysis.get('_meta', {}).get('company_name', 'Unknown')

        st.markdown("---")

        # Header
        st.markdown(f"## {company_analyzed}")

        # Word Document Export Button (above Analysis Summary)
        st.markdown("""
        <style>
        button[kind="secondary"] p {
            text-transform: none !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Full-width Word export button
        with st.spinner("Creating Word document..."):
            try:
                # Create Word document with slide content
                export_manager = ExportManager()
                docx_bytes = export_manager.create_docx_content(
                    company_analyzed,
                    analysis
                )

                # Provide download button
                filename = f"{company_analyzed.replace(' ', '_').lower()}_slide_content.docx"

                st.download_button(
                    label="Download Word Doc",
                    data=docx_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="download_docx_main_top"
                )

                st.success("Word document created successfully!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")
                st.exception(e)

        # Summary metrics
        display_analysis_summary(analysis)

        st.markdown("---")

        # Tab navigation: Main Analysis vs Background & Details
        tab1, tab2 = st.tabs(["📊 Main Analysis (Copy/Paste Content)", "📋 Background & Details"])

        with tab1:
            # MAIN ANALYSIS TAB - Slide-based layout for easy copy/paste
            display_main_analysis_slides(analysis)

        with tab2:
            # BACKGROUND & DETAILS TAB - Detailed information
            display_company_profile(analysis.get('company_profile', {}))
            display_business_units(analysis.get('business_units', []))
            display_deep_research_findings(analysis.get('deep_research_findings', {}))
            display_agreement_landscape_by_function(analysis.get('agreement_landscape_by_function', {}))
            display_opportunities(analysis.get('optimization_opportunities', []))
            display_agreement_matrix(analysis.get('agreement_matrix', {}))


if __name__ == "__main__":
    main()
