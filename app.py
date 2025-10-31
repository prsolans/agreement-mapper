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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
        background-color: #bee3f8;
        border-left: 4px solid #3182ce;
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


async def run_research(company_name: str, api_key: str, progress_containers: dict, status_obj):
    """Execute the research asynchronously with progress tracking"""

    agent = CompanyResearchAgent(api_key=api_key)

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


def display_opportunities(opportunities: list):
    """Display optimization opportunities"""

    with st.expander("Optimization Opportunities", expanded=False):
        for i, opp in enumerate(opportunities, 1):
            priority = opp.get('implementation', {}).get('priority', 'medium')
            priority_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(priority, '⚪')

            st.markdown(f"### {priority_color} {i}. {opp.get('title', 'Unknown')}")
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
                        st.markdown(f"**🔧 Systems:** {', '.join(systems_impacted)}")

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
                        use_container_width=True
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
                        use_container_width=True
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
                    use_container_width=True
                )

                st.success("Word document created successfully!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")
                st.exception(e)


def main():
    """Main application"""

    init_session_state()

    # Header
    st.markdown('<h1 class="main-header">Agreement Map</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Company Analysis & Agreement Landscape Research</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown('### <i class="fas fa-cog" style="color: rgb(255, 75, 75);"></i> Configuration', unsafe_allow_html=True)

        # Check if API key is already in environment
        env_api_key = os.environ.get('OPENAI_API_KEY')

        if env_api_key:
            st.success("API Key loaded from .env file")
            api_key = env_api_key
        else:
            # API Key input
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys"
            )

            # Store in environment if provided
            if api_key:
                os.environ['OPENAI_API_KEY'] = api_key

        st.markdown("---")

        st.markdown('### <i class="fas fa-book" style="color: rgb(255, 75, 75);"></i> About', unsafe_allow_html=True)
        st.markdown("""
        This tool uses AI to research companies and generate comprehensive agreement landscape analyses.

        **Features:**
        - Parallel research agents (4x faster)
        - Company profile analysis
        - Business unit breakdown
        - Agreement landscape mapping
        - Optimization opportunities
        - Interactive visualization
        """)

        st.markdown("---")

    # Main content
    if not api_key:
        st.markdown('<div class="warning-box"><i class="fas fa-exclamation-triangle"></i> Please enter your OpenAI API key in the sidebar to get started.</div>', unsafe_allow_html=True)
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
            result = asyncio.run(run_research(company_name, api_key, progress_containers, None))

            st.session_state.analysis_result = result
            st.markdown('<div class="success-box"><i class="fas fa-check-circle" style="color: rgb(255, 75, 75);"></i> Analysis complete!</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.exception(e)
            return

    # Display results
    if st.session_state.analysis_result:
        analysis = st.session_state.analysis_result
        company_analyzed = analysis.get('_meta', {}).get('company_name', 'Unknown')

        st.markdown("---")

        # Header with export options
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"## {company_analyzed}")

        with col2:
            export_option = st.selectbox(
                "Export",
                ["Download as...", "JSON", "PNG Image", "PowerPoint", "Word Doc"],
                label_visibility="collapsed"
            )

        # Word Document Export Button (above Analysis Summary)
        st.markdown("""
        <style>
        button[kind="secondary"] p {
            text-transform: none !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif !important;
        }
        </style>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            word_button = st.button("Export Slide Content as Word Doc", type="secondary")

        if word_button:
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
                        use_container_width=True
                    )

                    st.success("Word document created successfully!")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    st.exception(e)

        # Summary metrics
        display_analysis_summary(analysis)

        # Export handling
        if export_option == "JSON":
            json_str = json.dumps(analysis, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"{company_analyzed.replace(' ', '_').lower()}_analysis.json",
                mime="application/json",
                use_container_width=True
            )

        elif export_option == "PNG Image":
            with st.spinner("Generating high-resolution image..."):
                try:
                    # Read visualization HTML
                    viz_path = Path(__file__).parent / "visualization.html"

                    if not viz_path.exists():
                        st.error("Visualization file not found")
                    else:
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
                            use_container_width=True
                        )

                        st.success("PNG generated successfully!")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    st.exception(e)

        elif export_option == "PowerPoint":
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
                        use_container_width=True
                    )

                    st.success("PowerPoint created successfully! (Import to Google Slides)")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    st.exception(e)

        elif export_option == "Word Doc":
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
                        use_container_width=True
                    )

                    st.success("Word document created successfully!")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    st.exception(e)

        st.markdown("---")

        # Detailed sections
        display_company_profile(analysis.get('company_profile', {}))
        display_business_units(analysis.get('business_units', []))
        display_agreement_landscape_by_function(analysis.get('agreement_landscape_by_function', {}))
        display_opportunities(analysis.get('optimization_opportunities', []))
        display_agreement_matrix(analysis.get('agreement_matrix', {}))


if __name__ == "__main__":
    main()
